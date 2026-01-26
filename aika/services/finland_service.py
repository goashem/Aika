"""Service for Finland-specific data (road, electricity, transit, aurora)."""

from ..models import (RoadWeather, ElectricityPrice, DetailedElectricity, AuroraForecast, TransportDisruptions, CO2Intensity)
from ..providers import road as road_provider
from ..providers import electricity as electricity_provider
from ..providers import aurora as aurora_provider
from ..providers import transit as transit_provider


def get_road_weather(latitude, longitude, country_code):
    """Get road weather conditions."""
    data = road_provider.get_road_weather(latitude, longitude, country_code)
    if not data:
        return RoadWeather()

    return RoadWeather(condition=data.get("condition", "NO_DATA"), reason=data.get("reason"))


def get_electricity(now, timezone, country_code):
    """Get current electricity price."""
    data = electricity_provider.get_electricity_price(now, timezone, country_code)
    if not data:
        return ElectricityPrice()

    from ..models import CO2Intensity

    # Get CO2 intensity
    co2_data = electricity_provider.get_co2_intensity(now, timezone, country_code)
    co2_model = None
    if co2_data:
        co2_model = CO2Intensity(intensity=co2_data.get("intensity", 0.0), unit=co2_data.get("unit", "gCO2/kWh"), level=co2_data.get("level", "low"))

    return ElectricityPrice(price_15min=data.get("price_15min"), price_hour=data.get("price_hour"), co2=co2_model)


def get_detailed_electricity(now, timezone, country_code):
    """Get detailed electricity pricing."""
    data = electricity_provider.get_detailed_electricity_pricing(now, timezone, country_code)
    if not data:
        return DetailedElectricity()

    return DetailedElectricity(current_price=data.get("current_price"), cheapest_hour=data.get("cheapest_hour"),
                               most_expensive_hour=data.get("most_expensive_hour"), three_cheapest_hours=data.get("three_cheapest_hours", []),
                               today_prices=data.get("today_prices", []), tomorrow_prices=data.get("tomorrow_prices", []),
                               future_prices=data.get("future_prices", []), timestamp=data.get("timestamp", ""))


def get_aurora():
    """Get aurora forecast."""
    data = aurora_provider.get_aurora_forecast()
    if not data:
        return AuroraForecast()

    return AuroraForecast(kp=data.get("kp", 0.0), fmi_activity=data.get("fmi_activity"))


def get_transport(latitude, longitude, now, country_code, digitransit_api_key=None):
    """Get transport disruptions."""
    # data = transit_provider.get_transport_disruptions(latitude, longitude, now, country_code, digitransit_api_key)

    data = transit_provider.get_transport_disruptions(latitude, longitude, now, country_code, digitransit_api_key)

    # Initialize model
    model = TransportDisruptions()

    if data and "alerts" in data:
        model.alerts = data.get("alerts", [])

    # Fetch nearby bus stops if in Föli area
    if transit_provider.is_in_foli_area(latitude, longitude):
        from ..models import TransitStop
        stops_data = transit_provider.get_foli_nearby_stops(latitude, longitude)
        if stops_data:
            model.stops = [TransitStop(name=s["name"], code=s["code"], distance=s["distance"], departures=s["departures"]) for s in stops_data]

    return model
