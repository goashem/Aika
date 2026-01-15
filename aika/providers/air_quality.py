"""Air quality data provider."""
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
