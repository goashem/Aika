"""Legacy geolocation helpers delegating to provider implementations."""

from .providers import geocoding as geocoding_provider

get_coordinates_for_city = geocoding_provider.get_coordinates_for_city
get_coordinates_with_details = geocoding_provider.get_coordinates_with_details
reverse_geocode = geocoding_provider.reverse_geocode
get_timezone_for_coordinates = geocoding_provider.get_timezone_for_coordinates
