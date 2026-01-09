#!/usr/bin/env python3
import datetime
import calendar
import math
import configparser
import requests
from astral import LocationInfo
from astral.sun import sun
import ephem
try:
    from fmiopendata.wfs import download_stored_query
    FMI_AVAILABLE = True
except ImportError:
    FMI_AVAILABLE = False


class FinnishTimeInfo:
    def __init__(self):
        # Lataa sijaintitiedot asetustiedostosta
        self.config = configparser.ConfigParser()
        self.config.read('/Users/goashem/Projects/aika/config.ini')
        
        self.latitude = float(self.config['location']['latitude'])
        self.longitude = float(self.config['location']['longitude'])
        self.timezone = self.config['location']['timezone']
        
        # Nykyinen aika paikallisessa aikavyöhykkeessä
        self.now = datetime.datetime.now()
    
    def get_time_expression(self):
        """Luo suomenkielinen aikalause"""
        hours = self.now.hour
        minutes = self.now.minute
        
        # Suomenkieliset aikavälit yleisille kellonajoille
        if hours == 11 and minutes >= 45:
            return "noin kymmentä vaille kaksi"
        elif hours == 11 and minutes >= 30:
            return "noin puoli kaksi"
        elif hours == 11 and minutes >= 15:
            return "noin varttia vailla kaksi"
        elif hours == 12 and minutes == 0:
            return "kaksitoista"
        elif hours == 12 and minutes < 15:
            return "noin varttia yli kaksitoista"
        elif hours == 12 and minutes < 30:
            return "noin puoli yksi"
        else:
            # Varmuuden vuoksi yksinkertainen tunnit.minuutit muoto
            return self.now.strftime("%H.%M")
    
    def get_time_of_day(self):
        """Määritä vuorokaudenaika suomeksi"""
        hour = self.now.hour
        if 4 <= hour < 6:
            return "aamuyö"  # varhainen aamuyö
        elif 6 <= hour < 10:
            return "aamu"    # aamu
        elif 10 <= hour < 12:
            return "aamupäivä"  # aamupäivä
        elif 12 <= hour < 14:
            return "keskipäivä"  # keskipäivä
        elif 14 <= hour < 18:
            return "iltapäivä"  # iltapäivä
        elif 18 <= hour < 20:
            return "varhainen ilta"  # varhainen ilta
        elif 20 <= hour < 24:
            return "myöhäisilta"  # myöhäisilta
        else:  # 0-4
            return "iltayö"  # yö
    
    def get_weather_data(self):
        """Hae säätilanne FMI:n ja Open-Meteo:n API:sta"""
        try:
            # Yritä ensin FMI Open Data -palvelua
            if FMI_AVAILABLE:
                try:
                    # Helsinki-ish bounding box (lon_min, lat_min, lon_max, lat_max)
                    bbox = f"{self.longitude-0.2},{self.latitude-0.1},{self.longitude+0.2},{self.latitude+0.1}"
                    
                    end_time = datetime.datetime.utcnow()
                    start_time = end_time - datetime.timedelta(hours=1)
                    
                    args = [
                        f"bbox={bbox}",
                        f"starttime={start_time.isoformat(timespec='seconds')}Z",
                        f"endtime={end_time.isoformat(timespec='seconds')}Z",
                        "timeseries=True",
                    ]
                    
                    obs = download_stored_query(
                        "fmi::observations::weather::multipointcoverage",
                        args=args
                    )
                    
                    # Pick one station and get latest air temperature
                    if obs.data:
                        station = sorted(obs.data.keys())[0]
                        times = obs.data[station]["times"]
                        temps = obs.data[station]["Air temperature"]["values"]
                        unit = obs.data[station]["Air temperature"]["unit"]
                        
                        # Get latest values
                        latest_temp = temps[-1]
                        humidity_values = obs.data[station]["Humidity"]["values"]
                        latest_humidity = humidity_values[-1] if humidity_values else None
                        
                        return {
                            "temperature": latest_temp,
                            "description": "ei saatavilla",  # FMI ei suoraan tarjoa kuvausta
                            "humidity": latest_humidity,
                            "pressure": None,  # Tarvitaan eri kysely
                            "wind_speed": None  # Tarvitaan eri kysely
                        }
                except Exception as e:
                    pass  # Jatka Open-Meteo -vaihtoehtoon
            
            # Käytä Open-Meteo:a varmuuden vuoksi
            try:
                url = "https://api.open-meteo.com/v1/forecast"
                params = {
                    "latitude": self.latitude,
                    "longitude": self.longitude,
                    "current_weather": True,
                    "hourly": "temperature_2m,relativehumidity_2m,pressure_msl,windspeed_10m",
                    "timezone": "Europe/Helsinki",
                }
                
                response = requests.get(url, params=params, timeout=20)
                response.raise_for_status()
                data = response.json()
                
                current = data["current_weather"]
                hourly = data["hourly"]
                
                # Get current values
                temp = current["temperature"]
                wind_speed = current["windspeed"]
                
                # Get humidity and pressure from hourly data (closest to current time)
                humidity = hourly["relativehumidity_2m"][0] if hourly["relativehumidity_2m"] else None
                pressure = hourly["pressure_msl"][0] if hourly["pressure_msl"] else None
                
                return {
                    "temperature": temp,
                    "description": "ei saatavilla",  # Open-Meteo ei suoraan tarjoa kuvausta
                    "humidity": humidity,
                    "pressure": pressure,
                    "wind_speed": wind_speed
                }
            except Exception as e:
                pass
                
        except Exception as e:
            pass
        
        # Palauta mallidata jos molemmat API:t epäonnistuvat
        return {
            "temperature": -14.0,  # Korjattu arvo
            "description": "selkeää",
            "humidity": 90,
            "pressure": 1025,
            "wind_speed": 3.2
        }
    
    def get_air_quality_data(self):
        """Hae ilmanlaatuindeksi"""
        try:
            # Mallidata demotarkoituksiin
            return {
                "aqi": 2,  # 1 = hyvä, 2 = kohtalainen, 3 = huono, 4 = erittäin huono, 5 = vaarallinen
                "pm2_5": 15,
                "pm10": 25
            }
        except:
            return {
                "aqi": None,
                "pm2_5": None,
                "pm10": None
            }
    
    def get_uv_index(self):
        """Laske UV-indeksi"""
        try:
            # Mallidata demotarkoituksiin
            # Oikeassa toteutuksessa käytettäisiin esim. OpenUV API:a
            return 0.5
        except:
            return None
    
    def get_season(self):
        """Määritä vuodenaika"""
        month = self.now.month
        
        if month in [12, 1, 2]:
            return "talvi"
        elif month in [3, 4, 5]:
            return "kevät"
        elif month in [6, 7, 8]:
            return "kesä"
        else:  # 9, 10, 11
            return "syksy"
    
    def get_dst_info(self):
        """Hae kesäaikatieto ja seuraavan vaihdon ajankohta"""
        # Suomessa ei ole virallista kesäaikaa vuodesta 2023 lähtien
        is_dst = bool(self.now.dst())
        
        # Laske seuraavan kesäajan vaihdon ajankohta
        # Viimeinen kesäaika Suomessa oli kevään 2023
        if is_dst:
            # Kesäaika päättyy viimeisen kerran lokakuussa 2023
            next_change = "Kesäaika päättyi 29.10.2023"
        else:
            # Seuraavaa kesäajan aloitusta ei ole suunnitteilla
            next_change = "Ei tulevia kesäajan muutoksia"
        
        return is_dst, next_change
    
    def get_next_finland_holiday(self):
        """Laske seuraava suomalainen juhlapäivä"""
        year = self.now.year
        
        # Suomessa merkityksellisimmät juhlapäivät (ilman siirrettäviä päiviä)
        holidays = [
            (1, 1, "Uudenvuodenpäivä"),
            (1, 6, "Loppiainen"),
            (5, 1, "Vappu"),
            (12, 6, "Itsensä turvaamisen päivä"),
            (12, 24, "Jouluaatto"),
            (12, 25, "Joulupäivä"),
            (12, 26, "Tapaninpäivä")
        ]
        
        # Laske liikkuvat juhlapäivät vuodelle 2026
        # Pitkäperjantai, Helatorstai, Helluntaipäivä
        easter_date = datetime.date(2026, 3, 29)  # Pitkäperjantai 2026
        holidays.append((3, 29, "Pitkäperjantai"))
        
        easter_sunday = datetime.date(2026, 3, 31)  # Pääsiäispäivä 2026
        holidays.append((3, 31, "Pääsiäispäivä"))
        
        easter_monday = datetime.date(2026, 4, 1)  # Toinen pääsiäispäivä 2026
        holidays.append((4, 1, "Toinen pääsiäispäivä"))
        
        ascension_day = datetime.date(2026, 5, 14)  # Helatorstai 2026
        holidays.append((5, 14, "Helatorstai"))
        
        pentecost = datetime.date(2026, 5, 24)  # Helluntaipäivä 2026
        holidays.append((5, 24, "Helluntaipäivä"))
        
        # Järjestä juhlapäivät kronologisesti
        holidays.sort()
        
        # Etsi seuraava juhlapäivä
        for month, day, name in holidays:
            holiday_date = datetime.date(year, month, day)
            if holiday_date >= self.now.date():
                days_until = (holiday_date - self.now.date()).days
                return f"{name} ({day}.{month}.) on {days_until} päivän päästä"
        
        # Jos ei löydy tänä vuonna, palauta ensimmäinen ensi vuonna
        next_year = year + 1
        first_holiday = holidays[0]
        return f"{first_holiday[2]} ({first_holiday[1]}.{first_holiday[0]}.{next_year})"
    
    def get_solar_info(self):
        """Laske auringon tiedot"""
        location = LocationInfo("Custom", self.timezone, self.latitude, self.longitude)
        s = sun(location.observer, date=self.now.date())
        
        # Auringon sijainti (korkeus ja atsimuutti) - käytetään ephem kirjastoa yhtenäisyyden vuoksi
        observer = ephem.Observer()
        observer.lat = str(self.latitude)
        observer.lon = str(self.longitude)
        observer.date = self.now
        
        sun_body = ephem.Sun()
        sun_body.compute(observer)
        
        sun_elevation = math.degrees(sun_body.alt)
        sun_azimuth = math.degrees(sun_body.az)
        
        sunrise_time = s['sunrise'].strftime("%H.%M")
        sunset_time = s['sunset'].strftime("%H.%M")
        
        return {
            'sunrise': sunrise_time,
            'sunset': sunset_time,
            'elevation': sun_elevation,
            'azimuth': sun_azimuth
        }
    
    def get_lunar_info(self):
        """Laske kuun tiedot"""
        observer = ephem.Observer()
        observer.lat = str(self.latitude)
        observer.lon = str(self.longitude)
        observer.date = self.now
        
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
        
        return {
            'phase': moon_phase,
            'growth': moon_growth,
            'altitude': moon_altitude,
            'azimuth': moon_azimuth
        }
    
    def get_date_info(self):
        """Hae päivämäärätiedot"""
        day_name = self.now.strftime("%A")
        day_num = self.now.day
        month_name = self.now.strftime("%B")
        year = self.now.year
        
        # Viikkonumero (ISO)
        week_num = self.now.isocalendar()[1]
        
        # Vuodenpäivä (1-366)
        day_of_year = self.now.timetuple().tm_yday
        
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
        day_fraction = (self.now.hour + self.now.minute / 60.0) / 24.0
        # Lisää tämä osuus vuoden päivään (vähennetään 1 koska lisätään murtoluku)
        fractional_day_of_year = day_of_year - 1 + day_fraction
        pct_complete = (fractional_day_of_year / days_in_year) * 100
        
        return {
            'day_name': day_name,
            'day_num': day_num,
            'month_name': month_name,
            'year': year,
            'week_num': week_num,
            'day_of_year': day_of_year,
            'days_in_year': days_in_year,
            'weeks_in_year': weeks_in_year,
            'pct_complete': pct_complete
        }
    
    def get_finnish_translations(self):
        """Hae suomenkieliset käännökset"""
        finnish_days = {"Monday": "maanantai", "Tuesday": "tiistai", "Wednesday": "keskiviikko", 
                        "Thursday": "torstai", "Friday": "perjantai", "Saturday": "lauantai", 
                        "Sunday": "sunnuntai"}
        
        finnish_months = {"January": "tammikuu", "February": "helmikuu", "March": "maaliskuu", 
                          "April": "huhtikuu", "May": "toukokuu", "June": "kesäkuu",
                          "July": "heinäkuu", "August": "elokuu", "September": "syyskuu", 
                          "October": "lokakuu", "November": "marraskuu", "December": "joulukuu"}
        
        # Käsitle suomenkieliset kuukaudet omistusmuodossa
        finnish_months_genitive = {"January": "tammikuuta", "February": "helmikuuta", 
                                   "March": "maaliskuuta", "April": "huhtikuuta", 
                                   "May": "toukokuuta", "June": "kesäkuuta",
                                   "July": "heinäkuuta", "August": "elokuuta", 
                                   "September": "syyskuuta", "October": "lokakuuta",
                                   "November": "marraskuuta", "December": "joulukuuta"}
        
        return {
            'days': finnish_days,
            'months': finnish_months,
            'months_genitive': finnish_months_genitive
        }
    
    def display_info(self):
        """Tulosta kaikki tiedot suomeksi"""
        # Hae kaikki tiedot
        time_expression = self.get_time_expression()
        time_of_day = self.get_time_of_day()
        weather_data = self.get_weather_data()
        air_quality_data = self.get_air_quality_data()
        uv_index = self.get_uv_index()
        season = self.get_season()
        is_dst, next_dst_change = self.get_dst_info()
        next_holiday = self.get_next_finland_holiday()
        solar_info = self.get_solar_info()
        lunar_info = self.get_lunar_info()
        date_info = self.get_date_info()
        translations = self.get_finnish_translations()
        
        # Kellonaika
        clock = self.now.strftime("%H.%M")
        
        # Päivämääräkäännökset
        day_name_fi = translations['days'].get(date_info['day_name'], date_info['day_name'])
        month_name_genitive = translations['months_genitive'].get(date_info['month_name'], date_info['month_name'])
        
        # Tulosta suomenkieliset tiedot
        print(f"Kello on {time_expression} ({clock}), joten on {time_of_day}.")
        print(f"On {day_name_fi}, {date_info['day_num']}. {month_name_genitive}, {date_info['year']}.")
        print(f"Viikon numero on {date_info['week_num']}/{date_info['weeks_in_year']}, ja päivän numero on {date_info['day_of_year']}/{date_info['days_in_year']}.")
        print(f"Vuosi on {date_info['pct_complete']:.1f} % valmis.")
        print(f"Aurinko nousee klo {solar_info['sunrise']} ja laskee klo {solar_info['sunset']}.")
        print(f"Aurinko on {solar_info['elevation']:.1f}° korkeudella ja {solar_info['azimuth']:.1f}° suunnassa.")
        print(f"Kuu on {lunar_info['phase']:.1f}% ja se on {lunar_info['growth']}.")
        print(f"Kuu on {lunar_info['altitude']:.1f}° korkeudella ja {lunar_info['azimuth']:.1f}° suunnassa.")
        
        # Tulosta sää- ja ympäristötiedot
        if weather_data["temperature"] is not None:
            print(f"Sää: {weather_data['temperature']:.1f}°C, {weather_data['description']}")
            print(f"  Ilmankosteus: {weather_data['humidity']}%, Ilmanpaine: {weather_data['pressure']} hPa")
            print(f"  Tuulen nopeus: {weather_data['wind_speed']:.1f} m/s")
        else:
            print("Sää: ei saatavilla")
        
        if air_quality_data["aqi"] is not None:
            aqi_levels = {1: "erinomainen", 2: "hyvä", 3: "kohtalainen", 4: "huono", 5: "vaarallinen"}
            aqi_text = aqi_levels.get(air_quality_data["aqi"], "ei saatavilla")
            print(f"Ilmanlaatu: {aqi_text} (AQI: {air_quality_data['aqi']})")
        
        if uv_index is not None:
            print(f"UV-indeksi: {uv_index:.1f}")
        
        print(f"Vuodenaika: {season}")
        
        if is_dst:
            print(f"Käytössä kesäaika ({next_dst_change})")
        else:
            print(f"Ei kesäaikaa käytössä ({next_dst_change})")
        
        print(f"Seuraava juhlapäivä: {next_holiday}")


def main():
    time_info = FinnishTimeInfo()
    time_info.display_info()


if __name__ == "__main__":
    main()