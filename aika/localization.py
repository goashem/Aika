"""Localization and translation utilities."""


def get_finnish_translations():
    """
    Provides Finnish translations for the days of the week and months of the year.
    Additionally, includes the genitive case for Finnish months.
    """
    finnish_days = {"Monday": "maanantai", "Tuesday": "tiistai", "Wednesday": "keskiviikko", "Thursday": "torstai", "Friday": "perjantai",
                    "Saturday": "lauantai", "Sunday": "sunnuntai"}

    finnish_months = {"January": "tammikuu", "February": "helmikuu", "March": "maaliskuu", "April": "huhtikuu", "May": "toukokuu", "June": "kesakuu",
                      "July": "heinakuu", "August": "elokuu", "September": "syyskuu", "October": "lokakuu", "November": "marraskuu", "December": "joulukuu"}

    finnish_months_genitive = {"January": "tammikuuta", "February": "helmikuuta", "March": "maaliskuuta", "April": "huhtikuuta", "May": "toukokuuta",
                               "June": "kesakuuta", "July": "heinakuuta", "August": "elokuuta", "September": "syyskuuta", "October": "lokakuuta",
                               "November": "marraskuuta", "December": "joulukuuta"}

    return {'days': finnish_days, 'months': finnish_months, 'months_genitive': finnish_months_genitive}


def get_finnish_hour(hour):
    """Get Finnish word for hour number in nominative case."""
    finnish_hours = {1: "yksi", 2: "kaksi", 3: "kolme", 4: "nelja", 5: "viisi", 6: "kuusi", 7: "seitseman", 8: "kahdeksan", 9: "yhdeksan", 10: "kymmenen",
                     11: "yksitoista", 12: "kaksitoista"}
    return finnish_hours.get(hour, str(hour))


def get_time_expression(now, language):
    """Generate a natural language time expression for the given time."""
    hours = now.hour
    minutes = now.minute

    # Convert 24-hour format to 12-hour format for expressions
    display_hour = hours % 12
    if display_hour == 0:
        display_hour = 12

    next_hour = (hours + 1) % 12
    if next_hour == 0:
        next_hour = 12

    finnish_current_hour = get_finnish_hour(display_hour)
    finnish_next_hour = get_finnish_hour(next_hour)

    if minutes <= 7:
        if language == 'fi':
            return f"noin {finnish_current_hour}"
        else:
            return f"about {display_hour} o'clock"
    elif minutes <= 22:
        if language == 'fi':
            return f"noin varttia yli {finnish_current_hour}"
        else:
            return f"about quarter past {display_hour}"
    elif minutes <= 37:
        if language == 'fi':
            return f"noin puoli {finnish_next_hour}"
        else:
            return f"about half past {display_hour}"
    elif minutes <= 52:
        if language == 'fi':
            return f"noin varttia vaille {finnish_next_hour}"
        else:
            return f"about quarter to {next_hour}"
    else:
        if language == 'fi':
            return f"noin {finnish_next_hour}"
        else:
            return f"about {next_hour} o'clock"


def get_time_of_day(hour, translations):
    """Get the time of day category."""
    time_of_day_translations = translations['time_expressions']['time_of_day']

    if 4 <= hour < 6:
        return time_of_day_translations['early_morning']
    elif 6 <= hour < 10:
        return time_of_day_translations['morning']
    elif 10 <= hour < 12:
        return time_of_day_translations['forenoon']
    elif 12 <= hour < 14:
        return time_of_day_translations['noon']
    elif 14 <= hour < 18:
        return time_of_day_translations['afternoon']
    elif 18 <= hour < 20:
        return time_of_day_translations['early_evening']
    elif 20 <= hour < 24:
        return time_of_day_translations['late_evening']
    else:  # 0-4
        return time_of_day_translations['night']


