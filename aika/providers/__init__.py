"""Data providers for Aika.

This package contains modules that fetch raw data from external APIs.
Each provider returns raw dictionaries that are converted to typed models
by the services layer.
"""

from . import weather
from . import air_quality
from . import marine
from . import road
from . import electricity
from . import aurora
from . import transit
from . import geocoding
from . import nowcast

__all__ = [
    "weather",
    "air_quality",
    "marine",
    "road",
    "electricity",
    "aurora",
    "transit",
    "geocoding",
    "nowcast",
]
