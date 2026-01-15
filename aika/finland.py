"""Finland-specific features: road weather, electricity prices, aurora, transit."""
import datetime
from typing import Any

import requests

# Try to import ENTSO-E packages
try:
    from entsoe import EntsoePandasClient
    import pandas as pd
    ENTSOE_AVAILABLE = True
except ImportError:
    ENTSOE_AVAILABLE = False
    pd = None
    EntsoePandasClient = None

try:
    from aika.cache import get_cached_data, cache_data
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False
    # Define dummy functions if cache module is not available
    def get_cached_data(api_name):
        return None
    def cache_data(api_name, data):
        pass

try:
    from zoneinfo import ZoneInfo as _ZoneInfo

    ZONEINFO_AVAILABLE = True
except ImportError:
    _ZoneInfo = None
    ZONEINFO_AVAILABLE = False

ZoneInfo: Any = _ZoneInfo


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


def get_road_weather(latitude, longitude, country_code):
    """Get road weather conditions from Fintraffic Digitraffic API (Finland only)."""
    if country_code != 'FI':
        return None
    
    # Check cache first
    cache_key = f"road_weather_{latitude}_{longitude}"
    if CACHE_AVAILABLE:
        cached_data = get_cached_data(cache_key)
        if cached_data:
            return cached_data
            
    try:
        margin = 0.3
        url = "https://tie.digitraffic.fi/api/weather/v1/forecast-sections-simple/forecasts"
        params = {"xMin": longitude - margin, "yMin": latitude - margin, "xMax": longitude + margin, "yMax": latitude + margin}
        headers = {"Digitraffic-User": "AikaApp/1.0"}
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        def normalize_condition(value):
            if not value:
                return None
            value = value.upper()
            suffix = '_CONDITION'
            if value.endswith(suffix):
                value = value[:-len(suffix)]
            return value

        worst_condition = None
        condition_reason = None
        condition_priority = {"NO_DATA": -1, "NORMAL": 0, "POOR": 1, "VERY_POOR": 2}

        for section in data.get("forecastSections", []):
            forecasts = section.get("forecasts", [])
            if not forecasts:
                continue
            forecast = forecasts[0]
            overall = normalize_condition(forecast.get("overallRoadCondition"))
            if overall is None:
                continue
            current_priority = condition_priority.get(overall, -1)
            worst_priority = condition_priority.get(worst_condition, -1) if worst_condition else -1
            if current_priority > worst_priority:
                worst_condition = overall
                reason = forecast.get("forecastConditionReason", {})
                if reason.get("roadCondition"):
                    condition_reason = reason.get("roadCondition")
                elif reason.get("windCondition"):
                    condition_reason = reason.get("windCondition")

        if worst_condition is None:
            road_weather_data = {"condition": "NO_DATA", "reason": None}
        else:
            road_weather_data = {"condition": worst_condition, "reason": condition_reason}
            
        # Cache the data before returning
        if CACHE_AVAILABLE:
            cache_data(cache_key, road_weather_data)
            
        return road_weather_data
    except:
        # Cache the data before returning
        if CACHE_AVAILABLE:
            cache_data(cache_key, None)
        return None


