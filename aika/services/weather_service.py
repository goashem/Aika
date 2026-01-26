"""Weather service for retrieving and structuring weather data."""

from ..models import (WeatherData, AirQuality, SolarRadiation, MarineData, FloodData, Nowcast, MorningForecast, Forecast12h, Forecast7day, PollenInfo, PollenForecast)
from ..providers import weather as weather_provider
from ..providers import air_quality as air_quality_provider
from ..providers import marine as marine_provider
from ..providers import nowcast as nowcast_provider
from ..providers import pollen as pollen_provider


def get_weather(latitude, longitude, timezone):
    """Get current weather conditions."""
    data = weather_provider.get_weather_data(latitude, longitude, timezone)
    if not data:
        return WeatherData()

    return WeatherData(temperature=data.get("temperature"), apparent_temp=data.get("apparent_temp"), description=data.get("description", "not available"),
                       humidity=data.get("humidity"), pressure=data.get("pressure"), wind_speed=data.get("wind_speed"),
                       wind_direction=data.get("wind_direction"), gust_speed=data.get("gust_speed"), visibility=data.get("visibility"),
                       precip_intensity=data.get("precip_intensity"), precipitation_probability=data.get("precipitation_probability"),
                       weather_code=data.get("weather_code"), snow_depth=data.get("snow_depth"))


def get_air_quality(latitude, longitude, timezone):
    """Get air quality data."""
    data = air_quality_provider.get_air_quality(latitude, longitude, timezone)
    if not data:
        return AirQuality()

    return AirQuality(aqi=data.get("aqi"), european_aqi=data.get("european_aqi"), pm2_5=data.get("pm2_5"), pm10=data.get("pm10"))


def get_uv_index(latitude, longitude):
    """Get UV index."""
    return air_quality_provider.get_uv_index(latitude, longitude)


def get_uv_forecast(latitude, longitude, timezone):
    """Get comprehensive UV forecast."""
    data = air_quality_provider.get_uv_forecast(latitude, longitude, timezone)
    if not data:
        from ..models import UvForecast
        return UvForecast()
    
    from ..models import UvForecast
    return UvForecast(
        current_uv=data.get("current_uv", 0.0),
        max_uv_today=data.get("max_uv_today", 0.0),
        peak_time=data.get("peak_time", ""),
        uv_category=data.get("uv_category", "low"),
        safe_exposure_time=data.get("safe_exposure_time", ""),
        protection_recommendations=data.get("protection_recommendations", []),
        burn_time_by_skin_type=data.get("burn_time_by_skin_type", {}),
        skin_type=data.get("skin_type", 3)
    )


def get_solar_radiation(latitude, longitude, timezone):
    """Get solar radiation data."""
    data = weather_provider.get_solar_radiation(latitude, longitude, timezone)
    if not data:
        return SolarRadiation()

    return SolarRadiation(cloud_cover=data.get("cloud_cover"), ghi=data.get("ghi"), dni=data.get("dni"), dhi=data.get("dhi"), gti=data.get("gti"),
                          direct=data.get("direct"))


def get_marine_data(latitude, longitude, timezone):
    """Get marine/wave data."""
    data = marine_provider.get_marine_data(latitude, longitude, timezone)
    if not data:
        return MarineData()

    return MarineData(wave_height=data.get("wave_height"), wave_direction=data.get("wave_direction"), wave_period=data.get("wave_period"),
                      wind_wave_height=data.get("wind_wave_height"), swell_wave_height=data.get("swell_wave_height"),
                      sea_temperature=data.get("sea_temperature"), sea_ice_cover=data.get("sea_ice_cover"))


def get_flood_data(latitude, longitude):
    """Get flood/river discharge data."""
    data = marine_provider.get_flood_data(latitude, longitude)
    if not data:
        return FloodData()

    return FloodData(river_discharge=data.get("river_discharge"), river_discharge_mean=data.get("river_discharge_mean"),
                     river_discharge_max=data.get("river_discharge_max"))


