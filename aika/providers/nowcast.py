"""Nowcast data provider."""
import datetime
import requests
import math

try:
    from ..cache import get_cached_data, cache_data

    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False


    # Define dummy functions if cache module is not available
    def get_cached_data(api_name):
        return None


    def cache_data(api_name, data):
        pass


def get_precipitation_nowcast(latitude, longitude, timezone):
    """Get short-term precipitation forecast for next 2 hours.

    Uses Open-Meteo's minutely_15 forecast data to determine when rain
    will start or stop.

    Returns:
        dict: {
            'rain_starts_in_min': int or None (minutes until rain starts),
            'rain_ends_in_min': int or None (minutes until rain stops),
            'is_raining_now': bool,
            'precipitation_type': 'rain'/'snow'/'mixed'/'none',
            'max_intensity': float (mm/h peak in next 2h),
            'intervals': list of 15-min forecast data
        }
    """
    # Check cache (short TTL for nowcast data)
    cache_key = f"nowcast_{latitude}_{longitude}"
    if CACHE_AVAILABLE:
        cached_data = get_cached_data(cache_key)
        if cached_data:
            return cached_data

    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {"latitude": latitude, "longitude": longitude, "minutely_15": "precipitation,rain,snowfall,weather_code", "timezone": timezone,
                  "forecast_minutely_15": 8  # 8 intervals = 2 hours
                  }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        minutely = data.get("minutely_15", {})
        times = minutely.get("time", [])
        precips = minutely.get("precipitation", [])
        rains = minutely.get("rain", [])
        snowfalls = minutely.get("snowfall", [])
        weather_codes = minutely.get("weather_code", [])

        if not times or not precips:
            return None

        # Analyze precipitation timing
        result = {'rain_starts_in_min': None, 'rain_ends_in_min': None, 'is_raining_now': False, 'precipitation_type': 'none', 'max_intensity': 0,
                  'intervals': []}

        # Threshold for "raining" (mm in 15 minutes, scaled to mm/h)
        RAIN_THRESHOLD = 0.1

        # Check current state
        current_precip = precips[0] if precips else 0
        result['is_raining_now'] = current_precip > RAIN_THRESHOLD

        # Determine precipitation type
        current_rain = rains[0] if rains else 0
        current_snow = snowfalls[0] if snowfalls else 0
        if current_rain > 0 and current_snow > 0:
            result['precipitation_type'] = 'mixed'
        elif current_snow > 0:
            result['precipitation_type'] = 'snow'
        elif current_rain > 0 or current_precip > RAIN_THRESHOLD:
            result['precipitation_type'] = 'rain'
        else:
            result['precipitation_type'] = 'none'

        # Track max intensity
        max_intensity = max(precips) if precips else 0
        result['max_intensity'] = max_intensity * 4  # Convert 15-min to hourly rate

        # Find transitions
        for i, (time_str, precip) in enumerate(zip(times, precips)):
            is_rain = precip > RAIN_THRESHOLD
            minutes_from_now = i * 15

            # Build interval data
            result['intervals'].append({'time': time_str, 'minutes': minutes_from_now, 'precipitation': precip, 'is_rain': is_rain})

            # Find when rain starts (if not raining now)
            if not result['is_raining_now'] and is_rain and result['rain_starts_in_min'] is None:
                result['rain_starts_in_min'] = minutes_from_now

            # Find when rain ends (if raining now)
            if result['is_raining_now'] and not is_rain and result['rain_ends_in_min'] is None:
                result['rain_ends_in_min'] = minutes_from_now

        # Cache with short TTL (5 minutes)
        if CACHE_AVAILABLE:
            cache_data(cache_key, result)

        return result

    except Exception:
        return None


