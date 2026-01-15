"""Finnish electricity price data provider - ENTSO-E and Porssisahko APIs."""

import datetime
from typing import Any

import requests

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


def get_electricity_price(now, timezone, country_code):
    """Get the current electricity spot price from ENTSO-E (primary) or Porssisahko.net (fallback).

    Returns both 15-minute price (v2) and hourly price (v1) when available.

    Returns:
        dict: Electricity price data with price_15min and price_hour, or None
    """
    if country_code != 'FI':
        return None

    cache_key = f"electricity_price_{country_code}"
    if CACHE_AVAILABLE:
        cached_data = get_cached_data(cache_key)
        if cached_data:
            return cached_data

    result = {}

    # Try ENTSO-E API first (primary source)
    if ENTSOE_AVAILABLE:
        try:
            from datetime import timedelta

            client = EntsoePandasClient(api_key='c0f2fe43-b535-45db-b402-e7374aa1ea59')

            date_base = now
            date_entsoe_start = (date_base - timedelta(0)).strftime("%Y%m%d")
            date_entsoe_end = (date_base + timedelta(2)).strftime("%Y%m%d")

            entsoe_start = pd.Timestamp(date_entsoe_start, tz='Europe/Helsinki')
            entsoe_end = pd.Timestamp(date_entsoe_end, tz='Europe/Helsinki')

            ts = client.query_day_ahead_prices('FI', start=entsoe_start, end=entsoe_end)

            if not ts.empty:
                ts_cents = ts * 0.1

                current_time = pd.Timestamp(now, tz='Europe/Helsinki')

                future_prices = ts_cents[ts_cents.index >= current_time]
                if not future_prices.empty:
                    current_price = future_prices.iloc[0]
                    result["price_15min"] = round(float(current_price), 3)

                    current_hour = current_time.floor('H')
                    next_hour = current_hour + pd.Timedelta(hours=1)

                    hour_prices = ts_cents[(ts_cents.index >= current_hour) & (ts_cents.index < next_hour)]
                    if not hour_prices.empty:
                        hourly_avg = hour_prices.mean()
                        result["price_hour"] = round(float(hourly_avg), 3)

        except Exception:
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

                            if start_local <= now_quarter <= end_local:
                                result["price_15min"] = round(price_entry.get("price", 0), 3)
                                break
                        except:
                            continue

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

                if "price_hour" not in result and prices:
                    result["price_hour"] = round(prices[0].get("price", 0), 3)
        except:
            pass

    electricity_data = result if result else None

    if CACHE_AVAILABLE:
        cache_data(cache_key, electricity_data)

    return electricity_data


def get_detailed_electricity_pricing(now, timezone, country_code):
    """Get detailed electricity pricing information including future prices and cheapest hours.

    Returns:
        dict: Detailed pricing information or None
    """
    if country_code != 'FI':
        return None

    try:
        url = "https://api.porssisahko.net/v2/latest-prices.json"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        prices = data.get("prices", [])
        if not prices:
            return None

        pricing_info = {
            "current_price": None,
            "cheapest_hour": None,
            "most_expensive_hour": None,
            "three_cheapest_hours": [],
            "tomorrow_prices": [],
            "future_prices": [],
            "timestamp": now.isoformat(),
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

                    if start_local <= now_quarter <= end_local:
                        pricing_info["current_price"] = round(price_entry.get("price", 0), 3)
                        break
                except:
                    continue

        # Process future prices
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
                        "date": start_local.date(),
                    }

                    if start_local > now:
                        future_prices.append(price_data)

                        if start_local.date() == tomorrow:
                            pricing_info["tomorrow_prices"].append(price_data)

                except:
                    continue

        future_prices_sorted = sorted(future_prices, key=lambda x: x["price"])

        if future_prices_sorted:
            pricing_info["cheapest_hour"] = future_prices_sorted[0]
            pricing_info["most_expensive_hour"] = future_prices_sorted[-1]
            pricing_info["three_cheapest_hours"] = future_prices_sorted[:3]
            pricing_info["future_prices"] = future_prices_sorted

        return pricing_info
    except Exception:
        return None
