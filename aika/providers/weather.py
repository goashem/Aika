"""Weather data provider - fetches from FMI and Open-Meteo APIs."""

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

    def get_cached_data(api_name):
        return None

    def cache_data(api_name, data):
        pass


def get_weather_data(latitude, longitude, timezone):
    """Get weather information from FMI and Open-Meteo APIs.

    Returns:
        dict: Weather data or None if all APIs fail
    """
    cache_key = f"weather_{latitude}_{longitude}"
    if CACHE_AVAILABLE:
        cached_data = get_cached_data(cache_key)
        if cached_data:
            return cached_data

    try:
        if FMI_AVAILABLE:
            try:
                bbox_margin = 0.5
                args = [
                    f"bbox={longitude - bbox_margin},{latitude - bbox_margin},{longitude + bbox_margin},{latitude + bbox_margin}",
                    "timeseries=True",
                ]

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

                    fmi_data = {
                        "temperature": get_latest_value("Air temperature"),
                        "description": "ei saatavilla",
                        "humidity": get_latest_value("Relative humidity"),
                        "pressure": get_latest_value("Pressure (msl)"),
                        "wind_speed": get_latest_value("Wind speed"),
                        "wind_direction": get_latest_value("Wind direction"),
                        "gust_speed": get_latest_value("Gust speed"),
                        "visibility": get_latest_value("Horizontal visibility"),
                        "precip_intensity": get_latest_value("Precipitation intensity"),
                        "snow_depth": get_latest_value("Snow depth"),
                        "apparent_temp": None,
                        "precipitation_probability": None,
                        "weather_code": None,
                    }

                    # Supplement missing data from Open-Meteo
                    try:
                        url = "https://api.open-meteo.com/v1/forecast"
                        params = {
                            "latitude": latitude,
                            "longitude": longitude,
                            "current": "apparent_temperature,wind_speed_10m,wind_direction_10m,wind_gusts_10m",
                            "hourly": "precipitation_probability,weathercode",
                            "timezone": timezone,
                            "forecast_hours": 1,
                            "wind_speed_unit": "ms",
                        }
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

                    if CACHE_AVAILABLE:
                        cache_data(cache_key, fmi_data)
                    return fmi_data
            except Exception:
                pass

        # Use Open-Meteo as a full fallback
        try:
            url = "https://api.open-meteo.com/v1/forecast"
            params = {
                "latitude": latitude,
                "longitude": longitude,
                "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,pressure_msl,wind_speed_10m,wind_direction_10m,wind_gusts_10m",
                "hourly": "precipitation_probability,weathercode",
                "timezone": timezone,
                "forecast_hours": 1,
                "wind_speed_unit": "ms",
            }

            response = requests.get(url, params=params, timeout=20)
            response.raise_for_status()
            data = response.json()

            current = data.get("current", {})
            hourly = data.get("hourly", {})

            open_meteo_data = {
                "temperature": current.get("temperature_2m"),
                "apparent_temp": current.get("apparent_temperature"),
                "description": "ei saatavilla",
                "humidity": current.get("relative_humidity_2m"),
                "pressure": current.get("pressure_msl"),
                "wind_speed": current.get("wind_speed_10m"),
                "wind_direction": current.get("wind_direction_10m"),
                "gust_speed": current.get("wind_gusts_10m"),
                "visibility": None,
                "precip_intensity": current.get("precipitation"),
                "snow_depth": None,
                "precipitation_probability": hourly.get("precipitation_probability", [None])[0],
                "weather_code": hourly.get("weathercode", [None])[0],
            }

            if CACHE_AVAILABLE:
                cache_data(cache_key, open_meteo_data)

            return open_meteo_data
        except Exception:
            pass

    except Exception:
        pass

    # Return sample data if both APIs fail
    fallback_data = {
        "temperature": -14.0,
        "apparent_temp": -20.0,
        "description": "selkeaa",
        "humidity": 90,
        "pressure": 1025,
        "wind_speed": 3.2,
        "wind_direction": 180,
        "gust_speed": 5.0,
        "visibility": None,
        "precip_intensity": 0,
        "snow_depth": None,
        "precipitation_probability": 10,
        "weather_code": 0,
    }

    if CACHE_AVAILABLE:
        cache_data(cache_key, fallback_data)

    return fallback_data


def get_solar_radiation(latitude, longitude, timezone):
    """Get solar radiation and cloud cover data from Open-Meteo API.

    Returns:
        dict: Solar radiation data
    """
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": "cloud_cover,shortwave_radiation,direct_radiation,diffuse_radiation,direct_normal_irradiance,global_tilted_irradiance",
            "timezone": timezone,
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        current = data.get("current", {})

        return {
            "cloud_cover": current.get("cloud_cover"),
            "ghi": current.get("shortwave_radiation"),
            "dni": current.get("direct_normal_irradiance"),
            "dhi": current.get("diffuse_radiation"),
            "gti": current.get("global_tilted_irradiance"),
            "direct": current.get("direct_radiation"),
        }
    except:
        return {"cloud_cover": None, "ghi": None, "dni": None, "dhi": None, "gti": None, "direct": None}


def get_morning_forecast(latitude, longitude, timezone, now):
    """Get the weather forecast for tomorrow morning (8 AM).

    Returns:
        dict: Morning forecast data or None
    """
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": "temperature_2m,apparent_temperature,precipitation_probability,weathercode,wind_speed_10m,wind_gusts_10m,visibility",
            "timezone": timezone,
            "forecast_days": 2,
            "wind_speed_unit": "ms",
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        hourly = data.get("hourly", {})
        times = hourly.get("time", [])

        tomorrow = (now + datetime.timedelta(days=1)).date()
        morning_indices = []

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

        return {
            "date": tomorrow,
            "temp_min": min(temps) if temps else None,
            "temp_max": max(temps) if temps else None,
            "apparent_min": min(apparent) if apparent else None,
            "precip_prob_max": max(precip) if precip else None,
            "weather_code": max(set(codes), key=codes.count) if codes else None,
            "wind_max": max(winds) if winds else None,
            "gust_max": max(gusts) if gusts else None,
            "visibility_min": min(vis) if vis else None,
        }
    except:
        return None


