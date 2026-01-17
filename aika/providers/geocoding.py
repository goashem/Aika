"""Geocoding and timezone data provider."""
import requests

try:
    from timezonefinder import TimezoneFinder

    TIMEZONE_FINDER_AVAILABLE = True
    tf = TimezoneFinder()
except ImportError:
    TIMEZONE_FINDER_AVAILABLE = False
    tf = None

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


def get_coordinates_for_city(city):
    """Get coordinates for a city using OpenStreetMap Nominatim API.

    Returns:
        tuple: (latitude, longitude) or None if not found
    """
    # Check cache first
    cache_key = f"geocoding_{city}"
    if CACHE_AVAILABLE:
        cached_data = get_cached_data(cache_key)
        if cached_data:
            return cached_data

    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {'q': city, 'format': 'json', 'limit': 1}
        headers = {'User-Agent': 'AikaApp/1.0 (educational project)'}

        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data:
            lat = float(data[0]['lat'])
            lon = float(data[0]['lon'])
            coordinates = (lat, lon)
            # Cache the data before returning
            if CACHE_AVAILABLE:
                cache_data(cache_key, coordinates)
            return coordinates
    except Exception as e:
        print(f"Error getting coordinates: {e}")
        # Cache the data before returning
        if CACHE_AVAILABLE:
            cache_data(cache_key, None)

    return None


def get_coordinates_with_details(city):
    """Get coordinates and location details for a city.

    Returns:
        dict: {'lat': float, 'lon': float, 'city': str, 'country': str, 'country_code': str} or None
    """
    # Check cache first
    cache_key = f"geocoding_details_{city}"
    if CACHE_AVAILABLE:
        cached_data = get_cached_data(cache_key)
        if cached_data:
            return cached_data

    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {'q': city, 'format': 'json', 'limit': 1, 'addressdetails': 1}
        headers = {'User-Agent': 'AikaApp/1.0 (educational project)'}

        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data:
            address = data[0].get('address', {})
            coordinates_data = {'lat': float(data[0]['lat']), 'lon': float(data[0]['lon']),
                                'city': address.get('city') or address.get('town') or address.get('village') or address.get('municipality') or city,
                                'country': address.get('country', ''), 'country_code': address.get('country_code', '').upper() or 'FI'}
            # Cache the data before returning
            if CACHE_AVAILABLE:
                cache_data(cache_key, coordinates_data)
            return coordinates_data
    except Exception as e:
        print(f"Error getting coordinates: {e}")
        # Cache the data before returning
        if CACHE_AVAILABLE:
            cache_data(cache_key, None)

    return None


def reverse_geocode(latitude, longitude):
    """Get city and country names from coordinates using reverse geocoding.

    Returns:
        tuple: (city, country, country_code) or (None, None, None) if failed
    """
    # Check cache first
    cache_key = f"reverse_geocoding_{latitude}_{longitude}"
    if CACHE_AVAILABLE:
        cached_data = get_cached_data(cache_key)
        if cached_data:
            return cached_data

    try:
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {'lat': latitude, 'lon': longitude, 'format': 'json', 'addressdetails': 1}
        headers = {'User-Agent': 'AikaApp/1.0 (educational project)'}

        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data:
            address = data.get('address', {})
            city = address.get('city') or address.get('town') or address.get('village') or address.get('municipality')
            country = address.get('country', '')
            country_code = address.get('country_code', '').upper()
            geocode_data = (city, country, country_code)
            # Cache the data before returning
            if CACHE_AVAILABLE:
                cache_data(cache_key, geocode_data)
            return geocode_data
    except:
        # Cache the data before returning
        if CACHE_AVAILABLE:
            cache_data(cache_key, (None, None, None))
        pass
    return None, None, None


def get_timezone_for_coordinates(latitude, longitude):
    """Get the timezone name for coordinates.

    Returns:
        str: Timezone name (e.g., 'Europe/Helsinki')
    """
    if TIMEZONE_FINDER_AVAILABLE and tf:
        # Try a "unique" fast path
        tz = tf.unique_timezone_at(lng=longitude, lat=latitude)
        if tz:
            return tz

        # Try land-only zones
        tz = tf.timezone_at_land(lng=longitude, lat=latitude)
        if tz:
            return tz

        # Accept ocean timezones too, or fallback to UTC
        tz = tf.timezone_at(lng=longitude, lat=latitude)
        return tz or "UTC"

    # Fallback for Finland
    if 59 <= latitude <= 70 and 20 <= longitude <= 32:
        return "Europe/Helsinki"
    else:
        return "UTC"
