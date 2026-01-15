"""Weather warning calculations."""

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
