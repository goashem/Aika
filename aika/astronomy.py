"""Astronomical calculations for sun, moon, and eclipses."""
import datetime
import math
from typing import Any

import ephem
from astral import LocationInfo
from astral.sun import sun

try:
    from zoneinfo import ZoneInfo

    ZONEINFO_AVAILABLE = True
except ImportError:
    ZONEINFO_AVAILABLE = False


def create_observer(latitude, longitude, now, timezone):
    """Create and configure an astronomical observer instance.

    Returns:
        ephem.Observer: Observer object initialized with location and time
    """
    observer = ephem.Observer()
    observer.lat = str(latitude)
    observer.lon = str(longitude)

    # ephem expects UTC time
    if ZONEINFO_AVAILABLE:
        local_tz = ZoneInfo(timezone)
        local_dt = now.replace(tzinfo=local_tz)
        utc_dt = local_dt.astimezone(ZoneInfo('UTC'))
        observer.date = utc_dt.replace(tzinfo=None)
    else:
        utc_offset = 2
        observer.date = now - datetime.timedelta(hours=utc_offset)

    return observer


def get_solar_info(latitude, longitude, now, timezone):
    """Calculate solar info including dawn, sunrise, noon, sunset, dusk times and sun position."""
    location = LocationInfo(name="Custom", region="Custom", timezone=timezone, latitude=latitude, longitude=longitude)

    # Pass timezone to get local times instead of UTC
    if ZONEINFO_AVAILABLE:
        local_tz = ZoneInfo(timezone)
        s = sun(location.observer, date=now.date(), tzinfo=local_tz)
    else:
        s = sun(location.observer, date=now.date())

    # Sun position using ephem
    observer = create_observer(latitude, longitude, now, timezone)
    sun_body = ephem.Sun()
    sun_body.compute(observer)

    sun_elevation = math.degrees(sun_body.alt)
    sun_azimuth = math.degrees(sun_body.az)

    return {'dawn': s['dawn'].strftime("%H.%M"), 'sunrise': s['sunrise'].strftime("%H.%M"), 'noon': s['noon'].strftime("%H.%M"),
            'sunset': s['sunset'].strftime("%H.%M"), 'dusk': s['dusk'].strftime("%H.%M"), 'elevation': sun_elevation, 'azimuth': sun_azimuth}


def get_lunar_info(latitude, longitude, now, timezone, translations):
    """Calculate lunar info including phase, position, and rise/set/transit times."""
    observer = create_observer(latitude, longitude, now, timezone)

    moon = ephem.Moon()
    moon.compute(observer)

    # Moon phase (percentage)
    moon_phase = moon.phase

    # Is the moon waxing or waning?
    moon_growth_dict = translations['moon_growth']
    if moon.phase < 50:
        moon_growth = moon_growth_dict['growing']
    else:
        moon_growth = moon_growth_dict['waning']

    # Moon altitude and azimuth
    moon_altitude = math.degrees(moon.alt)
    moon_azimuth = math.degrees(moon.az)

    # Helper to convert ephem date to local time string
    def ephem_to_local_time(ephem_date):
        utc_datetime = ephem.Date(ephem_date).datetime()
        if ZONEINFO_AVAILABLE:
            utc_datetime = utc_datetime.replace(tzinfo=ZoneInfo('UTC'))
            local_datetime = utc_datetime.astimezone(ZoneInfo(timezone))
            return local_datetime.strftime("%H.%M")
        else:
            local_datetime = utc_datetime + datetime.timedelta(hours=2)
            return local_datetime.strftime("%H.%M")

    # Get moon rise/set/transit times for today
    if ZONEINFO_AVAILABLE:
        local_midnight = now.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=ZoneInfo(timezone))
        utc_midnight = local_midnight.astimezone(ZoneInfo('UTC'))
        observer.date = utc_midnight.replace(tzinfo=None)
    else:
        observer.date = now.replace(hour=0, minute=0, second=0, microsecond=0) - datetime.timedelta(hours=2)

    moon_rise = None
    moon_set = None
    moon_transit = None

    try:
        rise = observer.next_rising(moon)
        rise_dt = ephem.Date(rise).datetime()
        # Sets moon rise time if within current day
        if rise_dt.date() == now.date() or (rise_dt + datetime.timedelta(hours=2)).date() == now.date():
            moon_rise = ephem_to_local_time(rise)
    except (ephem.AlwaysUpError, ephem.NeverUpError):
        pass

    try:
        setting = observer.next_setting(moon)
        set_dt = ephem.Date(setting).datetime()
        if set_dt.date() == now.date() or (set_dt + datetime.timedelta(hours=2)).date() == now.date():
            moon_set = ephem_to_local_time(setting)
    except (ephem.AlwaysUpError, ephem.NeverUpError):
        pass

    try:
        transit = observer.next_transit(moon)
        transit_dt = ephem.Date(transit).datetime()
        # Sets moon transit time if within current day
        if transit_dt.date() == now.date() or (transit_dt + datetime.timedelta(hours=2)).date() == now.date():
            moon_transit = ephem_to_local_time(transit)
    except:
        pass

    return {'phase': moon_phase, 'growth': moon_growth, 'altitude': moon_altitude, 'azimuth': moon_azimuth, 'rise': moon_rise, 'set': moon_set,
            'transit': moon_transit}


def get_next_eclipse(latitude, longitude, now):
    """Calculate the next locally visible solar and lunar eclipses using ephem."""
    try:
        observer = ephem.Observer()
        observer.lat = str(latitude)
        observer.lon = str(longitude)

        next_lunar = None
        next_solar = None

        moon = ephem.Moon()
        sun_body = ephem.Sun()

        # Search for the next LOCALLY VISIBLE lunar eclipse (up to 3 years ahead)
        search_date = ephem.Date(now)
        # Identifies next locally visible lunar eclipse within constraints
        for _ in range(60):
            next_full = ephem.next_full_moon(search_date)
            full_moon_date = ephem.Date(next_full).datetime()

            observer.date = next_full
            moon.compute(observer)
            sun_body.compute(observer)

            moon_lat = abs(float(moon.hlat))

            if moon_lat < 0.02:
                moon_alt = float(moon.alt)
                if moon_alt > 0:
                    eclipse_type = "total" if moon_lat < 0.008 else "partial"
                    next_lunar = {"date": full_moon_date, "type": eclipse_type}
                    break

            search_date = next_full + 1

        # Search for the next LOCALLY VISIBLE solar eclipse (up to 3 years ahead)
        search_date = ephem.Date(now)
        # Identifies next visible solar eclipse within constraints
        for _ in range(60):
            next_new = ephem.next_new_moon(search_date)
            new_moon_date = ephem.Date(next_new).datetime()

            observer.date = next_new
            moon.compute(observer)
            sun_body.compute(observer)

            moon_lat = abs(float(moon.hlat))

            # Determines next visible solar eclipse type and date
            if moon_lat < 0.02:
                sun_alt = float(sun_body.alt)
                if sun_alt > 0:
                    sep = float(ephem.separation(sun_body, moon))
                    sep_deg = math.degrees(sep)

                    if sep_deg < 1.5:
                        eclipse_type = "total" if sep_deg < 0.3 else "partial"
                        next_solar = {"date": new_moon_date, "type": eclipse_type}
                        break

            search_date = next_new + 1

        return {"lunar": next_lunar, "solar": next_solar}
    except:
        return None