def get_nowcast(latitude, longitude, timezone, country_code):
    """Get precipitation nowcast."""
    # Nowcast precipitation
    precip_data = nowcast_provider.get_precipitation_nowcast(latitude, longitude, timezone)

    # Lightning activity
    lightning_data = nowcast_provider.get_lightning_activity(latitude, longitude, country_code)

    # Structure it into the model
    if precip_data:
        nowcast = Nowcast(rain_starts_in_min=precip_data.get("rain_starts_in_min"), rain_ends_in_min=precip_data.get("rain_ends_in_min"),
                          is_raining_now=precip_data.get("is_raining_now", False), precipitation_type=precip_data.get("precipitation_type", "none"),
                          max_intensity=precip_data.get("max_intensity", 0.0), intervals=precip_data.get("intervals", []))
    else:
        nowcast = Nowcast()

    # Add lightning data if available
    if lightning_data:
        nowcast.strikes_1h = lightning_data.get("strikes_1h", 0)
        nowcast.nearest_km = lightning_data.get("nearest_km")
        nowcast.activity_level = lightning_data.get("activity_level", "none")
        nowcast.is_active = lightning_data.get("is_active", False)

    return nowcast


def get_morning_forecast(latitude, longitude, timezone, now):
    """Get forecast for tomorrow morning."""
    data = weather_provider.get_morning_forecast(latitude, longitude, timezone, now)
    if not data:
        return MorningForecast()

    return MorningForecast(forecast_date=data.get("date"),  # Provider returns 'date', model has 'forecast_date'
                           temp_min=data.get("temp_min"), temp_max=data.get("temp_max"), apparent_min=data.get("apparent_min"),
                           precip_prob_max=data.get("precip_prob_max"), weather_code=data.get("weather_code"), wind_max=data.get("wind_max"),
                           gust_max=data.get("gust_max"), visibility_min=data.get("visibility_min"))


def get_forecast_12h(latitude, longitude, timezone, now):
    """Get 12-hour forecast summary."""
    data = weather_provider.get_12h_forecast_summary(latitude, longitude, timezone, now)
    if not data:
        return Forecast12h()

    return Forecast12h(rain_windows=data.get("rain_windows", []), strongest_wind=data.get("strongest_wind"), temp_range=data.get("temp_range"))


def get_forecast_7day(latitude, longitude, timezone):
    """Get 7-day forecast."""
    data = weather_provider.get_7day_forecast(latitude, longitude, timezone)
    if not data:
        return Forecast7day()

    return Forecast7day(days=data.get("days", []), best_outdoor_window=data.get("best_outdoor_window"), snow_accumulation_cm=data.get("snow_accumulation_cm"))


def get_pollen_info(latitude, longitude, timezone):
    """Get pollen forecast information."""
    data = pollen_provider.get_pollen_forecast(latitude, longitude, timezone)
    if not data:
        return PollenInfo()

    # Create current pollen forecast
    current_data = data.get("current", {})
    if current_data:
        current_forecast = PollenForecast(
            date=current_data.get("date"),
            birch=current_data.get("birch", 0),
            grass=current_data.get("grass", 0),
            alder=current_data.get("alder", 0),
            mugwort=current_data.get("mugwort", 0),
            ragweed=current_data.get("ragweed", 0),
            olive=current_data.get("olive", 0),
            peak_times=current_data.get("peak_times", [])
        )
    else:
        current_forecast = None

    # Create daily forecast list
    daily_forecasts = []
    for forecast_data in data.get("forecast", []):
        daily_forecasts.append(PollenForecast(
            date=forecast_data.get("date"),
            birch=forecast_data.get("birch", 0),
            grass=forecast_data.get("grass", 0),
            alder=forecast_data.get("alder", 0),
            mugwort=forecast_data.get("mugwort", 0),
            ragweed=forecast_data.get("ragweed", 0),
            olive=forecast_data.get("olive", 0),
            peak_times=forecast_data.get("peak_times", [])
        ))

    # Determine allergen risk level
    allergen_risk = "low"
    if current_forecast:
        max_pollen = max([
            current_forecast.birch,
            current_forecast.grass,
            current_forecast.alder,
            current_forecast.mugwort,
            current_forecast.ragweed
        ], default=0)
        
        if max_pollen >= 4:
            allergen_risk = "high"
        elif max_pollen >= 3:
            allergen_risk = "moderate"

    return PollenInfo(
        current=current_forecast,
        daily_forecast=daily_forecasts,
        recommendations=data.get("recommendations", []),
        allergen_risk=allergen_risk
    )