def get_electricity_price(now, timezone, country_code):
    """Get the current electricity spot price from ENTSO-E (primary) or Porssisahko.net (fallback).
    
    Returns both 15-minute price (v2) and hourly price (v1) when available.
    """
    if country_code != 'FI':
        return None
    
    # Check cache first
    cache_key = f"electricity_price_{country_code}"
    if CACHE_AVAILABLE:
        cached_data = get_cached_data(cache_key)
        if cached_data:
            return cached_data
    
    result = {}
    
    # Try ENTSO-E API first (primary source)
    if ENTSOE_AVAILABLE:
        try:
            from entsoe import EntsoePandasClient
            import pandas as pd
            from datetime import timedelta
            
            # Use the same API key from the existing implementation
            client = EntsoePandasClient(api_key='c0f2fe43-b535-45db-b402-e7374aa1ea59')
            
            # Get date range (today + 1 day ahead for day-ahead prices)
            date_base = now
            date_entsoe_start = (date_base - timedelta(0)).strftime("%Y%m%d")
            date_entsoe_end = (date_base + timedelta(2)).strftime("%Y%m%d")
            
            # Create timestamps
            entsoe_start = pd.Timestamp(date_entsoe_start, tz='Europe/Helsinki')
            entsoe_end = pd.Timestamp(date_entsoe_end, tz='Europe/Helsinki')
            
            # Query day ahead prices
            ts = client.query_day_ahead_prices('FI', start=entsoe_start, end=entsoe_end)
            
            if not ts.empty:
                # Convert to cents/kWh (EUR/MWh * 0.1 = cents/kWh)
                ts_cents = ts * 0.1
                
                # Find current price based on timestamp
                current_time = pd.Timestamp(now, tz='Europe/Helsinki')
                
                # Find the price for the current 15-minute interval
                future_prices = ts_cents[ts_cents.index >= current_time]
                if not future_prices.empty:
                    # Get the first (closest) future price which should be the current interval
                    current_price = future_prices.iloc[0]
                    result["price_15min"] = round(float(current_price), 3)
                    
                    # Also get hourly average around current time
                    current_hour = current_time.floor('H')  # Floor to current hour
                    next_hour = current_hour + pd.Timedelta(hours=1)
                    
                    # Get prices for the current hour
                    hour_prices = ts_cents[(ts_cents.index >= current_hour) & (ts_cents.index < next_hour)]
                    if not hour_prices.empty:
                        hourly_avg = hour_prices.mean()
                        result["price_hour"] = round(float(hourly_avg), 3)
                        
        except Exception as e:
            # ENTSO-E failed, fall back to Porssisahko.net
            pass
    
    # Fallback to Porssisahko.net if ENTSO-E fails or is not available
    if not result:
        # Try to get 15-minute price from v2 API
        try:
            url = "https://api.porssisahko.net/v2/latest-prices.json"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            prices = data.get("prices", [])
            if prices:
                # Find the price entry that matches the current time
                now_quarter = now.replace(second=0, microsecond=0)
                for price_entry in prices:
                    start_str = price_entry.get("startDate", "")
                    end_str = price_entry.get("endDate", "")
                    if start_str and end_str:
                        try:
                            start_dt = datetime.datetime.fromisoformat(start_str.replace("Z", "+00:00"))
                            end_dt = datetime.datetime.fromisoformat(end_str.replace("Z", "+00:00"))
                            if ZONEINFO_AVAILABLE:
                                local_tz = ZoneInfo(timezone)
                                start_local = start_dt.astimezone(local_tz).replace(tzinfo=None)
                                end_local = end_dt.astimezone(local_tz).replace(tzinfo=None)
                            else:
                                start_local = start_dt.replace(tzinfo=None)
                                end_local = end_dt.replace(tzinfo=None)

                            # Check if current time falls within this quarter hour
                            if start_local <= now_quarter <= end_local:
                                result["price_15min"] = round(price_entry.get("price", 0), 3)
                                break
                        except:
                            continue

                # If no exact match, use the first (most recent) price
                if "price_15min" not in result and prices:
                    result["price_15min"] = round(prices[0].get("price", 0), 3)
        except:
            pass
        
        # Try to get hourly price from v1 API
        try:
            url = "https://api.porssisahko.net/v1/latest-prices.json"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            prices = data.get("prices", [])
            if prices:
                now_hour = now.replace(minute=0, second=0, microsecond=0)
                for price_entry in prices:
                    start_str = price_entry.get("startDate", "")
                    if start_str:
                        try:
                            start_dt = datetime.datetime.fromisoformat(start_str.replace("Z", "+00:00"))
                            if ZONEINFO_AVAILABLE:
                                local_tz = ZoneInfo(timezone)
                                start_local = start_dt.astimezone(local_tz).replace(tzinfo=None)
                            else:
                                start_local = start_dt.replace(tzinfo=None)

                            if start_local.hour == now_hour.hour and start_local.date() == now_hour.date():
                                result["price_hour"] = round(price_entry.get("price", 0), 3)
                                break
                        except:
                            continue

                # If no exact match, use the first (most recent) price
                if "price_hour" not in result and prices:
                    result["price_hour"] = round(prices[0].get("price", 0), 3)
        except:
            pass
    
    electricity_data = result if result else None
    
    # Cache the data before returning
    if CACHE_AVAILABLE:
        cache_data(cache_key, electricity_data)
        
    return electricity_data


