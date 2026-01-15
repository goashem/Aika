"""Weather data fetching and processing."""
import datetime
import math
import requests

try:
    from fmiopendata.wfs import download_stored_query

    FMI_AVAILABLE = True
except ImportError:
    FMI_AVAILABLE = False

try:
    from aika.cache import get_cached_data, cache_data
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False
    # Define dummy functions if cache module is not available
    def get_cached_data(api_name):
        return None
    def cache_data(api_name, data):
        pass


def degrees_to_compass(degrees):
    """Convert wind direction in degrees to compass direction key.

    Returns a key like 'N', 'NNE', 'NE', etc. that can be used
    to look up the localized direction name.
    """
    if degrees is None:
        return None

    # Normalize to 0-360
    degrees = degrees % 360

    # 16-point compass, each sector is 22.5 degrees
    # Offset by 11.25 so N is centered at 0
    directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']

    index = round(degrees / 22.5) % 16
    return directions[index]


def get_weather_data(latitude, longitude, timezone):
    """Get weather information from FMI and Open-Meteo APIs."""
    # Check cache first
    cache_key = f"weather_{latitude}_{longitude}"
    if CACHE_AVAILABLE:
        cached_data = get_cached_data(cache_key)
        if cached_data:
            return cached_data
    
    try:
        # Try FMI Open Data service first
        if FMI_AVAILABLE:
            try:
                bbox_margin = 0.5
                args = [f"bbox={longitude - bbox_margin},{latitude - bbox_margin},{longitude + bbox_margin},{latitude + bbox_margin}", "timeseries=True", ]

                obs = download_stored_query("fmi::observations::weather::multipointcoverage", args=args)

                if obs.data:
                    station = sorted(obs.data.keys())[0]
                    station_data = obs.data[station]

                    def get_latest_value(key):
                        if key in station_data:
                            vals = station_data[key]["values"]
                            if vals:
                                val = vals[-1]
                                if val is not None and not (isinstance(val, float) and math.isnan(val)):
                                    return val
                        return None

                    fmi_data = {"temperature": get_latest_value("Air temperature"), "description": "ei saatavilla",
                                "humidity": get_latest_value("Relative humidity"), "pressure": get_latest_value("Pressure (msl)"),
                                "wind_speed": get_latest_value("Wind speed"), "wind_direction": get_latest_value("Wind direction"),
                                "gust_speed": get_latest_value("Gust speed"), "visibility": get_latest_value("Horizontal visibility"),
                                "precip_intensity": get_latest_value("Precipitation intensity"), "snow_depth": get_latest_value("Snow depth"),
                                "apparent_temp": None, "precipitation_probability": None, "weather_code": None}

                    # Supplement missing data from Open-Meteo
                    try:
                        url = "https://api.open-meteo.com/v1/forecast"
                        params = {"latitude": latitude, "longitude": longitude,
                                  "current": "apparent_temperature,wind_speed_10m,wind_direction_10m,wind_gusts_10m",
                                  "hourly": "precipitation_probability,weathercode", "timezone": timezone, "forecast_hours": 1, "wind_speed_unit": "ms", }
                        response = requests.get(url, params=params, timeout=10)
                        response.raise_for_status()
                        data = response.json()

                        current = data.get("current", {})
                        hourly = data.get("hourly", {})

                        fmi_data["apparent_temp"] = current.get("apparent_temperature")

                        if fmi_data["wind_speed"] is None:
                            fmi_data["wind_speed"] = current.get("wind_speed_10m")
                        if fmi_data["wind_direction"] is None:
                            fmi_data["wind_direction"] = current.get("wind_direction_10m")
                        if fmi_data["gust_speed"] is None:
                            fmi_data["gust_speed"] = current.get("wind_gusts_10m")

                        if fmi_data["precipitation_probability"] is None:
                            if hourly.get("precipitation_probability"):
                                fmi_data["precipitation_probability"] = hourly["precipitation_probability"][0]
                        if fmi_data["weather_code"] is None:
                            if hourly.get("weathercode"):
                                fmi_data["weather_code"] = hourly["weathercode"][0]
                    except:
                        pass

                    # Cache the data before returning
                    if CACHE_AVAILABLE:
                        cache_key = f"weather_{latitude}_{longitude}"
                        cache_data(cache_key, fmi_data)
                    return fmi_data
            except Exception:
                pass

        # Use Open-Meteo as a full fallback
        try:
            url = "https://api.open-meteo.com/v1/forecast"
            params = {"latitude": latitude, "longitude": longitude,
                      "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,pressure_msl,wind_speed_10m,wind_direction_10m,wind_gusts_10m",
                      "hourly": "precipitation_probability,weathercode", "timezone": timezone, "forecast_hours": 1, "wind_speed_unit": "ms", }

            response = requests.get(url, params=params, timeout=20)
            response.raise_for_status()
            data = response.json()

            current = data.get("current", {})
            hourly = data.get("hourly", {})

            open_meteo_data = {"temperature": current.get("temperature_2m"), "apparent_temp": current.get("apparent_temperature"), "description": "ei saatavilla",
                               "humidity": current.get("relative_humidity_2m"), "pressure": current.get("pressure_msl"), "wind_speed": current.get("wind_speed_10m"),
                               "wind_direction": current.get("wind_direction_10m"), "gust_speed": current.get("wind_gusts_10m"), "visibility": None,
                               "precip_intensity": current.get("precipitation"), "snow_depth": None,
                               "precipitation_probability": hourly.get("precipitation_probability", [None])[0], "weather_code": hourly.get("weathercode", [None])[0]}
            
            # Cache the data before returning
            if CACHE_AVAILABLE:
                cache_key = f"weather_{latitude}_{longitude}"
                cache_data(cache_key, open_meteo_data)
                
            return open_meteo_data
        except Exception:
            pass

    except Exception:
        pass

    # Return sample data if both APIs fail
    fallback_data = {"temperature": -14.0, "apparent_temp": -20.0, "description": "selkeaa", "humidity": 90, "pressure": 1025, "wind_speed": 3.2, "wind_direction": 180,
                     "gust_speed": 5.0, "visibility": None, "precip_intensity": 0, "snow_depth": None, "precipitation_probability": 10, "weather_code": 0}
    
    # Cache the data before returning
    if CACHE_AVAILABLE:
        cache_key = f"weather_{latitude}_{longitude}"
        cache_data(cache_key, fallback_data)
        
    return fallback_data


