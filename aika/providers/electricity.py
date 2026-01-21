"""Electricity data provider."""
import datetime
import requests
from typing import Any

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
    from zoneinfo import ZoneInfo as _ZoneInfo

    ZONEINFO_AVAILABLE = True
except ImportError:
    _ZoneInfo = None
    ZONEINFO_AVAILABLE = False

ZoneInfo: Any = _ZoneInfo

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


def get_co2_intensity(now, timezone, country_code):
    """Calculate current CO2 intensity of electricity generation."""
    if country_code != 'FI' or not ENTSOE_AVAILABLE:
        return None

    cache_key = f"co2_intensity_{country_code}"
    if CACHE_AVAILABLE:
        cached_data = get_cached_data(cache_key)
        if cached_data:
            return cached_data

    try:
        from entsoe import EntsoePandasClient
        import pandas as pd
        from datetime import timedelta

        # CO2 Emission factors (gCO2/kWh) - approximate values for Finland
        factors = {'Fossil Hard coal': 820, 'Fossil Peat': 1060, 'Fossil Oil': 650, 'Fossil Gas': 490, 'Waste': 300, 'Other': 300, 'Biomass': 0,
                   # considered neutral in this simplified calc
                   'Nuclear': 0, 'Hydro Run-of-river and poundage': 0, 'Wind Onshore': 0, 'Solar': 0, 'Other renewable': 0}

        client = EntsoePandasClient(api_key='c0f2fe43-b535-45db-b402-e7374aa1ea59')

        # Ensure start is timezone aware and correct
        ts = pd.Timestamp(now)
        if ts.tz is None:
            ts = ts.tz_localize(timezone)
        else:
            ts = ts.tz_convert(timezone)

        # Look back up to 24 hours for data
        for i in range(24):
            try:
                # Try current hour (minus i hours)
                start = ts.floor('h') - timedelta(hours=i)
                end = start + timedelta(hours=1)

                # Query generation
                gen = client.query_generation('FI', start=start, end=end)
                if not gen.empty:
                    break
            except:
                continue
        else:
            # Loop completed without break = no data found
            return None

        if not gen.empty:
            # Calculate total emissions and total generation
            total_emissions = 0
            total_gen = 0

            # Use the first row (current hour)
            current_mix = gen.iloc[0]

            for source, amount in current_mix.items():
                if amount > 0:
                    factor = factors.get(source, 0)
                    total_emissions += amount * factor
                    total_gen += amount

            if total_gen > 0:
                intensity = total_emissions / total_gen

                level = "low"
                if intensity > 100: level = "moderate"
                if intensity > 200: level = "high"

                result = {"intensity": round(intensity, 1), "unit": "gCO2/kWh", "level": level}

                if CACHE_AVAILABLE:
                    cache_data(cache_key, result)

                return result

    except Exception:
        pass

    return None


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
        pricing_info = {"current_price": None, "cheapest_hour": None, "most_expensive_hour": None, "three_cheapest_hours": [], "today_prices": [], "tomorrow_prices": [],
                        "future_prices": [], "timestamp": now.isoformat()}

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
                        start_local = start_dt.astimezone(local_tz)
                        end_local = end_dt.astimezone(local_tz)
                    else:
                        start_local = start_dt
                        end_local = end_dt

                    # Check if current time falls within this quarter hour
                    if start_local <= now <= end_local:
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
                        start_local = start_dt.astimezone(local_tz)
                    else:
                        start_local = start_dt

                    price_value = price_entry.get("price", 0)
                    price_data = {"price": round(price_value, 3), "datetime": start_local.isoformat(), "hour": start_local.hour, "date": start_local.date()}

                    # Add to future prices if it's in the future
                    if start_local > now:
                        future_prices.append(price_data)

                    # Collect today's prices
                    if start_local.date() == now.date():
                        pricing_info["today_prices"].append(price_data)

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