def get_detailed_electricity_pricing(now, timezone, country_code):
    """Get detailed electricity pricing information including future prices and cheapest hours.
    
    Returns:
        dict: Detailed pricing information including current price, future prices,
              cheapest hours, and tomorrow's prices when available.
    """
    if country_code != 'FI':
        return None
    
    try:
        # Get detailed pricing data from v2 API (15-minute intervals)
        url = "https://api.porssisahko.net/v2/latest-prices.json"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        prices = data.get("prices", [])
        if not prices:
            return None
            
        # Process pricing data
        pricing_info = {
            "current_price": None,
            "cheapest_hour": None,
            "most_expensive_hour": None,
            "three_cheapest_hours": [],
            "tomorrow_prices": [],
            "future_prices": [],
            "timestamp": now.isoformat()
        }
        
        # Find current price
        now_quarter = now.replace(second=0, microsecond=0)
        for price_entry in prices:
            start_str = price_entry.get("startDate", "")
            end_str = price_entry.get("endDate", "")
            if start_str and end_str:
                try:
                    start_dt = datetime.datetime.fromisoformat(start_str.replace("Z", "+00:00"))
                    end_dt = datetime.datetime.fromisoformat(end_str.replace("Z", "+00:00"))
                    if ZONEINFO_AVAILABLE:
                        local_tz = ZoneInfo(timezone)
                        start_local = start_dt.astimezone(local_tz).replace(tzinfo=None)
                        end_local = end_dt.astimezone(local_tz).replace(tzinfo=None)
                    else:
                        start_local = start_dt.replace(tzinfo=None)
                        end_local = end_dt.replace(tzinfo=None)
                    
                    # Check if current time falls within this quarter hour
                    if start_local <= now_quarter <= end_local:
                        pricing_info["current_price"] = round(price_entry.get("price", 0), 3)
                        break
                except:
                    continue
        
        # Process future prices and find cheapest/most expensive hours
        future_prices = []
        tomorrow = (now + datetime.timedelta(days=1)).date()
        
        for price_entry in prices:
            start_str = price_entry.get("startDate", "")
            if start_str:
                try:
                    start_dt = datetime.datetime.fromisoformat(start_str.replace("Z", "+00:00"))
                    if ZONEINFO_AVAILABLE:
                        local_tz = ZoneInfo(timezone)
                        start_local = start_dt.astimezone(local_tz).replace(tzinfo=None)
                    else:
                        start_local = start_dt.replace(tzinfo=None)
                    
                    price_value = price_entry.get("price", 0)
                    price_data = {
                        "price": round(price_value, 3),
                        "datetime": start_local.isoformat(),
                        "hour": start_local.hour,
                        "date": start_local.date()
                    }
                    
                    # Add to future prices if it's in the future
                    if start_local > now:
                        future_prices.append(price_data)
                        
                        # Collect tomorrow's prices
                        if start_local.date() == tomorrow:
                            pricing_info["tomorrow_prices"].append(price_data)
                            
                except:
                    continue
        
        # Sort future prices by price value
        future_prices_sorted = sorted(future_prices, key=lambda x: x["price"])
        
        # Find cheapest and most expensive hours
        if future_prices_sorted:
            pricing_info["cheapest_hour"] = future_prices_sorted[0]
            pricing_info["most_expensive_hour"] = future_prices_sorted[-1]
            # Get the 3 cheapest upcoming hours
            pricing_info["three_cheapest_hours"] = future_prices_sorted[:3]
            # Store all future prices
            pricing_info["future_prices"] = future_prices_sorted
            
        return pricing_info
    except Exception as e:
        return None


def get_aurora_forecast():
    """Get aurora forecast (Kp index) from NOAA and FMI."""
    # Check cache first
    cache_key = "aurora_forecast"
    if CACHE_AVAILABLE:
        cached_data = get_cached_data(cache_key)
        if cached_data:
            return cached_data
            
    try:
        kp_value = None
        fmi_activity = None

        try:
            url = "https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            if len(data) > 1:
                latest = data[-1]
                if len(latest) > 1:
                    kp_value = float(latest[1])
        except:
            pass

        try:
            url = "https://rwc-finland.fmi.fi/api/mag-activity/latest"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                fmi_activity = data.get("activity_level")
        except:
            pass

        if kp_value is not None:
            aurora_data = {"kp": kp_value, "fmi_activity": fmi_activity}
        else:
            aurora_data = None
            
        # Cache the data before returning
        if CACHE_AVAILABLE:
            cache_data(cache_key, aurora_data)
            
        return aurora_data
    except:
        # Cache the data before returning
        if CACHE_AVAILABLE:
            cache_data(cache_key, None)
        return None