# Holiday name translations (bidirectional: Finnish->English and English->Finnish)
HOLIDAY_TRANSLATIONS = {  # Finnish holidays (Finnish -> English)
    'Uudenvuodenpaiva': 'New Year\'s Day', 'Loppiainen': 'Epiphany', 'Pitkaperjantai': 'Good Friday', 'Paasiaispaiva': 'Easter Sunday',
    'Toinen paasiaispaiva': 'Easter Monday', 'Vappu': 'May Day', 'Helatorstai': 'Ascension Day', 'Helluntaipaiva': 'Whit Sunday',
    'Juhannusaatto': 'Midsummer Eve', 'Juhannuspaiva': 'Midsummer Day', 'Pyhainpaiva': 'All Saints\' Day', 'Itsenaisyyspaiva': 'Independence Day',
    'Jouluaatto': 'Christmas Eve', 'Joulupaiva': 'Christmas Day', 'Tapaninpaiva': 'Boxing Day',

    # International holidays (English -> Finnish)
    'New Year\'s Day': 'Uudenvuodenpaiva', 'Early May Bank Holiday': 'Varhaiskevaan pankkipyha', 'Spring Bank Holiday': 'Kevaan pankkipyha',
    'Summer Bank Holiday': 'Kesan pankkipyha', 'Martin Luther King Jr. Day': 'Martin Luther Kingin paiva',
    'Washington\'s Birthday': 'Washingtonin syntymapaiva', 'Memorial Day': 'Muiston paiva', 'Independence Day': 'Itsensa turvaamisen paiva',
    'Labor Day': 'Tyontekijoiden paiva', 'Columbus Day': 'Kolumbuksen paiva', 'Veterans Day': 'Veteraanien paiva', 'Thanksgiving': 'Kiitoskyyhkynen',
    'Day after Thanksgiving': 'Kiitoskyyhkysen jalkipaiva', 'Family Day': 'Perheen paiva', 'Victoria Day': 'Victoria-paiva', 'Canada Day': 'Kanadan paiva',
    'Civic Holiday': 'Kansalaisten paiva', 'Remembrance Day': 'Muistopaiva', 'Australia Day': 'Australian paiva', 'Easter Saturday': 'Paasiaislauantai',
    'Anzac Day': 'Anzac-paiva', 'Queen\'s Birthday': 'Kuningattaren syntymapaiva', 'St. Patrick\'s Day': 'St. Patrickin paiva',
    'June Bank Holiday': 'Kesakuun pankkipyha', 'August Bank Holiday': 'Elokuun pankkipyha', 'October Bank Holiday': 'Lokakuun pankkipyha',
    'St. Stephen\'s Day': 'Tapaninpaiva'}


