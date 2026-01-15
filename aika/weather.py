"""Weather data fetching and processing."""

from .providers import air_quality as air_quality_provider
from .providers import marine as marine_provider
from .providers import weather as weather_provider


def degrees_to_compass(degrees):
    """Convert wind direction in degrees to compass direction key.

    Returns a key like 'N', 'NNE', 'NE', etc. that can be used
    to look up the localized direction name.
    """
    if degrees is None:
        return None

    # Normalize to 0-360
    degrees = degrees % 360

    # 16-point compass, each sector is 22.5 degrees
    # Offset by 11.25 so N is centered at 0
    directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']

    index = round(degrees / 22.5) % 16
    return directions[index]


def get_weather_data(latitude, longitude, timezone):
    """Wrapper for providers.weather.get_weather_data."""
    return weather_provider.get_weather_data(latitude, longitude, timezone)



def get_weather_description(weather_code, language):
    """Translate Open-Meteo weather code to description."""
    if weather_code is None:
        return "ei saatavilla" if language == 'fi' else "not available"

    weather_codes_fi = {0: "selkeää", 1: "enimmäkseen selkeää", 2: "puolipilvistä", 3: "pilvistä", 45: "sumua", 48: "huurtuvaa sumua",
                        51: "kevyttä tihkusadetta", 53: "tihkusadetta", 55: "tiheää tihkusadetta", 56: "jäätävää tihkua", 57: "tiheää jäätävää tihkua",
                        61: "kevyttä sadetta", 63: "sadetta", 65: "rankkasadetta", 66: "jäätävää sadetta", 67: "rankkaa jäätävää sadetta",
                        71: "kevyttä lumisadetta", 73: "lumisadetta", 75: "tiheää lumisadetta", 77: "lumijyväsiä", 80: "kevyitä sadekuuroja", 81: "sadekuuroja",
                        82: "rankkoja sadekuuroja", 85: "kevyitä lumikuuroja", 86: "rankkoja lumikuuroja", 95: "ukkosta", 96: "ukkosta ja rakeita",
                        99: "ukkosta ja rankkoja rakeita"}

    weather_codes_en = {0: "clear sky", 1: "mainly clear", 2: "partly cloudy", 3: "overcast", 45: "fog", 48: "depositing rime fog", 51: "light drizzle",
                        53: "drizzle", 55: "dense drizzle", 56: "light freezing drizzle", 57: "dense freezing drizzle", 61: "light rain", 63: "rain",
                        65: "heavy rain", 66: "light freezing rain", 67: "heavy freezing rain", 71: "light snow", 73: "snow", 75: "heavy snow",
                        77: "snow grains", 80: "light rain showers", 81: "rain showers", 82: "violent rain showers", 85: "light snow showers",
                        86: "heavy snow showers", 95: "thunderstorm", 96: "thunderstorm with hail", 99: "thunderstorm with heavy hail"}

    codes = weather_codes_fi if language == 'fi' else weather_codes_en
    return codes.get(weather_code, "tuntematon" if language == 'fi' else "unknown")


def get_uv_index(latitude, longitude):
    """Wrapper for providers.air_quality.get_uv_index."""
    return air_quality_provider.get_uv_index(latitude, longitude)


def get_air_quality(latitude, longitude, timezone):
    """Wrapper for providers.air_quality.get_air_quality."""
    return air_quality_provider.get_air_quality(latitude, longitude, timezone)

def get_solar_radiation(latitude, longitude, timezone):
    """Wrapper for providers.weather.get_solar_radiation."""
    return weather_provider.get_solar_radiation(latitude, longitude, timezone)


def get_marine_data(latitude, longitude, timezone):
    """Wrapper for providers.marine.get_marine_data."""
    return marine_provider.get_marine_data(latitude, longitude, timezone)


def get_flood_data(latitude, longitude):
    """Wrapper for providers.marine.get_flood_data."""
    return marine_provider.get_flood_data(latitude, longitude)


def get_morning_forecast(latitude, longitude, timezone, now):
    """Wrapper for providers.weather.get_morning_forecast."""
    return weather_provider.get_morning_forecast(latitude, longitude, timezone, now)


def _calculate_outdoor_score(hour_data):
    """Calculate outdoor activity suitability score (0-100).

    Factors (weighted):
    - Precipitation probability: -2 per percentage point above 20%
    - Temperature comfort: optimal at 10-25°C
    - Wind: -3 per m/s above 5
    """
    score = 100

    # Precipitation penalty
    precip_prob = hour_data.get('precipitation_probability', 0) or 0
    if precip_prob > 20:
        score -= (precip_prob - 20) * 2

    # Temperature comfort
    temp = hour_data.get('temperature', 15) or 15
    if temp < 10:
        score -= (10 - temp) * 2
    elif temp > 25:
        score -= (temp - 25) * 2

    # Wind penalty
    wind = hour_data.get('wind_speed', 0) or 0
    if wind > 5:
        score -= (wind - 5) * 3

    # Weather code penalty for bad weather
    weather_code = hour_data.get('weather_code', 0) or 0
    if weather_code >= 51:  # Any precipitation
        score -= 20
    if weather_code >= 95:  # Thunderstorm
        score -= 30

    return max(0, min(100, score))


def get_12h_forecast_summary(latitude, longitude, timezone, now):
    """Wrapper for providers.weather.get_12h_forecast_summary."""
    return weather_provider.get_12h_forecast_summary(latitude, longitude, timezone, now)


def get_7day_forecast(latitude, longitude, timezone):
    """Wrapper for providers.weather.get_7day_forecast."""
    return weather_provider.get_7day_forecast(latitude, longitude, timezone)


def get_weather_warnings(weather_data, uv_index, air_quality_data, translations):
    """Create weather warnings based on weather conditions, UV index, and air quality."""
    warnings = []
    date_strings = translations['date']

    # Temperature warnings
    if weather_data.get("temperature") is not None:
        temp = weather_data["temperature"]
        if temp <= -30:
            warnings.append(date_strings['cold_warning_extreme'])
        elif temp <= -20:
            warnings.append(date_strings['cold_warning_severe'])
        elif temp <= -10:
            warnings.append(date_strings['cold_warning'])

    # Wind warnings
    if weather_data.get("wind_speed") is not None:
        wind_speed = weather_data["wind_speed"]
        if wind_speed >= 25:
            warnings.append(date_strings['wind_warning_high'])
        elif wind_speed >= 15:
            warnings.append(date_strings['wind_advisory'])

    # Precipitation probability warnings
    if weather_data.get("precipitation_probability") is not None:
        precip_prob = weather_data["precipitation_probability"]
        if precip_prob >= 80:
            warnings.append(date_strings['precipitation_warning_high'])
        elif precip_prob >= 50:
            warnings.append(date_strings['precipitation_advisory'])

    # Weather code-based warnings
    if weather_data.get("weather_code") is not None:
        weather_code = weather_data["weather_code"]
        if weather_code in [51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82]:
            warnings.append(date_strings['rain_warning'])
        elif weather_code in [71, 73, 75, 77, 85, 86]:
            warnings.append(date_strings['snow_warning'])
        elif weather_code in [95, 96, 99]:
            warnings.append(date_strings['thunderstorm_warning'])

    # UV index warnings
    if uv_index is not None and uv_index >= 6:
        warnings.append(date_strings['uv_warning'])

    # Air quality warnings
    if air_quality_data is not None and air_quality_data.get('aqi') is not None:
        aqi = air_quality_data['aqi']
        if aqi >= 4:
            warnings.append(date_strings['air_quality_warning'])

    return warnings
