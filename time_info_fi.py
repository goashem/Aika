#!/usr/bin/env python3
import datetime
import calendar
import math
import configparser
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


class TimeInfo:
    def __init__(self):
        # Load location data from config file or ask user
        self.config = configparser.ConfigParser()
        config_file = '/Users/goashem/Projects/aika/config.ini'

        if not self.config.read(config_file):
            # Config file not found, ask user for information
            self.create_config_interactively(config_file)

        self.latitude = float(self.config['location']['latitude'])
        self.longitude = float(self.config['location']['longitude'])
        self.timezone = self.config['location']['timezone']
        self.language = self.config['location'].get('language', 'fi')  # Default: Finnish

        # Current time in local timezone
        self.now = datetime.datetime.now()

    def create_config_interactively(self, config_file):
        """Create config file by asking user for information"""
        print("Configuration file not found. Let's set up your location preferences.")

        # Ask for location
        while True:
            city = input("Enter your city (e.g., Helsinki, Turku): ").strip()
            if city:
                # Try to get coordinates for the city
                coords = self.get_coordinates_for_city(city)
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
        self.timezone = self.get_timezone_for_coordinates(self.latitude, self.longitude)

        # Create and save config file
        self.config['location'] = {'latitude': str(self.latitude), 'longitude': str(self.longitude), 'timezone': self.timezone, 'language': self.language}

        # Write config file
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        with open(config_file, 'w') as f:
            self.config.write(f)

        print(f"Configuration saved to {config_file}")

    def get_coordinates_for_city(self, city):
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

    def get_translations(self):
        """Get the translations for the chosen language"""
        translations = {'fi': {  # Ajan ilmaisut
            'time_expressions': {'nearly_ten_to_two': 'noin kymmentä vaille kaksi', 'half_past_one': 'noin puoli yksi',
                                 'quarter_to_two': 'noin varttia vailla kaksi', 'quarter_past_twelve': 'noin varttia yli kaksitoista', 'twelve': 'kaksitoista',
                                 'time_of_day': {'early_morning': 'aamuyö', 'morning': 'aamu', 'forenoon': 'aamupäivä', 'noon': 'keskipäivä',
                                                 'afternoon': 'iltapäivä', 'early_evening': 'varhainen ilta', 'late_evening': 'myöhäisilta',
                                                 'night': 'iltayö'}},  # Päivämäärä
            'date': {'week': 'viikko', 'day': 'päivä', 'year_complete': 'vuosi on {pct:.1f} % valmis', 'sunrise': 'aurinko nousee klo {time}',
                     'sunset': 'laskee klo {time}', 'sun_position': 'aurinko on {elevation:.1f}° korkeudella ja {azimuth:.1f}° suunnassa',
                     'moon_phase': 'kuu on {phase:.1f}% ja se on {growth}', 'moon_position': 'kuu on {altitude:.1f}° korkeudella ja {azimuth:.1f}° suunnassa',
                     'weather': 'sää: {temp:.1f}°c, {desc}', 'humidity': '  ilmankosteus: {humidity}%, ilmanpaine: {pressure} hpa',
                     'wind': '  tuulen nopeus: {speed:.1f} m/s', 'precipitation': '  sadetodennäköisyys: {prob:.0f}%',
                     'air_quality': 'ilmanlaatu: {quality} (aqi: {aqi})', 'uv_index': 'uv-indeksi: {index:.1f}', 'uv_low': 'uv-indeksi: {index:.1f} (matala)',
                     'uv_moderate': 'uv-indeksi: {index:.1f} (kohtalainen, huomioi aurinko)',
                     'uv_high': 'uv-indeksi: {index:.1f} (korkea, käytä aurinkorasvaa)',
                     'uv_very_high': 'uv-indeksi: {index:.1f} (erittäin korkea, suojaa ihosi!)', 'season': 'vuodenaika: {season}',
                     'dst_on': 'käytössä kesäaika ({change})', 'dst_off': 'ei kesäaikaa käytössä ({change})', 'next_holiday': 'seuraava juhlapäivä: {holiday}',
                     'warnings': 'varoitukset:', 'cold_warning_extreme': 'äärimmäinen kylmävaroitus: äärimmäisen vaarallisia kylmiä lämpötiloja!',
                     'cold_warning_severe': 'vaikea kylmävaroitus: hyvin kylmiä lämpötiloja, varaudu varotoimiin',
                     'cold_warning': 'kylmävaroitus: kylmiä lämpötiloja, pukeudu lämpimästi',
                     'wind_warning_high': 'kovien tuulien varoitus: voimakkaita tuulia, kiinnitä irtaimet',
                     'wind_advisory': 'tuulivaroitus: kohtalaisia tuulia odotettavissa',
                     'precipitation_warning_high': 'suuren sateen varoitus: hyvin todennäköistä sadetta',
                     'precipitation_advisory': 'sadetodennäköisyysvaroitus: mahdollista sadetta', 'rain_warning': 'sadevaroitus: sadetta odotettavissa',
                     'snow_warning': 'lumivaroitus: lumisadetta odotettavissa', 'thunderstorm_warning': 'ukkosvaroitus: ukkosmyrskyjä odotettavissa'},
            # Vuodenaika
            'seasons': {'winter': 'talvi', 'spring': 'kevät', 'summer': 'kesä', 'autumn': 'syksy'},  # Kuun vaiheet
            'moon_growth': {'growing': 'kasvava', 'waning': 'vähenevä'},  # Ilmanlaatu
            'air_quality_levels': {1: 'erinomainen', 2: 'hyvä', 3: 'kohtalainen', 4: 'huono', 5: 'vaarallinen'}}, 'en': {  # Time expressions
            'time_expressions': {'nearly_ten_to_two': 'nearly ten to two', 'half_past_one': 'about half past one', 'quarter_to_two': 'about quarter to two',
                                 'quarter_past_twelve': 'about quarter past twelve', 'twelve': 'twelve',
                                 'time_of_day': {'early_morning': 'early morning', 'morning': 'morning', 'forenoon': 'forenoon', 'noon': 'noon',
                                                 'afternoon': 'afternoon', 'early_evening': 'early evening', 'late_evening': 'late evening', 'night': 'night'}},
            # Date
            'date': {'week': 'week', 'day': 'day', 'year_complete': 'the year is {pct:.1f} % complete', 'sunrise': 'sun rises at {time}',
                     'sunset': 'sets at {time}', 'sun_position': 'sun is at {elevation:.1f}° elevation and {azimuth:.1f}° direction',
                     'moon_phase': 'moon is {phase:.1f}% and it is {growth}',
                     'moon_position': 'moon is at {altitude:.1f}° elevation and {azimuth:.1f}° direction', 'weather': 'weather: {temp:.1f}°c, {desc}',
                     'humidity': '  humidity: {humidity}%, pressure: {pressure} hpa', 'wind': '  wind speed: {speed:.1f} m/s',
                     'precipitation': '  precipitation probability: {prob:.0f}%', 'air_quality': 'air quality: {quality} (aqi: {aqi})',
                     'uv_index': 'uv index: {index:.1f}', 'uv_low': 'uv index: {index:.1f} (low)',
                     'uv_moderate': 'uv index: {index:.1f} (moderate, beware of sun)', 'uv_high': 'uv index: {index:.1f} (high, use sunscreen)',
                     'uv_very_high': 'uv index: {index:.1f} (very high, protect your skin!)', 'season': 'season: {season}',
                     'dst_on': 'daylight saving time in use ({change})', 'dst_off': 'no daylight saving time in use ({change})',
                     'next_holiday': 'next holiday: {holiday}', 'warnings': 'warnings:',
                     'cold_warning_extreme': 'extreme cold warning: extremely dangerous cold temperatures!',
                     'cold_warning_severe': 'severe cold warning: very cold temperatures, take precautions',
                     'cold_warning': 'cold warning: cold temperatures, dress warmly',
                     'wind_warning_high': 'high wind warning: strong winds, secure loose objects', 'wind_advisory': 'wind advisory: moderate winds expected',
                     'precipitation_warning_high': 'high precipitation warning: very likely precipitation',
                     'precipitation_advisory': 'precipitation advisory: possible precipitation', 'rain_warning': 'rain warning: precipitation expected',
                     'snow_warning': 'snow warning: snowfall expected', 'thunderstorm_warning': 'thunderstorm warning: thunderstorms expected'},  # Season
            'seasons': {'winter': 'winter', 'spring': 'spring', 'summer': 'summer', 'autumn': 'autumn'},  # Moon phases
            'moon_growth': {'growing': 'growing', 'waning': 'waning'},  # Air quality
            'air_quality_levels': {1: 'excellent', 2: 'good', 3: 'moderate', 4: 'poor', 5: 'dangerous'}}}

        return translations.get(self.language, translations['fi'])

    def get_time_expression(self):
        """Luo aikalause valitulla kielellä"""
        hours = self.now.hour
        minutes = self.now.minute

        translations = self.get_translations()['time_expressions']

        # Time intervals for common times of day
        if hours == 11 and minutes >= 45:
            return translations['nearly_ten_to_two']
        elif hours == 11 and minutes >= 30:
            return translations['half_past_one']
        elif hours == 11 and minutes >= 15:
            return translations['quarter_to_two']
        elif hours == 12 and minutes == 0:
            return translations['twelve']
        elif hours == 12 and minutes < 15:
            return translations['quarter_past_twelve']
        elif hours == 12 and minutes < 30:
            return translations['half_past_one']
        else:
            # Varmuuden vuoksi yksinkertainen tunnit.minuutit muoto
            return self.now.strftime("%H.%M")

    def get_time_of_day(self):
        """Määritä vuorokaudenaika valitulla kielellä"""
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
                    # Use place parameter instead of defining bounding box
                    args = ["place=Turku",  # Use Turku, which is near the coordinates
                            "timeseries=True", ]

                    obs = download_stored_query("fmi::observations::weather::multipointcoverage", args=args)

                    # Pick one station and get the latest air temperature
                    if obs.data:
                        station = sorted(obs.data.keys())[0]
                        times = obs.data[station]["times"]
                        temps = obs.data[station]["Air temperature"]["values"]
                        unit = obs.data[station]["Air temperature"]["unit"]

                        # Get latest values
                        latest_temp = temps[-1]
                        humidity_values = obs.data[station]["Humidity"]["values"]
                        latest_humidity = humidity_values[-1] if humidity_values else None

                        return {"temperature": latest_temp, "description": "ei saatavilla",  # FMI ei suoraan tarjoa kuvausta
                                "humidity": latest_humidity, "pressure": None,  # Tarvitaan eri kysely
                                "wind_speed": None  # Tarvitaan eri kysely
                                }
                except Exception as e:
                    pass  # Jatka Open-Meteo -vaihtoehtoon

            # Use Open-Meteo as fallback
            try:
                url = "https://api.open-meteo.com/v1/forecast"
                params = {"latitude": self.latitude, "longitude": self.longitude, "current_weather": True,
                          "hourly": "temperature_2m,relativehumidity_2m,pressure_msl,windspeed_10m,precipitation_probability,weathercode",
                          "timezone": "Europe/Helsinki", "forecast_hours": 24,  # Ennuste seuraavalle 24 tunnille
                          }

                response = requests.get(url, params=params, timeout=20)
                response.raise_for_status()
                data = response.json()

                current = data["current_weather"]
                hourly = data["hourly"]

                # Get current values
                temp = current["temperature"]
                wind_speed = current["windspeed"]

                # Get humidity and pressure from hourly data (closest to current time)
                humidity = hourly["relativehumidity_2m"][0] if hourly["relativehumidity_2m"] else None
                pressure = hourly["pressure_msl"][0] if hourly["pressure_msl"] else None

                # Get precipitation probability for next few hours
                precip_prob = hourly["precipitation_probability"][0] if hourly["precipitation_probability"] else None

                # Get weather code to determine if it's rain or snow
                weather_code = hourly["weathercode"][0] if hourly["weathercode"] else None

                return {"temperature": temp, "description": "ei saatavilla",  # Open-Meteo ei suoraan tarjoa kuvausta
                        "humidity": humidity, "pressure": pressure, "wind_speed": wind_speed, "precipitation_probability": precip_prob,
                        "weather_code": weather_code}
            except Exception as e:
                pass

        except Exception as e:
            pass

        # Return sample data if both APIs fail
        return {"temperature": -14.0,  # Korjattu arvo
                "description": "selkeää", "humidity": 90, "pressure": 1025, "wind_speed": 3.2, "precipitation_probability": 10,  # 10% probability
                "weather_code": 0  # Clear
                }

    def get_air_quality_data(self):
        """Get air quality index"""
        try:
            # Mallidata demotarkoituksiin
            return {"aqi": 2,  # 1 = good, 2 = moderate, 3 = poor, 4 = very poor, 5 = dangerous
                    "pm2_5": 15, "pm10": 25}
        except:
            return {"aqi": None, "pm2_5": None, "pm10": None}

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

    def get_weather_warnings(self, weather_data):
        """Create weather warnings based on weather conditions"""
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

        # Weather code based warnings
        if weather_data.get("weather_code") is not None:
            weather_code = weather_data["weather_code"]
            # Weather codes: https://open-meteo.com/en/docs
            if weather_code in [51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82]:  # Rain
                warnings.append(translations['rain_warning'])
            elif weather_code in [71, 73, 75, 77, 85, 86]:  # Snow
                warnings.append(translations['snow_warning'])
            elif weather_code in [95, 96, 99]:  # Thunderstorms
                warnings.append(translations['thunderstorm_warning'])

        return warnings

    def get_season(self):
        """Determine the season based on hemisphere"""
        month = self.now.month
        season_translations = self.get_translations()['seasons']

        # Determine if we're in Northern or Southern hemisphere
        is_northern_hemisphere = self.latitude >= 0

        if is_northern_hemisphere:
            # Northern hemisphere seasons
            if month in [12, 1, 2]:
                return season_translations['winter']
            elif month in [3, 4, 5]:
                return season_translations['spring']
            elif month in [6, 7, 8]:
                return season_translations['summer']
            else:  # 9, 10, 11
                return season_translations['autumn']
        else:
            # Southern hemisphere seasons (opposite)
            if month in [12, 1, 2]:
                return season_translations['summer']
            elif month in [3, 4, 5]:
                return season_translations['autumn']
            elif month in [6, 7, 8]:
                return season_translations['winter']
            else:  # 9, 10, 11
                return season_translations['spring']

    def get_dst_info(self):
        """Get daylight saving time information and next transition"""
        try:
            # Calculate next DST transition
            next_transition = next_dst_transition(self.timezone, start=self.now)
            if next_transition:
                # Format the transition date in a user-friendly way
                transition_date = next_transition.strftime("%d.%m.%Y")
                if next_transition.dst().total_seconds() > self.now.astimezone(ZoneInfo(self.timezone)).dst().total_seconds():
                    next_change = f"DST starts on {transition_date}"
                else:
                    next_change = f"DST ends on {transition_date}"
            else:
                next_change = "No DST changes found"

            # Check current DST status
            current_tz = ZoneInfo(self.timezone)
            is_dst = bool(self.now.astimezone(current_tz).dst())

        except Exception:
            # Fallback if zoneinfo is not available
            is_dst = bool(self.now.dst())
            next_change = "DST information not available"

        return is_dst, next_change

    def get_next_finland_holiday(self):
        """Get the next Finnish public holiday"""
        try:
            if HOLIDAYS_AVAILABLE:
                # Include current year + next year so "next holiday" works near year-end
                years = (self.now.year, self.now.year + 1)
                
                # Get Finnish public holidays
                fi_holidays = holidays.country_holidays('FI', years=years)
                
                # Find the next holiday
                current_date = self.now.date()
                for holiday_date in sorted(fi_holidays.keys()):
                    if holiday_date >= current_date:
                        days_until = (holiday_date - current_date).days
                        holiday_name = fi_holidays[holiday_date]
                        # Return holiday name and days until in the current language
                        if self.language == 'fi':
                            return f"{holiday_name} ({holiday_date.strftime('%d.%m.')}) on {days_until} päivän päästä"
                        else:
                            return f"{holiday_name} ({holiday_date.strftime('%d.%m.')}) in {days_until} days"
                
                # If no holiday found this year, return first one next year
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
        holidays_list = [
            (1, 1, "Uudenvuodenpäivä"),
            (1, 6, "Loppiainen"),
            (5, 1, "Vappu"),
            (12, 6, "Itsensä turvaamisen päivä"),
            (12, 24, "Jouluaatto"),
            (12, 25, "Joulupäivä"),
            (12, 26, "Tapaninpäivä")
        ]
        
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

    def get_solar_info(self):
        """Calculate solar infot"""
        location = LocationInfo("Custom", self.timezone, self.latitude, self.longitude)
        s = sun(location.observer, date=self.now.date())

        # Sun position (elevation and azimuth) - use ephem library for consistency
        observer = ephem.Observer()
        observer.lat = str(self.latitude)
        observer.lon = str(self.longitude)
        observer.date = self.now

        sun_body = ephem.Sun()
        sun_body.compute(observer)

        sun_elevation = math.degrees(sun_body.alt)
        sun_azimuth = math.degrees(sun_body.az)

        sunrise_time = s['sunrise'].strftime("%H.%M")
        sunset_time = s['sunset'].strftime("%H.%M")

        return {'sunrise': sunrise_time, 'sunset': sunset_time, 'elevation': sun_elevation, 'azimuth': sun_azimuth}

    def get_lunar_info(self):
        """Calculate lunar info"""
        observer = ephem.Observer()
        observer.lat = str(self.latitude)
        observer.lon = str(self.longitude)
        observer.date = self.now

        moon = ephem.Moon()
        moon.compute(observer)

        # Kuun vaihe (prosentteina)
        moon_phase = moon.phase

        # Is the moon waxing or waning
        if moon.phase < 50:
            moon_growth = "kasvava"  # Nouvante (growing)
        else:
            moon_growth = "vähenevä"  # Calante (waning)

        # Kuun korkeus ja atsimuutti
        moon_altitude = math.degrees(moon.alt)
        moon_azimuth = math.degrees(moon.az)

        return {'phase': moon_phase, 'growth': moon_growth, 'altitude': moon_altitude, 'azimuth': moon_azimuth}

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

    def get_finnish_translations(self):
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

    def display_info(self):
        """Display all information in the selected language"""
        # Get all information
        time_expression = self.get_time_expression()
        time_of_day = self.get_time_of_day()
        weather_data = self.get_weather_data()
        air_quality_data = self.get_air_quality_data()
        uv_index = self.get_uv_index()
        season = self.get_season()
        is_dst, next_dst_change = self.get_dst_info()
        next_holiday = self.get_next_finland_holiday()
        solar_info = self.get_solar_info()
        lunar_info = self.get_lunar_info()
        date_info = self.get_date_info()
        translations = self.get_translations()
        finnish_translations = self.get_finnish_translations()

        # Time
        clock = self.now.strftime("%H.%M")

        # Date translations (always in Finnish for proper grammar)
        day_name_fi = finnish_translations['days'].get(date_info['day_name'], date_info['day_name'])
        month_name_genitive = finnish_translations['months_genitive'].get(date_info['month_name'], date_info['month_name'])

        # Display information in the selected language
        date_strings = translations['date']

        print(f"The time is {time_expression} ({clock}), so it's {time_of_day}.")
        print(f"It's {day_name_fi}, {date_info['day_num']}. {month_name_genitive}, {date_info['year']}.")
        print(f"Week number is {date_info['week_num']}/{date_info['weeks_in_year']}, and day number is {date_info['day_of_year']}/{date_info['days_in_year']}.")
        print(date_strings['year_complete'].format(pct=date_info['pct_complete']))
        print(date_strings['sunrise'].format(time=solar_info['sunrise']) + " and " + date_strings['sunset'].format(time=solar_info['sunset']) + ".")
        print(date_strings['sun_position'].format(elevation=solar_info['elevation'], azimuth=solar_info['azimuth']))
        print(date_strings['moon_phase'].format(phase=lunar_info['phase'], growth=lunar_info['growth']))
        print(date_strings['moon_position'].format(altitude=lunar_info['altitude'], azimuth=lunar_info['azimuth']))

        # Display weather and environmental information
        if weather_data["temperature"] is not None:
            print(date_strings['weather'].format(temp=weather_data['temperature'], desc=weather_data['description']))
            print(date_strings['humidity'].format(humidity=weather_data['humidity'], pressure=weather_data['pressure']))
            print(date_strings['wind'].format(speed=weather_data['wind_speed']))
            if weather_data.get('precipitation_probability') is not None:
                print(date_strings['precipitation'].format(prob=weather_data['precipitation_probability']))
        else:
            print("Weather: not available")

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
            print("UV index: not available")

        print(date_strings['season'].format(season=season))

        if is_dst:
            print(date_strings['dst_on'].format(change=next_dst_change))
        else:
            print(date_strings['dst_off'].format(change=next_dst_change))

        print(date_strings['next_holiday'].format(holiday=next_holiday))

        # Display weather warnings
        weather_warnings = self.get_weather_warnings(weather_data)
        if weather_warnings:
            print(f"\n{date_strings['warnings']}")
            for warning in weather_warnings:
                print(f"  ⚠️  {warning}")


def main():
    time_info = TimeInfo()
    time_info.display_info()


if __name__ == "__main__":
    main()