def get_weather_description(weather_code, language):
    """Translate Open-Meteo weather code to description."""
    if weather_code is None:
        return "ei saatavilla" if language == 'fi' else "not available"

    weather_codes_fi = {0: "selkeää", 1: "enimmäkseen selkeää", 2: "puolipilvistä", 3: "pilvistä", 45: "sumua", 48: "huurtuvaa sumua",
                        51: "kevyttä tihkusadetta", 53: "tihkusadetta", 55: "tiheää tihkusadetta", 56: "jäätävää tihkua", 57: "tiheää jäätävää tihkua",
                        61: "kevyttä sadetta", 63: "sadetta", 65: "rankkasadetta", 66: "jäätävää sadetta", 67: "rankkaa jäätävää sadetta",
                        71: "kevyttä lumisadetta", 73: "lumisadetta", 75: "tiheää lumisadetta", 77: "lumijyväsiä", 80: "kevyitä sadekuuroja", 81: "sadekuuroja",
                        82: "rankkoja sadekuuroja", 85: "kevyitä lumikuuroja", 86: "rankkoja lumikuuroja", 95: "ukkosta", 96: "ukkosta ja rakeita",
                        99: "ukkosta ja rankkoja rakeita"}

    weather_codes_en = {0: "clear sky", 1: "mainly clear", 2: "partly cloudy", 3: "overcast", 45: "fog", 48: "depositing rime fog", 51: "light drizzle",
                        53: "drizzle", 55: "dense drizzle", 56: "light freezing drizzle", 57: "dense freezing drizzle", 61: "light rain", 63: "rain",
                        65: "heavy rain", 66: "light freezing rain", 67: "heavy freezing rain", 71: "light snow", 73: "snow", 75: "heavy snow",
                        77: "snow grains", 80: "light rain showers", 81: "rain showers", 82: "violent rain showers", 85: "light snow showers",
                        86: "heavy snow showers", 95: "thunderstorm", 96: "thunderstorm with hail", 99: "thunderstorm with heavy hail"}

    codes = weather_codes_fi if language == 'fi' else weather_codes_en
    return codes.get(weather_code, "tuntematon" if language == 'fi' else "unknown")


