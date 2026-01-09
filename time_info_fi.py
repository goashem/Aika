#!/usr/bin/env python3
import datetime
import calendar
import math
import configparser
from astral import LocationInfo
from astral.sun import sun
import ephem


def translate_to_finnish(text):
    """
    Yksinkertainen käännössanakirja yleisiin aikaan liittyviin termeihin.
    Tuotantokäytössä kannattaa käyttää oikeaa käännöskirjastoa tai API:a.
    """
    translations = {"morning": "aamu", "afternoon": "iltapäivä", "evening": "ilta", "night": "yö", "Monday": "maanantai", "Tuesday": "tiistai",
                    "Wednesday": "keskiviikko", "Thursday": "torstai", "Friday": "perjantai", "Saturday": "lauantai", "Sunday": "sunnuntai",
                    "January": "tammikuu", "February": "helmikuu", "March": "maaliskuu", "April": "huhtikuu", "May": "toukokuu", "June": "kesäkuu",
                    "July": "heinäkuu", "August": "elokuu", "September": "syyskuu", "October": "lokakuu", "November": "marraskuu", "December": "joulukuu",
                    "st": ".", "nd": ".", "rd": ".", "th": "."}

    for english, finnish in translations.items():
        text = text.replace(english, finnish)
    return text


def get_time_info():
    # Lataa sijaintitiedot asetustiedostosta
    config = configparser.ConfigParser()
    config.read('/Users/goashem/Projects/aika/config.ini')
    
    latitude = float(config['location']['latitude'])
    longitude = float(config['location']['longitude'])
    timezone = config['location']['timezone']
    
    # Nykyinen aika paikallisessa aikavyöhykkeessä
    now = datetime.datetime.now()

    # Laske aika desimaalitunteina keskipäivästä (12:00) lukien
    # Negatiivinen tarkoittaa ennen keskipäivää, positiivinen jälkeen
    decimal_hour = now.hour + now.minute / 60.0
    time_from_noon = decimal_hour - 12.0
    time_words = f"{time_from_noon:.2f}".rstrip('0').rstrip('.')

    # Luo suomenkielinen aikalause
    # Esimerkiksi 11:47 pitäisi olla "noin kymmentä vaille kaksi"
    hours = now.hour
    minutes = now.minute

    # Suomenkieliset aikavälit yleisille kellonajoille
    if hours == 11 and minutes >= 45:
        time_expression = "noin kymmentä vaille kaksi"
    elif hours == 11 and minutes >= 30:
        time_expression = "noin puoli kaksi"
    elif hours == 11 and minutes >= 15:
        time_expression = "noin varttia vailla kaksi"
    elif hours == 12 and minutes == 0:
        time_expression = "kaksitoista"
    elif hours == 12 and minutes < 15:
        time_expression = "noin varttia yli kaksitoista"
    elif hours == 12 and minutes < 30:
        time_expression = "noin puoli yksi"
    else:
        # Varmuuden vuoksi yksinkertainen tunnit.minuutit muoto
        time_expression = now.strftime("%H.%M")

    # Vuorokaudenaika (tarkemmat suomenkieliset termit)
    hour = now.hour
    if 4 <= hour < 6:
        time_of_day = "aamuyö"  # varhainen aamuyö
    elif 6 <= hour < 10:
        time_of_day = "aamu"    # aamu
    elif 10 <= hour < 12:
        time_of_day = "aamupäivä"  # aamupäivä
    elif 12 <= hour < 14:
        time_of_day = "keskipäivä"  # keskipäivä
    elif 14 <= hour < 18:
        time_of_day = "iltapäivä"  # iltapäivä
    elif 18 <= hour < 20:
        time_of_day = "varhainen ilta"  # varhainen ilta
    elif 20 <= hour < 24:
        time_of_day = "myöhäisilta"  # myöhäisilta
    else:  # 0-4
        time_of_day = "iltayö"  # yö
    
    # Laske auringon nousu, lasku ja sijainti
    location = LocationInfo("Custom", timezone, latitude, longitude)
    s = sun(location.observer, date=now.date())
    
    # Auringon sijainti (korkeus ja atsimuutti)
    from astral.sun import elevation, azimuth
    sun_elevation = elevation(location.observer, now)
    sun_azimuth = azimuth(location.observer, now)
    
    # Laske kuun tiedot
    observer = ephem.Observer()
    observer.lat = str(latitude)
    observer.lon = str(longitude)
    observer.date = now
    
    moon = ephem.Moon()
    moon.compute(observer)
    
    # Kuun vaihe (prosentteina)
    moon_phase = moon.phase
    
    # Onko kuu kasvava vai vähenevä
    if moon.phase < 50:
        moon_growth = "kasvava"  # Nouvante (growing)
    else:
        moon_growth = "vähenevä"  # Calante (waning)
    
    # Kuun korkeus ja atsimuutti
    moon_altitude = math.degrees(moon.alt)
    moon_azimuth = math.degrees(moon.az)

    # Päivämääräkomponentit
    day_name = now.strftime("%A")
    day_num = now.day
    month_name = now.strftime("%B")
    year = now.year

    # Viikkonumero (ISO)
    week_num = now.isocalendar()[1]

    # Vuodenpäivä (1-366)
    day_of_year = now.timetuple().tm_yday

    # Järjestysluvun pääte erikoistapauksineen
    if 11 <= day_num % 100 <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(day_num % 10, "th")

    # Vuoden päivien määrä (karkausvuosien tarkistus)
    if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0):
        days_in_year = 366
    else:
        days_in_year = 365

    # Viikkojen määrä vuodessa (joulukuun 28. päivän viikkonumero on viimeinen ISO-viikko)
    last_week = datetime.date(year, 12, 28).isocalendar()[1]
    weeks_in_year = last_week

    # Prosenttiosuus valmiina (1 desimaali) - mukaan lukien päivän kellonaika
    # Laske kuinka suuri osa nykyisestä päivästä on kulunut (tunnit + minuutit)
    day_fraction = (now.hour + now.minute / 60.0) / 24.0
    # Lisää tämä osuus vuoden päivään (vähennetään 1 koska lisätään murtoluku)
    fractional_day_of_year = day_of_year - 1 + day_fraction
    pct_complete = (fractional_day_of_year / days_in_year) * 100

    # Muotoile tuloste samalla tavalla kuin alkuperäisessä skriptissä
    # Käytä suomalaista aikamuotoa (tunnit.minuutit)
    clock = now.strftime("%H.%M")

    # Tarkemmat suomenkieliset käännökset (time_of_day on jo suomeksi)
    finnish_time_of_day = {}

    finnish_days = {"Monday": "maanantai", "Tuesday": "tiistai", "Wednesday": "keskiviikko", "Thursday": "torstai", "Friday": "perjantai",
                    "Saturday": "lauantai", "Sunday": "sunnuntai"}

    finnish_months = {"January": "tammikuu", "February": "helmikuu", "March": "maaliskuu", "April": "huhtikuu", "May": "toukokuu", "June": "kesäkuu",
                      "July": "heinäkuu", "August": "elokuu", "September": "syyskuu", "October": "lokakuu", "November": "marraskuu", "December": "joulukuu"}

    # Käsitle suomenkieliset kuukaudet omistusmuodossa
    finnish_months_genitive = {"January": "tammikuuta", "February": "helmikuuta", "March": "maaliskuuta", "April": "huhtikuuta", "May": "toukokuuta",
                               "June": "kesäkuuta", "July": "heinäkuuta", "August": "elokuuta", "September": "syyskuuta", "October": "lokakuuta",
                               "November": "marraskuuta", "December": "joulukuuta"}

    month_name_genitive = finnish_months_genitive.get(month_name, month_name)

    # Tulosta suomenkieliset tiedot
    day_name_fi = finnish_days.get(day_name, day_name)
    month_name_fi = finnish_months.get(month_name, month_name)

    # Muuta aika suomenkieliseen muotoon
    sunrise_time = s['sunrise'].strftime("%H.%M")
    sunset_time = s['sunset'].strftime("%H.%M")
    
    print(f"Kello on {time_expression} ({clock}), joten on {time_of_day}.")
    print(f"On {day_name_fi}, {day_num}. {month_name_genitive}, {year}.")
    print(f"Viikon numero on {week_num}/{weeks_in_year}, ja päivän numero on {day_of_year}/{days_in_year}.")
    print(f"Vuosi on {pct_complete:.1f} % valmis.")
    print(f"Aurinko nousee klo {sunrise_time} ja laskee klo {sunset_time}.")
    print(f"Aurinko on {sun_elevation:.1f}° korkeudella ja {sun_azimuth:.1f}° suunnassa.")
    print(f"Kuu on {moon_phase:.1f}% ja se on {moon_growth}.")
    print(f"Kuu on {moon_altitude:.1f}° korkeudella ja {moon_azimuth:.1f}° suunnassa.")


if __name__ == "__main__":
    get_time_info()
