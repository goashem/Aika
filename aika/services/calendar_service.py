"""Service for calendar, holiday, and date calculations."""

from ..models import DateInfo
from ..calculations import calendar


def get_date_info(now):
    """Get comprehensive date information."""
    data = calendar.get_date_info(now)

    return DateInfo(day_name=data.get("day_name", ""), day_num=data.get("day_num", 0), month_name=data.get("month_name", ""), year=data.get("year", 0),
                    week_num=data.get("week_num", 0), day_of_year=data.get("day_of_year", 0), days_in_year=data.get("days_in_year", 365),
                    weeks_in_year=data.get("weeks_in_year", 52), pct_complete=data.get("pct_complete", 0.0))


def get_season(now, latitude, translations):
    """Get the current season."""
    return calendar.get_season(now, latitude, translations)


def get_name_day(now, country_code):
    """Get name day (Finland only)."""
    return calendar.get_name_day(now, country_code)


def get_next_holiday(now, country_code, language, holiday_translations):
    """Get next holiday."""
    return calendar.get_next_holiday(now, country_code, language, holiday_translations)