def get_uv_index(latitude, longitude):
    """Get UV index from Open-Meteo API."""
    # Check cache first
    cache_key = f"uv_index_{latitude}_{longitude}"
    if CACHE_AVAILABLE:
        cached_data = get_cached_data(cache_key)
        if cached_data is not None:
            return cached_data
    
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {"latitude": latitude, "longitude": longitude, "hourly": "uv_index", "timezone": "Europe/Helsinki", "forecast_days": 1, }

        response = requests.get(url, params=params, timeout=20)
        response.raise_for_status()
        data = response.json()

        uv_index = data["hourly"]["uv_index"][0] if data["hourly"]["uv_index"] else 0.5
        # Cache the data before returning
        if CACHE_AVAILABLE:
            cache_data(cache_key, uv_index)
        return uv_index
    except:
        fallback_value = 0.5
        # Cache the data before returning
        if CACHE_AVAILABLE:
            cache_data(cache_key, fallback_value)
        return fallback_value


def get_air_quality(latitude, longitude, timezone):
    """Get air quality data from Open-Meteo Air Quality API."""
    # Check cache first
    cache_key = f"air_quality_{latitude}_{longitude}"
    if CACHE_AVAILABLE:
        cached_data = get_cached_data(cache_key)
        if cached_data:
            return cached_data
    
    try:
        url = "https://air-quality-api.open-meteo.com/v1/air-quality"
        params = {"latitude": latitude, "longitude": longitude, "current": "european_aqi,pm10,pm2_5", "timezone": timezone}

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        current = data.get("current", {})
        european_aqi = current.get("european_aqi")
        pm10 = current.get("pm10")
        pm2_5 = current.get("pm2_5")

        aqi_simple = None
        if european_aqi is not None:
            if european_aqi <= 20:
                aqi_simple = 1
            elif european_aqi <= 40:
                aqi_simple = 2
            elif european_aqi <= 60:
                aqi_simple = 3
            elif european_aqi <= 80:
                aqi_simple = 4
            else:
                aqi_simple = 5

        air_quality_data = {"aqi": aqi_simple, "european_aqi": european_aqi, "pm2_5": pm2_5, "pm10": pm10}
        # Cache the data before returning
        if CACHE_AVAILABLE:
            cache_data(cache_key, air_quality_data)
        return air_quality_data
    except:
        fallback_data = {"aqi": None, "european_aqi": None, "pm2_5": None, "pm10": None}
        # Cache the data before returning
        if CACHE_AVAILABLE:
            cache_data(cache_key, fallback_data)
        return fallback_data


def get_solar_radiation(latitude, longitude, timezone):
    """Get solar radiation and cloud cover data from Open-Meteo API."""
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {"latitude": latitude, "longitude": longitude,
                  "current": "cloud_cover,shortwave_radiation,direct_radiation,diffuse_radiation,direct_normal_irradiance,global_tilted_irradiance",
                  "timezone": timezone}

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        current = data.get("current", {})

        return {"cloud_cover": current.get("cloud_cover"), "ghi": current.get("shortwave_radiation"), "dni": current.get("direct_normal_irradiance"),
                "dhi": current.get("diffuse_radiation"), "gti": current.get("global_tilted_irradiance"), "direct": current.get("direct_radiation")}
    except:
        return {"cloud_cover": None, "ghi": None, "dni": None, "dhi": None, "gti": None, "direct": None}


def get_marine_data(latitude, longitude, timezone):
    """Get marine/wave data from Open-Meteo Marine API."""
    try:
        url = "https://marine-api.open-meteo.com/v1/marine"
        params = {"latitude": latitude, "longitude": longitude, "current": "wave_height,wave_direction,wave_period,wind_wave_height,swell_wave_height",
                  "timezone": timezone}

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        current = data.get("current", {})
        return {"wave_height": current.get("wave_height"), "wave_direction": current.get("wave_direction"), "wave_period": current.get("wave_period"),
                "wind_wave_height": current.get("wind_wave_height"), "swell_wave_height": current.get("swell_wave_height")}
    except:
        return {"wave_height": None, "wave_direction": None, "wave_period": None, "wind_wave_height": None, "swell_wave_height": None}


def get_flood_data(latitude, longitude):
    """Get river discharge/flood data from Open-Meteo Flood API."""
    try:
        url = "https://flood-api.open-meteo.com/v1/flood"
        params = {"latitude": latitude, "longitude": longitude, "daily": "river_discharge,river_discharge_mean,river_discharge_max", "forecast_days": 1}

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        daily = data.get("daily", {})
        return {"river_discharge": daily.get("river_discharge", [None])[0], "river_discharge_mean": daily.get("river_discharge_mean", [None])[0],
                "river_discharge_max": daily.get("river_discharge_max", [None])[0]}
    except:
        return {"river_discharge": None, "river_discharge_mean": None, "river_discharge_max": None}


