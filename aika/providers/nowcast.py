"""Nowcast data provider."""
import datetime
import requests

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
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "minutely_15": "precipitation,rain,snowfall,weather_code",
            "timezone": timezone,
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
        result = {
            'rain_starts_in_min': None,
            'rain_ends_in_min': None,
            'is_raining_now': False,
            'precipitation_type': 'none',
            'max_intensity': 0,
            'intervals': []
        }

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
            result['intervals'].append({
                'time': time_str,
                'minutes': minutes_from_now,
                'precipitation': precip,
                'is_rain': is_rain
            })

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
    """Get recent lightning activity (Finland only, seasonal May-September).

    Uses FMI lightning API to detect nearby thunderstorm activity.

    Returns:
        dict: {
            'strikes_1h': int (strikes in last hour within radius),
            'nearest_km': float or None (distance to nearest recent strike),
            'activity_level': 'none'/'low'/'moderate'/'high',
            'is_active': bool
        }
    """
    # Only available in Finland during thunderstorm season
    if country_code != 'FI':
        return None

    # Check if it's thunderstorm season (May-September)
    now = datetime.datetime.now()
    if now.month < 5 or now.month > 9:
        return None

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
        # Use simple query first as it's lighter
        # Suppress "No observations found" message from the library
        with suppress_stdout():
            try:
                # Multipoint with bbox for Finland to catch everything relevant
                # Using a wide bbox covering Finland approx 19-32E, 59-71N
                bbox = "bbox=19,59,32,71"
                obs = download_and_parse("fmi::observations::lightning::multipointcoverage", args=[bbox])
            except Exception:
                # Fallback or no data
                return None

        if not obs or obs.latitudes is None or len(obs.latitudes) == 0:
             result = {
                'strikes_1h': 0,
                'nearest_km': None,
                'activity_level': 'none',
                'is_active': False
            }
        else:
            # Calculate distance to user
            # Simple Haversine approximation or Euclidian for short distances
            # We have arrays of lats/lons
            
            # Filter for last 1 hour
            now_utc = datetime.datetime.utcnow()
            one_hour_ago = now_utc - datetime.timedelta(hours=1)
            
            # Filter valid indices
            valid_indices = [i for i, t in enumerate(obs.times) if t >= one_hour_ago]
            
            if not valid_indices:
                 result = {
                    'strikes_1h': 0,
                    'nearest_km': None,
                    'activity_level': 'none',
                    'is_active': False
                }
            else:
                strikes_count = len(valid_indices)
                
                # Find nearest
                min_dist_sq = float('inf')
                
                # Simple flat earth approx is enough for "nearest" ranking usually, 
                # but let's do a rough km conversion: 1 deg lat ~ 111km, 1 deg lon ~ 55km (at 60N)
                lat_scale = 111.0
                lon_scale = 55.0
                
                for i in valid_indices:
                    d_lat = (obs.latitudes[i] - latitude) * lat_scale
                    d_lon = (obs.longitudes[i] - longitude) * lon_scale
                    dist_sq = d_lat*d_lat + d_lon*d_lon
                    if dist_sq < min_dist_sq:
                        min_dist_sq = dist_sq
                
                nearest_km = math.sqrt(min_dist_sq)
                
                # Activity level logic
                if strikes_count > 100 or nearest_km < 10:
                    activity = 'high'
                elif strikes_count > 20 or nearest_km < 50:
                    activity = 'moderate'
                else:
                    activity = 'low'
                    
                result = {
                    'strikes_1h': strikes_count,
                    'nearest_km': round(nearest_km, 1),
                    'activity_level': activity,
                    'is_active': True
                }

        if CACHE_AVAILABLE:
            cache_data(cache_key, result)

        return result

    except Exception:
        return None