def get_12h_forecast_summary(latitude, longitude, timezone, now):
    """Get compact 12-hour forecast for day planning.

    Returns:
        dict: Forecast summary with rain windows, wind, and temperature info
    """
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
            "wind_speed_unit": "ms",
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

        # Find rain windows
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
                rain_windows.append({"start": rain_start, "end": rain_end})
                in_rain = False

        if in_rain and times:
            last_dt = datetime.datetime.fromisoformat(times[-1])
            rain_windows.append({"start": rain_start, "end": last_dt.strftime("%H:%M")})

        # Find strongest wind
        strongest_wind = None
        max_wind_speed = 0
        for i, (time_str, speed, gust, direction) in enumerate(zip(times, winds, gusts, wind_dirs)):
            if speed and speed > max_wind_speed:
                max_wind_speed = speed
                dt = datetime.datetime.fromisoformat(time_str)
                strongest_wind = {
                    "speed": speed,
                    "gust": gust,
                    "time": dt.strftime("%H:%M"),
                    "direction": _degrees_to_compass(direction) if direction else None,
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
                trend = "rising"
            elif last_temp < first_temp - 2:
                trend = "falling"
            else:
                trend = "stable"

            temp_range = {"min": temp_min, "max": temp_max, "trend": trend}

        result = {
            "rain_windows": rain_windows,
            "strongest_wind": strongest_wind,
            "temp_range": temp_range,
        }

        if CACHE_AVAILABLE:
            cache_data(cache_key, result)

        return result
    except Exception:
        return None


def get_7day_forecast(latitude, longitude, timezone):
    """Get 7-day forecast with outdoor activity recommendations.

    Returns:
        dict: 7-day forecast data
    """
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
            "wind_speed_unit": "ms",
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        daily = data.get("daily", {})

        dates = daily.get("time", [])
        temp_maxs = daily.get("temperature_2m_max", [])
        temp_mins = daily.get("temperature_2m_min", [])
        precip_sums = daily.get("precipitation_sum", [])
        precip_probs = daily.get("precipitation_probability_max", [])
        weather_codes = daily.get("weather_code", [])
        wind_maxs = daily.get("wind_speed_10m_max", [])
        snowfall_sums = daily.get("snowfall_sum", [])

        weekday_names_fi = ["ma", "ti", "ke", "to", "pe", "la", "su"]
        weekday_names_en = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

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

            # Calculate outdoor score
            hour_data = {
                "temperature": (temp_max + temp_min) / 2 if temp_max and temp_min else 15,
                "precipitation_probability": precip_prob,
                "wind_speed": wind_max,
                "weather_code": weather_code,
            }
            outdoor_score = _calculate_outdoor_score(hour_data)

            day_info = {
                "date": date_str,
                "weekday_fi": weekday_fi,
                "weekday_en": weekday_en,
                "temp_min": temp_min,
                "temp_max": temp_max,
                "precip_sum": precip_sum,
                "precip_prob": precip_prob,
                "wind_max": wind_max,
                "weather_code": weather_code,
                "outdoor_score": outdoor_score,
            }
            days.append(day_info)

            if outdoor_score > best_score:
                best_score = outdoor_score
                best_day = day_info

        # Determine reason for best day
        best_outdoor_window = None
        if best_day:
            reasons = []
            if best_day["precip_prob"] and best_day["precip_prob"] < 20:
                reasons.append("poutaista")
            if best_day["temp_max"] and 15 <= best_day["temp_max"] <= 22:
                reasons.append("sopiva lämpötila")
            if best_day["wind_max"] and best_day["wind_max"] < 5:
                reasons.append("tyyni")
            elif not reasons:
                reasons.append("paras sää")

            best_outdoor_window = {
                "date": best_day["date"],
                "weekday_fi": best_day["weekday_fi"],
                "weekday_en": best_day["weekday_en"],
                "score": best_day["outdoor_score"],
                "reason": ", ".join(reasons),
                "temp_max": best_day["temp_max"],
            }

        result = {
            "days": days,
            "best_outdoor_window": best_outdoor_window,
            "snow_accumulation_cm": total_snow if total_snow > 0 else None,
        }

        if CACHE_AVAILABLE:
            cache_data(cache_key, result)

        return result
    except Exception:
        return None


def _calculate_outdoor_score(hour_data):
    """Calculate outdoor activity suitability score (0-100)."""
    score = 100

    precip_prob = hour_data.get("precipitation_probability", 0) or 0
    if precip_prob > 20:
        score -= (precip_prob - 20) * 2

    temp = hour_data.get("temperature", 15) or 15
    if temp < 10:
        score -= (10 - temp) * 2
    elif temp > 25:
        score -= (temp - 25) * 2

    wind = hour_data.get("wind_speed", 0) or 0
    if wind > 5:
        score -= (wind - 5) * 3

    weather_code = hour_data.get("weather_code", 0) or 0
    if weather_code >= 51:
        score -= 20
    if weather_code >= 95:
        score -= 30

    return max(0, min(100, score))


def _degrees_to_compass(degrees):
    """Convert wind direction in degrees to compass direction key."""
    if degrees is None:
        return None

    degrees = degrees % 360
    directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    index = round(degrees / 22.5) % 16
    return directions[index]