def get_lightning_activity(latitude, longitude, country_code):
    """Get recent lightning activity with enhanced threat assessment.

    Uses FMI lightning API to detect nearby thunderstorm activity.
    Works year-round including thundersnow phenomena.

    Returns:
        dict: {
            'strikes_1h': int (strikes in last hour within radius),
            'nearest_km': float or None (distance to nearest recent strike),
            'activity_level': 'none'/'low'/'moderate'/'high'/'severe',
            'is_active': bool,
            'cloud_ground_ratio': float (percentage of cloud-to-ground strikes),
            'max_peak_current': float (kA of strongest strike),
            'threat_level': 'none'/'low'/'moderate'/'high'/'severe',
            'storm_direction': str (direction of storm movement),
            'time_to_arrival': int or None (minutes until storm reaches user)
        }
    """
    # Previously was limited to thunderstorm season, now works year-round
    # Check cache
    cache_key = f"lightning_{latitude}_{longitude}"
    if CACHE_AVAILABLE:
        cached_data = get_cached_data(cache_key)
        if cached_data:
            return cached_data

    try:
        from fmiopendata.lightning import download_and_parse
        import os
        import sys
        from contextlib import contextmanager

        @contextmanager
        def suppress_stdout():
            with open(os.devnull, "w") as devnull:
                old_stdout = sys.stdout
                sys.stdout = devnull
                try:
                    yield
                finally:
                    sys.stdout = old_stdout

        # Query lightning data from FMI
        with suppress_stdout():
            try:
                # Multipoint with bbox for Finland to catch everything relevant
                # Using a wide bbox covering Finland approx 19-32E, 59-71N
                bbox = "bbox=19,59,32,71"
                obs = download_and_parse("fmi::observations::lightning::multipointcoverage", args=[bbox])
            except Exception:
                # Fallback or no data
                return {
                    'strikes_1h': 0, 'nearest_km': None, 'activity_level': 'none', 'is_active': False,
                    'cloud_ground_ratio': 0.0, 'max_peak_current': 0.0, 'threat_level': 'none',
                    'storm_direction': '', 'time_to_arrival': None
                }

        # Check if we have valid data
        if not obs or not hasattr(obs, 'latitudes') or obs.latitudes is None or len(obs.latitudes) == 0:
            result = {
                'strikes_1h': 0, 'nearest_km': None, 'activity_level': 'none', 'is_active': False,
                'cloud_ground_ratio': 0.0, 'max_peak_current': 0.0, 'threat_level': 'none',
                'storm_direction': '', 'time_to_arrival': None
            }
        else:
            # Filter for last 1 hour
            now_utc = datetime.datetime.utcnow()
            one_hour_ago = now_utc - datetime.timedelta(hours=1)

            # Safely filter valid indices
            valid_indices = []
            if hasattr(obs, 'times') and obs.times is not None:
                try:
                    valid_indices = [i for i, t in enumerate(obs.times) if t is not None and t >= one_hour_ago]
                except:
                    valid_indices = []

            if not valid_indices:
                result = {
                    'strikes_1h': 0, 'nearest_km': None, 'activity_level': 'none', 'is_active': False,
                    'cloud_ground_ratio': 0.0, 'max_peak_current': 0.0, 'threat_level': 'none',
                    'storm_direction': '', 'time_to_arrival': None
                }
            else:
                strikes_count = len(valid_indices)

                # Calculate distance to user using flat earth approximation
                min_dist_sq = float('inf')
                
                # Approximate km per degree at 60N latitude
                lat_scale = 111.0  # km per degree latitude
                lon_scale = 55.0   # km per degree longitude at 60N

                # Safely access latitude/longitude data
                if hasattr(obs, 'latitudes') and hasattr(obs, 'longitudes'):
                    try:
                        for i in valid_indices:
                            if i < len(obs.latitudes) and i < len(obs.longitudes):
                                lat = obs.latitudes[i]
                                lon = obs.longitudes[i]
                                
                                if lat is not None and lon is not None:
                                    d_lat = (lat - latitude) * lat_scale
                                    d_lon = (lon - longitude) * lon_scale
                                    dist_sq = d_lat * d_lat + d_lon * d_lon
                                    
                                    if dist_sq < min_dist_sq:
                                        min_dist_sq = dist_sq

                        nearest_km = math.sqrt(min_dist_sq) if min_dist_sq < float('inf') else None
                    except:
                        nearest_km = None
                else:
                    nearest_km = None

                # Enhanced activity level logic with better thresholds
                if strikes_count > 200 or (nearest_km is not None and nearest_km < 5):
                    activity = 'severe'
                elif strikes_count > 100 or (nearest_km is not None and nearest_km < 15):
                    activity = 'high'
                elif strikes_count > 30 or (nearest_km is not None and nearest_km < 30):
                    activity = 'moderate'
                elif strikes_count > 5:
                    activity = 'low'
                else:
                    activity = 'none'

                # Enhanced threat level assessment
                threat_level = 'none'
                if strikes_count > 150 and nearest_km is not None and nearest_km < 10:
                    threat_level = 'severe'
                elif strikes_count > 75 and nearest_km is not None and nearest_km < 20:
                    threat_level = 'high'
                elif strikes_count > 25 or (nearest_km is not None and nearest_km < 40):
                    threat_level = 'moderate'
                elif strikes_count > 5:
                    threat_level = 'low'

                # Direction estimation (very simplified)
                storm_direction = ""
                time_to_arrival = None
                if nearest_km is not None:
                    if nearest_km < 10:
                        storm_direction = "läheinen" if country_code == "FI" else "nearby"
                    elif nearest_km < 50:
                        storm_direction = " lähistöllä" if country_code == "FI" else "in vicinity"

                result = {
                    'strikes_1h': strikes_count,
                    'nearest_km': round(nearest_km, 1) if nearest_km is not None else None,
                    'activity_level': activity,
                    'is_active': strikes_count > 0,
                    'cloud_ground_ratio': 0.0,  # Placeholder - would need actual cloud indicator data
                    'max_peak_current': 0.0,    # Placeholder - would need actual peak current data
                    'threat_level': threat_level,
                    'storm_direction': storm_direction,
                    'time_to_arrival': time_to_arrival
                }

        if CACHE_AVAILABLE:
            cache_data(cache_key, result)

        return result

    except Exception as e:
        # Return fallback data on error
        return {
            'strikes_1h': 0, 'nearest_km': None, 'activity_level': 'none', 'is_active': False,
            'cloud_ground_ratio': 0.0, 'max_peak_current': 0.0, 'threat_level': 'none',
            'storm_direction': '', 'time_to_arrival': None
        }