def get_morning_forecast(latitude, longitude, timezone, now):
    """Get the weather forecast for tomorrow morning (8 AM)."""
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {"latitude": latitude, "longitude": longitude,
                  "hourly": "temperature_2m,apparent_temperature,precipitation_probability,weathercode,wind_speed_10m,wind_gusts_10m,visibility",
                  "timezone": timezone, "forecast_days": 2, "wind_speed_unit": "ms", }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        hourly = data.get("hourly", {})
        times = hourly.get("time", [])

        tomorrow = (now + datetime.timedelta(days=1)).date()
        morning_indices = []

        # Identifies indices for tomorrow's 8 AM data points
        for i, time_str in enumerate(times):
            dt = datetime.datetime.fromisoformat(time_str)
            if dt.date() == tomorrow and dt.hour == 8:
                morning_indices.append(i)

        if not morning_indices:
            return None

        temps = [hourly["temperature_2m"][i] for i in morning_indices if hourly["temperature_2m"][i] is not None]
        apparent = [hourly["apparent_temperature"][i] for i in morning_indices if hourly["apparent_temperature"][i] is not None]
        precip = [hourly["precipitation_probability"][i] for i in morning_indices if hourly["precipitation_probability"][i] is not None]
        codes = [hourly["weathercode"][i] for i in morning_indices if hourly["weathercode"][i] is not None]
        winds = [hourly["wind_speed_10m"][i] for i in morning_indices if hourly["wind_speed_10m"][i] is not None]
        gusts = [hourly["wind_gusts_10m"][i] for i in morning_indices if hourly["wind_gusts_10m"][i] is not None]
        vis = [hourly["visibility"][i] for i in morning_indices if hourly.get("visibility") and hourly["visibility"][i] is not None]

        return {"date": tomorrow, "temp_min": min(temps) if temps else None, "temp_max": max(temps) if temps else None,
                "apparent_min": min(apparent) if apparent else None, "precip_prob_max": max(precip) if precip else None,
                "weather_code": max(set(codes), key=codes.count) if codes else None, "wind_max": max(winds) if winds else None,
                "gust_max": max(gusts) if gusts else None, "visibility_min": min(vis) if vis else None}
    except:
        return None


def _calculate_outdoor_score(hour_data):
    """Calculate outdoor activity suitability score (0-100).

    Factors (weighted):
    - Precipitation probability: -2 per percentage point above 20%
    - Temperature comfort: optimal at 10-25°C
    - Wind: -3 per m/s above 5
    """
    score = 100

    # Precipitation penalty
    precip_prob = hour_data.get('precipitation_probability', 0) or 0
    if precip_prob > 20:
        score -= (precip_prob - 20) * 2

    # Temperature comfort
    temp = hour_data.get('temperature', 15) or 15
    if temp < 10:
        score -= (10 - temp) * 2
    elif temp > 25:
        score -= (temp - 25) * 2

    # Wind penalty
    wind = hour_data.get('wind_speed', 0) or 0
    if wind > 5:
        score -= (wind - 5) * 3

    # Weather code penalty for bad weather
    weather_code = hour_data.get('weather_code', 0) or 0
    if weather_code >= 51:  # Any precipitation
        score -= 20
    if weather_code >= 95:  # Thunderstorm
        score -= 30

    return max(0, min(100, score))


