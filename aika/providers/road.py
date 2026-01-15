"""Finnish road weather data provider - Fintraffic Digitraffic API."""

import requests

try:
    from aika.cache import get_cached_data, cache_data
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False

    def get_cached_data(api_name):
        return None

    def cache_data(api_name, data):
        pass


def get_road_weather(latitude, longitude, country_code):
    """Get road weather conditions from Fintraffic Digitraffic API (Finland only).

    Returns:
        dict: Road weather data with condition and reason, or None
    """
    if country_code != 'FI':
        return None

    cache_key = f"road_weather_{latitude}_{longitude}"
    if CACHE_AVAILABLE:
        cached_data = get_cached_data(cache_key)
        if cached_data:
            return cached_data

    try:
        margin = 0.3
        url = "https://tie.digitraffic.fi/api/weather/v1/forecast-sections-simple/forecasts"
        params = {
            "xMin": longitude - margin,
            "yMin": latitude - margin,
            "xMax": longitude + margin,
            "yMax": latitude + margin,
        }
        headers = {"Digitraffic-User": "AikaApp/1.0"}
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        def normalize_condition(value):
            if not value:
                return None
            value = value.upper()
            suffix = '_CONDITION'
            if value.endswith(suffix):
                value = value[:-len(suffix)]
            return value

        worst_condition = None
        condition_reason = None
        condition_priority = {"NO_DATA": -1, "NORMAL": 0, "POOR": 1, "VERY_POOR": 2}

        for section in data.get("forecastSections", []):
            forecasts = section.get("forecasts", [])
            if not forecasts:
                continue
            forecast = forecasts[0]
            overall = normalize_condition(forecast.get("overallRoadCondition"))
            if overall is None:
                continue
            current_priority = condition_priority.get(overall, -1)
            worst_priority = condition_priority.get(worst_condition, -1) if worst_condition else -1
            if current_priority > worst_priority:
                worst_condition = overall
                reason = forecast.get("forecastConditionReason", {})
                if reason.get("roadCondition"):
                    condition_reason = reason.get("roadCondition")
                elif reason.get("windCondition"):
                    condition_reason = reason.get("windCondition")

        if worst_condition is None:
            road_weather_data = {"condition": "NO_DATA", "reason": None}
        else:
            road_weather_data = {"condition": worst_condition, "reason": condition_reason}

        if CACHE_AVAILABLE:
            cache_data(cache_key, road_weather_data)

        return road_weather_data
    except:
        if CACHE_AVAILABLE:
            cache_data(cache_key, None)
        return None
