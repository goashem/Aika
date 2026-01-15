"""Legacy nowcast helpers delegating to provider implementations."""

from .providers import nowcast as nowcast_provider

get_precipitation_nowcast = nowcast_provider.get_precipitation_nowcast
get_lightning_activity = nowcast_provider.get_lightning_activity