def get_12h_forecast_summary(latitude, longitude, timezone, now):
    """Get compact 12-hour forecast for day planning.

    Returns:
        dict: {
            'rain_windows': [{start: "HH:MM", end: "HH:MM"}],
            'strongest_wind': {speed, gust, time, direction},
            'temp_range': {min, max, trend}
        }
    """
    # Check cache
    cache_key = f"forecast_12h_{latitude}_{longitude}"
    if CACHE_AVAILABLE:
        cached_data = get_cached_data(cache_key)
        if cached_data:
            return cached_data

    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": "temperature_2m,precipitation_probability,precipitation,weather_code,wind_speed_10m,wind_gusts_10m,wind_direction_10m",
            "timezone": timezone,
            "forecast_hours": 12,
            "wind_speed_unit": "ms"
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        hourly = data.get("hourly", {})
        times = hourly.get("time", [])
        temps = hourly.get("temperature_2m", [])
        precip_probs = hourly.get("precipitation_probability", [])
        precips = hourly.get("precipitation", [])
        winds = hourly.get("wind_speed_10m", [])
        gusts = hourly.get("wind_gusts_10m", [])
        wind_dirs = hourly.get("wind_direction_10m", [])

        # Find rain windows (precipitation > 0.1 mm or probability > 50%)
        rain_windows = []
        in_rain = False
        rain_start = None

        for i, time_str in enumerate(times):
            dt = datetime.datetime.fromisoformat(time_str)
            precip = precips[i] if i < len(precips) else 0
            prob = precip_probs[i] if i < len(precip_probs) else 0

            is_rain = (precip and precip > 0.1) or (prob and prob > 50)

            if is_rain and not in_rain:
                rain_start = dt.strftime("%H:%M")
                in_rain = True
            elif not is_rain and in_rain:
                rain_end = dt.strftime("%H:%M")
                rain_windows.append({'start': rain_start, 'end': rain_end})
                in_rain = False

        # Close any ongoing rain window
        if in_rain and times:
            last_dt = datetime.datetime.fromisoformat(times[-1])
            rain_windows.append({'start': rain_start, 'end': last_dt.strftime("%H:%M")})

        # Find strongest wind
        strongest_wind = None
        max_wind_speed = 0
        for i, (time_str, speed, gust, direction) in enumerate(zip(times, winds, gusts, wind_dirs)):
            if speed and speed > max_wind_speed:
                max_wind_speed = speed
                dt = datetime.datetime.fromisoformat(time_str)
                strongest_wind = {
                    'speed': speed,
                    'gust': gust,
                    'time': dt.strftime("%H:%M"),
                    'direction': degrees_to_compass(direction) if direction else None
                }

        # Temperature range and trend
        valid_temps = [t for t in temps if t is not None]
        temp_range = None
        if valid_temps:
            temp_min = min(valid_temps)
            temp_max = max(valid_temps)
            first_temp = valid_temps[0]
            last_temp = valid_temps[-1]

            if last_temp > first_temp + 2:
                trend = 'rising'
            elif last_temp < first_temp - 2:
                trend = 'falling'
            else:
                trend = 'stable'

            temp_range = {
                'min': temp_min,
                'max': temp_max,
                'trend': trend
            }

        result = {
            'rain_windows': rain_windows,
            'strongest_wind': strongest_wind,
            'temp_range': temp_range
        }

        if CACHE_AVAILABLE:
            cache_data(cache_key, result)

        return result
    except Exception:
        return None


