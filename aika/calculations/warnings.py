"""Weather warning calculations."""


def get_weather_warnings(weather_data, uv_forecast, air_quality_data, lightning_data, pollen_data, translations):
    """Create weather warnings based on weather conditions, UV forecast, air quality, lightning, and pollen."""
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

    # UV warnings - now using UV forecast object
    if uv_forecast is not None:
        # If it's the new UvForecast model object
        if hasattr(uv_forecast, 'current_uv'):
            uv_index = uv_forecast.current_uv
        # If it's a dictionary from the provider
        elif isinstance(uv_forecast, dict):
            uv_index = uv_forecast.get('current_uv', uv_forecast.get('uv_index', 0))
        # If it's just the numeric UV index
        else:
            uv_index = uv_forecast
            
        if uv_index is not None and uv_index >= 6:
            warnings.append(date_strings['uv_warning'])

    # Air quality warnings
    if air_quality_data is not None and air_quality_data.get('aqi') is not None:
        aqi = air_quality_data['aqi']
        if aqi >= 4:
            warnings.append(date_strings['air_quality_warning'])

    # Lightning warnings
    if lightning_data is not None:
        threat_level = lightning_data.get('threat_level', 'none')
        nearest_km = lightning_data.get('nearest_km')
        
        if threat_level in ['severe', 'high']:
            if nearest_km is not None and nearest_km < 10:
                warnings.append(date_strings['lightning_warning_immediate'])
            elif nearest_km is not None and nearest_km < 30:
                warnings.append(date_strings['lightning_warning_nearby'])
            else:
                warnings.append(date_strings['lightning_warning_severe'])

    # Pollen warnings
    if pollen_data is not None:
        current_pollen = pollen_data.current if hasattr(pollen_data, 'current') else pollen_data.get('current')
        if current_pollen:
            # Check for high pollen levels across different types
            high_pollen_count = 0
            very_high_pollen_count = 0
            
            # Handle both model objects and dictionaries
            if hasattr(current_pollen, 'birch'):
                # It's a PollenForecast model object
                pollen_types = ['birch', 'grass', 'alder', 'mugwort', 'ragweed']
                for pollen_type in pollen_types:
                    level = getattr(current_pollen, pollen_type, 0)
                    if level >= 4:  # High level
                        very_high_pollen_count += 1
                    elif level >= 3:  # Moderate level
                        high_pollen_count += 1
            else:
                # It's a dictionary
                pollen_types = ['birch', 'grass', 'alder', 'mugwort', 'ragweed']
                for pollen_type in pollen_types:
                    level = current_pollen.get(pollen_type, 0)
                    if level >= 4:  # High level
                        very_high_pollen_count += 1
                    elif level >= 3:  # Moderate level
                        high_pollen_count += 1
            
            if very_high_pollen_count > 0:
                warnings.append(date_strings['pollen_warning_very_high'])
            elif high_pollen_count > 2 or very_high_pollen_count > 0:
                warnings.append(date_strings['pollen_warning_high'])
            elif high_pollen_count > 0:
                warnings.append(date_strings['pollen_warning_moderate'])

    return warnings