def get_translations(language):
    """Get the translations for the chosen language."""
    translations = {'fi': {'time_expressions': {'nearly_ten_to_two': 'noin kymmentä vaille kaksi', 'half_past_one': 'noin puoli yksi',
                                                'quarter_to_two': 'noin varttia vailla kaksi', 'quarter_past_twelve': 'noin varttia yli kaksitoista',
                                                'twelve': 'kaksitoista',
                                                'time_of_day': {'early_morning': 'aamuyö', 'morning': 'aamu', 'forenoon': 'aamupäivä', 'noon': 'keskipäivä',
                                                                'afternoon': 'iltapäivä', 'early_evening': 'varhainen ilta', 'late_evening': 'myöhäisilta',
                                                                'night': 'iltayö'}},
                           'date': {'week': 'Viikko', 'day': 'Päivä', 'year_complete': 'Vuosi on {pct:.1f} % valmis', 'dawn': 'Sarastus klo {time}',
                                    'sunrise': 'aurinko nousee klo {time}', 'noon': 'keskipäivä klo {time}', 'sunset': 'laskee klo {time}',
                                    'dusk': 'hämärä klo {time}', 'sun_position': 'Aurinko on {elevation:.1f}° korkeudella, suunta {azimuth}',
                                    'moon_phase': 'Kuu on {phase:.1f}% ja se on {growth}',
                                    'moon_special_phases': {'new': 'Tänään on uusikuu', 'full': 'Tänään on täysikuu'},
                                    'moon_phase_names': {'new': 'uusikuu', 'full': 'täysikuu'},
                                    'moon_next_phase': 'Seuraava {phase}: {date} klo {time}',
                                    'moon_position': 'Kuu on {altitude:.1f}° korkeudella, suunta {azimuth}', 'moon_rise': 'Kuu nousee klo {time}',
                                    'moon_transit': 'huipussaan klo {time}', 'moon_set': 'laskee klo {time}', 'sun_visible': '(näkyvissä)',
                                    'sun_below': '(horisontin alla)', 'moon_visible': '(näkyvissä)', 'moon_below': '(horisontin alla)',
                                    'snow_depth': 'Lumen syvyys: {depth:.0f} cm', 'cloud_cover': 'Pilvisyys: {cover}%',
                                    'solar_radiation': 'Auringon säteily: {ghi:.0f} W/m² (suora: {dni:.0f} W/m²)',
                                    'solar_for_panels': 'Aurinkopaneeleille: {gti:.0f} W/m² (kiinteä) / {dni:.0f} W/m² (seuranta)',
                                    'weather': 'Sää: {temp:.1f}°c, {desc}', 'feels_like': 'Tuntuu kuin: {temp:.1f}°c',
                                    'humidity': 'Ilmankosteus: {humidity}%, ilmanpaine: {pressure} hpa',
                                    'wind_full': 'Tuuli: {speed:.1f} m/s {dir} (puuskat {gust:.1f} m/s)', 'wind_no_gust': 'Tuuli: {speed:.1f} m/s {dir}',
                                    'visibility': 'Näkyvyys: {vis:.1f} km', 'precip_intensity': 'Sateen intensiteetti: {intensity:.1f} mm/h',
                                    'wave_info': 'Aallot: {height:.1f} m, jakso {period:.1f} s, suunta {dir}',
                                    'flood_discharge': 'Jokivirtaama: {discharge:.1f} m³/s',
                                    'flood_warning': 'Tulvavaroitus: korkea jokivirtaama ({discharge:.1f} m³/s)',
                                    'wave_warning': 'Aaltovaroitus: korkeat aallot ({height:.1f} m)',
                                    'morning_forecast': 'Huomisaamu ({date}): {temp_min:.0f}–{temp_max:.0f}°c, {desc}',
                                    'morning_wind': 'Aamutuuli: {wind:.0f} m/s (puuskat {gust:.0f} m/s)',
                                    'morning_precip': 'Sateen todennäköisyys aamulla: {prob:.0f}%', 'morning_visibility': 'Näkyvyys aamulla: {vis:.1f} km',
                                    'local_time': 'Paikallinen aika: {time}', 'wind': 'Tuulen nopeus: {speed:.1f} m/s',
                                    'precipitation': 'Sateen todennäköisyys: {prob:.0f}%', 'air_quality': 'Ilmanlaatu: {quality} (aqi: {aqi})',
                                    'uv_index': 'Uv-indeksi: {index:.1f}', 'uv_low': 'Uv-indeksi: {index:.1f} (matala)',
                                    'uv_moderate': 'Uv-indeksi: {index:.1f} (kohtalainen, huomioi aurinko)',
                                    'uv_high': 'Uv-indeksi: {index:.1f} (korkea, käytä aurinkorasvaa)',
                                    'uv_very_high': 'Uv-indeksi: {index:.1f} (erittäin korkea, suojaa ihosi!)', 'season': 'Vuodenaika: {season}',
                                    'next_holiday': 'Seuraava juhlapäivä: {holiday}', 'warnings': 'Varoitukset:',
                                    'cold_warning_extreme': 'Äärimmäinen kylmävaroitus: äärimmäisen vaarallisia kylmiä lämpötiloja!',
                                    'cold_warning_severe': 'Vaikea kylmävaroitus: hyvin kylmiä lämpötiloja, varaudu varotoimiin',
                                    'cold_warning': 'Kylmävaroitus: kylmiä lämpötiloja, pukeudu lämpimästi',
                                    'wind_warning_high': 'Kovien tuulien varoitus: voimakkaita tuulia, kiinnitä irtaimet',
                                    'wind_advisory': 'Tuulivaroitus: kohtalaisia tuulia odotettavissa',
                                    'precipitation_warning_high': 'Suuren sateen varoitus: hyvin todennäköistä sadetta',
                                    'precipitation_advisory': 'Sadetodennäköisyysvaroitus: mahdollista sadetta',
                                    'rain_warning': 'Sadevaroitus: sadetta odotettavissa', 'snow_warning': 'Lumivaroitus: lumisadetta odotettavissa',
                                    'thunderstorm_warning': 'Ukkosvaroitus: ukkosmyrskyjä odotettavissa',
                                    'uv_warning': 'UV-varoitus: korkea UV-indeksi, suojaa ihosi',
                                    'air_quality_warning': 'Ilmanlaatuvaroitus: huono ilmanlaatu, vältä ulkoilua', 'road_weather': 'Ajokeli: {condition}',
                                    'road_weather_reason': 'Ajokeli: {condition} ({reason})', 'road_weather_unavailable': 'Ajokeli: ei tietoa',
                                    'road_conditions': {'NORMAL': 'normaali', 'POOR': 'huono', 'VERY_POOR': 'erittäin huono', 'NO_DATA': 'ei tietoa'},
                                    'road_reasons': {'FROST': 'pakkanen', 'SLUSH': 'sohjo', 'ICE': 'jää', 'SNOW': 'lumi', 'WIND': 'kova tuuli',
                                                     'DRIFTING_SNOW': 'pöllyävä lumi'}, 'electricity_price': 'Sähkön hinta nyt: {price:.2f} c/kWh',
                                    'electricity_price_low': 'Sähkön hinta nyt: {price:.2f} c/kWh (edullinen)',
                                    'electricity_price_high': 'Sähkön hinta nyt: {price:.2f} c/kWh (kallis)',
                                    'aurora_forecast': 'Revontuliennuste: Kp {kp:.0f}',
                                    'aurora_visible_south': 'Revontuliennuste: Kp {kp:.0f} (näkyvissä Etelä-Suomessa)',
                                    'aurora_visible_north': 'Revontuliennuste: Kp {kp:.0f} (näkyvissä Pohjois-Suomessa)',
                                    'aurora_unlikely': 'Revontuliennuste: Kp {kp:.0f} (epätodennäköinen)',
                                    'next_eclipse_solar': 'Seuraava auringonpimennys: {date} ({type})',
                                    'next_eclipse_lunar': 'Seuraava kuunpimennys: {date} ({type})',
                                    'eclipse_types': {'total': 'täydellinen', 'partial': 'osittainen', 'annular': 'rengasmainen', 'penumbral': 'puolivarjo'},
                                    'transport_disruptions': 'Liikenteen häiriöt:', 'no_disruptions': 'Ei häiriöitä',
                                    'road_warning_poor': 'Ajokelivaroitus: huono ajokeli',
                                    'road_warning_very_poor': 'Ajokelivaroitus: erittäin huono ajokeli ({reason})',
                                    'electricity_warning_high': 'Sähkövaroitus: kallis sähkö nyt ({price:.1f} c/kWh)',
                                    'electricity_warning_very_high': 'Sähkövaroitus: erittäin kallis sähkö nyt ({price:.1f} c/kWh)',
                                    'compass_directions': {'N': 'pohjoinen', 'NNE': 'pohjois-koillinen', 'NE': 'koillinen', 'ENE': 'itä-koillinen', 'E': 'itä',
                                                           'ESE': 'itä-kaakko', 'SE': 'kaakko', 'SSE': 'etelä-kaakko', 'S': 'etelä', 'SSW': 'etelä-lounas',
                                                           'SW': 'lounas', 'WSW': 'länsi-lounas', 'W': 'länsi', 'WNW': 'länsi-luode', 'NW': 'luode',
                                                           'NNW': 'pohjois-luode'}},
                           'seasons': {'winter': 'talvi', 'spring': 'kevät', 'summer': 'kesä', 'autumn': 'syksy'},
                           'moon_growth': {'growing': 'kasvava', 'waning': 'pienenevä'},
                           'air_quality_levels': {1: 'erinomainen', 2: 'hyvä', 3: 'kohtalainen', 4: 'huono', 5: 'vaarallinen'}}, 'en': {
        'time_expressions': {'nearly_ten_to_two': 'nearly ten to two', 'half_past_one': 'about half past one', 'quarter_to_two': 'about quarter to two',
                             'quarter_past_twelve': 'about quarter past twelve', 'twelve': 'twelve',
                             'time_of_day': {'early_morning': 'early morning', 'morning': 'morning', 'forenoon': 'forenoon', 'noon': 'noon',
                                             'afternoon': 'afternoon', 'early_evening': 'early evening', 'late_evening': 'late evening', 'night': 'night'}},
        'date': {'week': 'Week', 'day': 'Day', 'year_complete': 'The year is {pct:.1f} % complete', 'dawn': 'Dawn at {time}', 'sunrise': 'sunrise at {time}',
                 'noon': 'noon at {time}', 'sunset': 'sunset at {time}', 'dusk': 'dusk at {time}',
                 'sun_position': 'Sun is at {elevation:.1f}° elevation, direction {azimuth}', 'moon_phase': 'Moon is {phase:.1f}% and it is {growth}',
                 'moon_special_phases': {'new': 'Today is a new moon', 'full': 'Today is a full moon'},
                 'moon_phase_names': {'new': 'new moon', 'full': 'full moon'},
                 'moon_next_phase': 'Next {phase}: {date} at {time}',
                 'moon_position': 'Moon is at {altitude:.1f}° elevation, direction {azimuth}', 'moon_rise': 'Moon rises at {time}',
                 'moon_transit': 'peaks at {time}', 'moon_set': 'sets at {time}', 'sun_visible': '(visible)', 'sun_below': '(below horizon)',
                 'moon_visible': '(visible)', 'moon_below': '(below horizon)', 'snow_depth': 'Snow depth: {depth:.0f} cm',
                 'cloud_cover': 'Cloud cover: {cover}%', 'solar_radiation': 'Solar radiation: {ghi:.0f} W/m² (direct: {dni:.0f} W/m²)',
                 'solar_for_panels': 'For solar panels: {gti:.0f} W/m² (fixed) / {dni:.0f} W/m² (tracking)', 'weather': 'Weather: {temp:.1f}°c, {desc}',
                 'feels_like': 'Feels like: {temp:.1f}°c', 'humidity': 'Humidity: {humidity}%, pressure: {pressure} hpa',
                 'wind_full': 'Wind: {speed:.1f} m/s from {dir} (gusts {gust:.1f} m/s)', 'wind_no_gust': 'Wind: {speed:.1f} m/s from {dir}',
                 'visibility': 'Visibility: {vis:.1f} km', 'precip_intensity': 'Precipitation intensity: {intensity:.1f} mm/h',
                 'wave_info': 'Waves: {height:.1f} m, period {period:.1f} s, direction {dir}', 'flood_discharge': 'River discharge: {discharge:.1f} m³/s',
                 'flood_warning': 'Flood warning: high river discharge ({discharge:.1f} m³/s)', 'wave_warning': 'Wave warning: high waves ({height:.1f} m)',
                 'morning_forecast': 'Tomorrow morning ({date}): {temp_min:.0f}–{temp_max:.0f}°c, {desc}',
                 'morning_wind': 'Morning wind: {wind:.0f} m/s (gusts {gust:.0f} m/s)', 'morning_precip': 'Morning precipitation probability: {prob:.0f}%',
                 'morning_visibility': 'Morning visibility: {vis:.1f} km', 'local_time': 'Local time: {time}', 'wind': 'Wind speed: {speed:.1f} m/s',
                 'precipitation': 'Precipitation probability: {prob:.0f}%', 'air_quality': 'Air quality: {quality} (aqi: {aqi})',
                 'uv_index': 'Uv index: {index:.1f}', 'uv_low': 'Uv index: {index:.1f} (low)', 'uv_moderate': 'Uv index: {index:.1f} (moderate, beware of sun)',
                 'uv_high': 'Uv index: {index:.1f} (high, use sunscreen)', 'uv_very_high': 'Uv index: {index:.1f} (very high, protect your skin!)',
                 'season': 'Season: {season}', 'next_holiday': 'Next holiday: {holiday}', 'warnings': 'Warnings:',
                 'cold_warning_extreme': 'Extreme cold warning: extremely dangerous cold temperatures!',
                 'cold_warning_severe': 'Severe cold warning: very cold temperatures, take precautions',
                 'cold_warning': 'Cold warning: cold temperatures, dress warmly', 'wind_warning_high': 'High wind warning: strong winds, secure loose objects',
                 'wind_advisory': 'Wind advisory: moderate winds expected',
                 'precipitation_warning_high': 'High precipitation warning: very likely precipitation',
                 'precipitation_advisory': 'Precipitation advisory: possible precipitation', 'rain_warning': 'Rain warning: precipitation expected',
                 'snow_warning': 'Snow warning: snowfall expected', 'thunderstorm_warning': 'Thunderstorm warning: thunderstorms expected',
                 'uv_warning': 'UV warning: high UV index, protect your skin',
                 'air_quality_warning': 'Air quality warning: poor air quality, avoid outdoor activities', 'road_weather': 'Road conditions: {condition}',
                 'road_weather_reason': 'Road conditions: {condition} ({reason})', 'road_weather_unavailable': 'Road conditions: unavailable',
                 'road_conditions': {'NORMAL': 'normal', 'POOR': 'poor', 'VERY_POOR': 'very poor', 'NO_DATA': 'unavailable'},
                 'road_reasons': {'FROST': 'frost', 'SLUSH': 'slush', 'ICE': 'ice', 'SNOW': 'snow', 'WIND': 'high wind', 'DRIFTING_SNOW': 'drifting snow'},
                 'electricity_price': 'Electricity price now: {price:.2f} c/kWh', 'electricity_price_low': 'Electricity price now: {price:.2f} c/kWh (cheap)',
                 'electricity_price_high': 'Electricity price now: {price:.2f} c/kWh (expensive)', 'aurora_forecast': 'Aurora forecast: Kp {kp:.0f}',
                 'aurora_visible_south': 'Aurora forecast: Kp {kp:.0f} (visible in Southern Finland)',
                 'aurora_visible_north': 'Aurora forecast: Kp {kp:.0f} (visible in Northern Finland)',
                 'aurora_unlikely': 'Aurora forecast: Kp {kp:.0f} (unlikely)', 'next_eclipse_solar': 'Next solar eclipse: {date} ({type})',
                 'next_eclipse_lunar': 'Next lunar eclipse: {date} ({type})',
                 'eclipse_types': {'total': 'total', 'partial': 'partial', 'annular': 'annular', 'penumbral': 'penumbral'},
                 'transport_disruptions': 'Transport disruptions:', 'no_disruptions': 'No disruptions',
                 'road_warning_poor': 'Road warning: poor driving conditions',
                 'road_warning_very_poor': 'Road warning: very poor driving conditions ({reason})',
                 'electricity_warning_high': 'Electricity warning: expensive now ({price:.1f} c/kWh)',
                 'electricity_warning_very_high': 'Electricity warning: very expensive now ({price:.1f} c/kWh)',
                 'compass_directions': {'N': 'north', 'NNE': 'north-northeast', 'NE': 'northeast', 'ENE': 'east-northeast', 'E': 'east',
                                        'ESE': 'east-southeast', 'SE': 'southeast', 'SSE': 'south-southeast', 'S': 'south', 'SSW': 'south-southwest',
                                        'SW': 'southwest', 'WSW': 'west-southwest', 'W': 'west', 'WNW': 'west-northwest', 'NW': 'northwest',
                                        'NNW': 'north-northwest'}}, 'seasons': {'winter': 'winter', 'spring': 'spring', 'summer': 'summer', 'autumn': 'autumn'},
        'moon_growth': {'growing': 'growing', 'waning': 'waning'}, 'air_quality_levels': {1: 'excellent', 2: 'good', 3: 'moderate', 4: 'poor', 5: 'dangerous'}}}

    return translations.get(language, translations['fi'])
