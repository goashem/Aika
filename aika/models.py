"""Data models for Aika library.

This module contains all typed dataclasses representing the domain entities.
These models provide a structured, typed interface for the library API.
"""

from dataclasses import dataclass, field
from datetime import datetime
from datetime import date as date_type
from typing import Literal


# ============================================================================
# Weather Models
# ============================================================================

@dataclass
class WeatherData:
    """Current weather conditions."""
    temperature: float | None = None
    apparent_temp: float | None = None
    description: str = "not available"
    humidity: int | None = None
    pressure: float | None = None
    wind_speed: float | None = None
    wind_direction: float | None = None
    gust_speed: float | None = None
    visibility: float | None = None
    precip_intensity: float | None = None
    precipitation_probability: int | None = None
    weather_code: int | None = None
    snow_depth: float | None = None


@dataclass
class AirQuality:
    """Air quality measurements."""
    aqi: int | None = None
    european_aqi: int | None = None
    pm2_5: float | None = None
    pm10: float | None = None


@dataclass
class SolarRadiation:
    """Solar radiation measurements."""
    cloud_cover: int | None = None
    ghi: float | None = None  # Global Horizontal Irradiance
    dni: float | None = None  # Direct Normal Irradiance
    dhi: float | None = None  # Diffuse Horizontal Irradiance
    gti: float | None = None  # Global Tilted Irradiance
    direct: float | None = None


@dataclass
class MarineData:
    """Marine and wave data."""
    wave_height: float | None = None
    wave_direction: float | None = None
    wave_period: float | None = None
    wind_wave_height: float | None = None
    swell_wave_height: float | None = None


@dataclass
class FloodData:
    """River discharge and flood data."""
    river_discharge: float | None = None
    river_discharge_mean: float | None = None
    river_discharge_max: float | None = None


@dataclass
class Nowcast:
    """Short-term precipitation forecast (next 2 hours)."""
    rain_starts_in_min: int | None = None
    rain_ends_in_min: int | None = None
    is_raining_now: bool = False
    precipitation_type: Literal["rain", "snow", "mixed", "none"] = "none"
    max_intensity: float = 0.0
    intervals: list[dict] = field(default_factory=list)


@dataclass
class MorningForecast:
    """Weather forecast for tomorrow morning."""
    forecast_date: date_type | None = None
    temp_min: float | None = None
    temp_max: float | None = None
    apparent_min: float | None = None
    precip_prob_max: int | None = None
    weather_code: int | None = None
    wind_max: float | None = None
    gust_max: float | None = None
    visibility_min: float | None = None


@dataclass
class Forecast12h:
    """12-hour forecast summary."""
    rain_windows: list[dict] = field(default_factory=list)
    strongest_wind: dict | None = None
    temp_range: dict | None = None


@dataclass
class Forecast7day:
    """7-day forecast with outdoor activity recommendations."""
    days: list[dict] = field(default_factory=list)
    best_outdoor_window: dict | None = None
    snow_accumulation_cm: float | None = None


# ============================================================================
# Astronomy Models
# ============================================================================

@dataclass
class SolarInfo:
    """Solar times and position."""
    dawn: str = ""
    sunrise: str = ""
    noon: str = ""
    sunset: str = ""
    dusk: str = ""
    elevation: float = 0.0
    azimuth: float = 0.0


@dataclass
class DaylightInfo:
    """Daylight duration information."""
    daylight_hours: float = 0.0
    daylight_minutes: int = 0
    change_from_yesterday: int = 0
    change_direction: Literal["longer", "shorter", "same"] = "same"


@dataclass
class GoldenBlueHours:
    """Golden hour and blue hour times."""
    morning_golden_hour: dict | None = None
    evening_golden_hour: dict | None = None
    morning_blue_hour: dict | None = None
    evening_blue_hour: dict | None = None
    is_golden_hour_now: bool = False
    is_blue_hour_now: bool = False