# Finnish city bounding boxes mapped to Digitransit feed names
# Format: (min_lat, max_lat, min_lon, max_lon, feed_name, router)
FINNISH_CITY_FEEDS = [  # Helsinki region uses HSL router
    (60.10, 60.40, 24.50, 25.20, "HSL", "hsl"),  # Waltti cities
    (60.30, 60.60, 22.00, 22.60, "FOLI", "waltti"),  # Turku
    (61.40, 61.60, 23.60, 24.00, "tampere", "waltti"),  # Tampere
    (64.85, 65.15, 25.30, 25.70, "OULU", "waltti"),  # Oulu
    (62.10, 62.40, 25.55, 25.95, "LINKKI", "waltti"),  # Jyväskylä
    (62.75, 63.05, 27.50, 27.90, "Kuopio", "waltti"),  # Kuopio
    (60.85, 61.10, 25.45, 25.85, "Lahti", "waltti"),  # Lahti
    (62.45, 62.75, 29.55, 29.95, "Joensuu", "waltti"),  # Joensuu
    (62.95, 63.25, 21.45, 21.85, "Vaasa", "waltti"),  # Vaasa
    (61.35, 61.65, 21.60, 22.00, "Pori", "waltti"),  # Pori
    (60.85, 61.15, 24.30, 24.65, "Hameenlinna", "waltti"),  # Hämeenlinna
    (60.35, 60.60, 26.75, 27.15, "Kotka", "waltti"),  # Kotka
    (60.70, 61.00, 26.50, 26.90, "Kouvola", "waltti"),  # Kouvola
    (60.90, 61.20, 28.00, 28.40, "Lappeenranta", "waltti"),  # Lappeenranta
    (66.35, 66.65, 25.55, 25.95, "Rovaniemi", "waltti"),  # Rovaniemi
    (64.10, 64.40, 27.55, 27.95, "Kajaani", "waltti"),  # Kajaani
    (61.55, 61.85, 27.10, 27.50, "Mikkeli", "waltti"),  # Mikkeli
    (59.95, 60.15, 23.35, 23.65, "Raasepori", "waltti"),  # Raasepori
    (60.35, 60.55, 22.65, 23.05, "Salo", "waltti"),  # Salo
]


def get_city_feed(latitude, longitude):
    """Get Digitransit feed name and router for a location.

    Returns:
        tuple: (feed_name, router) or (None, None) if not in a known city
    """
    for min_lat, max_lat, min_lon, max_lon, feed, router in FINNISH_CITY_FEEDS:
        if min_lat <= latitude <= max_lat and min_lon <= longitude <= max_lon:
            return feed, router
    return None, None


def is_in_foli_area(latitude, longitude):
    """Check if location is in Föli area (Turku, Kaarina, Raisio, Lieto, Naantali, Rusko, Paimio)."""
    return 60.3 <= latitude <= 60.6 and 22.0 <= longitude <= 22.6


