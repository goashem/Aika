"""Aika Public API."""

import datetime
from typing import Optional

from .services.snapshot import build_snapshot
from .models import (
    AikaSnapshot, WeatherData, Location, RawData, ComputedData,
    DateInfo, SolarInfo, LunarInfo
)

# Re-export key models
__all__ = [
    'get_snapshot',
    'AikaSnapshot',
    'WeatherData',
    'Location',
    'RawData',
    'ComputedData',
    'DateInfo',
    'SolarInfo',
    'LunarInfo'
]


def get_snapshot(
    latitude: Optional[float] = None, 
    longitude: Optional[float] = None,
    location_query: Optional[str] = None,
    language: str = "fi",
    digitransit_api_key: Optional[str] = None
) -> AikaSnapshot:
    """Get a complete snapshot of time, weather, and astronomical data.
    
    Args:
        latitude: Latitude in decimal degrees (optional if location_query provided)
        longitude: Longitude in decimal degrees (optional if location_query provided)
        location_query: City name or address to geocode (optional if coordinates provided)
        language: Language code ('fi' or 'en'), defaults to 'fi'
        digitransit_api_key: API key for Digitransit (optional, for transport alerts)
        
    Returns:
        AikaSnapshot: Complete data object containing raw and computed data
    """
    return build_snapshot(
        location_query=location_query,
        latitude=latitude,
        longitude=longitude,
        language=language,
        digitransit_api_key=digitransit_api_key
    )
