"""Cache management for API responses with configurable TTL."""

import json
import os
import time
from typing import Any, Optional


def get_cache_path(api_name: str) -> str:
    """Get the file path for caching an API response."""
    return f"temp/{api_name}.json"


def is_cache_valid(cache_file: str, ttl_seconds: int) -> bool:
    """Check if cache file exists and is not expired."""
    if not os.path.exists(cache_file):
        return False
    
    # Check if file is older than TTL
    file_age = time.time() - os.path.getmtime(cache_file)
    return file_age < ttl_seconds


def load_cached_data(cache_file: str) -> Optional[Any]:
    """Load data from cache file if it exists and is valid."""
    if not os.path.exists(cache_file):
        return None
        
    try:
        with open(cache_file, 'r') as f:
            return json.load(f)
    except:
        # If cache is corrupted, remove it
        try:
            os.remove(cache_file)
        except:
            pass
        return None


def save_cached_data(cache_file: str, data: Any) -> None:
    """Save data to cache file."""
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(cache_file), exist_ok=True)
        
        with open(cache_file, 'w') as f:
            json.dump(data, f)
    except:
        pass  # Silently fail if can't write cache


# TTL values in seconds for different API data types
CACHE_TTLS = {
    # Weather data - 15 minutes
    'weather_current': 15 * 60,
    'weather_forecast': 15 * 60,
    'air_quality': 15 * 60,
    'uv_index': 15 * 60,
    'solar_radiation': 30 * 60,
    
    # Finnish specific data
    'electricity_prices': 60 * 60,  # 1 hour
    'road_weather': 30 * 60,  # 30 minutes
    'aurora_forecast': 2 * 60 * 60,  # 2 hours
    'transport_alerts': 60 * 60,  # 1 hour
    
    # Geolocation data
    'geocoding': 24 * 60 * 60,  # 24 hours
    'reverse_geocoding': 24 * 60 * 60,  # 24 hours
    
    # Marine and flood data
    'marine_data': 60 * 60,  # 1 hour
    'flood_data': 60 * 60,  # 1 hour
    
    # Forecast data
    'morning_forecast': 15 * 60,  # 15 minutes

    # Nowcast and extended forecasts
    'nowcast': 5 * 60,  # 5 minutes (fresh data critical)
    'lightning': 10 * 60,  # 10 minutes
    'forecast_12h': 30 * 60,  # 30 minutes
    'forecast_7day': 60 * 60,  # 1 hour
}


def get_cached_data(api_name: str) -> Optional[Any]:
    """Load cached data for an API if available and not expired."""
    cache_file = get_cache_path(api_name)
    ttl = CACHE_TTLS.get(api_name, 15 * 60)  # Default to 15 minutes
    
    if is_cache_valid(cache_file, ttl):
        return load_cached_data(cache_file)
    return None


def cache_data(api_name: str, data: Any) -> None:
    """Cache data for an API."""
    cache_file = get_cache_path(api_name)
    save_cached_data(cache_file, data)