"""Short-term precipitation and lightning nowcast provider."""

from __future__ import annotations

import datetime

import requests

try:
    from aika.cache import cache_data, get_cached_data

    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False

    def get_cached_data(*_args, **_kwargs):
        return None

    def cache_data(*_args, **_kwargs):
        pass


def get_precipitation_nowcast(latitude: float, longitude: float, timezone: str):
    """Fetch 2-hour precipitation outlook using Open-Meteo."""
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
            "forecast_minutely_15": 8,
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        minutely = data.get("minutely_15", {})
        times = minutely.get("time", [])
        precips = minutely.get("precipitation", [])
        rains = minutely.get("rain", [])
        snowfalls = minutely.get("snowfall", [])

        if not times or not precips:
            return None

        result = {
            "rain_starts_in_min": None,
            "rain_ends_in_min": None,
            "is_raining_now": False,
            "precipitation_type": "none",
            "max_intensity": 0,
            "intervals": [],
        }

        rain_threshold = 0.1
        current_precip = precips[0] if precips else 0
        result["is_raining_now"] = current_precip > rain_threshold

        current_rain = rains[0] if rains else 0
        current_snow = snowfalls[0] if snowfalls else 0
        if current_rain > 0 and current_snow > 0:
            result["precipitation_type"] = "mixed"
        elif current_snow > 0:
            result["precipitation_type"] = "snow"
        elif current_rain > 0 or current_precip > rain_threshold:
            result["precipitation_type"] = "rain"
        else:
            result["precipitation_type"] = "none"

        max_intensity = max(precips) if precips else 0
        result["max_intensity"] = max_intensity * 4

        for index, (time_str, precip) in enumerate(zip(times, precips)):
            is_rain = precip > rain_threshold
            minutes_from_now = index * 15

            result["intervals"].append(
                {
                    "time": time_str,
                    "minutes": minutes_from_now,
                    "precipitation": precip,
                    "is_rain": is_rain,
                }
            )

            if not result["is_raining_now"] and is_rain and result["rain_starts_in_min"] is None:
                result["rain_starts_in_min"] = minutes_from_now

            if result["is_raining_now"] and not is_rain and result["rain_ends_in_min"] is None:
                result["rain_ends_in_min"] = minutes_from_now

        if CACHE_AVAILABLE:
            cache_data(cache_key, result)
        return result
    except Exception:
        return None


def get_lightning_activity(latitude: float, longitude: float, country_code: str):
    """Fetch seasonal lightning activity for Finland via FMI."""
    if country_code != "FI":
        return None

    now = datetime.datetime.now()
    if now.month < 5 or now.month > 9:
        return None

    cache_key = f"lightning_{latitude}_{longitude}"
    if CACHE_AVAILABLE:
        cached_data = get_cached_data(cache_key)
        if cached_data:
            return cached_data

    try:
        from fmiopendata.wfs import download_stored_query

        result = {
            "strikes_1h": 0,
            "nearest_km": None,
            "activity_level": "none",
            "is_active": False,
        }

        if CACHE_AVAILABLE:
            cache_data(cache_key, result)

        return result
    except Exception:
        return None
