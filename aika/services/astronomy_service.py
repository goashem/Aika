"""Astronomy service for calculating solar and lunar information."""

from ..models import (SolarInfo, DaylightInfo, GoldenBlueHours, SunCountdown, LunarInfo, EclipseInfo)
from ..calculations import astronomy


def get_solar_info(latitude, longitude, now, timezone):
    """Get solar times and position."""
    data = astronomy.get_solar_info(latitude, longitude, now, timezone)

    return SolarInfo(dawn=data.get("dawn", ""), sunrise=data.get("sunrise", ""), noon=data.get("noon", ""), sunset=data.get("sunset", ""),
                     dusk=data.get("dusk", ""), elevation=data.get("elevation", 0.0), azimuth=data.get("azimuth", 0.0))


def get_daylight_info(latitude, longitude, now, timezone):
    """Get daylight duration information."""
    data = astronomy.get_daylight_info(latitude, longitude, now, timezone)
    if not data:
        return DaylightInfo()

    return DaylightInfo(daylight_hours=data.get("daylight_hours", 0.0), daylight_minutes=data.get("daylight_minutes", 0),
                        change_from_yesterday=data.get("change_from_yesterday", 0), change_direction=data.get("change_direction", "same"))


def get_golden_blue_hours(latitude, longitude, now, timezone):
    """Get golden and blue hour times."""
    data = astronomy.get_golden_blue_hours(latitude, longitude, now, timezone)

    return GoldenBlueHours(morning_golden_hour=data.get("morning_golden_hour"), evening_golden_hour=data.get("evening_golden_hour"),
                           morning_blue_hour=data.get("morning_blue_hour"), evening_blue_hour=data.get("evening_blue_hour"),
                           is_golden_hour_now=data.get("is_golden_hour_now", False), is_blue_hour_now=data.get("is_blue_hour_now", False))


def get_sun_countdown(latitude, longitude, now, timezone):
    """Get countdown to next sunrise/sunset."""
    data = astronomy.get_sun_countdown(latitude, longitude, now, timezone)
    if not data:
        return SunCountdown()

    return SunCountdown(time_to_sunrise=data.get("time_to_sunrise"), time_to_sunset=data.get("time_to_sunset"), sun_is_up=data.get("sun_is_up", False),
                        next_event=data.get("next_event"), next_event_time=data.get("next_event_time"), next_event_in_minutes=data.get("next_event_in_minutes"))


def get_lunar_info(latitude, longitude, now, timezone, translations):
    """Get lunar phase and position info."""
    data = astronomy.get_lunar_info(latitude, longitude, now, timezone, translations)

    return LunarInfo(phase=data.get("phase", 0.0), growth=data.get("growth", ""), altitude=data.get("altitude", 0.0), azimuth=data.get("azimuth", 0.0),
                     rise=data.get("rise"), set=data.get("set"), transit=data.get("transit"), special_phase=data.get("special_phase"),
                     future_phases=data.get("future_phases", []))


def get_eclipse_info(latitude, longitude, now):
    """Get next eclipse information."""
    data = astronomy.get_next_eclipse(latitude, longitude, now)
    if not data:
        return EclipseInfo()

    return EclipseInfo(lunar=data.get("lunar"), solar=data.get("solar"))