@dataclass
class SunCountdown:
    """Time to next sunrise or sunset."""
    time_to_sunrise: int | None = None
    time_to_sunset: int | None = None
    sun_is_up: bool = False
    next_event: Literal["sunrise", "sunset"] | None = None
    next_event_time: str | None = None
    next_event_in_minutes: int | None = None


@dataclass
class LunarInfo:
    """Lunar phase and position."""
    phase: float = 0.0
    growth: str = ""
    altitude: float = 0.0
    azimuth: float = 0.0
    rise: str | None = None
    set: str | None = None
    transit: str | None = None
    special_phase: Literal["new", "full"] | None = None
    future_phases: list[dict] = field(default_factory=list)


@dataclass
class EclipseInfo:
    """Next visible eclipses."""
    lunar: dict | None = None
    solar: dict | None = None


# ============================================================================
# Finland-Specific Models
# ============================================================================

@dataclass
class RoadWeather:
    """Finnish road weather conditions."""
    condition: Literal["NORMAL", "POOR", "VERY_POOR", "NO_DATA"] = "NO_DATA"
    reason: str | None = None


@dataclass
class ElectricityPrice:
    """Current electricity spot price."""
    price_15min: float | None = None
    price_hour: float | None = None


@dataclass
class DetailedElectricity:
    """Detailed electricity pricing with future prices."""
    current_price: float | None = None
    cheapest_hour: dict | None = None
    most_expensive_hour: dict | None = None
    three_cheapest_hours: list[dict] = field(default_factory=list)
    tomorrow_prices: list[dict] = field(default_factory=list)
    future_prices: list[dict] = field(default_factory=list)
    timestamp: str = ""


@dataclass
class AuroraForecast:
    """Aurora borealis forecast."""
    kp: float = 0.0
    fmi_activity: str | None = None


@dataclass
class TransportDisruptions:
    """Public transport disruptions."""
    alerts: list[dict] = field(default_factory=list)
    error: str | None = None


# ============================================================================
# Calendar Models
# ============================================================================

@dataclass
class DateInfo:
    """Comprehensive date information."""
    day_name: str = ""
    day_num: int = 0
    month_name: str = ""
    year: int = 0
    week_num: int = 0
    day_of_year: int = 0
    days_in_year: int = 365
    weeks_in_year: int = 52
    pct_complete: float = 0.0


# ============================================================================
# Location Model
# ============================================================================

@dataclass
class Location:
    """Location information."""
    latitude: float = 0.0
    longitude: float = 0.0
    city_name: str | None = None
    country_name: str | None = None
    country_code: str = "FI"
    timezone: str = "Europe/Helsinki"


# ============================================================================
# Composite Models (Main Containers)
# ============================================================================

@dataclass
class RawData:
    """Raw data from providers."""
    weather: WeatherData | None = None
    air_quality: AirQuality | None = None
    uv_index: float | None = None
    solar_radiation: SolarRadiation | None = None
    marine: MarineData | None = None
    flood: FloodData | None = None
    road_weather: RoadWeather | None = None
    electricity: ElectricityPrice | None = None
    detailed_electricity: DetailedElectricity | None = None
    aurora: AuroraForecast | None = None
    transport: TransportDisruptions | None = None
    nowcast: Nowcast | None = None


@dataclass
class ComputedData:
    """Calculated/derived data."""
    solar_info: SolarInfo | None = None
    daylight_info: DaylightInfo | None = None
    golden_blue: GoldenBlueHours | None = None
    sun_countdown: SunCountdown | None = None
    lunar_info: LunarInfo | None = None
    eclipse_info: EclipseInfo | None = None
    date_info: DateInfo | None = None
    season: str = ""
    name_day: str | None = None
    next_holiday: str = ""
    time_expression: str = ""
    time_of_day: str = ""
    morning_forecast: MorningForecast | None = None
    forecast_12h: Forecast12h | None = None
    forecast_7day: Forecast7day | None = None


@dataclass
class AikaSnapshot:
    """Complete snapshot returned by the library API.

    This is the main data structure containing all raw and computed data
    for a given location and time.
    """
    location: Location
    raw: RawData
    computed: ComputedData
    warnings: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    language: str = "fi"
    country_code: str = "FI"
