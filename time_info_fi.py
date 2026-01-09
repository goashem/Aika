#!/usr/bin/env python3
import datetime
import calendar
import math
import configparser
from typing import Any

import requests
import os
from astral import LocationInfo
from astral.sun import sun
import ephem

try:
    from fmiopendata.wfs import download_stored_query

    FMI_AVAILABLE = True
except ImportError:
    FMI_AVAILABLE = False

try:
    from zoneinfo import ZoneInfo

    ZONEINFO_AVAILABLE = True
except ImportError:
    ZONEINFO_AVAILABLE = False

try:
    from timezonefinder import TimezoneFinder

    TIMEZONE_FINDER_AVAILABLE = True
    tf = TimezoneFinder()
except ImportError:
    TIMEZONE_FINDER_AVAILABLE = False
    tf = None

try:
    import holidays

    HOLIDAYS_AVAILABLE = True
except ImportError:
    HOLIDAYS_AVAILABLE = False


def get_coordinates_for_city(city):
    """Get coordinates for a city using OpenStreetMap Nominatim API"""
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {'q': city, 'format': 'json', 'limit': 1}

        # Add headers to comply with Nominatim usage policy
        headers = {'User-Agent': 'FinnishTimeInfoApp/1.0 (educational project)'}

        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data:
            lat = float(data[0]['lat'])
            lon = float(data[0]['lon'])
            return lat, lon
    except Exception as e:
        print(f"Error getting coordinates: {e}")

    return None


def get_timezone_for_coordinates(latitude, longitude):
    """Get timezone name for coordinates"""
    if TIMEZONE_FINDER_AVAILABLE and tf:
        # Try "unique" fast path
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
        return "UTC"  # Default fallback


def get_air_quality_data():
    """Legacy function - returns mock data. Use TimeInfo.get_air_quality() instead."""
    return {"aqi": None, "pm2_5": None, "pm10": None, "european_aqi": None}


def get_finnish_translations():
    """Hae suomenkieliset käännökset"""
    finnish_days = {"Monday": "maanantai", "Tuesday": "tiistai", "Wednesday": "keskiviikko", "Thursday": "torstai", "Friday": "perjantai",
                    "Saturday": "lauantai", "Sunday": "sunnuntai"}

    finnish_months = {"January": "tammikuu", "February": "helmikuu", "March": "maaliskuu", "April": "huhtikuu", "May": "toukokuu", "June": "kesäkuu",
                      "July": "heinäkuu", "August": "elokuu", "September": "syyskuu", "October": "lokakuu", "November": "marraskuu", "December": "joulukuu"}

    # Handle Finnish months in genitive case
    finnish_months_genitive = {"January": "tammikuuta", "February": "helmikuuta", "March": "maaliskuuta", "April": "huhtikuuta", "May": "toukokuuta",
                               "June": "kesäkuuta", "July": "heinäkuuta", "August": "elokuuta", "September": "syyskuuta", "October": "lokakuuta",
                               "November": "marraskuuta", "December": "joulukuuta"}

    return {'days': finnish_days, 'months': finnish_months, 'months_genitive': finnish_months_genitive}


def _get_finnish_hour(hour):
    """Get Finnish word for hour number in nominative case"""
    finnish_hours = {1: "yksi", 2: "kaksi", 3: "kolme", 4: "neljä", 5: "viisi", 6: "kuusi", 7: "seitsemän", 8: "kahdeksan", 9: "yhdeksän", 10: "kymmenen",
                     11: "yksitoista", 12: "kaksitoista"}
    return finnish_hours.get(hour, str(hour))


