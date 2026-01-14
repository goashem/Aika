"""Display and output formatting."""
import datetime
from typing import Any

from astral import LocationInfo
from astral.sun import sun

try:
    from zoneinfo import ZoneInfo as _ZoneInfo

    ZONEINFO_AVAILABLE = True
except ImportError:
    _ZoneInfo = None
    ZONEINFO_AVAILABLE = False

ZoneInfo: Any = _ZoneInfo

from .localization import get_finnish_translations, get_time_expression, get_time_of_day
from .weather import get_weather_description, degrees_to_compass


def display_info(ti):
    """Display all information in the selected language.

    Args:
        ti: TimeInfo instance with all necessary data
    """
    from .weather import (get_weather_data, get_uv_index, get_air_quality, get_solar_radiation, get_marine_data, get_flood_data, get_morning_forecast,
                          get_weather_warnings)
    from .astronomy import get_solar_info, get_lunar_info, get_next_eclipse
    from .calendar_info import get_date_info, get_season, get_next_holiday
    from .finland import (get_road_weather, get_electricity_price, get_aurora_forecast, get_transport_disruptions, get_detailed_electricity_pricing)
    from .localization import get_translations

    # Get all information
    translations = get_translations(ti.language)
    time_expression = get_time_expression(ti.now, ti.language)
    time_of_day = get_time_of_day(ti.now.hour, translations)
    weather_data = get_weather_data(ti.latitude, ti.longitude, ti.timezone)
    air_quality_data = get_air_quality(ti.latitude, ti.longitude, ti.timezone)
    uv_index = get_uv_index(ti.latitude, ti.longitude)
    solar_radiation = get_solar_radiation(ti.latitude, ti.longitude, ti.timezone)
    marine_data = get_marine_data(ti.latitude, ti.longitude, ti.timezone)
    flood_data = get_flood_data(ti.latitude, ti.longitude)
    morning_forecast = get_morning_forecast(ti.latitude, ti.longitude, ti.timezone, ti.now)
    season = get_season(ti.now, ti.latitude, translations)
    next_holiday = get_next_holiday(ti.now, ti.country_code, ti.language)
    solar_info = get_solar_info(ti.latitude, ti.longitude, ti.now, ti.timezone)
    lunar_info = get_lunar_info(ti.latitude, ti.longitude, ti.now, ti.timezone, translations)
    date_info = get_date_info(ti.now)
    finnish_translations = get_finnish_translations()

    # Finland-specific data
    road_weather = get_road_weather(ti.latitude, ti.longitude, ti.country_code)
    electricity_price = get_electricity_price(ti.now, ti.timezone, ti.country_code)
    detailed_electricity = get_detailed_electricity_pricing(ti.now, ti.timezone, ti.country_code)
    aurora_forecast = get_aurora_forecast()
    next_eclipse = get_next_eclipse(ti.latitude, ti.longitude, ti.now)
    transport_disruptions = get_transport_disruptions(ti.latitude, ti.longitude, ti.now, ti.country_code, ti.digitransit_api_key)

    # Time
    clock = ti.now.strftime("%H.%M")

    # Check if location timezone differs from system timezone
    location_time_str = None
    if ZONEINFO_AVAILABLE and ti.system_timezone:
        try:
            location_tz = ZoneInfo(ti.timezone)
            location_now = datetime.datetime.now(location_tz)
            location_time_str = location_now.strftime("%H.%M")

            system_now = datetime.datetime.now().astimezone()
            if location_now.hour != system_now.hour or location_now.minute != system_now.minute:
                pass
            else:
                location_time_str = None
        except:
            location_time_str = None

    date_strings = translations['date']

    # Display location at the top
    if ti.city_name and ti.country_name:
        print(f"\U0001F4CD {ti.city_name}, {ti.country_name}\n")
    elif ti.city_name:
        print(f"\U0001F4CD {ti.city_name}\n")

    # Display introductory sentences
    if ti.language == 'fi':
        day_name_local = finnish_translations['days'].get(date_info['day_name'], date_info['day_name'])
        month_name_genitive = finnish_translations['months_genitive'].get(date_info['month_name'], date_info['month_name'])
        print(f"Kello on {time_expression} ({clock}), joten on {time_of_day}.")
        print(f"On {day_name_local}, {date_info['day_num']}. {month_name_genitive}, {date_info['year']}.")
        print(
            f"Viikon numero on {date_info['week_num']}/{date_info['weeks_in_year']}, ja päivän numero on {date_info['day_of_year']}/{date_info['days_in_year']}.")
    else:
        day_name_local = date_info['day_name']
        month_name_local = date_info['month_name']
        print(f"The time is {time_expression} ({clock}), so it's {time_of_day}.")
        print(f"It's {day_name_local}, {date_info['day_num']} {month_name_local} {date_info['year']}.")
        print(f"Week number is {date_info['week_num']}/{date_info['weeks_in_year']}, and day number is {date_info['day_of_year']}/{date_info['days_in_year']}.")

    if location_time_str:
        print(date_strings['local_time'].format(time=location_time_str))

    print(date_strings['year_complete'].format(pct=date_info['pct_complete']))

    # Solar times
    solar_line = date_strings['dawn'].format(time=solar_info['dawn']) + ", "
    solar_line += date_strings['sunrise'].format(time=solar_info['sunrise']) + ", "
    solar_line += date_strings['noon'].format(time=solar_info['noon']) + ", "
    solar_line += date_strings['sunset'].format(time=solar_info['sunset']) + ", "
    solar_line += date_strings['dusk'].format(time=solar_info['dusk'])
    print(solar_line)

    # Sun position
    sun_visibility = date_strings['sun_visible'] if solar_info['elevation'] > 0 else date_strings['sun_below']
    sun_compass_key = degrees_to_compass(solar_info['azimuth'])
    sun_compass_dir = date_strings['compass_directions'].get(sun_compass_key, sun_compass_key)
    print(date_strings['sun_position'].format(elevation=solar_info['elevation'], azimuth=sun_compass_dir) + " " + sun_visibility)

    # Solar radiation
    if solar_radiation.get('cloud_cover') is not None:
        print(date_strings['cloud_cover'].format(cover=solar_radiation['cloud_cover']))
    ghi = solar_radiation.get('ghi')
    dni = solar_radiation.get('dni')
    if ghi is not None and dni is not None:
        if ghi > 0 or dni > 0:
            print(date_strings['solar_radiation'].format(ghi=ghi, dni=dni))
            if solar_radiation.get('gti') is not None:
                print(date_strings['solar_for_panels'].format(gti=solar_radiation['gti'], dni=dni))

    # Lunar info
    print(date_strings['moon_phase'].format(phase=lunar_info['phase'], growth=lunar_info['growth']))

    special_phase_key = lunar_info.get('special_phase')
    if special_phase_key:
        special_map = date_strings.get('moon_special_phases', {})
        special_text = special_map.get(special_phase_key)
        if special_text:
            print(special_text)

    moon_visibility = date_strings['moon_visible'] if lunar_info['altitude'] > 0 else date_strings['moon_below']
    moon_compass_key = degrees_to_compass(lunar_info['azimuth'])
    moon_compass_dir = date_strings['compass_directions'].get(moon_compass_key, moon_compass_key)
    print(date_strings['moon_position'].format(altitude=lunar_info['altitude'], azimuth=moon_compass_dir) + " " + moon_visibility)

    moon_times = []
    if lunar_info.get('rise'):
        moon_times.append(date_strings['moon_rise'].format(time=lunar_info['rise']))
    if lunar_info.get('transit'):
        moon_times.append(date_strings['moon_transit'].format(time=lunar_info['transit']))
    if lunar_info.get('set'):
        moon_times.append(date_strings['moon_set'].format(time=lunar_info['set']))
    if moon_times:
        print(", ".join(moon_times))

    future_phases = lunar_info.get('future_phases') or []
    phase_labels = date_strings.get('moon_phase_names', {})
    next_phase_template = date_strings.get('moon_next_phase')
    if next_phase_template:
        for phase_entry in future_phases:
            phase_dt = phase_entry.get('datetime')
            if not phase_dt:
                continue
            date_str = phase_dt.strftime("%d.%m.%Y")
            time_str = phase_dt.strftime("%H.%M")
            label = phase_labels.get(phase_entry.get('type'), phase_entry.get('type'))
            print(next_phase_template.format(phase=label, date=date_str, time=time_str))

    # Weather
    if weather_data["temperature"] is not None:
        weather_desc = get_weather_description(weather_data.get('weather_code'), ti.language)
        print(date_strings['weather'].format(temp=weather_data['temperature'], desc=weather_desc))

        if weather_data.get('apparent_temp') is not None:
            print(date_strings['feels_like'].format(temp=weather_data['apparent_temp']))

        if weather_data['humidity'] is not None and weather_data['pressure'] is not None:
            print(date_strings['humidity'].format(humidity=weather_data['humidity'], pressure=weather_data['pressure']))

        if weather_data.get('wind_speed') is not None and weather_data.get('wind_direction') is not None:
            compass_key = degrees_to_compass(weather_data['wind_direction'])
            compass_dir = date_strings['compass_directions'].get(compass_key, compass_key)
            if weather_data.get('gust_speed') is not None:
                print(date_strings['wind_full'].format(speed=weather_data['wind_speed'], dir=compass_dir, gust=weather_data['gust_speed']))
            else:
                print(date_strings['wind_no_gust'].format(speed=weather_data['wind_speed'], dir=compass_dir))
        elif weather_data.get('wind_speed') is not None:
            print(date_strings['wind'].format(speed=weather_data['wind_speed']))

        if weather_data.get('visibility') is not None and weather_data['visibility'] > 0:
            print(date_strings['visibility'].format(vis=weather_data['visibility'] / 1000))

        if weather_data.get('precip_intensity') is not None and weather_data['precip_intensity'] > 0:
            print(date_strings['precip_intensity'].format(intensity=weather_data['precip_intensity']))

        if weather_data.get('precipitation_probability') is not None:
            print(date_strings['precipitation'].format(prob=weather_data['precipitation_probability']))

        if weather_data.get('snow_depth') is not None and weather_data['snow_depth'] > 0:
            print(date_strings['snow_depth'].format(depth=weather_data['snow_depth']))
    else:
        if ti.language == 'fi':
            print("Sää: ei saatavilla")
        else:
            print("Weather: not available")

    # Marine data
    wave_height = marine_data.get('wave_height')
    if wave_height is not None and wave_height > 0.1:
        wave_compass_key = degrees_to_compass(marine_data.get('wave_direction'))
        wave_compass_dir = date_strings['compass_directions'].get(wave_compass_key, wave_compass_key) if wave_compass_key else '?'
        print(date_strings['wave_info'].format(height=wave_height, period=marine_data.get('wave_period', 0), dir=wave_compass_dir))

    # Air quality
    if air_quality_data["aqi"] is not None:
        aqi_text = translations['air_quality_levels'].get(air_quality_data["aqi"], "not available")
        print(date_strings['air_quality'].format(quality=aqi_text, aqi=air_quality_data['aqi']))

    # UV index
    if uv_index is not None:
        if uv_index >= 8:
            print(date_strings['uv_very_high'].format(index=uv_index))
        elif uv_index >= 6:
            print(date_strings['uv_high'].format(index=uv_index))
        elif uv_index >= 3:
            print(date_strings['uv_moderate'].format(index=uv_index))
        else:
            print(date_strings['uv_low'].format(index=uv_index))
    else:
        if ti.language == 'fi':
            print("UV-indeksi: ei saatavilla")
        else:
            print("UV index: not available")

    print(date_strings['season'].format(season=season))
    print(date_strings['next_holiday'].format(holiday=next_holiday))

    # Finland-specific features
    if ti.country_code == 'FI':
        if road_weather:
            condition_value = str(road_weather.get('condition', 'NORMAL'))
            reason_value = road_weather.get('reason')
            if condition_value == 'NO_DATA':
                unavailable_text = date_strings.get('road_weather_unavailable')
                if unavailable_text:
                    print(unavailable_text)
                else:
                    condition_text = date_strings.get('road_conditions', {}).get('NO_DATA', condition_value.lower())
                    print(date_strings['road_weather'].format(condition=condition_text))
            else:
                condition_text = date_strings.get('road_conditions', {}).get(condition_value, condition_value.lower())
                if reason_value:
                    reason_key = str(reason_value)
                    reason_text = date_strings.get('road_reasons', {}).get(reason_key, reason_key.lower())
                    print(date_strings['road_weather_reason'].format(condition=condition_text, reason=reason_text))
                else:
                    print(date_strings['road_weather'].format(condition=condition_text))

        if electricity_price:
            price_15min = electricity_price.get('price_15min')
            price_hour = electricity_price.get('price_hour')
            
            # Display both prices if available
            if price_15min is not None and price_hour is not None:
                if price_15min < 5:
                    print(date_strings['electricity_price_low_dual'].format(price=price_15min, hour_price=price_hour))
                elif price_15min > 15:
                    print(date_strings['electricity_price_high_dual'].format(price=price_15min, hour_price=price_hour))
                else:
                    print(date_strings['electricity_price_dual'].format(price=price_15min, hour_price=price_hour))
            # Fallback to original display if only one price is available
            elif price_15min is not None:
                price = price_15min
                if price < 5:
                    print(date_strings['electricity_price_low'].format(price=price))
                elif price > 15:
                    print(date_strings['electricity_price_high'].format(price=price))
                else:
                    print(date_strings['electricity_price'].format(price=price))
            elif price_hour is not None:
                price = price_hour
                if price < 5:
                    print(date_strings['electricity_price_low'].format(price=price))
                elif price > 15:
                    print(date_strings['electricity_price_high'].format(price=price))
                else:
                    print(date_strings['electricity_price'].format(price=price))
                    
        # Display detailed electricity pricing information if available
        if detailed_electricity:
            # Show cheapest and most expensive future hours on one line with Finnish format
            cheapest_hour = detailed_electricity.get('cheapest_hour')
            most_expensive_hour = detailed_electricity.get('most_expensive_hour')
            
            if cheapest_hour and most_expensive_hour:
                # Determine if the hours are today or tomorrow/later
                if ZONEINFO_AVAILABLE and _ZoneInfo:
                    try:
                        # Get current date in Helsinki timezone
                        current_time = datetime.datetime.now(_ZoneInfo('Europe/Helsinki'))
                        current_date = current_time.date()
                        
                        # Parse the datetime strings to check dates
                        cheapest_dt = datetime.datetime.fromisoformat(cheapest_hour['datetime'])
                        most_expensive_dt = datetime.datetime.fromisoformat(most_expensive_hour['datetime'])
                        
                        # Convert to Helsinki timezone if needed
                        if cheapest_dt.tzinfo is None:
                            cheapest_dt = cheapest_dt.replace(tzinfo=_ZoneInfo('Europe/Helsinki'))
                        if most_expensive_dt.tzinfo is None:
                            most_expensive_dt = most_expensive_dt.replace(tzinfo=_ZoneInfo('Europe/Helsinki'))
                        
                        # Check if dates match current date
                        cheapest_date = cheapest_dt.date()
                        most_expensive_date = most_expensive_dt.date()
                        
                        # Format date indicators
                        cheapest_date_indicator = ""
                        most_expensive_date_indicator = ""
                        
                        if cheapest_date > current_date:
                            if cheapest_date == current_date + datetime.timedelta(days=1):
                                cheapest_date_indicator = " (huomenna)"
                            else:
                                cheapest_date_indicator = f" ({cheapest_date.strftime('%d.%m.')})"
                                
                        if most_expensive_date > current_date:
                            if most_expensive_date == current_date + datetime.timedelta(days=1):
                                most_expensive_date_indicator = " (huomenna)"
                            else:
                                most_expensive_date_indicator = f" ({most_expensive_date.strftime('%d.%m.')})"
                        
                        print(f"Halvin sähkö: {cheapest_hour['hour']:02d}:00 ({cheapest_hour['price']:.2f} c/kWh){cheapest_date_indicator}. "
                              f"Kallein sähkö: {most_expensive_hour['hour']:02d}:00 ({most_expensive_hour['price']:.2f} c/kWh){most_expensive_date_indicator}")
                    except:
                        # Fallback to simple display if datetime parsing fails
                        print(f"Halvin sähkö: {cheapest_hour['hour']:02d}:00 ({cheapest_hour['price']:.2f} c/kWh). "
                              f"Kallein sähkö: {most_expensive_hour['hour']:02d}:00 ({most_expensive_hour['price']:.2f} c/kWh)")
                else:
                    # Fallback if zoneinfo is not available
                    print(f"Halvin sähkö: {cheapest_hour['hour']:02d}:00 ({cheapest_hour['price']:.2f} c/kWh). "
                          f"Kallein sähkö: {most_expensive_hour['hour']:02d}:00 ({most_expensive_hour['price']:.2f} c/kWh)")

        if aurora_forecast:
            kp = aurora_forecast.get('kp', 0)
            if kp >= 5:
                print(date_strings['aurora_visible_south'].format(kp=kp))
            elif kp >= 3:
                print(date_strings['aurora_visible_north'].format(kp=kp))
            else:
                print(date_strings['aurora_unlikely'].format(kp=kp))

    # Eclipses
    if next_eclipse:
        eclipse_types = date_strings.get('eclipse_types', {})
        if next_eclipse.get('solar'):
            solar_eclipse = next_eclipse['solar']
            eclipse_date = solar_eclipse['date'].strftime('%d.%m.%Y')
            eclipse_type = eclipse_types.get(solar_eclipse['type'], solar_eclipse['type'])
            print(date_strings['next_eclipse_solar'].format(date=eclipse_date, type=eclipse_type))
        if next_eclipse.get('lunar'):
            lunar_eclipse = next_eclipse['lunar']
            eclipse_date = lunar_eclipse['date'].strftime('%d.%m.%Y')
            eclipse_type = eclipse_types.get(lunar_eclipse['type'], lunar_eclipse['type'])
            print(date_strings['next_eclipse_lunar'].format(date=eclipse_date, type=eclipse_type))

    # Transport disruptions
    if ti.country_code == 'FI' and transport_disruptions:
        if transport_disruptions.get('error'):
            error = transport_disruptions['error']
            if ti.language == 'fi':
                print(f"\n\u26A0\uFE0F Liikennetiedot: {error}")
            else:
                print(f"\n\u26A0\uFE0F Transport info: {error}")
        else:
            alerts = transport_disruptions.get('alerts', [])
            if alerts:
                print(f"\n{date_strings['transport_disruptions']}")
                for alert in alerts:
                    header = alert.get('header', '')
                    if header:
                        print(f"  - {header}")

    # Morning forecast
    if morning_forecast:
        morning_desc = get_weather_description(morning_forecast.get('weather_code'), ti.language)
        temp_min = morning_forecast['temp_min'] or 0
        temp_max = morning_forecast['temp_max'] or 0
        date_str = morning_forecast['date'].strftime('%d.%m')
        if temp_min == temp_max:
            if ti.language == 'fi':
                print(f"\nHuomisaamu ({date_str}): {temp_min:.0f}°c, {morning_desc}")
            else:
                print(f"\nTomorrow morning ({date_str}): {temp_min:.0f}°c, {morning_desc}")
        else:
            print(f"\n{date_strings['morning_forecast'].format(date=date_str, temp_min=temp_min, temp_max=temp_max, desc=morning_desc)}")

        # Tomorrow's sunrise
        tomorrow = ti.now + datetime.timedelta(days=1)
        location = LocationInfo(name="Custom", region="Custom", timezone=ti.timezone, latitude=ti.latitude, longitude=ti.longitude)
        if ZONEINFO_AVAILABLE:
            local_tz = ZoneInfo(ti.timezone)
            tomorrow_sun = sun(location.observer, date=tomorrow.date(), tzinfo=local_tz)
        else:
            tomorrow_sun = sun(location.observer, date=tomorrow.date())
        tomorrow_sunrise = tomorrow_sun['sunrise'].strftime("%H.%M")
        print(date_strings['sunrise'].format(time=tomorrow_sunrise).capitalize())

        if morning_forecast.get('wind_max') and morning_forecast.get('gust_max'):
            print(date_strings['morning_wind'].format(wind=morning_forecast['wind_max'], gust=morning_forecast['gust_max']))
        if morning_forecast.get('precip_prob_max') and morning_forecast['precip_prob_max'] > 0:
            print(date_strings['morning_precip'].format(prob=morning_forecast['precip_prob_max']))
        if morning_forecast.get('visibility_min') and morning_forecast['visibility_min'] < 10000:
            print(date_strings['morning_visibility'].format(vis=morning_forecast['visibility_min'] / 1000))

    # Weather warnings
    weather_warnings = get_weather_warnings(weather_data, uv_index, air_quality_data, translations)

    river_discharge = flood_data.get('river_discharge')
    if river_discharge is not None:
        mean = flood_data.get('river_discharge_mean', 0) or 0
        if mean > 0 and river_discharge > mean * 2:
            weather_warnings.append(date_strings['flood_warning'].format(discharge=river_discharge))

    wave_height_warning = marine_data.get('wave_height')
    if wave_height_warning is not None and wave_height_warning >= 1.5:
        weather_warnings.append(date_strings['wave_warning'].format(height=wave_height_warning))

    if road_weather:
        condition = str(road_weather.get('condition', 'NORMAL'))
        reason = road_weather.get('reason')
        if condition == 'VERY_POOR':
            reason_key = str(reason) if reason else ''
            reason_text = date_strings.get('road_reasons', {}).get(reason_key, reason_key.lower()) if reason_key else ''
            weather_warnings.append(date_strings['road_warning_very_poor'].format(reason=reason_text))
        elif condition == 'POOR':
            weather_warnings.append(date_strings['road_warning_poor'])

    if electricity_price:
        # Use 15-minute price for warnings if available, otherwise fall back to hourly price
        price = electricity_price.get('price_15min') or electricity_price.get('price_hour', 0)
        if price >= 18:
            weather_warnings.append(date_strings['electricity_warning_very_high'].format(price=price))
        elif price >= 12:
            weather_warnings.append(date_strings['electricity_warning_high'].format(price=price))

    if weather_warnings:
        print(f"\n{date_strings['warnings']}")
        for warning in weather_warnings:
            print(f"  \u26A0\uFE0F  {warning}")
