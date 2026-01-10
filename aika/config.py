"""Configuration management for Aika."""
import configparser
import os

from .geolocation import get_coordinates_for_city, get_timezone_for_coordinates

DEFAULT_CONFIG_PATH = './config.ini'


def load_config(config_path=None):
    """Load configuration from file.

    Returns:
        configparser.ConfigParser or None if file not found
    """
    config = configparser.ConfigParser()
    path = config_path or DEFAULT_CONFIG_PATH

    if config.read(path):
        return config
    return None


def create_config_interactively(config_path=None):
    """Create the config file by asking user for information.

    Returns:
        dict: Configuration values
    """
    config_path = config_path or DEFAULT_CONFIG_PATH
    print("Configuration file not found. Let's set up your location preferences.")

    # Ask for location
    latitude = None
    longitude = None
    while True:
        city = input("Enter your city (e.g., Helsinki, Turku): ").strip()
        if city:
            coords = get_coordinates_for_city(city)
            if coords:
                latitude, longitude = coords
                break
            else:
                print("Could not find coordinates for that city. Please try another city.")
        else:
            print("Please enter a valid city name.")

    # Ask for language
    while True:
        lang = input("Choose language (fi/en): ").strip().lower()
        if lang in ['fi', 'en']:
            language = lang
            break
        else:
            print("Please enter 'fi' for Finnish or 'en' for English.")

    # Determine timezone based on coordinates
    timezone = get_timezone_for_coordinates(latitude, longitude)

    # Create and save the config file
    config = configparser.ConfigParser()
    config['location'] = {'latitude': str(latitude), 'longitude': str(longitude), 'timezone': timezone, 'language': language}

    # Ensure directory exists
    config_dir = os.path.dirname(config_path)
    if config_dir:
        os.makedirs(config_dir, exist_ok=True)

    with open(config_path, 'w') as f:
        config.write(f)

    print(f"Configuration saved to {config_path}")

    return {'latitude': latitude, 'longitude': longitude, 'timezone': timezone, 'language': language}
