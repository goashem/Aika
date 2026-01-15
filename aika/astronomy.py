"""Astronomical calculations for sun, moon, and eclipses."""
import datetime
import math
from typing import Any

import ephem
from astral import LocationInfo, SunDirection
from astral.sun import sun, golden_hour, blue_hour

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


def get_daylight_info(latitude, longitude, now, timezone):
    """Calculate daylight length and change from yesterday.

    Returns:
        dict: {
            'daylight_hours': float,
            'daylight_minutes': int,
            'change_from_yesterday': int (+/- minutes),
            'change_direction': 'longer'/'shorter'/'same'
        }
    """
    location = LocationInfo(name="Custom", region="Custom", timezone=timezone, latitude=latitude, longitude=longitude)

    if ZONEINFO_AVAILABLE:
        local_tz = ZoneInfo(timezone)
    else:
        local_tz = None

    try:
        # Today's sun times
        today_sun = sun(location.observer, date=now.date(), tzinfo=local_tz)
        today_sunrise = today_sun['sunrise']
        today_sunset = today_sun['sunset']
        today_daylight = (today_sunset - today_sunrise).total_seconds() / 60  # minutes

        # Yesterday's sun times
        yesterday = now.date() - datetime.timedelta(days=1)
        yesterday_sun = sun(location.observer, date=yesterday, tzinfo=local_tz)
        yesterday_sunrise = yesterday_sun['sunrise']
        yesterday_sunset = yesterday_sun['sunset']
        yesterday_daylight = (yesterday_sunset - yesterday_sunrise).total_seconds() / 60

        change = int(round(today_daylight - yesterday_daylight))

        if change > 0:
            change_direction = 'longer'
        elif change < 0:
            change_direction = 'shorter'
        else:
            change_direction = 'same'

        return {
            'daylight_hours': today_daylight / 60,
            'daylight_minutes': int(today_daylight),
            'change_from_yesterday': change,
            'change_direction': change_direction
        }
    except Exception:
        return None


def get_golden_blue_hours(latitude, longitude, now, timezone):
    """Calculate golden hour and blue hour times.

    Golden hour: sun 0-6 degrees above horizon (soft, warm light)
    Blue hour: sun 4-6 degrees below horizon (soft, blue light)

    Returns:
        dict with morning/evening golden/blue hour times, and current state flags
    """
    location = LocationInfo(name="Custom", region="Custom", timezone=timezone, latitude=latitude, longitude=longitude)

    if ZONEINFO_AVAILABLE:
        local_tz = ZoneInfo(timezone)
    else:
        local_tz = None

    result = {
        'morning_blue_hour': None,
        'morning_golden_hour': None,
        'evening_golden_hour': None,
        'evening_blue_hour': None,
        'is_golden_hour_now': False,
        'is_blue_hour_now': False
    }

    try:
        # Morning golden hour (sun rising)
        try:
            mg = golden_hour(location.observer, now.date(), SunDirection.RISING, local_tz)
            result['morning_golden_hour'] = {
                'start': mg[0].strftime("%H.%M"),
                'end': mg[1].strftime("%H.%M")
            }
        except ValueError:
            pass  # No golden hour (polar regions)

        # Evening golden hour (sun setting)
        try:
            eg = golden_hour(location.observer, now.date(), SunDirection.SETTING, local_tz)
            result['evening_golden_hour'] = {
                'start': eg[0].strftime("%H.%M"),
                'end': eg[1].strftime("%H.%M")
            }
        except ValueError:
            pass

        # Morning blue hour
        try:
            mb = blue_hour(location.observer, now.date(), SunDirection.RISING, local_tz)
            result['morning_blue_hour'] = {
                'start': mb[0].strftime("%H.%M"),
                'end': mb[1].strftime("%H.%M")
            }
        except ValueError:
            pass

        # Evening blue hour
        try:
            eb = blue_hour(location.observer, now.date(), SunDirection.SETTING, local_tz)
            result['evening_blue_hour'] = {
                'start': eb[0].strftime("%H.%M"),
                'end': eb[1].strftime("%H.%M")
            }
        except ValueError:
            pass

        # Check if currently in golden/blue hour
        if ZONEINFO_AVAILABLE:
            current = now.replace(tzinfo=local_tz)
        else:
            current = now

        # Check morning golden hour
        if result['morning_golden_hour']:
            try:
                mg = golden_hour(location.observer, now.date(), SunDirection.RISING, local_tz)
                if mg[0] <= current <= mg[1]:
                    result['is_golden_hour_now'] = True
            except:
                pass

        # Check evening golden hour
        if result['evening_golden_hour'] and not result['is_golden_hour_now']:
            try:
                eg = golden_hour(location.observer, now.date(), SunDirection.SETTING, local_tz)
                if eg[0] <= current <= eg[1]:
                    result['is_golden_hour_now'] = True
            except:
                pass

        # Check morning blue hour
        if result['morning_blue_hour']:
            try:
                mb = blue_hour(location.observer, now.date(), SunDirection.RISING, local_tz)
                if mb[0] <= current <= mb[1]:
                    result['is_blue_hour_now'] = True
            except:
                pass

        # Check evening blue hour
        if result['evening_blue_hour'] and not result['is_blue_hour_now']:
            try:
                eb = blue_hour(location.observer, now.date(), SunDirection.SETTING, local_tz)
                if eb[0] <= current <= eb[1]:
                    result['is_blue_hour_now'] = True
            except:
                pass

    except Exception:
        pass

    return result