def get_digitransit_alerts(now, feed_name, router, digitransit_api_key):
    """Get alerts from Digitransit API for a specific feed.

    Args:
        now: Current datetime
        feed_name: Feed to filter by (e.g., "FOLI", "tampere", "OULU")
        router: Digitransit router to use ("hsl" or "waltti")
        digitransit_api_key: API key for Digitransit

    Returns:
        list: List of alert dicts or empty list
    """
    if not digitransit_api_key:
        return []

    alerts = []
    now_ts = int(now.timestamp())
    one_day_ago = now_ts - 86400

    try:
        url = f"https://api.digitransit.fi/routing/v2/{router}/gtfs/v1"
        query = """
        {
          alerts {
            alertHeaderText
            alertDescriptionText
            alertSeverityLevel
            effectiveStartDate
            effectiveEndDate
            feed
          }
        }
        """
        headers = {"Content-Type": "application/json", "digitransit-subscription-key": digitransit_api_key}

        response = requests.post(url, json={"query": query}, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            dt_alerts = data.get("data", {}).get("alerts", [])

            for alert in dt_alerts:
                # Filter by feed (case-insensitive)
                alert_feed = alert.get("feed", "")
                if alert_feed.upper() != feed_name.upper():
                    continue

                start_ts = alert.get("effectiveStartDate", 0) or 0
                end_ts = alert.get("effectiveEndDate") or float('inf')
                header = alert.get("alertHeaderText", "")

                # Only include if current and started within last 24 hours
                if header and start_ts <= now_ts <= end_ts and start_ts >= one_day_ago:
                    alerts.append({"header": header, "description": alert.get("alertDescriptionText", ""), "severity": alert.get("alertSeverityLevel", "INFO"),
                                   "starttime": start_ts})
    except:
        pass

    return alerts


def get_foli_alerts(now, digitransit_api_key=None):
    """Get public transport alerts for Föli/Turku area.

    Combines alerts from:
    1. Föli API (no API key needed)
    2. Digitransit "waltti" API filtered to FOLI feed (if an API key provided)

    Only shows alerts published within the last 24 hours, sorted by start date descending.
    """
    alerts = []
    seen_headers = set()  # To avoid duplicates
    now_ts = int(now.timestamp())
    one_day_ago = now_ts - 86400  # 24 hours in seconds

    # Source 1: Föli API (unique to Turku)
    try:
        url = "https://data.foli.fi/alerts/messages"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Check for emergency message first (always show at top)
        if data.get('emergency_message') and data['emergency_message'].get('header'):
            header = data['emergency_message'].get('header', '')
            if header and header not in seen_headers:
                seen_headers.add(header)
                alerts.append({"header": header, "message": data['emergency_message'].get('message', ''), "severity": "SEVERE", "starttime": now_ts + 999999999
                               # Ensure it's first after sorting
                               })

        # Check for global message (always show near top)
        if data.get('global_message') and data['global_message'].get('header'):
            header = data['global_message'].get('header', '')
            if header and header not in seen_headers:
                seen_headers.add(header)
                alerts.append({"header": header, "message": data['global_message'].get('message', ''), "severity": "INFO", "starttime": now_ts + 999999998
                               # Ensure it's second after sorting
                               })

        # Get active messages - only show if published within last 24 hours
        for msg in data.get('messages', []):
            if msg.get('isactive'):
                repeat = msg.get('repeat', [])
                if repeat and len(repeat) > 0:
                    start_ts = repeat[0][0] if len(repeat[0]) > 0 else 0
                    end_ts = repeat[0][1] if len(repeat[0]) > 1 else float('inf')
                else:
                    start_ts = 0
                    end_ts = float('inf')

                header = msg.get('header', '')
                if start_ts <= now_ts <= end_ts and start_ts >= one_day_ago:
                    if header and header not in seen_headers:
                        seen_headers.add(header)
                        alerts.append({"header": header, "message": msg.get('message', ''), "severity": "WARNING" if msg.get('priority', 0) > 500 else "INFO",
                                       "starttime": start_ts})
    except:
        pass

    # Source 2: Digitransit FOLI feed
    for alert in get_digitransit_alerts(now, "FOLI", "waltti", digitransit_api_key):
        header = alert.get("header", "")
        if header and header not in seen_headers:
            seen_headers.add(header)
            alerts.append(alert)

    if not alerts:
        return None

    # Sort by starttime descending (newest first)
    alerts.sort(key=lambda x: x.get('starttime', 0), reverse=True)

    return {"alerts": alerts[:5]}


def get_city_alerts(now, feed_name, router, digitransit_api_key):
    """Get public transport alerts for a Finnish city.

    Only shows alerts published within the last 24 hours, sorted by start date descending.

    Args:
        now: Current datetime
        feed_name: Digitransit feed name (e.g., "tampere", "OULU")
        router: Digitransit router ("hsl" or "waltti")
        digitransit_api_key: API key for Digitransit

    Returns:
        dict with "alerts" list or None if no alerts/no API key
    """
    if not digitransit_api_key:
        return None

    alerts = get_digitransit_alerts(now, feed_name, router, digitransit_api_key)

    if not alerts:
        return None

    # Sort by starttime descending (newest first)
    alerts.sort(key=lambda x: x.get('starttime', 0), reverse=True)

    return {"alerts": alerts[:5]}


def get_transport_disruptions(latitude, longitude, now, country_code, digitransit_api_key):
    """Get public transport disruptions from Föli or Digitransit (Finland only).

    Uses geofencing to detect which city the user is in and fetches
    alerts from the appropriate source:
    - Turku area: Föli API + Digitransit FOLI feed (no API key needed for Föli)
    - Other cities: Digitransit with city-specific feed filtering
    """
    if country_code != 'FI':
        return None

    # Use Föli API + Digitransit FOLI feed for Turku area
    if is_in_foli_area(latitude, longitude):
        return get_foli_alerts(now, digitransit_api_key)

    # Check if user is in a known city
    feed_name, router = get_city_feed(latitude, longitude)

    if feed_name and router:
        # Use city-specific alerts
        return get_city_alerts(now, feed_name, router, digitransit_api_key)

    # Fallback: not in a known city, no alerts available
    return None
