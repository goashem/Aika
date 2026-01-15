"""Marine and flood data provider."""

import requests


def get_marine_data(latitude, longitude, timezone):
    """Get marine/wave data from Open-Meteo Marine API.

    Returns:
        dict: Marine data with wave height, direction, period
    """
    try:
        url = "https://marine-api.open-meteo.com/v1/marine"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": "wave_height,wave_direction,wave_period,wind_wave_height,swell_wave_height",
            "timezone": timezone,
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        current = data.get("current", {})
        return {
            "wave_height": current.get("wave_height"),
            "wave_direction": current.get("wave_direction"),
            "wave_period": current.get("wave_period"),
            "wind_wave_height": current.get("wind_wave_height"),
            "swell_wave_height": current.get("swell_wave_height"),
        }
    except:
        return {
            "wave_height": None,
            "wave_direction": None,
            "wave_period": None,
            "wind_wave_height": None,
            "swell_wave_height": None,
        }


def get_flood_data(latitude, longitude):
    """Get river discharge/flood data from Open-Meteo Flood API.

    Returns:
        dict: Flood data with river discharge values
    """
    try:
        url = "https://flood-api.open-meteo.com/v1/flood"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "daily": "river_discharge,river_discharge_mean,river_discharge_max",
            "forecast_days": 1,
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        daily = data.get("daily", {})
        return {
            "river_discharge": daily.get("river_discharge", [None])[0],
            "river_discharge_mean": daily.get("river_discharge_mean", [None])[0],
            "river_discharge_max": daily.get("river_discharge_max", [None])[0],
        }
    except:
        return {
            "river_discharge": None,
            "river_discharge_mean": None,
            "river_discharge_max": None,
        }
