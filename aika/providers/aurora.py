"""Aurora forecast provider."""
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


def get_aurora_forecast():
    """Get aurora forecast (Kp index) from NOAA and FMI."""
    # Check cache first
    cache_key = "aurora_forecast"
    if CACHE_AVAILABLE:
        cached_data = get_cached_data(cache_key)
        if cached_data:
            return cached_data

    try:
        kp_value = None
        fmi_activity = None

        try:
            url = "https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            if len(data) > 1:
                latest = data[-1]
                if len(latest) > 1:
                    kp_value = float(latest[1])
        except:
            pass

        try:
            url = "https://rwc-finland.fmi.fi/api/mag-activity/latest"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                fmi_activity = data.get("activity_level")
        except:
            pass

        if kp_value is not None:
            aurora_data = {"kp": kp_value, "fmi_activity": fmi_activity}
        else:
            aurora_data = None

        # Cache the data before returning
        if CACHE_AVAILABLE:
            cache_data(cache_key, aurora_data)

        return aurora_data
    except:
        # Cache the data before returning
        if CACHE_AVAILABLE:
            cache_data(cache_key, None)
        return None
