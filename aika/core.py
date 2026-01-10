"""Core TimeInfo class that coordinates all modules."""
import datetime
import os

try:
    from zoneinfo import ZoneInfo

    ZONEINFO_AVAILABLE = True
except ImportError:
    ZONEINFO_AVAILABLE = False

from .config import load_config, create_config_interactively
from .geolocation import (get_coordinates_for_city, get_coordinates_with_details, reverse_geocode, get_timezone_for_coordinates)
from .display import display_info


class TimeInfo:
    """Main class that coordinates all time and location information."""

    def __init__(self, location_query=None):
        """Initialize TimeInfo with location and configuration.

        Args:
            location_query: Optional city name to use instead of config
        """
        self.country_code = 'FI'
        self.city_name = None
        self.country_name = None
        self.digitransit_api_key = None
        self.system_timezone = None

        # Get system timezone
        if ZONEINFO_AVAILABLE:
            try:
                import time
                self.system_timezone = time.tzname[0]
                local_now = datetime.datetime.now().astimezone()
                self.system_timezone = str(local_now.tzinfo)
            except:
                self.system_timezone = None

        config = load_config()

        if location_query:
            # Use provided location query
            details = get_coordinates_with_details(location_query)
            if details:
                self.latitude = details['lat']
                self.longitude = details['lon']
                self.city_name = details['city']
                self.country_name = details['country']
                self.country_code = details['country_code']
                self.timezone = get_timezone_for_coordinates(self.latitude, self.longitude)

                # Use language from config if available
                if config:
                    self.language = config['location'].get('language', 'fi')
                    if 'api_keys' in config:
                        self.digitransit_api_key = config['api_keys'].get('digitransit')
                else:
                    self.language = 'fi'
            else:
                print(f"Could not find coordinates for '{location_query}', using default location.")
                if not config:
                    result = create_config_interactively()
                    self.latitude = result['latitude']
                    self.longitude = result['longitude']
                    self.timezone = result['timezone']
                    self.language = result['language']
                else:
                    self._load_from_config(config)
        elif not config:
            # Config file not found, ask user for information
            result = create_config_interactively()
            self.latitude = result['latitude']
            self.longitude = result['longitude']
            self.timezone = result['timezone']
            self.language = result['language']
        else:
            # Use config file settings
            self._load_from_config(config)

        # If city_name not set, try reverse geocoding
        if not self.city_name and hasattr(self, 'latitude'):
            city, country, country_code = reverse_geocode(self.latitude, self.longitude)
            if city:
                self.city_name = city
            if country:
                self.country_name = country
            if country_code and self.country_code == 'FI':
                self.country_code = country_code

        # Current time in local timezone
        self.now = datetime.datetime.now()

        # Set language from environment variable if available
        if 'LANGUAGE' in os.environ:
            self.language = os.environ['LANGUAGE']

    def _load_from_config(self, config):
        """Load settings from config object."""
        self.latitude = float(config['location']['latitude'])
        self.longitude = float(config['location']['longitude'])
        self.timezone = config['location']['timezone']
        self.language = config['location'].get('language', 'fi')
        self.country_code = config['location'].get('country_code', 'FI')
        self.city_name = config['location'].get('city_name')
        self.country_name = config['location'].get('country_name')

        if 'api_keys' in config:
            self.digitransit_api_key = config['api_keys'].get('digitransit')

    def display_info(self):
        """Display all information in the selected language."""
        display_info(self)


def main():
    """CLI entry point."""
    import sys

    if len(sys.argv) > 1:
        location_query = " ".join(sys.argv[1:])
        time_info = TimeInfo(location_query)
    else:
        time_info = TimeInfo()

    time_info.display_info()


if __name__ == "__main__":
    main()
