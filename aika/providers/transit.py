"""Public transport disruptions provider for Finnish cities."""

from __future__ import annotations

import requests

# Finnish city bounding boxes mapped to Digitransit feed names
# Format: (min_lat, max_lat, min_lon, max_lon, feed_name, router)
FINNISH_CITY_FEEDS = [
    (60.10, 60.40, 24.50, 25.20, "HSL", "hsl"),  # Helsinki region uses HSL router
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


def get_city_feed(latitude: float, longitude: float) -> tuple[str | None, str | None]:
    """Get Digitransit feed name and router for a location."""
    for min_lat, max_lat, min_lon, max_lon, feed, router in FINNISH_CITY_FEEDS:
        if min_lat <= latitude <= max_lat and min_lon <= longitude <= max_lon:
            return feed, router
    return None, None


def is_in_foli_area(latitude: float, longitude: float) -> bool:
    """Return True when the coordinates fall within the Föli service area."""
    return 60.3 <= latitude <= 60.6 and 22.0 <= longitude <= 22.6


def get_digitransit_alerts(now, feed_name: str, router: str, digitransit_api_key: str | None):
    """Fetch public transport alerts from Digitransit for a specific feed."""
    if not digitransit_api_key:
        return []

    alerts = []
    now_ts = int(now.timestamp())
    one_day_ago = now_ts - 86400

    try:
        url = f"https://api.digitransit.fi/routing/v2/{router}/gtfs/v1"
        query = (
            "\n        {\n          alerts {\n            alertHeaderText\n            alertDescriptionText\n            alertSeverityLevel\n            effectiveStartDate\n            effectiveEndDate\n            feed\n          }\n        }\n        "
        )
        headers = {
            "Content-Type": "application/json",
            "digitransit-subscription-key": digitransit_api_key,
        }

        response = requests.post(url, json={"query": query}, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            dt_alerts = data.get("data", {}).get("alerts", [])

            for alert in dt_alerts:
                alert_feed = alert.get("feed", "")
                if alert_feed.upper() != feed_name.upper():
                    continue

                start_ts = alert.get("effectiveStartDate", 0) or 0
                end_ts = alert.get("effectiveEndDate") or float("inf")
                header = alert.get("alertHeaderText", "")

                if header and start_ts <= now_ts <= end_ts and start_ts >= one_day_ago:
                    alerts.append(
                        {
                            "header": header,
                            "description": alert.get("alertDescriptionText", ""),
                            "severity": alert.get("alertSeverityLevel", "INFO"),
                            "starttime": start_ts,
                        }
                    )
    except Exception:
        pass

    return alerts


def get_foli_alerts(now, digitransit_api_key: str | None = None):
    """Fetch public transport alerts for Föli/Turku area from Föli and Digitransit."""
    alerts = []
    seen_headers: set[str] = set()
    now_ts = int(now.timestamp())
    one_day_ago = now_ts - 86400

    try:
        url = "https://data.foli.fi/alerts/messages"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        emergency = data.get("emergency_message")
        if emergency and emergency.get("header"):
            header = emergency.get("header", "")
            if header and header not in seen_headers:
                seen_headers.add(header)
                alerts.append(
                    {
                        "header": header,
                        "message": emergency.get("message", ""),
                        "severity": "SEVERE",
                        "starttime": now_ts + 999_999_999,
                    }
                )

        global_msg = data.get("global_message")
        if global_msg and global_msg.get("header"):
            header = global_msg.get("header", "")
            if header and header not in seen_headers:
                seen_headers.add(header)
                alerts.append(
                    {
                        "header": header,
                        "message": global_msg.get("message", ""),
                        "severity": "INFO",
                        "starttime": now_ts + 999_999_998,
                    }
                )

        for msg in data.get("messages", []):
            if not msg.get("isactive"):
                continue

            repeat = msg.get("repeat", [])
            if repeat and len(repeat) > 0:
                start_ts = repeat[0][0] if len(repeat[0]) > 0 else 0
                end_ts = repeat[0][1] if len(repeat[0]) > 1 else float("inf")
            else:
                start_ts = 0
                end_ts = float("inf")

            header = msg.get("header", "")
            if header and header not in seen_headers and start_ts <= now_ts <= end_ts and start_ts >= one_day_ago:
                seen_headers.add(header)
                alerts.append(
                    {
                        "header": header,
                        "message": msg.get("message", ""),
                        "severity": "WARNING" if msg.get("priority", 0) > 500 else "INFO",
                        "starttime": start_ts,
                    }
                )
    except Exception:
        pass

    for alert in get_digitransit_alerts(now, "FOLI", "waltti", digitransit_api_key):
        header = alert.get("header", "")
        if header and header not in seen_headers:
            seen_headers.add(header)
            alerts.append(alert)

    if not alerts:
        return None

    alerts.sort(key=lambda x: x.get("starttime", 0), reverse=True)
    return {"alerts": alerts[:5]}


def get_city_alerts(now, feed_name: str, router: str, digitransit_api_key: str | None):
    """Fetch public transport alerts for a specific Finnish city from Digitransit."""
    if not digitransit_api_key:
        return None

    alerts = get_digitransit_alerts(now, feed_name, router, digitransit_api_key)
    if not alerts:
        return None

    alerts.sort(key=lambda x: x.get("starttime", 0), reverse=True)
    return {"alerts": alerts[:5]}


def get_transport_disruptions(latitude: float, longitude: float, now, country_code: str, digitransit_api_key: str | None):
    """Provide Finnish public transport disruptions near the user location."""
    if country_code != "FI":
        return None

    if is_in_foli_area(latitude, longitude):
        return get_foli_alerts(now, digitransit_api_key)

    feed_name, router = get_city_feed(latitude, longitude)
    if feed_name and router:
        return get_city_alerts(now, feed_name, router, digitransit_api_key)

    return None
