"""Calendar, date, season, and holiday calculations."""
import datetime

try:
    import holidays as holidays_lib

    HOLIDAYS_AVAILABLE = True
except ImportError:
    HOLIDAYS_AVAILABLE = False

from .localization import HOLIDAY_TRANSLATIONS


def get_date_info(now):
    """Get comprehensive date information."""
    day_name = now.strftime("%A")
    day_num = now.day
    month_name = now.strftime("%B")
    year = now.year

    # Week number (ISO)
    week_num = now.isocalendar()[1]

    # Day of the year (1-366)
    day_of_year = now.timetuple().tm_yday

    # Ordinal suffix
    if 11 <= day_num % 100 <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(day_num % 10, "th")

    # Number of days in year (leap year check)
    if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0):
        days_in_year = 366
    else:
        days_in_year = 365

    # Weeks in a year
    last_week = datetime.date(year, 12, 28).isocalendar()[1]
    weeks_in_year = last_week

    # Percentage complete (including time of day)
    day_fraction = (now.hour + now.minute / 60.0) / 24.0
    fractional_day_of_year = day_of_year - 1 + day_fraction
    pct_complete = (fractional_day_of_year / days_in_year) * 100

    return {'day_name': day_name, 'day_num': day_num, 'month_name': month_name, 'year': year, 'week_num': week_num, 'day_of_year': day_of_year,
            'days_in_year': days_in_year, 'weeks_in_year': weeks_in_year, 'pct_complete': pct_complete}


def get_season(now, latitude, translations):
    """Determine the season based on hemisphere."""
    month = now.month
    season_translations = translations['seasons']

    is_northern_hemisphere = latitude >= 0

    if is_northern_hemisphere:
        if month in [12, 1, 2]:
            return season_translations['winter']
        elif month in [3, 4, 5]:
            return season_translations['spring']
        elif month in [6, 7, 8]:
            return season_translations['summer']
        else:
            return season_translations['autumn']
    else:
        if month in [12, 1, 2]:
            return season_translations['summer']
        elif month in [3, 4, 5]:
            return season_translations['autumn']
        elif month in [6, 7, 8]:
            return season_translations['winter']
        else:
            return season_translations['spring']


def get_next_holiday(now, country_code, language):
    """Get the name and date of the next public holiday."""
    try:
        # Determines next holiday and translates name based on language
        if HOLIDAYS_AVAILABLE:
            years = (now.year, now.year + 1)

            try:
                country_holidays_obj = holidays_lib.country_holidays(country_code, years=years)
            except NotImplementedError:
                country_holidays_obj = holidays_lib.country_holidays('FI', years=years)

            current_date = now.date()
            for holiday_date in sorted(country_holidays_obj.keys()):
                if holiday_date >= current_date:
                    days_until = (holiday_date - current_date).days
                    holiday_name = country_holidays_obj[holiday_date]

                    if language == 'fi':
                        finnish_holidays = ['Uudenvuodenpäivä', 'Loppiainen', 'Pitkäperjantai', 'Pääsiäispäivä', 'Toinen pääsiäispäivä', 'Vappu', 'Helatorstai',
                                            'Helluntaipäivä', 'Juhannusaatto', 'Juhannuspäivä', 'Pyhäinpäivä', 'Itsenäisyyspäivä', 'Jouluaatto', 'Joulupäivä',
                                            'Tapaninpäivä']
                        if holiday_name in finnish_holidays:
                            translated_name = holiday_name
                        else:
                            translated_name = HOLIDAY_TRANSLATIONS.get(holiday_name, holiday_name)
                        return f"{translated_name} ({holiday_date.strftime('%d.%m.')}) on {days_until} päivän päästä"
                    else:
                        finnish_holidays = {'Uudenvuodenpäivä': 'New Year\'s Day', 'Loppiainen': 'Epiphany', 'Pitkäperjantai': 'Good Friday',
                                            'Pääsiäispäivä': 'Easter Sunday', 'Toinen pääsiäispäivä': 'Easter Monday', 'Vappu': 'May Day',
                                            'Helatorstai': 'Ascension Day', 'Helluntaipäivä': 'Whit Sunday', 'Juhannusaatto': 'Midsummer Eve',
                                            'Juhannuspäivä': 'Midsummer Day', 'Pyhäinpäivä': 'All Saints\' Day', 'Itsenäisyyspäivä': 'Independence Day',
                                            'Jouluaatto': 'Christmas Eve', 'Joulupäivä': 'Christmas Day', 'Tapaninpäivä': 'Boxing Day'}
                        translated_name = finnish_holidays.get(holiday_name, holiday_name)
                        if translated_name == holiday_name:
                            translated_name = HOLIDAY_TRANSLATIONS.get(holiday_name, holiday_name)
                        return f"{translated_name} ({holiday_date.strftime('%d.%m.')}) in {days_until} days"

    except Exception:
        pass

    # Fallback to hardcoded holidays
    year = now.year
    holidays_list = [(1, 1, "Uudenvuodenpäivä"), (1, 6, "Loppiainen"), (5, 1, "Vappu"), (12, 6, "Itsenäisyyspäivä"), (12, 24, "Jouluaatto"),
                     (12, 25, "Joulupäivä"), (12, 26, "Tapaninpäivä")]

    if year == 2026:
        holidays_list.extend(
            [(3, 29, "Pitkäperjantai"), (3, 31, "Pääsiäispäivä"), (4, 1, "Toinen pääsiäispäivä"), (5, 14, "Helatorstai"), (5, 24, "Helluntaipäivä")])

    holidays_list.sort()

    for month, day, name in holidays_list:
        holiday_date = datetime.date(year, month, day)
        if holiday_date >= now.date():
            days_until = (holiday_date - now.date()).days
            if language == 'fi':
                return f"{name} ({day}.{month}.) on {days_until} päivän päästä"
            else:
                finnish_to_english = {'Uudenvuodenpäivä': 'New Year\'s Day', 'Loppiainen': 'Epiphany', 'Pitkäperjantai': 'Good Friday',
                                      'Pääsiäispäivä': 'Easter Sunday', 'Toinen pääsiäispäivä': 'Easter Monday', 'Vappu': 'May Day',
                                      'Helatorstai': 'Ascension Day', 'Helluntaipäivä': 'Whit Sunday', 'Itsenäisyyspäivä': 'Independence Day',
                                      'Jouluaatto': 'Christmas Eve', 'Joulupäivä': 'Christmas Day', 'Tapaninpäivä': 'Boxing Day'}
                translated_name = finnish_to_english.get(name, name)
                return f"{translated_name} ({day}.{month}.) in {days_until} days"

    # Next year
    next_year = year + 1
    first_holiday = holidays_list[0]
    days_until = (datetime.date(next_year, first_holiday[0], first_holiday[1]) - now.date()).days
    if language == 'fi':
        return f"{first_holiday[2]} ({first_holiday[1]}.{first_holiday[0]}.{next_year}) on {days_until} päivän päästä"
    else:
        finnish_to_english = {'Uudenvuodenpäivä': 'New Year\'s Day'}
        translated_name = finnish_to_english.get(first_holiday[2], first_holiday[2])
        return f"{translated_name} ({first_holiday[1]}.{first_holiday[0]}.{next_year}) in {days_until} days"
