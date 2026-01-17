"""Core orchestrator for Aika CLI."""

import sys
import os
from typing import Optional

from .api import get_snapshot
from .formats.display import display_info
from .config import load_config, create_config_interactively
from .providers.geocoding import get_coordinates_with_details


class TimeInfo:
    """Legacy wrapper for backward compatibility.
    
    This class is maintained to support existing code that might import it,
    but it now delegates to the new snapshot API.
    """

    def __init__(self, location_query: Optional[str] = None):
        """Initialize TimeInfo with location and configuration."""
        self.snapshot = None
        self._initialize(location_query)

    def _initialize(self, location_query: Optional[str] = None):
        """Initialize configuration and fetch snapshot."""
        latitude: Optional[float] = None
        longitude: Optional[float] = None
        language: str = 'fi'
        digitransit_api_key: Optional[str] = None

        config = load_config()

        # 1. Determine Location and Settings from Config/Args
        if location_query:
            # Use provided location query
            details = get_coordinates_with_details(location_query)
            if details:
                latitude = details['lat']
                longitude = details['lon']

                # Use language from config if available, otherwise default
                if config:
                    language = config['location'].get('language', 'fi')
                    if 'api_keys' in config:
                        digitransit_api_key = config['api_keys'].get('digitransit')
            else:
                print(f"Could not find coordinates for '{location_query}', using default location.")
                if not config:
                    result = create_config_interactively()
                    latitude = result['latitude']
                    longitude = result['longitude']
                    language = result['language']
                else:
                    latitude = float(config['location']['latitude'])
                    longitude = float(config['location']['longitude'])
                    language = config['location'].get('language', 'fi')
                    if 'api_keys' in config:
                        digitransit_api_key = config['api_keys'].get('digitransit')
        elif not config:
            # Config file not found, ask user for information
            result = create_config_interactively()
            latitude = result['latitude']
            longitude = result['longitude']
            language = result['language']
        else:
            # Use config file settings
            latitude = float(config['location']['latitude'])
            longitude = float(config['location']['longitude'])
            language = config['location'].get('language', 'fi')
            if 'api_keys' in config:
                digitransit_api_key = config['api_keys'].get('digitransit')

        # Override language from environment variable if available
        if 'LANGUAGE' in os.environ:
            language = os.environ['LANGUAGE']

        # 2. Fetch Snapshot
        self.snapshot = get_snapshot(latitude=latitude, longitude=longitude, language=language, digitransit_api_key=digitransit_api_key)

        # Populate legacy attributes for compatibility (if needed by external code)
        self.latitude = self.snapshot.location.latitude
        self.longitude = self.snapshot.location.longitude
        self.city_name = self.snapshot.location.city_name
        self.country_name = self.snapshot.location.country_name
        self.country_code = self.snapshot.location.country_code
        self.timezone = self.snapshot.location.timezone
        self.language = self.snapshot.language
        self.now = self.snapshot.timestamp

    def display_info(self):
        """Display all information using the new formatter."""
        if self.snapshot:
            display_info(self.snapshot)


def main():
    """CLI entry point."""
    if len(sys.argv) > 1:
        location_query = " ".join(sys.argv[1:])
        time_info = TimeInfo(location_query)
    else:
        time_info = TimeInfo()

    time_info.display_info()


if __name__ == "__main__":
    main()