def get_7day_forecast(latitude, longitude, timezone):
    """Get 7-day forecast with outdoor activity recommendations.

    Returns:
        dict: {
            'days': [{date, weekday, temp_min, temp_max, precip_sum, wind_max, weather_code, outdoor_score}],
            'best_outdoor_window': {date, weekday, score, reason},
            'snow_accumulation_cm': float or None
        }
    """
    # Check cache
    cache_key = f"forecast_7day_{latitude}_{longitude}"
    if CACHE_AVAILABLE:
        cached_data = get_cached_data(cache_key)
        if cached_data:
            return cached_data

    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max,weather_code,wind_speed_10m_max,snowfall_sum",
            "hourly": "temperature_2m,precipitation_probability,wind_speed_10m,weather_code",
            "timezone": timezone,
            "forecast_days": 7,
            "wind_speed_unit": "ms"
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        daily = data.get("daily", {})
        hourly = data.get("hourly", {})

        dates = daily.get("time", [])
        temp_maxs = daily.get("temperature_2m_max", [])
        temp_mins = daily.get("temperature_2m_min", [])
        precip_sums = daily.get("precipitation_sum", [])
        precip_probs = daily.get("precipitation_probability_max", [])
        weather_codes = daily.get("weather_code", [])
        wind_maxs = daily.get("wind_speed_10m_max", [])
        snowfall_sums = daily.get("snowfall_sum", [])

        # Day names for Finnish (short version)
        weekday_names_fi = ['ma', 'ti', 'ke', 'to', 'pe', 'la', 'su']
        weekday_names_en = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

        days = []
        best_day = None
        best_score = -1
        total_snow = 0

        for i, date_str in enumerate(dates):
            dt = datetime.datetime.fromisoformat(date_str)
            weekday_fi = weekday_names_fi[dt.weekday()]
            weekday_en = weekday_names_en[dt.weekday()]

            temp_max = temp_maxs[i] if i < len(temp_maxs) else None
            temp_min = temp_mins[i] if i < len(temp_mins) else None
            precip_sum = precip_sums[i] if i < len(precip_sums) else 0
            precip_prob = precip_probs[i] if i < len(precip_probs) else 0
            weather_code = weather_codes[i] if i < len(weather_codes) else 0
            wind_max = wind_maxs[i] if i < len(wind_maxs) else 0
            snowfall = snowfall_sums[i] if i < len(snowfall_sums) else 0

            if snowfall:
                total_snow += snowfall

            # Calculate outdoor score for this day
            hour_data = {
                'temperature': (temp_max + temp_min) / 2 if temp_max and temp_min else 15,
                'precipitation_probability': precip_prob,
                'wind_speed': wind_max,
                'weather_code': weather_code
            }
            outdoor_score = _calculate_outdoor_score(hour_data)

            day_info = {
                'date': date_str,
                'weekday_fi': weekday_fi,
                'weekday_en': weekday_en,
                'temp_min': temp_min,
                'temp_max': temp_max,
                'precip_sum': precip_sum,
                'precip_prob': precip_prob,
                'wind_max': wind_max,
                'weather_code': weather_code,
                'outdoor_score': outdoor_score
            }
            days.append(day_info)

            # Track best day
            if outdoor_score > best_score:
                best_score = outdoor_score
                best_day = day_info

        # Determine reason for best day
        best_outdoor_window = None
        if best_day:
            reasons = []
            if best_day['precip_prob'] and best_day['precip_prob'] < 20:
                reasons.append('poutaista' if True else 'dry')  # Will use FI for now
            if best_day['temp_max'] and 15 <= best_day['temp_max'] <= 22:
                reasons.append('sopiva lämpötila')
            if best_day['wind_max'] and best_day['wind_max'] < 5:
                reasons.append('tyyni')
            elif not reasons:
                reasons.append('paras sää')

            best_outdoor_window = {
                'date': best_day['date'],
                'weekday_fi': best_day['weekday_fi'],
                'weekday_en': best_day['weekday_en'],
                'score': best_day['outdoor_score'],
                'reason': ', '.join(reasons),
                'temp_max': best_day['temp_max']
            }

        result = {
            'days': days,
            'best_outdoor_window': best_outdoor_window,
            'snow_accumulation_cm': total_snow if total_snow > 0 else None
        }

        if CACHE_AVAILABLE:
            cache_data(cache_key, result)

        return result
    except Exception:
        return None


def get_weather_warnings(weather_data, uv_index, air_quality_data, translations):
    """Create weather warnings based on weather conditions, UV index, and air quality."""
    warnings = []
    date_strings = translations['date']

    # Temperature warnings
    if weather_data.get("temperature") is not None:
        temp = weather_data["temperature"]
        if temp <= -30:
            warnings.append(date_strings['cold_warning_extreme'])
        elif temp <= -20:
            warnings.append(date_strings['cold_warning_severe'])
        elif temp <= -10:
            warnings.append(date_strings['cold_warning'])

    # Wind warnings
    if weather_data.get("wind_speed") is not None:
        wind_speed = weather_data["wind_speed"]
        if wind_speed >= 25:
            warnings.append(date_strings['wind_warning_high'])
        elif wind_speed >= 15:
            warnings.append(date_strings['wind_advisory'])

    # Precipitation probability warnings
    if weather_data.get("precipitation_probability") is not None:
        precip_prob = weather_data["precipitation_probability"]
        if precip_prob >= 80:
            warnings.append(date_strings['precipitation_warning_high'])
        elif precip_prob >= 50:
            warnings.append(date_strings['precipitation_advisory'])

    # Weather code-based warnings
    if weather_data.get("weather_code") is not None:
        weather_code = weather_data["weather_code"]
        if weather_code in [51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82]:
            warnings.append(date_strings['rain_warning'])
        elif weather_code in [71, 73, 75, 77, 85, 86]:
            warnings.append(date_strings['snow_warning'])
        elif weather_code in [95, 96, 99]:
            warnings.append(date_strings['thunderstorm_warning'])

    # UV index warnings
    if uv_index is not None and uv_index >= 6:
        warnings.append(date_strings['uv_warning'])

    # Air quality warnings
    if air_quality_data is not None and air_quality_data.get('aqi') is not None:
        aqi = air_quality_data['aqi']
        if aqi >= 4:
            warnings.append(date_strings['air_quality_warning'])

    return warnings
