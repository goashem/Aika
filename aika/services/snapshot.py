"""Main service for building the AikaSnapshot."""

import datetime
from typing import Optional

from ..models import (
    Location, RawData, ComputedData, AikaSnapshot
)
from . import (
    weather_service, astronomy_service, finland_service, calendar_service
)
from ..providers import geocoding as geocoding_provider
from ..calculations import warnings as warnings_calc
from ..calculations import time_expr as time_expr_calc
from ..formats import localization as localization_format

# Note: Using absolute imports in implementation to avoid circular dependencies if any
# but explicit relative imports for internal modules used here.


def build_snapshot(
    location_query: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    language: str = "fi",
    digitransit_api_key: Optional[str] = None
) -> AikaSnapshot:
    """Build a complete AikaSnapshot for the given location."""
    
    # 1. Resolve Location
    lat, lon = 0.0, 0.0
    city_name = location_query
    country_name = None
    country_code = "FI" # Default
    timezone = "Europe/Helsinki" # Default
    
    # If coordinates provided directly
    if latitude is not None and longitude is not None:
        lat, lon = float(latitude), float(longitude)
        
        # Reverse geocode to get details
        r_city, r_country, r_cc = geocoding_provider.reverse_geocode(lat, lon)
        if r_city: city_name = r_city
        if r_country: country_name = r_country
        if r_cc: country_code = r_cc
        
        # Get timezone
        tz = geocoding_provider.get_timezone_for_coordinates(lat, lon)
        if tz: timezone = tz
        
    # If only location string provided
    elif location_query:
        details = geocoding_provider.get_coordinates_with_details(location_query)
        if details:
            lat = details['lat']
            lon = details['lon']
            city_name = details['city']
            country_name = details['country']
            country_code = details['country_code']
            
            # Get timezone
            tz = geocoding_provider.get_timezone_for_coordinates(lat, lon)
            if tz: timezone = tz
    
    # Create Location model
    location = Location(
        latitude=lat,
        longitude=lon,
        city_name=city_name,
        country_name=country_name,
        country_code=country_code,
        timezone=timezone
    )
    
    # 2. Get Current Time
    try:
        from zoneinfo import ZoneInfo
        now = datetime.datetime.now(ZoneInfo(timezone))
    except ImportError:
        now = datetime.datetime.now()
        
    # 3. Get Translations
    translations = localization_format.get_translations(language)
    
    # 4. Fetch Raw Data (Providers via Services)
    weather_data = weather_service.get_weather(lat, lon, timezone)
    air_quality = weather_service.get_air_quality(lat, lon, timezone)
    uv_index = weather_service.get_uv_index(lat, lon)
    solar_radiation = weather_service.get_solar_radiation(lat, lon, timezone)
    marine_data = weather_service.get_marine_data(lat, lon, timezone)
    flood_data = weather_service.get_flood_data(lat, lon)
    nowcast = weather_service.get_nowcast(lat, lon, timezone, country_code)
    
    road_weather = finland_service.get_road_weather(lat, lon, country_code)
    electricity = finland_service.get_electricity(now, timezone, country_code)
    detailed_elec = finland_service.get_detailed_electricity(now, timezone, country_code)
    aurora = finland_service.get_aurora()
    transport = finland_service.get_transport(lat, lon, now, country_code, digitransit_api_key)
    
    raw_data = RawData(
        weather=weather_data,
        air_quality=air_quality,
        uv_index=uv_index,
        solar_radiation=solar_radiation,
        marine=marine_data,
        flood=flood_data,
        road_weather=road_weather,
        electricity=electricity,
        detailed_electricity=detailed_elec,
        aurora=aurora,
        transport=transport,
        nowcast=nowcast
    )
    
    # 5. perform Calculations (via Services)
    solar_info = astronomy_service.get_solar_info(lat, lon, now, timezone)
    daylight_info = astronomy_service.get_daylight_info(lat, lon, now, timezone)
    golden_blue = astronomy_service.get_golden_blue_hours(lat, lon, now, timezone)
    sun_countdown = astronomy_service.get_sun_countdown(lat, lon, now, timezone)
    lunar_info = astronomy_service.get_lunar_info(lat, lon, now, timezone, translations)
    eclipse_info = astronomy_service.get_eclipse_info(lat, lon, now)
    
    date_info = calendar_service.get_date_info(now)
    season = calendar_service.get_season(now, lat, translations)
    name_day = calendar_service.get_name_day(now, country_code)
    next_holiday = calendar_service.get_next_holiday(now, country_code, language, localization_format.HOLIDAY_TRANSLATIONS)
    
    time_expression = time_expr_calc.get_time_expression(now, language)
    time_of_day = time_expr_calc.get_time_of_day(now.hour, translations)
    
    morning_forecast = weather_service.get_morning_forecast(lat, lon, timezone, now)
    forecast_12h = weather_service.get_forecast_12h(lat, lon, timezone, now)
    forecast_7day = weather_service.get_forecast_7day(lat, lon, timezone)
    
    computed_data = ComputedData(
        solar_info=solar_info,
        daylight_info=daylight_info,
        golden_blue=golden_blue,
        sun_countdown=sun_countdown,
        lunar_info=lunar_info,
        eclipse_info=eclipse_info,
        date_info=date_info,
        season=season,
        name_day=name_day,
        next_holiday=next_holiday,
        time_expression=time_expression,
        time_of_day=time_of_day,
        morning_forecast=morning_forecast,
        forecast_12h=forecast_12h,
        forecast_7day=forecast_7day
    )
    
    # 6. Generate Warnings
    # Convert WeatherData model to dict for warnings calculation (if needed by current impl)
    # The current warnings calculation expects a dict. Can we use the model directly?
    # No, get_weather_warnings expects a dict-like interface for "temperature", etc.
    # WeatherData is a dataclass, so we can use asdict or getattr.
    # But for now let's just construct a dict representing what get_weather_warnings expects.
    weather_dict = {
        "temperature": weather_data.temperature,
        "wind_speed": weather_data.wind_speed,
        "precipitation_probability": weather_data.precipitation_probability,
        "weather_code": weather_data.weather_code
    }
    
    aqi_dict = {"aqi": air_quality.aqi} if air_quality.aqi is not None else None
    
    warnings_list = warnings_calc.get_weather_warnings(
        weather_dict, 
        uv_index, 
        aqi_dict, 
        translations
    )
    
    # 7. Construct and Return Snapshot
    snapshot = AikaSnapshot(
        location=location,
        raw=raw_data,
        computed=computed_data,
        warnings=warnings_list,
        timestamp=now,
        language=language,
        country_code=country_code
    )
    
    return snapshot
