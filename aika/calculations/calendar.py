"""Calendar, date, season, and holiday calculations."""
import datetime

try:
    import holidays as holidays_lib

    HOLIDAYS_AVAILABLE = True
except ImportError:
    HOLIDAYS_AVAILABLE = False

# Finnish name day calendar (nimipäiväkalenteri)
# Format: (month, day): "Name1, Name2" or "Name1"
FINNISH_NAME_DAYS = {
    # January (Tammikuu)
    (1, 1): "Aapeli", (1, 2): "Aappo", (1, 3): "Elmo, Elmeri, Elmer", (1, 4): "Ruut",
    (1, 5): "Lea, Leea", (1, 6): "Harri", (1, 7): "Aukusti, Aku", (1, 8): "Hilppa, Titta",
    (1, 9): "Veikko, Veli", (1, 10): "Nyyrikki", (1, 11): "Kari, Karri", (1, 12): "Toini",
    (1, 13): "Nuutti", (1, 14): "Sakari, Saku", (1, 15): "Solja", (1, 16): "Ilmari, Ilmo",
    (1, 17): "Toni, Anttoni, Anton", (1, 18): "Laura", (1, 19): "Heikki, Henrik, Henri",
    (1, 20): "Henna, Henni, Henriikka", (1, 21): "Aune, Oona, Auni", (1, 22): "Visa",
    (1, 23): "Enni, Eine, Eini", (1, 24): "Senja, Jaakko", (1, 25): "Paavo, Pauli, Paavali",
    (1, 26): "Joonatan", (1, 27): "Viljo", (1, 28): "Kaarlo, Kaarle, Kalle",
    (1, 29): "Valtteri", (1, 30): "Irja", (1, 31): "Alli",
    # February (Helmikuu)
    (2, 1): "Riitta", (2, 2): "Aamu", (2, 3): "Valo", (2, 4): "Armas",
    (2, 5): "Asko", (2, 6): "Terhi, Teija", (2, 7): "Riku, Rikhard",
    (2, 8): "Laina", (2, 9): "Raija, Raisa", (2, 10): "Elina, Ella, Elli",
    (2, 11): "Talvikki", (2, 12): "Elma, Elmi", (2, 13): "Sulo, Sulho",
    (2, 14): "Voitto, Valentin, Tino", (2, 15): "Sinikka, Sini", (2, 16): "Kai",
    (2, 17): "Väinö, Väinämö", (2, 18): "Kaino", (2, 19): "Eija",
    (2, 20): "Heli, Helinä", (2, 21): "Keijo", (2, 22): "Tuulikki, Tuuli, Tuulia",
    (2, 23): "Aslak", (2, 24): "Matti, Matias", (2, 25): "Tuukka, Tuukko",
    (2, 26): "Nestori", (2, 27): "Torsti", (2, 28): "Onni", (2, 29): "Hilma",
    # March (Maaliskuu)
    (3, 1): "Alpo", (3, 2): "Virva, Virve, Virpi", (3, 3): "Kauko",
    (3, 4): "Ari, Arsi", (3, 5): "Laila, Leila", (3, 6): "Tarmo",
    (3, 7): "Tarja, Taru", (3, 8): "Vilppu", (3, 9): "Auvo",
    (3, 10): "Aurora, Aura", (3, 11): "Kalervo", (3, 12): "Reijo, Reko",
    (3, 13): "Erno, Ernesti", (3, 14): "Matilda, Tilda", (3, 15): "Risto",
    (3, 16): "Ilkka", (3, 17): "Kerttu", (3, 18): "Eetu, Edvard",
    (3, 19): "Jooseppi, Juuso", (3, 20): "Aki, Joakim, Kim", (3, 21): "Pentti",
    (3, 22): "Vihtori", (3, 23): "Akseli", (3, 24): "Kaapo, Gabriel",
    (3, 25): "Aija", (3, 26): "Manu, Immanuel, Manne", (3, 27): "Sauli, Saul",
    (3, 28): "Armi", (3, 29): "Jouni, Joni, Joonas", (3, 30): "Usko",
    (3, 31): "Irma",
    # April (Huhtikuu)
    (4, 1): "Raita", (4, 2): "Pellervo", (4, 3): "Samuli, Sami, Samppa",
    (4, 4): "Ukko", (4, 5): "Irene, Ira, Irina", (4, 6): "Vilho, Ville",
    (4, 7): "Allan, Ahvo", (4, 8): "Suoma, Suometar", (4, 9): "Elias, Eelis, Eljas",
    (4, 10): "Tero", (4, 11): "Verna", (4, 12): "Julius, Jyri, Jyrki",
    (4, 13): "Tellervo", (4, 14): "Taito", (4, 15): "Linda, Tuomi",
    (4, 16): "Jalo, Patrik", (4, 17): "Otto", (4, 18): "Valto, Valdemar",
    (4, 19): "Pilvi", (4, 20): "Lauha", (4, 21): "Anssi, Anselmi",
    (4, 22): "Alina", (4, 23): "Yrjö, Jyri", (4, 24): "Pertti, Albert",
    (4, 25): "Markku, Marko, Markus", (4, 26): "Terttu", (4, 27): "Merja",
    (4, 28): "Ilpo, Ilppo", (4, 29): "Teijo", (4, 30): "Mirja, Miia, Mira",
    # May (Toukokuu)
    (5, 1): "Vappu, Valpuri", (5, 2): "Vuokko, Viivi", (5, 3): "Outi",
    (5, 4): "Roosa, Ruusu", (5, 5): "Maini", (5, 6): "Ylermi",
    (5, 7): "Helmi, Hilma", (5, 8): "Heino", (5, 9): "Timo",
    (5, 10): "Aino, Aini", (5, 11): "Osmo", (5, 12): "Lotta",
    (5, 13): "Kukka, Floora", (5, 14): "Sofia, Sonja", (5, 15): "Emilia, Emma, Milla",
    (5, 16): "Esteri, Ester", (5, 17): "Maila, Mailis", (5, 18): "Erkki, Eerik, Eerika",
    (5, 19): "Emilia, Hemminki, Hemmo", (5, 20): "Lilja, Karoliina, Lilli",
    (5, 21): "Kosti, Konsta, Konstantin", (5, 22): "Hemminki, Hemmo",
    (5, 23): "Lyydia, Lyyli", (5, 24): "Tuukka, Touko", (5, 25): "Urpo",
    (5, 26): "Minna, Vilma, Vilhelmiina", (5, 27): "Ritva", (5, 28): "Alma",
    (5, 29): "Oiva", (5, 30): "Pasi", (5, 31): "Helga, Helka",
    # June (Kesäkuu)
    (6, 1): "Teemu, Nikodemus", (6, 2): "Venla", (6, 3): "Orvokki",
    (6, 4): "Toivo", (6, 5): "Sulevi", (6, 6): "Kustaa, Kyösti",
    (6, 7): "Suvi, Robert, Roope", (6, 8): "Salomon, Salomo",
    (6, 9): "Ensio", (6, 10): "Seppo", (6, 11): "Impi, Immu",
    (6, 12): "Esko", (6, 13): "Raili, Raila", (6, 14): "Kielo",
    (6, 15): "Vieno, Viena", (6, 16): "Päivi, Päivä", (6, 17): "Urho",
    (6, 18): "Tapio", (6, 19): "Siiri", (6, 20): "Into",
    (6, 21): "Ahti, Ahto", (6, 22): "Paula, Pauliina", (6, 23): "Aatto",
    (6, 24): "Johannes, Juhani, Juha, Jukka, Juhannus", (6, 25): "Uuno",
    (6, 26): "Jorma, Jarmo", (6, 27): "Elviira, Elvi", (6, 28): "Leo",
    (6, 29): "Pietari, Pekka, Petra, Petri", (6, 30): "Päiviö",
    # July (Heinäkuu)
    (7, 1): "Aaro, Aaron", (7, 2): "Maria, Mari, Maija", (7, 3): "Arvo",
    (7, 4): "Uljas", (7, 5): "Unto, Untamo", (7, 6): "Esa, Esaias",
    (7, 7): "Klaus, Launo", (7, 8): "Turo, Turkka", (7, 9): "Jasmin, Ilta",
    (7, 10): "Saima, Saimi", (7, 11): "Elli, Noora, Nelli", (7, 12): "Hermanni, Herkko",
    (7, 13): "Ilari, Joel, Joeli", (7, 14): "Aliina, Aliisa", (7, 15): "Rauni, Rauna",
    (7, 16): "Reino", (7, 17): "Ossi, Ossian", (7, 18): "Riikka",
    (7, 19): "Saara, Sari, Salli, Sara", (7, 20): "Marketta, Maarit, Reetta",
    (7, 21): "Johanna, Hanna, Jenni, Jenna", (7, 22): "Leena, Matleena, Leeni",
    (7, 23): "Olga, Oili", (7, 24): "Kristiina, Kirsi, Kirsti, Tiina",
    (7, 25): "Jaakko, Jaakoppi, Jaska", (7, 26): "Anna, Anne, Anni, Annikki, Anneli",
    (7, 27): "Heidi", (7, 28): "Atso", (7, 29): "Olavi, Olli, Uolevi",
    (7, 30): "Helena, Elena", (7, 31): "Helmi",
    # August (Elokuu)
    (8, 1): "Maire", (8, 2): "Kimmo", (8, 3): "Nino, Linnea, Nea",
    (8, 4): "Veera", (8, 5): "Salme, Sanelma", (8, 6): "Toini, Taina",
    (8, 7): "Lahja", (8, 8): "Sylvi, Sylvia", (8, 9): "Erja, Eira",
    (8, 10): "Lauri, Lasse", (8, 11): "Sisko", (8, 12): "Klaara",
    (8, 13): "Jesse", (8, 14): "Onerva", (8, 15): "Meri, Meeri",
    (8, 16): "Aulis", (8, 17): "Verneri", (8, 18): "Leevi",
    (8, 19): "Mauno, Magnus, Manu", (8, 20): "Sami, Samuel",
    (8, 21): "Soini, Veini", (8, 22): "Iivari, Iiva", (8, 23): "Signe, Varma",
    (8, 24): "Perttu", (8, 25): "Loviisa", (8, 26): "Ilmi, Ilma",
    (8, 27): "Rauli", (8, 28): "Tauno", (8, 29): "Iina",
    (8, 30): "Eemil, Eemeli", (8, 31): "Arvi",
    # September (Syyskuu)
    (9, 1): "Pirkka, Pipsa", (9, 2): "Sinikka", (9, 3): "Soile, Soili",
    (9, 4): "Ansa", (9, 5): "Topi, Topias", (9, 6): "Kaisa",
    (9, 7): "Regina", (9, 8): "Taimi", (9, 9): "Eevert, Isto",
    (9, 10): "Kalevi, Kaleva", (9, 11): "Santeri, Aleksanteri, Santtu",
    (9, 12): "Valma, Vilja", (9, 13): "Orvo", (9, 14): "Iida",
    (9, 15): "Sirpa, Sirke, Sirkku", (9, 16): "Hilla, Hellevi, Hillevi",
    (9, 17): "Aili, Aila", (9, 18): "Tyyne, Tytti", (9, 19): "Reija",
    (9, 20): "Varpu, Vaula", (9, 21): "Mervi", (9, 22): "Mauri",
    (9, 23): "Mielikki", (9, 24): "Alvar, Auno", (9, 25): "Kullervo",
    (9, 26): "Kuisma", (9, 27): "Viljami, Viljo", (9, 28): "Venja",
    (9, 29): "Mikko, Mika, Mikael, Miikka", (9, 30): "Sirja, Sorja",
    # October (Lokakuu)
    (10, 1): "Rauno, Rainer", (10, 2): "Valio", (10, 3): "Raimo",
    (10, 4): "Saija, Saila", (10, 5): "Inkeri, Inka", (10, 6): "Pinja, Minttu",
    (10, 7): "Pirjo, Pirkko", (10, 8): "Hilja", (10, 9): "Ilona",
    (10, 10): "Aleksi, Aleksis", (10, 11): "Ohto, Otso", (10, 12): "Aate, Aatos",
    (10, 13): "Tauno, Tatu", (10, 14): "Elsa, Else, Elsi", (10, 15): "Helvi, Heta",
    (10, 16): "Satu", (10, 17): "Saana, Saini", (10, 18): "Sointu",
    (10, 19): "Ulriikka", (10, 20): "Kasperi, Kauno", (10, 21): "Ursula",
    (10, 22): "Anja, Anita", (10, 23): "Severi", (10, 24): "Rasmus, Asmo",
    (10, 25): "Sointu", (10, 26): "Amanda, Manta, Niina", (10, 27): "Sabina",
    (10, 28): "Simo, Simon", (10, 29): "Alfred, Urmas", (10, 30): "Eila",
    (10, 31): "Arto, Artturi",
    # November (Marraskuu)
    (11, 1): "Lyly, Pyhäinpäivä", (11, 2): "Topi", (11, 3): "Terho",
    (11, 4): "Hertta", (11, 5): "Reima", (11, 6): "Kustaa, Kyösti",
    (11, 7): "Taisto", (11, 8): "Aatu", (11, 9): "Teuvo",
    (11, 10): "Martti", (11, 11): "Panu", (11, 12): "Virpi",
    (11, 13): "Kristian, Ano", (11, 14): "Iiris", (11, 15): "Janina, Janika, Janna",
    (11, 16): "Aarne, Aarno, Aarto", (11, 17): "Eino, Einari", (11, 18): "Tenho",
    (11, 19): "Elisabet, Liisa, Eliisa, Elise", (11, 20): "Jalmari, Jari",
    (11, 21): "Hilma", (11, 22): "Silja, Siiri", (11, 23): "Ismo",
    (11, 24): "Lempi, Lemmikki, Lemmi", (11, 25): "Katri, Kaarina, Katriina, Kaisa, Riina",
    (11, 26): "Sisko, Sini", (11, 27): "Hilkka", (11, 28): "Heini",
    (11, 29): "Aimo", (11, 30): "Antti, Antero, Atte",
    # December (Joulukuu)
    (12, 1): "Oskari", (12, 2): "Anelma, Unelma", (12, 3): "Meri",
    (12, 4): "Airi, Aira", (12, 5): "Selma", (12, 6): "Nikolaus, Niklas, Niilo, Niko",
    (12, 7): "Sampsa", (12, 8): "Kyllikki", (12, 9): "Anna, Anne",
    (12, 10): "Jutta, Judit", (12, 11): "Taneli, Daniel, Tatu", (12, 12): "Tuovi",
    (12, 13): "Seija, Lucia", (12, 14): "Stiina, Stiia", (12, 15): "Heimo",
    (12, 16): "Auli, Aulikki", (12, 17): "Raakel", (12, 18): "Aabraham, Rami",
    (12, 19): "Iikka, Iiro", (12, 20): "Benjamin, Kerkko", (12, 21): "Tuomas, Tomi, Tommi, Tuomo",
    (12, 22): "Raafael", (12, 23): "Senni", (12, 24): "Aatami, Eeva, Aadam",
    (12, 25): "Joulupäivä", (12, 26): "Tapani, Teppo, Tapaninpäivä", (12, 27): "Hannu, Hannes",
    (12, 28): "Piia", (12, 29): "Rauha", (12, 30): "Daavid, Taavetti, Taavi",
    (12, 31): "Sylvester, Silvo",
}


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


