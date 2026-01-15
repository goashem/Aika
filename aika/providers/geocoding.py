"""Geocoding and timezone provider functions."""

from __future__ import annotations

import requests

try:
    from timezonefinder import TimezoneFinder

    TIMEZONE_FINDER_AVAILABLE = True
    _tf = TimezoneFinder()
except ImportError:
    TIMEZONE_FINDER_AVAILABLE = False
    _tf = None

try:
    from aika.cache import cache_data, get_cached_data

    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False

    def get_cached_data(*_args, **_kwargs):
        return None

    def cache_data(*_args, **_kwargs):
        pass


def get_coordinates_for_city(city: str):
    """Lookup coordinates for a city via OpenStreetMap Nominatim API."""
    cache_key = f"geocoding_{city}"
    if CACHE_AVAILABLE:
        cached_data = get_cached_data(cache_key)
        if cached_data:
            return cached_data

    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {"q": city, "format": "json", "limit": 1}
        headers = {"User-Agent": "AikaApp/1.0 (educational project)"}

        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data:
            lat = float(data[0]["lat"])
            lon = float(data[0]["lon"])
            coordinates = (lat, lon)
            if CACHE_AVAILABLE:
                cache_data(cache_key, coordinates)
            return coordinates
    except Exception as exc:
        print(f"Error getting coordinates: {exc}")
        if CACHE_AVAILABLE:
            cache_data(cache_key, None)

    return None


def get_coordinates_with_details(city: str):
    """Return coordinates and metadata for a city search."""
    cache_key = f"geocoding_details_{city}"
    if CACHE_AVAILABLE:
        cached_data = get_cached_data(cache_key)
        if cached_data:
            return cached_data

    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {"q": city, "format": "json", "limit": 1, "addressdetails": 1}
        headers = {"User-Agent": "AikaApp/1.0 (educational project)"}

        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data:
            address = data[0].get("address", {})
            coordinates_data = {
                "lat": float(data[0]["lat"]),
                "lon": float(data[0]["lon"]),
                "city": address.get("city")
                or address.get("town")
                or address.get("village")
                or address.get("municipality")
                or city,
                "country": address.get("country", ""),
                "country_code": address.get("country_code", "").upper() or "FI",
            }
            if CACHE_AVAILABLE:
                cache_data(cache_key, coordinates_data)
            return coordinates_data
    except Exception as exc:
        print(f"Error getting coordinates: {exc}")
        if CACHE_AVAILABLE:
            cache_data(cache_key, None)

    return None


def reverse_geocode(latitude: float, longitude: float):
    """Reverse geocode coordinates to (city, country, country_code)."""
    cache_key = f"reverse_geocoding_{latitude}_{longitude}"
    if CACHE_AVAILABLE:
        cached_data = get_cached_data(cache_key)
        if cached_data:
            return cached_data

    try:
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {"lat": latitude, "lon": longitude, "format": "json", "addressdetails": 1}
        headers = {"User-Agent": "AikaApp/1.0 (educational project)"}

        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data:
            address = data.get("address", {})
            city = address.get("city") or address.get("town") or address.get("village") or address.get("municipality")
            country = address.get("country", "")
            country_code = address.get("country_code", "").upper()
            geocode_data = (city, country, country_code)
            if CACHE_AVAILABLE:
                cache_data(cache_key, geocode_data)
            return geocode_data
    except Exception:
        if CACHE_AVAILABLE:
            cache_data(cache_key, (None, None, None))

    return None, None, None


def get_timezone_for_coordinates(latitude: float, longitude: float) -> str:
    """Resolve timezone identifier for coordinates, defaulting to UTC."""
    if TIMEZONE_FINDER_AVAILABLE and _tf:
        tz = _tf.unique_timezone_at(lng=longitude, lat=latitude)
        if tz:
            return tz

        tz = _tf.timezone_at_land(lng=longitude, lat=latitude)
        if tz:
            return tz

        tz = _tf.timezone_at(lng=longitude, lat=latitude)
        return tz or "UTC"

    if 59 <= latitude <= 70 and 20 <= longitude <= 32:
        return "Europe/Helsinki"

    return "UTC"