def get_sun_countdown(latitude, longitude, now, timezone):
    """Calculate time remaining to next sunrise or sunset.

    Returns:
        dict: {
            'time_to_sunrise': int or None (minutes, if before sunrise),
            'time_to_sunset': int or None (minutes, if sun is up),
            'sun_is_up': bool,
            'next_event': 'sunrise' or 'sunset',
            'next_event_time': str (HH.MM),
            'next_event_in_minutes': int
        }
    """
    location = LocationInfo(name="Custom", region="Custom", timezone=timezone, latitude=latitude, longitude=longitude)

    if ZONEINFO_AVAILABLE:
        local_tz = ZoneInfo(timezone)
    else:
        local_tz = None

    try:
        # Get today's sun times
        today_sun = sun(location.observer, date=now.date(), tzinfo=local_tz)
        sunrise = today_sun['sunrise']
        sunset = today_sun['sunset']

        # Make current time timezone-aware for comparison
        if ZONEINFO_AVAILABLE:
            current = now.replace(tzinfo=local_tz)
        else:
            current = now

        result = {
            'time_to_sunrise': None,
            'time_to_sunset': None,
            'sun_is_up': False,
            'next_event': None,
            'next_event_time': None,
            'next_event_in_minutes': None
        }

        if current < sunrise:
            # Before sunrise
            minutes_to_sunrise = int((sunrise - current).total_seconds() / 60)
            result['time_to_sunrise'] = minutes_to_sunrise
            result['sun_is_up'] = False
            result['next_event'] = 'sunrise'
            result['next_event_time'] = sunrise.strftime("%H.%M")
            result['next_event_in_minutes'] = minutes_to_sunrise
        elif current < sunset:
            # Sun is up, waiting for sunset
            minutes_to_sunset = int((sunset - current).total_seconds() / 60)
            result['time_to_sunset'] = minutes_to_sunset
            result['sun_is_up'] = True
            result['next_event'] = 'sunset'
            result['next_event_time'] = sunset.strftime("%H.%M")
            result['next_event_in_minutes'] = minutes_to_sunset
        else:
            # After sunset, get tomorrow's sunrise
            tomorrow = now.date() + datetime.timedelta(days=1)
            tomorrow_sun = sun(location.observer, date=tomorrow, tzinfo=local_tz)
            tomorrow_sunrise = tomorrow_sun['sunrise']
            minutes_to_sunrise = int((tomorrow_sunrise - current).total_seconds() / 60)
            result['time_to_sunrise'] = minutes_to_sunrise
            result['sun_is_up'] = False
            result['next_event'] = 'sunrise'
            result['next_event_time'] = tomorrow_sunrise.strftime("%H.%M")
            result['next_event_in_minutes'] = minutes_to_sunrise

        return result
    except Exception:
        return None


def get_lunar_info(latitude, longitude, now, timezone, translations):
    """Calculate lunar info including phase, position, and rise/set/transit times."""
    observer = create_observer(latitude, longitude, now, timezone)

    moon = ephem.Moon()
    moon.compute(observer)

    # Helpers to convert ephem date to localized values
    def ephem_to_local_datetime(ephem_date):
        utc_datetime = ephem.Date(ephem_date).datetime()
        if ZONEINFO_AVAILABLE:
            utc_datetime = utc_datetime.replace(tzinfo=ZoneInfo('UTC'))
            return utc_datetime.astimezone(ZoneInfo(timezone))
        return utc_datetime + datetime.timedelta(hours=2)

    def ephem_to_local_time(ephem_date):
        return ephem_to_local_datetime(ephem_date).strftime("%H.%M")

    # Moon phase (percentage)
    moon_phase = moon.phase
    moon_cycle_position = getattr(moon, 'moon_phase', None)
    moon_elongation = getattr(moon, 'elong', None)

    # Flag special phases near new/full moons
    special_phase = None
    if moon_phase <= 1:
        special_phase = 'new'
    elif moon_phase >= 99:
        special_phase = 'full'

    # Is the moon waxing or waning?
    moon_growth_dict = translations['moon_growth']
    if moon_elongation is not None:
        moon_growth = moon_growth_dict['growing'] if float(moon_elongation) >= 0 else moon_growth_dict['waning']
    elif moon_cycle_position is not None:
        moon_growth = moon_growth_dict['growing'] if moon_cycle_position < 0.5 else moon_growth_dict['waning']
    else:
        moon_growth = moon_growth_dict['growing'] if moon_phase < 50 else moon_growth_dict['waning']

    # Upcoming principal lunar phases
    future_phases = []
    try:
        next_new = ephem_to_local_datetime(ephem.next_new_moon(observer.date))
        future_phases.append({'type': 'new', 'datetime': next_new})
    except Exception:
        pass
    try:
        next_full = ephem_to_local_datetime(ephem.next_full_moon(observer.date))
        future_phases.append({'type': 'full', 'datetime': next_full})
    except Exception:
        pass
    future_phases = [entry for entry in future_phases if entry.get('datetime')]
    future_phases.sort(key=lambda entry: entry['datetime'])

    # Moon altitude and azimuth

    moon_altitude = math.degrees(moon.alt)
    moon_azimuth = math.degrees(moon.az)

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
            'transit': moon_transit, 'special_phase': special_phase, 'future_phases': future_phases}


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