class TimeInfo:
    def __init__(self, location_query=None):
        # Load location data from config file or ask user
        self.config = configparser.ConfigParser()
        config_file = './config.ini'

        self.country_code = 'FI'  # Default to Finland

        # Store system timezone for comparison with location timezone
        self.system_timezone = None
        if ZONEINFO_AVAILABLE:
            try:
                # Get system's local timezone
                import time
                self.system_timezone = time.tzname[0]
                # Try to get proper IANA timezone name
                local_now = datetime.datetime.now().astimezone()
                self.system_timezone = str(local_now.tzinfo)
            except:
                self.system_timezone = None

        if location_query:
            # Use provided location query
            coords = self.get_coordinates_for_city(location_query)
            if coords:
                self.latitude, self.longitude = coords
                self.timezone = self.get_timezone_for_coordinates(self.latitude, self.longitude)
                self.language = 'fi'  # Default to Finnish for command line usage
            else:
                print(f"Could not find coordinates for '{location_query}', using default location.")
                if not self.config.read(config_file):
                    self.create_config_interactively(config_file)
                self.latitude = float(self.config['location']['latitude'])
                self.longitude = float(self.config['location']['longitude'])
                self.timezone = self.config['location']['timezone']
                self.language = self.config['location'].get('language', 'fi')
                self.country_code = self.config['location'].get('country_code', 'FI')
        elif not self.config.read(config_file):
            # Config file not found, ask user for information
            self.create_config_interactively(config_file)
        else:
            # Use config file settings
            self.latitude = float(self.config['location']['latitude'])
            self.longitude = float(self.config['location']['longitude'])
            self.timezone = self.config['location']['timezone']
            self.language = self.config['location'].get('language', 'fi')  # Default: Finnish
            self.country_code = self.config['location'].get('country_code', 'FI')

        # Current time in local timezone
        self.now = datetime.datetime.now()

    def create_config_interactively(self, config_file):
        """Create the config file by asking user for information"""
        print("Configuration file not found. Let's set up your location preferences.")

        # Ask for location
        while True:
            city = input("Enter your city (e.g., Helsinki, Turku): ").strip()
            if city:
                # Try to get coordinates for the city
                coords = get_coordinates_for_city(city)
                if coords:
                    self.latitude, self.longitude = coords
                    break
                else:
                    print("Could not find coordinates for that city. Please try another city.")
            else:
                print("Please enter a valid city name.")

        # Ask for language
        while True:
            lang = input("Choose language (fi/en): ").strip().lower()
            if lang in ['fi', 'en']:
                self.language = lang
                break
            else:
                print("Please enter 'fi' for Finnish or 'en' for English.")

        # Determine timezone based on coordinates
        self.timezone = get_timezone_for_coordinates(self.latitude, self.longitude)

        # Create and save the config file
        self.config['location'] = {'latitude': str(self.latitude), 'longitude': str(self.longitude), 'timezone': self.timezone, 'language': self.language}

        # Write the config file
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        with open(config_file, 'w') as f:
            self.config.write(f)

        print(f"Configuration saved to {config_file}")

    def get_translations(self):
        """Get the translations for the chosen language"""
        translations = {'fi': {'time_expressions': {'nearly_ten_to_two': 'noin kymmentä vaille kaksi', 'half_past_one': 'noin puoli yksi',
                                                    'quarter_to_two': 'noin varttia vailla kaksi', 'quarter_past_twelve': 'noin varttia yli kaksitoista',
                                                    'twelve': 'kaksitoista',
                                                    'time_of_day': {'early_morning': 'aamuyö', 'morning': 'aamu', 'forenoon': 'aamupäivä', 'noon': 'keskipäivä',
                                                                    'afternoon': 'iltapäivä', 'early_evening': 'varhainen ilta', 'late_evening': 'myöhäisilta',
                                                                    'night': 'iltayö'}},  # Päivämäärä
                               'date': {'week': 'Viikko', 'day': 'Päivä', 'year_complete': 'Vuosi on {pct:.1f} % valmis', 'dawn': 'Sarastus klo {time}',
                                        'sunrise': 'aurinko nousee klo {time}', 'noon': 'keskipäivä klo {time}', 'sunset': 'laskee klo {time}',
                                        'dusk': 'hämärä klo {time}', 'sun_position': 'Aurinko on {elevation:.1f}° korkeudella ja {azimuth:.1f}° suunnassa',
                                        'moon_phase': 'Kuu on {phase:.1f}% ja se on {growth}',
                                        'moon_position': 'Kuu on {altitude:.1f}° korkeudella ja {azimuth:.1f}° suunnassa', 'moon_rise': 'Kuu nousee klo {time}',
                                        'moon_transit': 'huipussaan klo {time}', 'moon_set': 'laskee klo {time}', 'sun_visible': '(näkyvissä)',
                                        'sun_below': '(horisontin alla)', 'moon_visible': '(näkyvissä)', 'moon_below': '(horisontin alla)',
                                        'snow_depth': 'Lumen syvyys: {depth:.0f} cm', 'cloud_cover': 'Pilvisyys: {cover}%',
                                        'solar_radiation': 'Auringon säteily: {ghi:.0f} W/m² (suora: {dni:.0f} W/m²)',
                                        'solar_for_panels': 'Aurinkopaneeleille: {gti:.0f} W/m² (kiinteä) / {dni:.0f} W/m² (seuranta)',
                                        'weather': 'Sää: {temp:.1f}°c, {desc}', 'feels_like': 'Tuntuu kuin: {temp:.1f}°c',
                                        'humidity': 'Ilmankosteus: {humidity}%, ilmanpaine: {pressure} hpa',
                                        'wind_full': 'Tuuli: {speed:.1f} m/s suunnasta {dir}° (puuskat {gust:.1f} m/s)',
                                        'wind_no_gust': 'Tuuli: {speed:.1f} m/s suunnasta {dir}°', 'visibility': 'Näkyvyys: {vis:.1f} km',
                                        'precip_intensity': 'Sateen intensiteetti: {intensity:.1f} mm/h',
                                        'wave_info': 'Aallot: {height:.1f} m, jakso {period:.1f} s, suunta {dir}°',
                                        'flood_discharge': 'Jokivirtaama: {discharge:.1f} m³/s',
                                        'flood_warning': 'Tulvavaroitus: korkea jokivirtaama ({discharge:.1f} m³/s)',
                                        'wave_warning': 'Aaltovaroitus: korkeat aallot ({height:.1f} m)',
                                        'morning_forecast': 'Huomisaamu ({date}): {temp_min:.0f}–{temp_max:.0f}°c, {desc}',
                                        'morning_wind': 'Aamutuuli: {wind:.0f} m/s (puuskat {gust:.0f} m/s)',
                                        'morning_precip': 'Sadetodennäköisyys aamulla: {prob:.0f}%', 'morning_visibility': 'Näkyvyys aamulla: {vis:.1f} km',
                                        'local_time': 'Paikallinen aika: {time}', 'wind': 'Tuulen nopeus: {speed:.1f} m/s',
                                        'precipitation': 'Sadetodennäköisyys: {prob:.0f}%', 'air_quality': 'Ilmanlaatu: {quality} (aqi: {aqi})',
                                        'uv_index': 'Uv-indeksi: {index:.1f}', 'uv_low': 'Uv-indeksi: {index:.1f} (matala)',
                                        'uv_moderate': 'Uv-indeksi: {index:.1f} (kohtalainen, huomioi aurinko)',
                                        'uv_high': 'Uv-indeksi: {index:.1f} (korkea, käytä aurinkorasvaa)',
                                        'uv_very_high': 'Uv-indeksi: {index:.1f} (erittäin korkea, suojaa ihosi!)', 'season': 'Vuodenaika: {season}',
                                        'next_holiday': 'Seuraava juhlapäivä: {holiday}', 'warnings': 'Varoitukset:',
                                        'cold_warning_extreme': 'Äärimmäinen kylmävaroitus: äärimmäisen vaarallisia kylmiä lämpötiloja!',
                                        'cold_warning_severe': 'Vaikea kylmävaroitus: hyvin kylmiä lämpötiloja, varaudu varotoimiin',
                                        'cold_warning': 'Kylmävaroitus: kylmiä lämpötiloja, pukeudu lämpimästi',
                                        'wind_warning_high': 'Kovien tuulien varoitus: voimakkaita tuulia, kiinnitä irtaimet',
                                        'wind_advisory': 'Tuulivaroitus: kohtalaisia tuulia odotettavissa',
                                        'precipitation_warning_high': 'Suuren sateen varoitus: hyvin todennäköistä sadetta',
                                        'precipitation_advisory': 'Sadetodennäköisyysvaroitus: mahdollista sadetta',
                                        'rain_warning': 'Sadevaroitus: sadetta odotettavissa', 'snow_warning': 'Lumivaroitus: lumisadetta odotettavissa',
                                        'thunderstorm_warning': 'Ukkosvaroitus: ukkosmyrskyjä odotettavissa',
                                        'uv_warning': 'UV-varoitus: korkea UV-indeksi, suojaa ihosi',
                                        'air_quality_warning': 'Ilmanlaatuvaroitus: huono ilmanlaatu, vältä ulkoilua'},
                               'seasons': {'winter': 'talvi', 'spring': 'kevät', 'summer': 'kesä', 'autumn': 'syksy'},  # Kuun vaiheet
                               'moon_growth': {'growing': 'kasvava', 'waning': 'vähenevä'},  # Ilmanlaatu
                               'air_quality_levels': {1: 'erinomainen', 2: 'hyvä', 3: 'kohtalainen', 4: 'huono', 5: 'vaarallinen'}}, 'en': {  # Time expressions
            'time_expressions': {'nearly_ten_to_two': 'nearly ten to two', 'half_past_one': 'about half past one', 'quarter_to_two': 'about quarter to two',
                                 'quarter_past_twelve': 'about quarter past twelve', 'twelve': 'twelve',
                                 'time_of_day': {'early_morning': 'early morning', 'morning': 'morning', 'forenoon': 'forenoon', 'noon': 'noon',
                                                 'afternoon': 'afternoon', 'early_evening': 'early evening', 'late_evening': 'late evening', 'night': 'night'}},
            # Date
            'date': {'week': 'Week', 'day': 'Day', 'year_complete': 'The year is {pct:.1f} % complete', 'dawn': 'Dawn at {time}',
                     'sunrise': 'sunrise at {time}', 'noon': 'noon at {time}', 'sunset': 'sunset at {time}', 'dusk': 'dusk at {time}',
                     'sun_position': 'Sun is at {elevation:.1f}° elevation and {azimuth:.1f}° direction',
                     'moon_phase': 'Moon is {phase:.1f}% and it is {growth}',
                     'moon_position': 'Moon is at {altitude:.1f}° elevation and {azimuth:.1f}° direction', 'moon_rise': 'Moon rises at {time}',
                     'moon_transit': 'peaks at {time}', 'moon_set': 'sets at {time}', 'sun_visible': '(visible)', 'sun_below': '(below horizon)',
                     'moon_visible': '(visible)', 'moon_below': '(below horizon)', 'snow_depth': 'Snow depth: {depth:.0f} cm',
                     'cloud_cover': 'Cloud cover: {cover}%', 'solar_radiation': 'Solar radiation: {ghi:.0f} W/m² (direct: {dni:.0f} W/m²)',
                     'solar_for_panels': 'For solar panels: {gti:.0f} W/m² (fixed) / {dni:.0f} W/m² (tracking)', 'weather': 'Weather: {temp:.1f}°c, {desc}',
                     'feels_like': 'Feels like: {temp:.1f}°c', 'wind_full': 'Wind: {speed:.1f} m/s from {dir}° (gusts {gust:.1f} m/s)',
                     'wind_no_gust': 'Wind: {speed:.1f} m/s from {dir}°', 'visibility': 'Visibility: {vis:.1f} km',
                     'precip_intensity': 'Precipitation intensity: {intensity:.1f} mm/h',
                     'wave_info': 'Waves: {height:.1f} m, period {period:.1f} s, direction {dir}°', 'flood_discharge': 'River discharge: {discharge:.1f} m³/s',
                     'flood_warning': 'Flood warning: high river discharge ({discharge:.1f} m³/s)', 'wave_warning': 'Wave warning: high waves ({height:.1f} m)',
                     'morning_forecast': 'Tomorrow morning ({date}): {temp_min:.0f}–{temp_max:.0f}°c, {desc}',
                     'morning_wind': 'Morning wind: {wind:.0f} m/s (gusts {gust:.0f} m/s)', 'morning_precip': 'Morning precipitation probability: {prob:.0f}%',
                     'morning_visibility': 'Morning visibility: {vis:.1f} km', 'local_time': 'Local time: {time}',
                     'humidity': 'Humidity: {humidity}%, pressure: {pressure} hpa', 'wind': 'Wind speed: {speed:.1f} m/s',
                     'precipitation': 'Precipitation probability: {prob:.0f}%', 'air_quality': 'Air quality: {quality} (aqi: {aqi})',
                     'uv_index': 'Uv index: {index:.1f}', 'uv_low': 'Uv index: {index:.1f} (low)',
                     'uv_moderate': 'Uv index: {index:.1f} (moderate, beware of sun)', 'uv_high': 'Uv index: {index:.1f} (high, use sunscreen)',
                     'uv_very_high': 'Uv index: {index:.1f} (very high, protect your skin!)', 'season': 'Season: {season}',
                     'next_holiday': 'Next holiday: {holiday}', 'warnings': 'Warnings:',
                     'cold_warning_extreme': 'Extreme cold warning: extremely dangerous cold temperatures!',
                     'cold_warning_severe': 'Severe cold warning: very cold temperatures, take precautions',
                     'cold_warning': 'Cold warning: cold temperatures, dress warmly',
                     'wind_warning_high': 'High wind warning: strong winds, secure loose objects', 'wind_advisory': 'Wind advisory: moderate winds expected',
                     'precipitation_warning_high': 'High precipitation warning: very likely precipitation',
                     'precipitation_advisory': 'Precipitation advisory: possible precipitation', 'rain_warning': 'Rain warning: precipitation expected',
                     'snow_warning': 'Snow warning: snowfall expected', 'thunderstorm_warning': 'Thunderstorm warning: thunderstorms expected',
                     'uv_warning': 'UV warning: high UV index, protect your skin',
                     'air_quality_warning': 'Air quality warning: poor air quality, avoid outdoor activities'},  # Season
            'seasons': {'winter': 'winter', 'spring': 'spring', 'summer': 'summer', 'autumn': 'autumn'},  # Moon phases
            'moon_growth': {'growing': 'growing', 'waning': 'waning'},  # Air quality
            'air_quality_levels': {1: 'excellent', 2: 'good', 3: 'moderate', 4: 'poor', 5: 'dangerous'}}}

        return translations.get(self.language, translations['fi'])

    def get_time_expression(self):
        """Generate a natural language time expression for the current time.

        Time is mapped to specific expressions such as "quarter to two",
        "half past one", etc. Times close to the hour (within ~7 minutes)
        are expressed as "about X o'clock".

        Returns:
            str: A string representation of the current time.
        """
        hours = self.now.hour
        minutes = self.now.minute

        # Convert 24-hour format to 12-hour format for expressions
        display_hour = hours % 12
        if display_hour == 0:
            display_hour = 12

        next_hour = (hours + 1) % 12
        if next_hour == 0:
            next_hour = 12

        finnish_current_hour = _get_finnish_hour(display_hour)
        finnish_next_hour = _get_finnish_hour(next_hour)

        # Time intervals for natural expressions:
        # 0-7: "about X" (just past the hour)
        # 8-22: "quarter past X"
        # 23-37: "half past X"
        # 38-52: "quarter to X+1"
        # 53-59: "about X+1" (almost next hour)

        if minutes <= 7:
            # About X o'clock (just past)
            if self.language == 'fi':
                return f"noin {finnish_current_hour}"
            else:
                return f"about {display_hour} o'clock"
        elif minutes <= 22:
            # Quarter past X
            if self.language == 'fi':
                return f"noin varttia yli {finnish_current_hour}"
            else:
                return f"about quarter past {display_hour}"
        elif minutes <= 37:
            # Half past X
            if self.language == 'fi':
                return f"noin puoli {finnish_next_hour}"
            else:
                return f"about half past {display_hour}"
        elif minutes <= 52:
            # Quarter to X+1
            if self.language == 'fi':
                return f"noin varttia vaille {finnish_next_hour}"
            else:
                return f"about quarter to {next_hour}"
        else:
            # About X+1 o'clock (almost next hour)
            if self.language == 'fi':
                return f"noin {finnish_next_hour}"
            else:
                return f"about {next_hour} o'clock"

    def get_coordinates_for_city(self, city):
        """Get coordinates and country for a city using OpenStreetMap Nominatim API"""
        try:
            url = "https://nominatim.openstreetmap.org/search"
            params = {'q': city, 'format': 'json', 'limit': 1, 'addressdetails': 1}

            # Add headers to comply with Nominatim usage policy
            headers = {'User-Agent': 'FinnishTimeInfoApp/1.0 (educational project)'}

            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data:
                lat = float(data[0]['lat'])
                lon = float(data[0]['lon'])

                # Extract country code from address details
                address = data[0].get('address', {})
                country_code = address.get('country_code', '').upper()
                self.country_code = country_code if country_code else 'FI'

                return lat, lon
        except Exception as e:
            print(f"Error getting coordinates: {e}")

        self.country_code = 'FI'  # Default to Finland
        return None

    def get_timezone_for_coordinates(self, latitude, longitude):
        """Get timezone name for coordinates"""
        if TIMEZONE_FINDER_AVAILABLE and tf:
            # Try "unique" fast path
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
            return "UTC"  # Default fallback

    def get_time_of_day(self):
        """Get time of day"""
        hour = self.now.hour
        time_of_day_translations = self.get_translations()['time_expressions']['time_of_day']

        if 4 <= hour < 6:
            return time_of_day_translations['early_morning']
        elif 6 <= hour < 10:
            return time_of_day_translations['morning']
        elif 10 <= hour < 12:
            return time_of_day_translations['forenoon']
        elif 12 <= hour < 14:
            return time_of_day_translations['noon']
        elif 14 <= hour < 18:
            return time_of_day_translations['afternoon']
        elif 18 <= hour < 20:
            return time_of_day_translations['early_evening']
        elif 20 <= hour < 24:
            return time_of_day_translations['late_evening']
        else:  # 0-4
            return time_of_day_translations['night']

    def get_weather_data(self):
        """Get weather information from FMI and Open-Meteo APIs"""
        try:
            # Try FMI Open Data service first
            if FMI_AVAILABLE:
                try:
                    # Use bounding box around coordinates to find nearest station
                    bbox_margin = 0.5  # degrees
                    args = [f"bbox={self.longitude - bbox_margin},{self.latitude - bbox_margin},{self.longitude + bbox_margin},{self.latitude + bbox_margin}",
                            "timeseries=True", ]

                    obs = download_stored_query("fmi::observations::weather::multipointcoverage", args=args)

                    # Pick one station and get the latest values
                    if obs.data:
                        station = sorted(obs.data.keys())[0]
                        station_data = obs.data[station]

                        # Get latest temperature (check for nan values)
                        latest_temp = None
                        if "Air temperature" in station_data:
                            temps = station_data["Air temperature"]["values"]
                            if temps:
                                val = temps[-1]
                                if val is not None and not (isinstance(val, float) and math.isnan(val)):
                                    latest_temp = val

                        # Get latest humidity (FMI uses "Relative humidity", check for nan)
                        latest_humidity = None
                        if "Relative humidity" in station_data:
                            humidity_values = station_data["Relative humidity"]["values"]
                            if humidity_values:
                                val = humidity_values[-1]
                                if val is not None and not (isinstance(val, float) and math.isnan(val)):
                                    latest_humidity = val

                        # Get the latest wind speed (check for nan values)
                        latest_wind = None
                        if "Wind speed" in station_data:
                            wind_values = station_data["Wind speed"]["values"]
                            if wind_values:
                                val = wind_values[-1]
                                if val is not None and not (isinstance(val, float) and math.isnan(val)):
                                    latest_wind = val

                        # Get the latest pressure (check for nan values)
                        latest_pressure = None
                        if "Pressure (msl)" in station_data:
                            pressure_values = station_data["Pressure (msl)"]["values"]
                            if pressure_values:
                                val = pressure_values[-1]
                                if val is not None and not (isinstance(val, float) and math.isnan(val)):
                                    latest_pressure = val

                        # Get snow depth (check for nan values)
                        snow_depth = None
                        if "Snow depth" in station_data:
                            snow_values = station_data["Snow depth"]["values"]
                            if snow_values:
                                val = snow_values[-1]
                                if val is not None and not (isinstance(val, float) and math.isnan(val)):
                                    snow_depth = val

                        # Get wind direction
                        wind_direction = None
                        if "Wind direction" in station_data:
                            dir_values = station_data["Wind direction"]["values"]
                            if dir_values:
                                val = dir_values[-1]
                                if val is not None and not (isinstance(val, float) and math.isnan(val)):
                                    wind_direction = val

                        # Get gust speed
                        gust_speed = None
                        if "Gust speed" in station_data:
                            gust_values = station_data["Gust speed"]["values"]
                            if gust_values:
                                val = gust_values[-1]
                                if val is not None and not (isinstance(val, float) and math.isnan(val)):
                                    gust_speed = val

                        # Get visibility
                        visibility = None
                        if "Horizontal visibility" in station_data:
                            vis_values = station_data["Horizontal visibility"]["values"]
                            if vis_values:
                                val = vis_values[-1]
                                if val is not None and not (isinstance(val, float) and math.isnan(val)):
                                    visibility = val

                        # Get precipitation intensity
                        precip_intensity = None
                        if "Precipitation intensity" in station_data:
                            precip_values = station_data["Precipitation intensity"]["values"]
                            if precip_values:
                                val = precip_values[-1]
                                if val is not None and not (isinstance(val, float) and math.isnan(val)):
                                    precip_intensity = val

                        fmi_data = {"temperature": latest_temp, "description": "ei saatavilla", "humidity": latest_humidity, "pressure": latest_pressure,
                                    "wind_speed": latest_wind, "wind_direction": wind_direction, "gust_speed": gust_speed, "visibility": visibility,
                                    "precip_intensity": precip_intensity, "snow_depth": snow_depth, "apparent_temp": None, "precipitation_probability": None,
                                    "weather_code": None}

                        # Supplement missing data from Open-Meteo
                        try:
                            url = "https://api.open-meteo.com/v1/forecast"
                            params = {"latitude": self.latitude, "longitude": self.longitude,
                                      "current": "apparent_temperature,wind_speed_10m,wind_direction_10m,wind_gusts_10m",
                                      "hourly": "precipitation_probability,weathercode", "timezone": self.timezone, "forecast_hours": 1, }
                            response = requests.get(url, params=params, timeout=10)
                            response.raise_for_status()
                            data = response.json()

                            current = data.get("current", {})
                            hourly = data.get("hourly", {})

                            # Always get the apparent temperature from Open-Meteo
                            fmi_data["apparent_temp"] = current.get("apparent_temperature")

                            # Supplement missing wind data
                            if fmi_data["wind_speed"] is None:
                                fmi_data["wind_speed"] = current.get("wind_speed_10m")
                            if fmi_data["wind_direction"] is None:
                                fmi_data["wind_direction"] = current.get("wind_direction_10m")
                            if fmi_data["gust_speed"] is None:
                                fmi_data["gust_speed"] = current.get("wind_gusts_10m")

                            # Get precipitation and weather code
                            if fmi_data["precipitation_probability"] is None:
                                if hourly.get("precipitation_probability"):
                                    fmi_data["precipitation_probability"] = hourly["precipitation_probability"][0]
                            if fmi_data["weather_code"] is None:
                                if hourly.get("weathercode"):
                                    fmi_data["weather_code"] = hourly["weathercode"][0]
                        except:
                            pass  # Keep FMI data as-is if Open-Meteo fails

                        return fmi_data
                except Exception as e:
                    pass  # Fall back to Open-Meteo entirely

            # Use Open-Meteo as full fallback if FMI fails
            try:
                url = "https://api.open-meteo.com/v1/forecast"
                params = {"latitude": self.latitude, "longitude": self.longitude,
                          "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,pressure_msl,wind_speed_10m,wind_direction_10m,wind_gusts_10m",
                          "hourly": "precipitation_probability,weathercode", "timezone": self.timezone, "forecast_hours": 1, }

                response = requests.get(url, params=params, timeout=20)
                response.raise_for_status()
                data = response.json()

                current = data.get("current", {})
                hourly = data.get("hourly", {})

                return {"temperature": current.get("temperature_2m"), "apparent_temp": current.get("apparent_temperature"), "description": "ei saatavilla",
                        "humidity": current.get("relative_humidity_2m"), "pressure": current.get("pressure_msl"), "wind_speed": current.get("wind_speed_10m"),
                        "wind_direction": current.get("wind_direction_10m"), "gust_speed": current.get("wind_gusts_10m"), "visibility": None,
                        "precip_intensity": current.get("precipitation"), "snow_depth": None,
                        "precipitation_probability": hourly.get("precipitation_probability", [None])[0], "weather_code": hourly.get("weathercode", [None])[0]}
            except Exception as e:
                pass

        except Exception as e:
            pass

        # Return sample data if both APIs fail
        return {"temperature": -14.0, "apparent_temp": -20.0, "description": "selkeää", "humidity": 90, "pressure": 1025, "wind_speed": 3.2,
                "wind_direction": 180, "gust_speed": 5.0, "visibility": None, "precip_intensity": 0, "snow_depth": None, "precipitation_probability": 10,
                "weather_code": 0}

    def get_weather_description(self, weather_code):
        """Translate Open-Meteo weather code to description"""
        if weather_code is None:
            return "ei saatavilla" if self.language == 'fi' else "not available"

        # Weather code translations (Open-Meteo WMO codes)
        weather_codes_fi = {0: "selkeää", 1: "enimmäkseen selkeää", 2: "puolipilvistä", 3: "pilvistä", 45: "sumua", 48: "huurtuvaa sumua",
                            51: "kevyttä tihkusadetta", 53: "tihkusadetta", 55: "tiheää tihkusadetta", 56: "jäätävää tihkua", 57: "tiheää jäätävää tihkua",
                            61: "kevyttä sadetta", 63: "sadetta", 65: "rankkasadetta", 66: "jäätävää sadetta", 67: "rankkaa jäätävää sadetta",
                            71: "kevyttä lumisadetta", 73: "lumisadetta", 75: "tiheää lumisadetta", 77: "lumijyväsiä", 80: "kevyitä sadekuuroja",
                            81: "sadekuuroja", 82: "rankkoja sadekuuroja", 85: "kevyitä lumikuuroja", 86: "rankkoja lumikuuroja", 95: "ukkosta",
                            96: "ukkosta ja rakeita", 99: "ukkosta ja rankkoja rakeita"}

        weather_codes_en = {0: "clear sky", 1: "mainly clear", 2: "partly cloudy", 3: "overcast", 45: "fog", 48: "depositing rime fog", 51: "light drizzle",
                            53: "drizzle", 55: "dense drizzle", 56: "light freezing drizzle", 57: "dense freezing drizzle", 61: "light rain", 63: "rain",
                            65: "heavy rain", 66: "light freezing rain", 67: "heavy freezing rain", 71: "light snow", 73: "snow", 75: "heavy snow",
                            77: "snow grains", 80: "light rain showers", 81: "rain showers", 82: "violent rain showers", 85: "light snow showers",
                            86: "heavy snow showers", 95: "thunderstorm", 96: "thunderstorm with hail", 99: "thunderstorm with heavy hail"}

        codes = weather_codes_fi if self.language == 'fi' else weather_codes_en
        return codes.get(weather_code, "tuntematon" if self.language == 'fi' else "unknown")

    def get_uv_index(self):
        """Get UV index from Open-Meteo API"""
        try:
            url = "https://api.open-meteo.com/v1/forecast"
            params = {"latitude": self.latitude, "longitude": self.longitude, "hourly": "uv_index", "timezone": "Europe/Helsinki", "forecast_days": 1, }

            response = requests.get(url, params=params, timeout=20)
            response.raise_for_status()
            data = response.json()

            # Get current UV index
            uv_index = data["hourly"]["uv_index"][0] if data["hourly"]["uv_index"] else 0.5
            return uv_index
        except:
            # Return sample data if API call fails
            return 0.5

    def get_air_quality(self):
        """Get air quality data from Open-Meteo Air Quality API"""
        try:
            url = "https://air-quality-api.open-meteo.com/v1/air-quality"
            params = {"latitude": self.latitude, "longitude": self.longitude, "current": "european_aqi,pm10,pm2_5", "timezone": self.timezone}

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            current = data.get("current", {})
            european_aqi = current.get("european_aqi")
            pm10 = current.get("pm10")
            pm2_5 = current.get("pm2_5")

            # Convert European AQI (0-100+) to simple 1-5 scale
            # EAQI: 0-20 Good, 21-40 Fair, 41-60 Moderate, 61-80 Poor, 81+ Very Poor
            aqi_simple = None
            if european_aqi is not None:
                if european_aqi <= 20:
                    aqi_simple = 1  # Good/Excellent
                elif european_aqi <= 40:
                    aqi_simple = 2  # Fair/Good
                elif european_aqi <= 60:
                    aqi_simple = 3  # Moderate
                elif european_aqi <= 80:
                    aqi_simple = 4  # Poor
                else:
                    aqi_simple = 5  # Very Poor/Dangerous

            return {"aqi": aqi_simple, "european_aqi": european_aqi, "pm2_5": pm2_5, "pm10": pm10}
        except:
            return {"aqi": None, "european_aqi": None, "pm2_5": None, "pm10": None}

    def get_solar_radiation(self):
        """Get solar radiation and cloud cover data from Open-Meteo API.

        Returns data useful for solar panel owners:
        - cloud_cover: Cloud coverage percentage
        - ghi: Global Horizontal Irradiance (total on flat surface) W/m²
        - dni: Direct Normal Irradiance (perpendicular to sun) W/m² - for tracking panels
        - dhi: Diffuse Horizontal Irradiance (scattered light) W/m²
        - gti: Global Tilted Irradiance W/m² - for fixed tilted panels
        """
        try:
            url = "https://api.open-meteo.com/v1/forecast"
            params = {"latitude": self.latitude, "longitude": self.longitude,
                      "current": "cloud_cover,shortwave_radiation,direct_radiation,diffuse_radiation,direct_normal_irradiance,global_tilted_irradiance",
                      "timezone": self.timezone}

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            current = data.get("current", {})

            return {"cloud_cover": current.get("cloud_cover"),  # %
                    "ghi": current.get("shortwave_radiation"),  # W/m² - Global Horizontal Irradiance
                    "dni": current.get("direct_normal_irradiance"),  # W/m² - Direct Normal Irradiance
                    "dhi": current.get("diffuse_radiation"),  # W/m² - Diffuse Horizontal Irradiance
                    "gti": current.get("global_tilted_irradiance"),  # W/m² - Global Tilted Irradiance
                    "direct": current.get("direct_radiation")  # W/m² - Direct radiation on horizontal
                    }
        except:
            return {"cloud_cover": None, "ghi": None, "dni": None, "dhi": None, "gti": None, "direct": None}

    def get_marine_data(self):
        """Get marine/wave data from Open-Meteo Marine API (for coastal areas)"""
        try:
            url = "https://marine-api.open-meteo.com/v1/marine"
            params = {"latitude": self.latitude, "longitude": self.longitude,
                      "current": "wave_height,wave_direction,wave_period,wind_wave_height,swell_wave_height", "timezone": self.timezone}

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            current = data.get("current", {})
            return {"wave_height": current.get("wave_height"),  # meters
                    "wave_direction": current.get("wave_direction"),  # degrees
                    "wave_period": current.get("wave_period"),  # seconds
                    "wind_wave_height": current.get("wind_wave_height"), "swell_wave_height": current.get("swell_wave_height")}
        except:
            return {"wave_height": None, "wave_direction": None, "wave_period": None, "wind_wave_height": None, "swell_wave_height": None}

    def get_flood_data(self):
        """Get river discharge/flood data from Open-Meteo Flood API"""
        try:
            url = "https://flood-api.open-meteo.com/v1/flood"
            params = {"latitude": self.latitude, "longitude": self.longitude, "daily": "river_discharge,river_discharge_mean,river_discharge_max",
                      "forecast_days": 1}

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            daily = data.get("daily", {})
            return {"river_discharge": daily.get("river_discharge", [None])[0],  # m³/s
                    "river_discharge_mean": daily.get("river_discharge_mean", [None])[0], "river_discharge_max": daily.get("river_discharge_max", [None])[0]}
        except:
            return {"river_discharge": None, "river_discharge_mean": None, "river_discharge_max": None}

    def get_morning_forecast(self):
        """Get weather forecast for tomorrow morning (6-9 AM)"""
        try:
            url = "https://api.open-meteo.com/v1/forecast"
            params = {"latitude": self.latitude, "longitude": self.longitude,
                      "hourly": "temperature_2m,apparent_temperature,precipitation_probability,weathercode,wind_speed_10m,wind_gusts_10m,visibility",
                      "timezone": self.timezone, "forecast_days": 2}

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            hourly = data.get("hourly", {})
            times = hourly.get("time", [])

            # Find tomorrow's morning hours (6-9 AM)
            tomorrow = (self.now + datetime.timedelta(days=1)).date()
            morning_indices = []

            for i, time_str in enumerate(times):
                dt = datetime.datetime.fromisoformat(time_str)
                if dt.date() == tomorrow and 6 <= dt.hour <= 9:
                    morning_indices.append(i)

            if not morning_indices:
                return None

            # Get average/worst values for morning
            temps = [hourly["temperature_2m"][i] for i in morning_indices if hourly["temperature_2m"][i] is not None]
            apparent = [hourly["apparent_temperature"][i] for i in morning_indices if hourly["apparent_temperature"][i] is not None]
            precip = [hourly["precipitation_probability"][i] for i in morning_indices if hourly["precipitation_probability"][i] is not None]
            codes = [hourly["weathercode"][i] for i in morning_indices if hourly["weathercode"][i] is not None]
            winds = [hourly["wind_speed_10m"][i] for i in morning_indices if hourly["wind_speed_10m"][i] is not None]
            gusts = [hourly["wind_gusts_10m"][i] for i in morning_indices if hourly["wind_gusts_10m"][i] is not None]
            vis = [hourly["visibility"][i] for i in morning_indices if hourly.get("visibility") and hourly["visibility"][i] is not None]

            return {"date": tomorrow, "temp_min": min(temps) if temps else None, "temp_max": max(temps) if temps else None,
                    "apparent_min": min(apparent) if apparent else None, "precip_prob_max": max(precip) if precip else None,
                    "weather_code": max(set(codes), key=codes.count) if codes else None,  # Most common
                    "wind_max": max(winds) if winds else None, "gust_max": max(gusts) if gusts else None, "visibility_min": min(vis) if vis else None}
        except:
            return None

    def get_weather_warnings(self, weather_data, uv_index=None, air_quality_data=None):
        """Create weather warnings based on weather conditions, UV index, and air quality"""
        warnings = []
        translations = self.get_translations()['date']

        # Temperature warnings
        if weather_data.get("temperature") is not None:
            temp = weather_data["temperature"]
            if temp <= -30:
                warnings.append(translations['cold_warning_extreme'])
            elif temp <= -20:
                warnings.append(translations['cold_warning_severe'])
            elif temp <= -10:
                warnings.append(translations['cold_warning'])

        # Wind warnings
        if weather_data.get("wind_speed") is not None:
            wind_speed = weather_data["wind_speed"]
            if wind_speed >= 25:
                warnings.append(translations['wind_warning_high'])
            elif wind_speed >= 15:
                warnings.append(translations['wind_advisory'])

        # Precipitation probability warnings
        if weather_data.get("precipitation_probability") is not None:
            precip_prob = weather_data["precipitation_probability"]
            if precip_prob >= 80:
                warnings.append(translations['precipitation_warning_high'])
            elif precip_prob >= 50:
                warnings.append(translations['precipitation_advisory'])

        # Weather code-based warnings
        if weather_data.get("weather_code") is not None:
            weather_code = weather_data["weather_code"]
            # Weather codes: https://open-meteo.com/en/docs
            if weather_code in [51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82]:  # Rain
                warnings.append(translations['rain_warning'])
            elif weather_code in [71, 73, 75, 77, 85, 86]:  # Snow
                warnings.append(translations['snow_warning'])
            elif weather_code in [95, 96, 99]:  # Thunderstorms
                warnings.append(translations['thunderstorm_warning'])

        # UV index warnings
        if uv_index is not None and uv_index >= 6:
            warnings.append(translations['uv_warning'])

        # Air quality warnings
        if air_quality_data is not None and air_quality_data.get('aqi') is not None:
            aqi = air_quality_data['aqi']
            if aqi >= 4:  # Poor or worse
                warnings.append(translations['air_quality_warning'])

        return warnings

    def get_season(self):
        """Determine the season based on hemisphere"""
        month = self.now.month
        season_translations = self.get_translations()['seasons']

        # Determine if we're in the Northern or the Southern Hemisphere
        is_northern_hemisphere = self.latitude >= 0

        if is_northern_hemisphere:
            # Northern Hemisphere seasons
            if month in [12, 1, 2]:
                return season_translations['winter']
            elif month in [3, 4, 5]:
                return season_translations['spring']
            elif month in [6, 7, 8]:
                return season_translations['summer']
            else:  # 9, 10, 11
                return season_translations['autumn']
        else:
            # Southern Hemisphere seasons (opposite)
            if month in [12, 1, 2]:
                return season_translations['summer']
            elif month in [3, 4, 5]:
                return season_translations['autumn']
            elif month in [6, 7, 8]:
                return season_translations['winter']
            else:  # 9, 10, 11
                return season_translations['spring']

    def get_next_holiday(self):
        """
        Get the name and the date of the next public holiday for the detected country
        and the number of days remaining until that holiday.

        Uses the country_code detected from the location (via Nominatim geocoding)
        to determine which country's holidays to use.

        Returns
        -------
        str
            A formatted string representing the next public holiday and the
            number of days until it occurs.
        """
        try:
            if HOLIDAYS_AVAILABLE:
                # Include current year + next year so "next holiday" works near year-end
                years = (self.now.year, self.now.year + 1)

                # Get public holidays for the detected country
                try:
                    country_holidays_obj = holidays.country_holidays(self.country_code, years=years)
                except NotImplementedError:
                    # Country not supported by holidays library, fallback to Finland
                    country_holidays_obj = holidays.country_holidays('FI', years=years)

                # Find the next holiday
                current_date = self.now.date()
                for holiday_date in sorted(country_holidays_obj.keys()):
                    if holiday_date >= current_date:
                        days_until = (holiday_date - current_date).days
                        holiday_name = country_holidays_obj[holiday_date]
                        # Return holiday name and days until in the current language
                        if self.language == 'fi':
                            return f"{holiday_name} ({holiday_date.strftime('%d.%m.')}) on {days_until} päivän päästä"
                        else:
                            return f"{holiday_name} ({holiday_date.strftime('%d.%m.')}) in {days_until} days"

                # If no holiday found this year, return first one next year
                try:
                    next_year_holidays = holidays.country_holidays(self.country_code, years=self.now.year + 1)
                except NotImplementedError:
                    next_year_holidays = holidays.country_holidays('FI', years=self.now.year + 1)
                if next_year_holidays:
                    first_holiday_date = min(next_year_holidays.keys())
                    first_holiday_name = next_year_holidays[first_holiday_date]
                    days_until = (first_holiday_date - current_date).days
                    if self.language == 'fi':
                        return f"{first_holiday_name} ({first_holiday_date.strftime('%d.%m.%Y')}) on {days_until} päivän päästä"
                    else:
                        return f"{first_holiday_name} ({first_holiday_date.strftime('%d.%m.%Y')}) in {days_until} days"

        except Exception as e:
            pass

        # Fallback to hardcoded holidays for 2026
        year = self.now.year

        # Most significant holidays in Finland (without movable days)
        holidays_list = [(1, 1, "Uudenvuodenpäivä"), (1, 6, "Loppiainen"), (5, 1, "Vappu"), (12, 6, "Itsensä turvaamisen päivä"), (12, 24, "Jouluaatto"),
                         (12, 25, "Joulupäivä"), (12, 26, "Tapaninpäivä")]

        # Calculate movable holidays for year 2026
        # Good Friday, Ascension Day, Pentecost
        easter_date = datetime.date(2026, 3, 29)  # Good Friday 2026
        holidays_list.append((3, 29, "Pitkäperjantai"))

        easter_sunday = datetime.date(2026, 3, 31)  # Easter Sunday 2026
        holidays_list.append((3, 31, "Pääsiäispäivä"))

        easter_monday = datetime.date(2026, 4, 1)  # Easter Monday 2026
        holidays_list.append((4, 1, "Toinen pääsiäispäivä"))

        ascension_day = datetime.date(2026, 5, 14)  # Ascension Day 2026
        holidays_list.append((5, 14, "Helatorstai"))

        pentecost = datetime.date(2026, 5, 24)  # Pentecost 2026
        holidays_list.append((5, 24, "Helluntaipäivä"))

        # Sort holidays chronologically
        holidays_list.sort()

        # Find the next holiday
        for month, day, name in holidays_list:
            holiday_date = datetime.date(year, month, day)
            if holiday_date >= self.now.date():
                days_until = (holiday_date - self.now.date()).days
                if self.language == 'fi':
                    return f"{name} ({day}.{month}.) on {days_until} päivän päästä"
                else:
                    return f"{name} ({day}.{month}.) in {days_until} days"

        # If not found this year, return the first one next year
        next_year = year + 1
        first_holiday = holidays_list[0]
        if self.language == 'fi':
            return f"{first_holiday[2]} ({first_holiday[1]}.{first_holiday[0]}.{next_year}) on {days_until} päivän päästä"
        else:
            return f"{first_holiday[2]} ({first_holiday[1]}.{first_holiday[0]}.{next_year}) in {days_until} days"

    @property
    def get_solar_info(self):
        """Calculate solar info including dawn, sunrise, noon, sunset, dusk times and sun position"""
        location = LocationInfo(name="Custom", region="Custom", timezone=self.timezone, latitude=self.latitude, longitude=self.longitude)

        # Pass timezone to get local times instead of UTC
        if ZONEINFO_AVAILABLE:
            local_tz = ZoneInfo(self.timezone)
            s = sun(location.observer, date=self.now.date(), tzinfo=local_tz)
        else:
            s = sun(location.observer, date=self.now.date())

        # Sun position (elevation and azimuth) - use ephem library
        observer = self.do_observer()

        sun_body = ephem.Sun()
        sun_body.compute(observer)

        sun_elevation = math.degrees(sun_body.alt)
        sun_azimuth = math.degrees(sun_body.az)

        # Format times (astral returns timezone-aware datetimes)
        dawn_time = s['dawn'].strftime("%H.%M")
        sunrise_time = s['sunrise'].strftime("%H.%M")
        noon_time = s['noon'].strftime("%H.%M")
        sunset_time = s['sunset'].strftime("%H.%M")
        dusk_time = s['dusk'].strftime("%H.%M")

        return {'dawn': dawn_time, 'sunrise': sunrise_time, 'noon': noon_time, 'sunset': sunset_time, 'dusk': dusk_time, 'elevation': sun_elevation,
                'azimuth': sun_azimuth}

    def do_observer(self) -> Any:
        """
        Creates and configures an astronomical observer instance with location
        and time information. The observer is set up to calculate astronomical
        phenomena such as sunrise, sunset, and twilight times for a given
        geographical location and time.

        Returns
        -------
        Any
            An observer object initialized with the specified latitude,
            longitude, and current date-time in UTC.
        """
        observer = ephem.Observer()
        observer.lat = str(self.latitude)
        observer.lon = str(self.longitude)

        # ephem expects UTC time, so convert local time to UTC
        if ZONEINFO_AVAILABLE:
            local_tz = ZoneInfo(self.timezone)
            local_dt = self.now.replace(tzinfo=local_tz)
            utc_dt = local_dt.astimezone(ZoneInfo('UTC'))
            observer.date = utc_dt.replace(tzinfo=None)
        else:
            # Fallback: assume Europe/Helsinki (UTC+2 in winter, UTC+3 in summer)
            utc_offset = 2  # Winter time
            observer.date = self.now - datetime.timedelta(hours=utc_offset)
        return observer

    def get_lunar_info(self):
        """Calculate lunar info including phase, position, and rise/set/transit times"""
        observer = self.do_observer()

        moon = ephem.Moon()
        moon.compute(observer)

        # Moon phase (percentage)
        moon_phase = moon.phase

        # Is the moon waxing or waning?
        if moon.phase < 50:
            moon_growth = "kasvava"  # waxing
        else:
            moon_growth = "vähenevä"  # waning

        # Moon altitude and azimuth
        moon_altitude = math.degrees(moon.alt)
        moon_azimuth = math.degrees(moon.az)

        # Helper to convert ephem date to local time string
        def ephem_to_local_time(ephem_date):
            utc_datetime = ephem.Date(ephem_date).datetime()
            if ZONEINFO_AVAILABLE:
                utc_datetime = utc_datetime.replace(tzinfo=ZoneInfo('UTC'))
                local_datetime = utc_datetime.astimezone(ZoneInfo(self.timezone))
                return local_datetime.strftime("%H.%M")
            else:
                # Fallback: add 2 hours for Finland winter time
                local_datetime = utc_datetime + datetime.timedelta(hours=2)
                return local_datetime.strftime("%H.%M")

        # Get moon rise/set/transit times for today
        # Reset observer to start of day (local midnight in UTC)
        if ZONEINFO_AVAILABLE:
            local_midnight = self.now.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=ZoneInfo(self.timezone))
            utc_midnight = local_midnight.astimezone(ZoneInfo('UTC'))
            observer.date = utc_midnight.replace(tzinfo=None)
        else:
            observer.date = self.now.replace(hour=0, minute=0, second=0, microsecond=0) - datetime.timedelta(hours=2)

        moon_rise = None
        moon_set = None
        moon_transit = None

        try:
            rise = observer.next_rising(moon)
            # Check if rise is within today (local time)
            rise_dt = ephem.Date(rise).datetime()
            # Sets moon rise time if within today
            if rise_dt.date() == self.now.date() or (rise_dt + datetime.timedelta(hours=2)).date() == self.now.date():
                moon_rise = ephem_to_local_time(rise)
        except (ephem.AlwaysUpError, ephem.NeverUpError):
            pass

        try:
            setting = observer.next_setting(moon)
            set_dt = ephem.Date(setting).datetime()
            # Converts valid moonset time to local time
            if set_dt.date() == self.now.date() or (set_dt + datetime.timedelta(hours=2)).date() == self.now.date():
                moon_set = ephem_to_local_time(setting)
        except (ephem.AlwaysUpError, ephem.NeverUpError):
            pass

        try:
            transit = observer.next_transit(moon)
            transit_dt = ephem.Date(transit).datetime()
            # Converts valid moon transit time to local format
            if transit_dt.date() == self.now.date() or (transit_dt + datetime.timedelta(hours=2)).date() == self.now.date():
                moon_transit = ephem_to_local_time(transit)
        except:
            pass

        return {'phase': moon_phase, 'growth': moon_growth, 'altitude': moon_altitude, 'azimuth': moon_azimuth, 'rise': moon_rise, 'set': moon_set,
                'transit': moon_transit}

    def get_date_info(self):
        """Get date info"""
        day_name = self.now.strftime("%A")
        day_num = self.now.day
        month_name = self.now.strftime("%B")
        year = self.now.year

        # Week number (ISO)
        week_num = self.now.isocalendar()[1]

        # Day of the year (1-366)
        day_of_year = self.now.timetuple().tm_yday

        # Ordinal suffix with special cases
        if 11 <= day_num % 100 <= 13:
            suffix = "th"
        else:
            suffix = {1: "st", 2: "nd", 3: "rd"}.get(day_num % 10, "th")

        # Number of days in year (leap year check)
        if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0):
            days_in_year = 366
        else:
            days_in_year = 365

        # Weeks in a year (week number of December 28th is the last ISO week)
        last_week = datetime.date(year, 12, 28).isocalendar()[1]
        weeks_in_year = last_week

        # Percentage complete (1 decimal) - including time of day
        # Calculate how much of the current day has passed (hours + minutes)
        day_fraction = (self.now.hour + self.now.minute / 60.0) / 24.0
        # Add this fraction to the day of year (subtract 1 because we're adding a fraction)
        fractional_day_of_year = day_of_year - 1 + day_fraction
        pct_complete = (fractional_day_of_year / days_in_year) * 100

        return {'day_name': day_name, 'day_num': day_num, 'month_name': month_name, 'year': year, 'week_num': week_num, 'day_of_year': day_of_year,
                'days_in_year': days_in_year, 'weeks_in_year': weeks_in_year, 'pct_complete': pct_complete}

    def display_info(self):
        """Display all information in the selected language"""
        # Get all information
        time_expression = self.get_time_expression()
        time_of_day = self.get_time_of_day()
        weather_data = self.get_weather_data()
        air_quality_data = self.get_air_quality()
        uv_index = self.get_uv_index()
        solar_radiation = self.get_solar_radiation()
        marine_data = self.get_marine_data()
        flood_data = self.get_flood_data()
        morning_forecast = self.get_morning_forecast()
        season = self.get_season()
        next_holiday = self.get_next_holiday()
        solar_info = self.get_solar_info
        lunar_info = self.get_lunar_info()
        date_info = self.get_date_info()
        translations = self.get_translations()
        finnish_translations = get_finnish_translations()

        # Time
        clock = self.now.strftime("%H.%M")

        # Check if location timezone differs from system timezone
        location_time_str = None
        if ZONEINFO_AVAILABLE and self.system_timezone:
            try:
                # Get the location's local time
                location_tz = ZoneInfo(self.timezone)
                location_now = datetime.datetime.now(location_tz)
                location_time_str = location_now.strftime("%H.%M")

                # Check if timezones are different by comparing current hour
                system_now = datetime.datetime.now().astimezone()
                if location_now.hour != system_now.hour or location_now.minute != system_now.minute:
                    # Timezones differ, we'll show local time
                    pass
                else:
                    location_time_str = None  # Same time, don't show
            except:
                location_time_str = None

        # Date translations (always in Finnish for proper grammar)
        day_name_fi = finnish_translations['days'].get(date_info['day_name'], date_info['day_name'])
        month_name_genitive = finnish_translations['months_genitive'].get(date_info['month_name'], date_info['month_name'])

        # Display information in the selected language
        date_strings = translations['date']

        # Display introductory sentences in the selected language
        if self.language == 'fi':
            print(f"Kello on {time_expression} ({clock}), joten on {time_of_day}.")
            print(f"On {day_name_fi}, {date_info['day_num']}. {month_name_genitive}, {date_info['year']}.")
            print(
                f"Viikon numero on {date_info['week_num']}/{date_info['weeks_in_year']}, ja päivän numero on {date_info['day_of_year']}/{date_info['days_in_year']}.")
        else:
            print(f"The time is {time_expression} ({clock}), so it's {time_of_day}.")
            print(f"It's {day_name_fi}, {date_info['day_num']}. {month_name_genitive}, {date_info['year']}.")
            print(
                f"Week number is {date_info['week_num']}/{date_info['weeks_in_year']}, and day number is {date_info['day_of_year']}/{date_info['days_in_year']}.")

        # Show local time at location if different from system timezone
        if location_time_str:
            print(date_strings['local_time'].format(time=location_time_str))

        print(date_strings['year_complete'].format(pct=date_info['pct_complete']))

        # Solar times: dawn, sunrise, noon, sunset, dusk
        solar_line = date_strings['dawn'].format(time=solar_info['dawn']) + ", "
        solar_line += date_strings['sunrise'].format(time=solar_info['sunrise']) + ", "
        solar_line += date_strings['noon'].format(time=solar_info['noon']) + ", "
        solar_line += date_strings['sunset'].format(time=solar_info['sunset']) + ", "
        solar_line += date_strings['dusk'].format(time=solar_info['dusk'])
        print(solar_line)

        # Sun position with visibility status
        sun_visibility = date_strings['sun_visible'] if solar_info['elevation'] > 0 else date_strings['sun_below']
        print(date_strings['sun_position'].format(elevation=solar_info['elevation'], azimuth=solar_info['azimuth']) + " " + sun_visibility)

        # Solar radiation and cloud cover (useful for solar panel owners)
        if solar_radiation.get('cloud_cover') is not None:
            print(date_strings['cloud_cover'].format(cover=solar_radiation['cloud_cover']))
        if solar_radiation.get('ghi') is not None and solar_radiation.get('dni') is not None:
            # Only show if sun is up and there's meaningful radiation
            if solar_radiation['ghi'] > 0 or solar_radiation['dni'] > 0:
                print(date_strings['solar_radiation'].format(ghi=solar_radiation['ghi'], dni=solar_radiation['dni']))
                if solar_radiation.get('gti') is not None:
                    print(date_strings['solar_for_panels'].format(gti=solar_radiation['gti'], dni=solar_radiation['dni']))

        # Lunar info: phase and times
        print(date_strings['moon_phase'].format(phase=lunar_info['phase'], growth=lunar_info['growth']))

        # Moon position with visibility status
        moon_visibility = date_strings['moon_visible'] if lunar_info['altitude'] > 0 else date_strings['moon_below']
        print(date_strings['moon_position'].format(altitude=lunar_info['altitude'], azimuth=lunar_info['azimuth']) + " " + moon_visibility)

        # Moon rise/transit/set times (if available for today)
        moon_times = []
        if lunar_info.get('rise'):
            moon_times.append(date_strings['moon_rise'].format(time=lunar_info['rise']))
        if lunar_info.get('transit'):
            moon_times.append(date_strings['moon_transit'].format(time=lunar_info['transit']))
        if lunar_info.get('set'):
            moon_times.append(date_strings['moon_set'].format(time=lunar_info['set']))
        if moon_times:
            print(", ".join(moon_times))

        # Display weather and environmental information
        if weather_data["temperature"] is not None:
            weather_desc = self.get_weather_description(weather_data.get('weather_code'))
            print(date_strings['weather'].format(temp=weather_data['temperature'], desc=weather_desc))

            # Feels like temperature
            if weather_data.get('apparent_temp') is not None:
                print(date_strings['feels_like'].format(temp=weather_data['apparent_temp']))

            if weather_data['humidity'] is not None and weather_data['pressure'] is not None:
                print(date_strings['humidity'].format(humidity=weather_data['humidity'], pressure=weather_data['pressure']))

            # Wind with direction and gusts
            if weather_data.get('wind_speed') is not None and weather_data.get('wind_direction') is not None:
                if weather_data.get('gust_speed') is not None:
                    print(
                        date_strings['wind_full'].format(speed=weather_data['wind_speed'], dir=weather_data['wind_direction'], gust=weather_data['gust_speed']))
                else:
                    print(date_strings['wind_no_gust'].format(speed=weather_data['wind_speed'], dir=weather_data['wind_direction']))
            elif weather_data.get('wind_speed') is not None:
                print(date_strings['wind'].format(speed=weather_data['wind_speed']))

            # Visibility (convert from meters to km)
            if weather_data.get('visibility') is not None and weather_data['visibility'] > 0:
                print(date_strings['visibility'].format(vis=weather_data['visibility'] / 1000))

            # Precipitation intensity
            if weather_data.get('precip_intensity') is not None and weather_data['precip_intensity'] > 0:
                print(date_strings['precip_intensity'].format(intensity=weather_data['precip_intensity']))

            if weather_data.get('precipitation_probability') is not None:
                print(date_strings['precipitation'].format(prob=weather_data['precipitation_probability']))

            # Show snow depth if available and > 0
            if weather_data.get('snow_depth') is not None and weather_data['snow_depth'] > 0:
                print(date_strings['snow_depth'].format(depth=weather_data['snow_depth']))
        else:
            if self.language == 'fi':
                print("Sää: ei saatavilla")
            else:
                print("Weather: not available")

        # Marine data (for coastal areas)
        if marine_data.get('wave_height') is not None and marine_data['wave_height'] > 0.1:
            print(date_strings['wave_info'].format(height=marine_data['wave_height'], period=marine_data.get('wave_period', 0),
                                                   dir=marine_data.get('wave_direction', 0)))

        # Flood data
        if flood_data.get('river_discharge') is not None:
            print(date_strings['flood_discharge'].format(discharge=flood_data['river_discharge']))

        if air_quality_data["aqi"] is not None:
            aqi_text = translations['air_quality_levels'].get(air_quality_data["aqi"], "not available")
            print(date_strings['air_quality'].format(quality=aqi_text, aqi=air_quality_data['aqi']))

        if uv_index is not None:
            # UV index warnings
            if uv_index >= 8:
                print(date_strings['uv_very_high'].format(index=uv_index))
            elif uv_index >= 6:
                print(date_strings['uv_high'].format(index=uv_index))
            elif uv_index >= 3:
                print(date_strings['uv_moderate'].format(index=uv_index))
            else:
                print(date_strings['uv_low'].format(index=uv_index))
        else:
            if self.language == 'fi':
                print("UV-indeksi: ei saatavilla")
            else:
                print("UV index: not available")

        print(date_strings['season'].format(season=season))

        print(date_strings['next_holiday'].format(holiday=next_holiday))

        # Morning forecast
        if morning_forecast:
            morning_desc = self.get_weather_description(morning_forecast.get('weather_code'))
            print(
                f"\n{date_strings['morning_forecast'].format(date=morning_forecast['date'].strftime('%d.%m'), temp_min=morning_forecast['temp_min'] or 0, temp_max=morning_forecast['temp_max'] or 0, desc=morning_desc)}")
            if morning_forecast.get('wind_max') and morning_forecast.get('gust_max'):
                print(date_strings['morning_wind'].format(wind=morning_forecast['wind_max'], gust=morning_forecast['gust_max']))
            if morning_forecast.get('precip_prob_max') and morning_forecast['precip_prob_max'] > 0:
                print(date_strings['morning_precip'].format(prob=morning_forecast['precip_prob_max']))
            if morning_forecast.get('visibility_min') and morning_forecast['visibility_min'] < 10000:
                print(date_strings['morning_visibility'].format(vis=morning_forecast['visibility_min'] / 1000))

        # Display weather warnings
        weather_warnings = self.get_weather_warnings(weather_data, uv_index, air_quality_data)

        # Add flood warnings
        if flood_data.get('river_discharge') is not None:
            mean = flood_data.get('river_discharge_mean', 0) or 0
            if mean > 0 and flood_data['river_discharge'] > mean * 2:
                weather_warnings.append(date_strings['flood_warning'].format(discharge=flood_data['river_discharge']))

        # Add wave warnings
        if marine_data.get('wave_height') is not None and marine_data['wave_height'] >= 1.5:
            weather_warnings.append(date_strings['wave_warning'].format(height=marine_data['wave_height']))

        if weather_warnings:
            print(f"\n{date_strings['warnings']}")
            for warning in weather_warnings:
                print(f"  ⚠️  {warning}")


def main():
    import sys

    # Check if the location parameter is provided
    if len(sys.argv) > 1:
        # Join all arguments to form the location string
        location_query = " ".join(sys.argv[1:])
        print(f"Getting information for: {location_query}")

        # Create TimeInfo with the specified location
        time_info = TimeInfo(location_query)
    else:
        # Use default behavior (config file or interactive)
        time_info = TimeInfo()

    time_info.display_info()


if __name__ == "__main__":
    main()
