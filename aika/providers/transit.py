"""Public transit data provider."""
import requests

try:
    from ..cache import get_cached_data, cache_data

    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False


    # Define dummy functions if cache module is not available
    def get_cached_data(api_name):
        return None


    def cache_data(api_name, data):
        pass

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
        return get_city_alerts(now, feed_name, router, digitransit_api_key)

    return None


def get_foli_nearby_stops(latitude, longitude, limit=20):
    """Get nearest Föli bus stops and their next departures.
    
    1. Download all stops from data.foli.fi/gtfs/stops (cached).
    2. Filter for stops within 1km.
    3. Get real-time departures for the nearest ones.
    """
    import math
    import requests

    # 1. Get All Stops
    stops_cache_key = "foli_gtfs_all_stops"
    stops_dict = None

    if CACHE_AVAILABLE:
        stops_dict = get_cached_data(stops_cache_key)

    if not stops_dict:
        try:
            url = "https://data.foli.fi/gtfs/stops"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                stops_dict = response.json()
                # Cache for 24 hours (stops don't change often)
                # But our simple cache might not support TTL, relying on simple persistence
                if CACHE_AVAILABLE:
                    cache_data(stops_cache_key, stops_dict)
        except:
            return None

    if not stops_dict:
        return None

    # 2. Filter by distance (Haversine approximation for speed)
    # 1 deg lat ~ 111km, 1 deg lon ~ 55km (at 60 deg lat)
    # 1km radius -> delta_lat ~ 0.009, delta_lon ~ 0.018
    min_lat, max_lat = latitude - 0.02, latitude + 0.02
    min_lon, max_lon = longitude - 0.04, longitude + 0.04

    candidate_stops = []

    # Helper for distance
    def haversine(lat1, lon1, lat2, lon2):
        R = 6371000  # meters
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)
        a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    for stop_id, stop in stops_dict.items():
        try:
            s_lat = float(stop.get("stop_lat", 0))
            s_lon = float(stop.get("stop_lon", 0))

            # Rough box check first
            if min_lat < s_lat < max_lat and min_lon < s_lon < max_lon:
                dist = haversine(latitude, longitude, s_lat, s_lon)
                if dist < 800:  # 800m limit
                    candidate_stops.append({"id": stop_id, "name": stop.get("stop_name", "Unknown"), "code": stop.get("stop_code", ""), "distance": int(dist)})
        except:
            continue

    # Sort by distance
    candidate_stops.sort(key=lambda x: x["distance"])
    nearest = candidate_stops[:limit]

    # 3. Get Real-time info for nearest
    results = []
    for stop in nearest:
        stop_code = stop["code"]
        if not stop_code: continue

        departures = []
        try:
            url = f"https://data.foli.fi/siri/sm/{stop_code}"
            resp = requests.get(url, timeout=3)
            if resp.status_code == 200:
                data = resp.json()
                # data["result"] is list of departures
                siri_result = data.get("result", [])

                count = 0
                for arr in siri_result:
                    if count >= 3: break  # Max 3 per stop

                    line = arr.get("lineref")
                    dest = arr.get("destinationdisplay")
                    exp_ts = arr.get("expectedarrivaltime")
                    aim_ts = arr.get("aimedarrivaltime")

                    if exp_ts and aim_ts:
                        diff = (exp_ts - aim_ts) / 60

                        status = "OK"
                        if diff > 2:
                            status = "LATE"
                        elif diff < -1:
                            status = "EARLY"

                        # Format HH:MM from timestamp
                        import datetime
                        time_str = datetime.datetime.fromtimestamp(exp_ts).strftime("%H:%M")

                        departures.append({"line": line, "headsign": dest, "time": time_str, "status": status, "diff_min": round(diff, 1)})
                        count += 1

        except:
            pass

        # Only add stop if it has upcoming departures? 
        # Or add anyway so user knows no bus is coming.
        results.append({"name": stop["name"], "code": stop["code"], "distance": stop["distance"], "departures": departures})

    return results
