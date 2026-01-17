"""Display and output formatting for AikaSnapshot."""

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

from .localization import get_finnish_translations, get_translations
from ..calculations.weather_utils import degrees_to_compass, get_weather_description
from ..models import AikaSnapshot


def display_info(snapshot: AikaSnapshot):
    """Display all information in the selected language.

    Args:
        snapshot: AikaSnapshot instance with all necessary data
    """
    # Shortcut variables
    loc = snapshot.location
    raw = snapshot.raw
    comp = snapshot.computed
    now = snapshot.timestamp
    language = snapshot.language
    country_code = snapshot.country_code

    translations = get_translations(language)
    date_strings = translations['date']
    finnish_translations = get_finnish_translations()

    # Time
    clock = now.strftime("%H.%M")

    # Check if location timezone differs from system timezone
    location_time_str = None
    if ZONEINFO_AVAILABLE:
        try:
            # Note: snapshot.timestamp is already localized to target timezone
            # But the logic in original display.py compared it to system local time

            # Helper to get system local time
            system_now = datetime.datetime.now().astimezone()

            # If snapshot timestamp (target location) differs from system now
            if now.hour != system_now.hour or now.minute != system_now.minute:
                location_time_str = now.strftime("%H.%M")
        except:
            location_time_str = None

    # Display location at the top
    if loc.city_name and loc.country_name:
        print(f"\U0001F3E0 {loc.city_name}, {loc.country_name}\n")
    elif loc.city_name:
        print(f"\U0001F3E0 {loc.city_name}\n")

    # Display introductory sentences
    date_info = comp.date_info
    time_expression = comp.time_expression
    time_of_day = comp.time_of_day

    if language == 'fi':
        day_name_local = finnish_translations['days'].get(date_info.day_name, date_info.day_name)
        month_name_genitive = finnish_translations['months_genitive'].get(date_info.month_name, date_info.month_name)
        print(f"Kello on {time_expression} ({clock}), joten on {time_of_day}.")
        print(f"On {day_name_local}, {date_info.day_num}. {month_name_genitive}, {date_info.year}.")
        print(f"Viikon numero on {date_info.week_num}/{date_info.weeks_in_year}, ja päivän numero on {date_info.day_of_year}/{date_info.days_in_year}.")
    else:
        day_name_local = date_info.day_name
        month_name_local = date_info.month_name
        print(f"The time is {time_expression} ({clock}), so it's {time_of_day}.")
        print(f"It's {day_name_local}, {date_info.day_num} {month_name_local} {date_info.year}.")
        print(f"Week number is {date_info.week_num}/{date_info.weeks_in_year}, and day number is {date_info.day_of_year}/{date_info.days_in_year}.")

    if location_time_str:
        print(date_strings['local_time'].format(time=location_time_str))

    print(date_strings['year_complete'].format(pct=date_info.pct_complete))

    # Solar times
    solar_info = comp.solar_info
    solar_line = date_strings['dawn'].format(time=solar_info.dawn) + ", "
    solar_line += date_strings['sunrise'].format(time=solar_info.sunrise) + ", "
    solar_line += date_strings['noon'].format(time=solar_info.noon) + ", "
    solar_line += date_strings['sunset'].format(time=solar_info.sunset) + ", "
    solar_line += date_strings['dusk'].format(time=solar_info.dusk)
    print(solar_line)

    # Sun position + Daylight length (combined)
    sun_visibility = date_strings['sun_visible'] if solar_info.elevation > 0 else date_strings['sun_below']
    sun_compass_key = degrees_to_compass(solar_info.azimuth)
    sun_compass_dir = date_strings['compass_directions'].get(sun_compass_key, sun_compass_key)
    sun_line = date_strings['sun_position'].format(elevation=solar_info.elevation, azimuth=sun_compass_dir) + " " + sun_visibility

    daylight_info = comp.daylight_info
    if daylight_info:
        change = daylight_info.change_from_yesterday
        if change == 0:
            sun_line += f". {date_strings['daylight_same'].format(hours=daylight_info.daylight_hours)}"
        else:
            change_str = f"+{change}" if change > 0 else str(change)
            sun_line += f". {date_strings['daylight_length'].format(hours=daylight_info.daylight_hours, change=change_str)}"
    print(sun_line)

    # Time to sunrise/sunset
    sun_countdown = comp.sun_countdown
    if sun_countdown and sun_countdown.next_event_in_minutes is not None:
        if sun_countdown.next_event_in_minutes <= 120:
            if sun_countdown.next_event == 'sunrise':
                print(date_strings['time_to_sunrise'].format(minutes=sun_countdown.next_event_in_minutes))
            else:
                print(date_strings['time_to_sunset'].format(minutes=sun_countdown.next_event_in_minutes))

    # Golden hour / Blue hour
    golden_blue = comp.golden_blue
    if golden_blue:
        # Show if currently in golden/blue hour
        if golden_blue.is_golden_hour_now:
            print(date_strings['golden_hour_now'])
        elif golden_blue.is_blue_hour_now:
            print(date_strings['blue_hour_now'])
        else:
            # Show upcoming evening golden hour if it's afternoon or later
            current_hour = now.hour
            if current_hour >= 12 and golden_blue.evening_golden_hour:
                gh = golden_blue.evening_golden_hour
                print(date_strings['golden_hour_evening'].format(start=gh['start'], end=gh['end']))

    # Solar radiation
    solar_radiation = raw.solar_radiation
    ghi = solar_radiation.ghi
    dni = solar_radiation.dni
    solar_parts = []
    if solar_radiation.cloud_cover is not None:
        solar_parts.append(date_strings['cloud_cover'].format(cover=solar_radiation.cloud_cover))
    if ghi is not None and dni is not None and (ghi > 0 or dni > 0):
        solar_parts.append(date_strings['solar_radiation'].format(ghi=ghi, dni=dni))
    if solar_parts:
        print(". ".join(solar_parts))
    if ghi is not None and dni is not None and (ghi > 0 or dni > 0) and solar_radiation.gti is not None:
        print(date_strings['solar_for_panels'].format(gti=solar_radiation.gti, dni=dni))

    # Lunar info
    lunar_info = comp.lunar_info
    moon_visibility = date_strings['moon_visible'] if lunar_info.altitude > 0 else date_strings['moon_below']
    moon_compass_key = degrees_to_compass(lunar_info.azimuth)
    moon_compass_dir = date_strings['compass_directions'].get(moon_compass_key, moon_compass_key)
    moon_line = date_strings['moon_phase'].format(phase=lunar_info.phase, growth=lunar_info.growth)
    moon_line += ". " + date_strings['moon_position'].format(altitude=lunar_info.altitude, azimuth=moon_compass_dir) + " " + moon_visibility

    special_phase_key = lunar_info.special_phase
    if special_phase_key:
        special_map = date_strings.get('moon_special_phases', {})
        special_text = special_map.get(special_phase_key)
        if special_text:
            moon_line += f". {special_text}"
    print(moon_line)

    moon_times = []
    if lunar_info.rise:
        moon_times.append(date_strings['moon_rise'].format(time=lunar_info.rise))
    if lunar_info.transit:
        moon_times.append(date_strings['moon_transit'].format(time=lunar_info.transit))
    if lunar_info.set:
        moon_times.append(date_strings['moon_set'].format(time=lunar_info.set))
    if moon_times:
        print(", ".join(moon_times))

    # Future moon phases
    future_phases = lunar_info.future_phases
    phase_labels = date_strings.get('moon_phase_names', {})
    next_phase_template = date_strings.get('moon_next_phase')
    if next_phase_template and future_phases:
        phase_parts = []
        for phase_entry in future_phases:
            # phase_entry is assumed to be dict as stored in model, but if it's already processed...
            # The service returns model with list[dict], so it's a dict.
            # But wait, original code used datetime object in phase_entry['datetime']
            # Providers/services need to return datetimes or strings?
            # Astronomy provider returns datetimes in the dict.
            # Model definition says `list[dict]`, so it preserves the types.
            phase_dt = phase_entry.get('datetime')
            if not phase_dt:
                continue
            date_str = phase_dt.strftime("%d.%m.")
            time_str = phase_dt.strftime("%H.%M")
            label = phase_labels.get(phase_entry.get('type'), phase_entry.get('type'))
            phase_parts.append(f"{label}: {date_str} klo {time_str}")
        if phase_parts:
            print(", ".join(phase_parts).capitalize())

    # Weather
    weather_data = raw.weather
    if weather_data.temperature is not None:
        weather_desc = get_weather_description(weather_data.weather_code, language)
        weather_line = date_strings['weather'].format(temp=weather_data.temperature, desc=weather_desc)
        if weather_data.apparent_temp is not None:
            weather_line += ". " + date_strings['feels_like'].format(temp=weather_data.apparent_temp)
        print(weather_line)

        if weather_data.humidity is not None and weather_data.pressure is not None:
            print(date_strings['humidity'].format(humidity=weather_data.humidity, pressure=weather_data.pressure))

        if weather_data.wind_speed is not None and weather_data.wind_direction is not None:
            compass_key = degrees_to_compass(weather_data.wind_direction)
            compass_dir = date_strings['compass_directions'].get(compass_key, compass_key)
            if weather_data.gust_speed is not None:
                print(date_strings['wind_full'].format(speed=weather_data.wind_speed, dir=compass_dir, gust=weather_data.gust_speed))
            else:
                print(date_strings['wind_no_gust'].format(speed=weather_data.wind_speed, dir=compass_dir))
        elif weather_data.wind_speed is not None:
            print(date_strings['wind'].format(speed=weather_data.wind_speed))

        if weather_data.visibility is not None and weather_data.visibility > 0:
            print(date_strings['visibility'].format(vis=weather_data.visibility / 1000))

        # Precipitation info
        precip_parts = []
        if weather_data.precip_intensity is not None and weather_data.precip_intensity > 0:
            precip_parts.append(date_strings['precip_intensity'].format(intensity=weather_data.precip_intensity))
        if weather_data.precipitation_probability is not None:
            precip_parts.append(date_strings['precipitation'].format(prob=weather_data.precipitation_probability))
        if weather_data.snow_depth is not None and weather_data.snow_depth > 0:
            precip_parts.append(date_strings['snow_depth'].format(depth=weather_data.snow_depth))
        if precip_parts:
            print(". ".join(precip_parts))
    else:
        if language == 'fi':
            print("Sää: ei saatavilla")
        else:
            print("Weather: not available")

    # Nowcast
    nowcast = raw.nowcast
    if nowcast and (nowcast.is_raining_now or nowcast.rain_starts_in_min is not None):
        precip_types = date_strings.get('precip_types', {})
        if nowcast.is_raining_now:
            precip_type = precip_types.get(nowcast.precipitation_type, 'rain')
            print(date_strings['currently_raining'].format(type=precip_type))
            if nowcast.rain_ends_in_min is not None:
                print(date_strings['rain_ends_in'].format(minutes=nowcast.rain_ends_in_min))
        else:
            if nowcast.rain_starts_in_min is not None:
                print(date_strings['rain_starts_in'].format(minutes=nowcast.rain_starts_in_min))
            else:
                print(date_strings['no_rain_2h'])

    # Lightning Info
    if nowcast and nowcast.is_active:
        dist = nowcast.nearest_km
        strikes = nowcast.strikes_1h
        if language == 'fi':
            print(f"\u26A1 Ukkosta havaittu! {strikes} iskua 1h aikana, lähin {dist} km päässä.")
        else:
            print(f"\u26A1 Thunderstorm detected! {strikes} strikes in 1h, nearest {dist} km away.")

    # Marine data
    marine_data = raw.marine
    wave_height = marine_data.wave_height
    marine_parts = []

    if wave_height is not None and wave_height > 0.1:
        wave_compass_key = degrees_to_compass(marine_data.wave_direction)
        wave_compass_dir = date_strings['compass_directions'].get(wave_compass_key, wave_compass_key) if wave_compass_key else '?'
        marine_parts.append(date_strings['wave_info'].format(height=wave_height, period=marine_data.wave_period or 0, dir=wave_compass_dir))

    if marine_data.sea_temperature is not None:
        if language == 'fi':
            marine_parts.append(f"Meriveden lämpötila: {marine_data.sea_temperature:.1f}°C")
        else:
            marine_parts.append(f"Sea water temperature: {marine_data.sea_temperature:.1f}°C")

    if marine_data.sea_ice_cover is not None and marine_data.sea_ice_cover > 0:
        if language == 'fi':
            marine_parts.append(f"Jään peittävyys: {marine_data.sea_ice_cover:.0f}%")
        else:
            marine_parts.append(f"Sea ice cover: {marine_data.sea_ice_cover:.0f}%")

    if marine_parts:
        print(". ".join(marine_parts))

    # Air quality + UV index
    air_quality_data = raw.air_quality
    uv_index = raw.uv_index
    env_parts = []
    if air_quality_data.aqi is not None:
        aqi_text = translations['air_quality_levels'].get(air_quality_data.aqi, "not available")
        env_parts.append(date_strings['air_quality'].format(quality=aqi_text, aqi=air_quality_data.aqi))
    if uv_index is not None:
        if uv_index >= 8:
            env_parts.append(date_strings['uv_very_high'].format(index=uv_index))
        elif uv_index >= 6:
            env_parts.append(date_strings['uv_high'].format(index=uv_index))
        elif uv_index >= 3:
            env_parts.append(date_strings['uv_moderate'].format(index=uv_index))
        else:
            env_parts.append(date_strings['uv_low'].format(index=uv_index))
    if env_parts:
        print(". ".join(env_parts))

    # 12-hour forecast summary
    forecast_12h = comp.forecast_12h
    if forecast_12h:
        forecast_parts = []
        rain_windows = forecast_12h.rain_windows
        if rain_windows:
            rain_strs = [date_strings['forecast_12h_rain'].format(start=w['start'], end=w['end']) for w in rain_windows[:2]]
            forecast_parts.extend(rain_strs)
        temp_range = forecast_12h.temp_range
        if temp_range:
            if temp_range['trend'] == 'rising':
                forecast_parts.append(date_strings['temp_trend_rising'].format(min=temp_range['min'], max=temp_range['max']))
            elif temp_range['trend'] == 'falling':
                forecast_parts.append(date_strings['temp_trend_falling'].format(min=temp_range['min'], max=temp_range['max']))
        strongest_wind = forecast_12h.strongest_wind
        if strongest_wind and strongest_wind.get('speed') and strongest_wind['speed'] > 10:
            forecast_parts.append(date_strings['forecast_wind_peak'].format(time=strongest_wind['time'], speed=strongest_wind['speed']))
        if forecast_parts:
            print(". ".join(forecast_parts))

    # 7-day forecast
    forecast_7day = comp.forecast_7day
    if forecast_7day:
        outlook_parts = []
        best = forecast_7day.best_outdoor_window
        if best:
            weekday = best.get('weekday_fi') if language == 'fi' else best.get('weekday_en')
            temp_info = f", {best['temp_max']:.0f}°C" if best.get('temp_max') else ""
            reason = best.get('reason', '')
            outlook_parts.append(date_strings['best_outdoor_day'].format(day=weekday, reason=reason + temp_info))
        snow = forecast_7day.snow_accumulation_cm
        if snow and snow > 0:
            outlook_parts.append(date_strings['snow_accumulation'].format(cm=snow))
        if outlook_parts:
            print(". ".join(outlook_parts))

    # Season + Name day + Next holiday
    season = comp.season
    next_holiday = comp.next_holiday
    calendar_parts = [date_strings['season'].format(season=season)]
    if country_code == 'FI':
        name_day = comp.name_day
        if name_day:
            calendar_parts.append(date_strings['name_day'].format(names=name_day))
    calendar_parts.append(date_strings['next_holiday'].format(holiday=next_holiday))
    print(". ".join(calendar_parts))

    # Finland-specific features
    road_weather = raw.road_weather
    electricity_price = raw.electricity
    detailed_electricity = raw.detailed_electricity
    aurora_forecast = raw.aurora

    if country_code == 'FI':
        if road_weather:
            condition_value = str(road_weather.condition)
            reason_value = road_weather.reason
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
            price_15min = electricity_price.price_15min
            price_hour = electricity_price.price_hour

            # Display both prices if available
            if price_15min is not None and price_hour is not None:
                if price_15min < 5:
                    print(date_strings['electricity_price_low_dual'].format(price=price_15min, hour_price=price_hour))
                elif price_15min > 15:
                    print(date_strings['electricity_price_high_dual'].format(price=price_15min, hour_price=price_hour))
                else:
                    print(date_strings['electricity_price_dual'].format(price=price_15min, hour_price=price_hour))
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

            if electricity_price.co2:
                level_map = {'low': 'matala' if language == 'fi' else 'low', 'moderate': 'kohtalainen' if language == 'fi' else 'moderate',
                             'high': 'korkea' if language == 'fi' else 'high'}
                level_str = level_map.get(electricity_price.co2.level, electricity_price.co2.level)
                if language == 'fi':
                    print(f"  CO₂: {electricity_price.co2.intensity:.0f} {electricity_price.co2.unit} ({level_str})")
                else:
                    print(f"  CO₂: {electricity_price.co2.intensity:.0f} {electricity_price.co2.unit} ({level_str})")

        # Detailed electricity
        if detailed_electricity:
            cheapest_hour = detailed_electricity.cheapest_hour
            most_expensive_hour = detailed_electricity.most_expensive_hour

            if cheapest_hour and most_expensive_hour:
                if ZONEINFO_AVAILABLE and _ZoneInfo:
                    try:
                        current_time = datetime.datetime.now(_ZoneInfo('Europe/Helsinki'))
                        current_date = current_time.date()

                        cheapest_dt = datetime.datetime.fromisoformat(cheapest_hour['datetime'])
                        most_expensive_dt = datetime.datetime.fromisoformat(most_expensive_hour['datetime'])

                        # Convert to Helsinki timezone if needed
                        if cheapest_dt.tzinfo is None:
                            cheapest_dt = cheapest_dt.replace(tzinfo=_ZoneInfo('Europe/Helsinki'))
                        if most_expensive_dt.tzinfo is None:
                            most_expensive_dt = most_expensive_dt.replace(tzinfo=_ZoneInfo('Europe/Helsinki'))

                        cheapest_date = cheapest_dt.date()
                        most_expensive_date = most_expensive_dt.date()

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

                        cheapest_minute = cheapest_dt.minute
                        most_expensive_minute = most_expensive_dt.minute

                        print(f"Halvin sähkö: {cheapest_hour['hour']:02d}:{cheapest_minute:02d} ({cheapest_hour['price']:.2f} c/kWh){cheapest_date_indicator}. "
                              f"Kallein sähkö: {most_expensive_hour['hour']:02d}:{most_expensive_minute:02d} ({most_expensive_hour['price']:.2f} c/kWh){most_expensive_date_indicator}")
                    except:
                        print(f"Halvin sähkö: {cheapest_hour['hour']:02d}:00 ({cheapest_hour['price']:.2f} c/kWh). "
                              f"Kallein sähkö: {most_expensive_hour['hour']:02d}:00 ({most_expensive_hour['price']:.2f} c/kWh)")
                else:
                    print(f"Halvin sähkö: {cheapest_hour['hour']:02d}:00 ({cheapest_hour['price']:.2f} c/kWh). "
                          f"Kallein sähkö: {most_expensive_hour['hour']:02d}:00 ({most_expensive_hour['price']:.2f} c/kWh)")

        if aurora_forecast:
            kp = aurora_forecast.kp
            if kp >= 5:
                print(date_strings['aurora_visible_south'].format(kp=kp))
            elif kp >= 3:
                print(date_strings['aurora_visible_north'].format(kp=kp))
            else:
                print(date_strings['aurora_unlikely'].format(kp=kp))

    # Eclipses
    next_eclipse = comp.eclipse_info
    if next_eclipse and (next_eclipse.solar or next_eclipse.lunar):
        eclipse_parts = []
        eclipse_types = date_strings.get('eclipse_types', {})
        if next_eclipse.solar:
            solar_eclipse = next_eclipse.solar
            eclipse_date = solar_eclipse['date'].strftime('%d.%m.%Y')
            eclipse_type = eclipse_types.get(solar_eclipse['type'], solar_eclipse['type'])
            eclipse_parts.append(date_strings['next_eclipse_solar'].format(date=eclipse_date, type=eclipse_type))
        if next_eclipse.lunar:
            lunar_eclipse = next_eclipse.lunar
            eclipse_date = lunar_eclipse['date'].strftime('%d.%m.%Y')
            eclipse_type = eclipse_types.get(lunar_eclipse['type'], lunar_eclipse['type'])
            eclipse_parts.append(date_strings['next_eclipse_lunar'].format(date=eclipse_date, type=eclipse_type))
        if eclipse_parts:
            print(". ".join(eclipse_parts))

    # Transport disruptions
    transport_disruptions = raw.transport
    if country_code == 'FI' and transport_disruptions:
        if transport_disruptions.error:
            error = transport_disruptions.error
            if language == 'fi':
                print(f"\n\u26A0\uFE0F Liikennetiedot: {error}")
            else:
                print(f"\n\u26A0\uFE0F Transport info: {error}")
        else:
            alerts = transport_disruptions.alerts
            if alerts:
                print(f"\n{date_strings['transport_disruptions']}")
                for alert in alerts:
                    header = alert.get('header', '')
                    if header:
                        print(f"  - {header}")

            # Analyze nearby transit to guess traffic conditions
            # Only show if user is in Föli area (calculated in snapshot)
            if snapshot.location.in_foli_area:
                if hasattr(transport_disruptions, 'stops') and transport_disruptions.stops:
                    total_departures = 0
                    late_departures = 0
                    very_late_departures = 0  # > 5 min

                    late_details = []

                    for stop in transport_disruptions.stops:
                        for dep in stop.departures:
                            total_departures += 1
                            status = dep.get("status")
                            if status == "LATE":
                                late_departures += 1
                                diff = dep.get("diff_min", 0)
                                if diff > 5:
                                    very_late_departures += 1

                                late_details.append(f"{stop.name}: Line {dep['line']} (+{diff:.0f} min)")

                    if total_departures > 0:
                        late_ratio = late_departures / total_departures

                        # Determine traffic status based on bus lateness
                        traffic_status = "Normaali" if language == 'fi' else "Normal"
                        if late_ratio > 0.4 or very_late_departures > 2:
                            traffic_status = "Ruuhkautunut / Ongelmia" if language == 'fi' else "Congested / Problems"
                        elif late_ratio > 0.2:
                            traffic_status = "Hieman viivettä" if language == 'fi' else "Slight delays"

                        label = "Lähiliikenne (Föli)" if language == 'fi' else "Local Transit"
                        print(f"\n{label}: {traffic_status}")

                        if language == 'fi':
                            print(f"  {late_departures}/{total_departures} bussia myöhässä alueella.")
                        else:
                            print(f"  {late_departures}/{total_departures} buses late in the area.")

                        if late_details:
                            header = "Huomattavat myöhästymiset:" if language == 'fi' else "Significant delays:"
                            print(f"  {header}")
                            for detail in late_details[:3]:  # Show top 3
                                print(f"    - {detail}")

    # Morning forecast
    morning_forecast = comp.morning_forecast
    if morning_forecast and morning_forecast.forecast_date:
        morning_desc = get_weather_description(morning_forecast.weather_code, language)
        temp_min = morning_forecast.temp_min or 0
        temp_max = morning_forecast.temp_max or 0
        date_str = morning_forecast.forecast_date.strftime('%d.%m')

        # Tomorrow's sunrise (recalculated because not in model, but we have lat/lon)
        tomorrow = now + datetime.timedelta(days=1)
        location = LocationInfo(name="Custom", region="Custom", timezone=loc.timezone, latitude=loc.latitude, longitude=loc.longitude)
        if ZONEINFO_AVAILABLE:
            local_tz = ZoneInfo(loc.timezone)
            tomorrow_sun = sun(location.observer, date=tomorrow.date(), tzinfo=local_tz)
        else:
            tomorrow_sun = sun(location.observer, date=tomorrow.date())
        tomorrow_sunrise = tomorrow_sun['sunrise'].strftime("%H.%M")

        if temp_min == temp_max:
            if language == 'fi':
                morning_line = f"Huomisaamu ({date_str}): {temp_min:.0f}°c, {morning_desc}, aurinko nousee klo {tomorrow_sunrise}"
            else:
                morning_line = f"Tomorrow morning ({date_str}): {temp_min:.0f}°c, {morning_desc}, sunrise at {tomorrow_sunrise}"
        else:
            morning_line = date_strings['morning_forecast'].format(date=date_str, temp_min=temp_min, temp_max=temp_max, desc=morning_desc)
            morning_line += f", {date_strings['sunrise'].format(time=tomorrow_sunrise)}"
        print(f"\n{morning_line}")

        morning_details = []
        if morning_forecast.wind_max and morning_forecast.gust_max:
            morning_details.append(date_strings['morning_wind'].format(wind=morning_forecast.wind_max, gust=morning_forecast.gust_max))
        if morning_forecast.precip_prob_max and morning_forecast.precip_prob_max > 0:
            morning_details.append(date_strings['morning_precip'].format(prob=morning_forecast.precip_prob_max))
        if morning_forecast.visibility_min and morning_forecast.visibility_min < 10000:
            morning_details.append(date_strings['morning_visibility'].format(vis=morning_forecast.visibility_min / 1000))
        if morning_details:
            print(". ".join(morning_details))

    # Warnings (from snapshot + additional ones calculated here if needed)
    weather_warnings = list(snapshot.warnings)

    if weather_data and weather_data.visibility is not None and weather_data.visibility < 1000:
        if language == 'fi':
            weather_warnings.append("Huono näkyvyys (sumua)")
        else:
            weather_warnings.append("Poor visibility (fog)")

    flood_data = raw.flood
    river_discharge = flood_data.river_discharge
    if river_discharge is not None:
        mean = flood_data.river_discharge_mean or 0
        if mean > 0 and river_discharge > mean * 2:
            weather_warnings.append(date_strings['flood_warning'].format(discharge=river_discharge))

    if wave_height is not None and wave_height >= 1.5:
        weather_warnings.append(date_strings['wave_warning'].format(height=wave_height))

    # Road and electricity warnings - check if already in list? 
    # The previous calculation in display.py added them. 
    # Snapshot warnings only include weather.py warnings.
    # So we add them here.

    if road_weather:
        condition = str(road_weather.condition)
        reason = road_weather.reason
        if condition == 'VERY_POOR':
            reason_key = str(reason) if reason else ''
            reason_text = date_strings.get('road_reasons', {}).get(reason_key, reason_key.lower()) if reason_key else ''
            weather_warnings.append(date_strings['road_warning_very_poor'].format(reason=reason_text))
        elif condition == 'POOR':
            weather_warnings.append(date_strings['road_warning_poor'])

    if electricity_price:
        price = electricity_price.price_15min or electricity_price.price_hour or 0
        if price >= 18:
            weather_warnings.append(date_strings['electricity_warning_very_high'].format(price=price))
        elif price >= 12:
            weather_warnings.append(date_strings['electricity_warning_high'].format(price=price))

    if weather_warnings:
        print(f"\n{date_strings['warnings']}")
        for warning in weather_warnings:
            # Avoid duplicates if any
            print(f"  \u26A0\uFE0F  {warning}")