def get_name_day(now, country_code):
    """Get Finnish name day for the given date.

    Args:
        now: Current datetime
        country_code: Country code (only 'FI' supported)

    Returns:
        str: Names for today, or None if not Finnish
    """
    if country_code != 'FI':
        return None

    key = (now.month, now.day)
    return FINNISH_NAME_DAYS.get(key)


def get_next_holiday(now, country_code, language, holiday_translations):
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
                            translated_name = holiday_translations.get(holiday_name, holiday_name)
                        return f"{translated_name} ({holiday_date.strftime('%d.%m.')}) on {days_until} päivän päästä"
                    else:
                        finnish_holidays = {'Uudenvuodenpäivä': 'New Year\'s Day', 'Loppiainen': 'Epiphany', 'Pitkäperjantai': 'Good Friday',
                                            'Pääsiäispäivä': 'Easter Sunday', 'Toinen pääsiäispäivä': 'Easter Monday', 'Vappu': 'May Day',
                                            'Helatorstai': 'Ascension Day', 'Helluntaipäivä': 'Whit Sunday', 'Juhannusaatto': 'Midsummer Eve',
                                            'Juhannuspäivä': 'Midsummer Day', 'Pyhäinpäivä': 'All Saints\' Day', 'Itsenäisyyspäivä': 'Independence Day',
                                            'Jouluaatto': 'Christmas Eve', 'Joulupäivä': 'Christmas Day', 'Tapaninpäivä': 'Boxing Day'}
                        translated_name = finnish_holidays.get(holiday_name, holiday_name)
                        if translated_name == holiday_name:
                            translated_name = holiday_translations.get(holiday_name, holiday_name)
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
