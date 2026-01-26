"""Air quality data provider."""
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


def get_uv_index(latitude, longitude):
    """Get UV index from Open-Meteo API."""
    # Check cache first
    cache_key = f"uv_index_{latitude}_{longitude}"
    if CACHE_AVAILABLE:
        cached_data = get_cached_data(cache_key)
        if cached_data is not None:
            return cached_data

    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {"latitude": latitude, "longitude": longitude, "hourly": "uv_index", "timezone": "Europe/Helsinki", "forecast_days": 1, }

        response = requests.get(url, params=params, timeout=20)
        response.raise_for_status()
        data = response.json()

        uv_index = data["hourly"]["uv_index"][0] if data["hourly"]["uv_index"] else 0.5
        # Cache the data before returning
        if CACHE_AVAILABLE:
            cache_data(cache_key, uv_index)
        return uv_index
    except:
        fallback_value = 0.5
        # Cache the data before returning
        if CACHE_AVAILABLE:
            cache_data(cache_key, fallback_value)
        return fallback_value


def get_uv_forecast(latitude, longitude, timezone):
    """Get comprehensive UV forecast with personalized recommendations.
    
    Returns:
        dict: {
            'current_uv': float,
            'max_uv_today': float,
            'peak_time': str (HH:MM),
            'uv_category': str ('low'/'moderate'/'high'/'very_high'/'extreme'),
            'safe_exposure_time': str,
            'protection_recommendations': list[str],
            'burn_time_by_skin_type': dict[int, int],
            'skin_type': int (default 3 for medium sensitivity),
            'vitamin_d_recommendation': str,
            'clothing_protection_level': str,
            'sunscreen_application_amount': str
        }
    """
    # Check cache first
    cache_key = f"uv_forecast_{latitude}_{longitude}"
    if CACHE_AVAILABLE:
        cached_data = get_cached_data(cache_key)
        if cached_data is not None:
            return cached_data

    try:
        # Get extended UV forecast data
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": latitude, 
            "longitude": longitude, 
            "hourly": "uv_index,uv_index_clear_sky",
            "timezone": timezone,
            "forecast_days": 2
        }

        response = requests.get(url, params=params, timeout=20)
        response.raise_for_status()
        data = response.json()

        # Extract UV data
        hourly_data = data.get("hourly", {})
        uv_indices = hourly_data.get("uv_index", [])
        times = hourly_data.get("time", [])
        
        if not uv_indices or not times:
            raise Exception("No UV data available")

        # Current UV index (first value)
        current_uv = uv_indices[0] if uv_indices else 0.5
        
        # Find maximum UV index for today
        max_uv_today = max(uv_indices) if uv_indices else current_uv
        
        # Find peak time
        peak_time = ""
        if uv_indices:
            peak_index = uv_indices.index(max_uv_today)
            if peak_index < len(times):
                # Extract time portion from ISO format
                peak_time = times[peak_index][-5:]  # Gets HH:MM from YYYY-MM-DDTHH:MM format

        # Determine UV category
        if current_uv >= 11:
            uv_category = "extreme"
        elif current_uv >= 8:
            uv_category = "very_high"
        elif current_uv >= 6:
            uv_category = "high"
        elif current_uv >= 3:
            uv_category = "moderate"
        else:
            uv_category = "low"

        # Personalized recommendations based on Fitzpatrick skin types
        # Allow configurable skin type (default medium sensitivity type 3)
        skin_type = 3  # Could be made configurable via user preferences
        
        # Safe exposure times by skin type (approximate)
        # Based on skin type 1-6 with corresponding MED (Minimal Erythemal Dose)
        burn_times = {
            1: 15,   # Very fair skin - very sensitive
            2: 20,   # Fair skin - sensitive
            3: 30,   # Medium skin - somewhat sensitive (default)
            4: 45,   # Olive skin - minimally sensitive
            5: 60,   # Brown skin - rarely burns
            6: 90    # Dark skin - rarely burns
        }
        
        # Calculate safe exposure time based on UV index
        base_time = burn_times.get(skin_type, 30)
        if current_uv > 0:
            safe_exposure_time = int(base_time / current_uv)
            safe_exposure_time = max(1, safe_exposure_time)  # Minimum 1 minute
        else:
            safe_exposure_time = "Unlimited with precautions"

        # Protection recommendations based on UV category
        recommendations = []
        if current_uv >= 3:
            recommendations.extend([
                "Käytä aurinkorasvaa SPF30+" if timezone.startswith("Europe") else "Use sunscreen SPF30+",
                "Käytä päähinnettä" if timezone.startswith("Europe") else "Wear a hat",
                "Suosi varjoa klo 10-16" if timezone.startswith("Europe") else "Seek shade between 10am-4pm"
            ])
        
        if current_uv >= 6:
            recommendations.extend([
                "Vältä suoraa aurinkoa" if timezone.startswith("Europe") else "Avoid direct sunlight",
                "Käytä pitkähihaisia vaatteita" if timezone.startswith("Europe") else "Wear long-sleeved clothing",
                "Käytä aurinkolaseja" if timezone.startswith("Europe") else "Wear sunglasses"
            ])
            
        if current_uv >= 8:
            recommendations.extend([
                "Minimoi ulkonaolo" if timezone.startswith("Europe") else "Minimize outdoor time",
                "Löydä varjoa auringon ollessa korkeimmillaan" if timezone.startswith("Europe") else "Find shade when sun is highest"
            ])

        # Burn times for different skin types
        burn_time_by_skin_type = {}
        for stype, base_minutes in burn_times.items():
            if current_uv > 0:
                burn_time = int(base_minutes / current_uv)
                burn_time_by_skin_type[stype] = max(1, burn_time)
            else:
                burn_time_by_skin_type[stype] = "Unlimited"

        # Enhanced UV personalization features
        
        # Vitamin D synthesis recommendation
        if current_uv >= 3 and current_uv <= 8:
            vitamin_d_recommendation = "Optimal time for vitamin D synthesis - short exposure beneficial"
        elif current_uv < 3:
            vitamin_d_recommendation = "Low UV levels - may need dietary supplements or UV lamps"
        else:
            vitamin_d_recommendation = "High UV - vitamin D synthesis good but sun protection essential"
            
        # Clothing protection level recommendation
        if current_uv >= 8:
            clothing_protection_level = "Full coverage required (UPF 50+ clothing)"
        elif current_uv >= 6:
            clothing_protection_level = "Good coverage recommended (UPF 30+ clothing)"
        elif current_uv >= 3:
            clothing_protection_level = "Standard protection adequate"
        else:
            clothing_protection_level = "Basic protection sufficient"

        # Sunscreen application amount guidance
        sunscreen_application_amount = "Apply generously (about 35ml for full body coverage)"

        result = {
            'current_uv': round(current_uv, 1),
            'max_uv_today': round(max_uv_today, 1),
            'peak_time': peak_time,
            'uv_category': uv_category,
            'safe_exposure_time': str(safe_exposure_time) + " min" if isinstance(safe_exposure_time, int) else safe_exposure_time,
            'protection_recommendations': recommendations,
            'burn_time_by_skin_type': burn_time_by_skin_type,
            'skin_type': skin_type,
            'vitamin_d_recommendation': vitamin_d_recommendation,
            'clothing_protection_level': clothing_protection_level,
            'sunscreen_application_amount': sunscreen_application_amount,
            'confidence': 0.9  # High confidence from Open-Meteo data
        }

        # Cache the data before returning
        if CACHE_AVAILABLE:
            cache_data(cache_key, result)
        return result

    except Exception as e:
        # Return fallback UV forecast data
        fallback_result = {
            'current_uv': 0.5,
            'max_uv_today': 0.5,
            'peak_time': "",
            'uv_category': 'low',
            'safe_exposure_time': "Unlimited with precautions",
            'protection_recommendations': [],
            'burn_time_by_skin_type': {1: "Unlimited", 2: "Unlimited", 3: "Unlimited", 4: "Unlimited", 5: "Unlimited", 6: "Unlimited"},
            'skin_type': 3,
            'vitamin_d_recommendation': "Low UV levels - may need dietary supplements",
            'clothing_protection_level': "Basic protection sufficient",
            'sunscreen_application_amount': "Apply standard amount",
            'confidence': 0.5  # Lower confidence for fallback data
        }
        
        # Cache the fallback data before returning
        if CACHE_AVAILABLE:
            cache_data(cache_key, fallback_result)
        return fallback_result


def get_air_quality(latitude, longitude, timezone):
    """Get air quality data from Open-Meteo Air Quality API."""
    # Check cache first
    cache_key = f"air_quality_{latitude}_{longitude}"
    if CACHE_AVAILABLE:
        cached_data = get_cached_data(cache_key)
        if cached_data:
            return cached_data

    try:
        url = "https://air-quality-api.open-meteo.com/v1/air-quality"
        params = {"latitude": latitude, "longitude": longitude, "current": "european_aqi,pm10,pm2_5", "timezone": timezone}

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        current = data.get("current", {})
        european_aqi = current.get("european_aqi")
        pm10 = current.get("pm10")
        pm2_5 = current.get("pm2_5")

        aqi_simple = None
        if european_aqi is not None:
            if european_aqi <= 20:
                aqi_simple = 1
            elif european_aqi <= 40:
                aqi_simple = 2
            elif european_aqi <= 60:
                aqi_simple = 3
            elif european_aqi <= 80:
                aqi_simple = 4
            else:
                aqi_simple = 5

        air_quality_data = {"aqi": aqi_simple, "european_aqi": european_aqi, "pm2_5": pm2_5, "pm10": pm10}
        # Cache the data before returning
        if CACHE_AVAILABLE:
            cache_data(cache_key, air_quality_data)
        return air_quality_data
    except:
        fallback_data = {"aqi": None, "european_aqi": None, "pm2_5": None, "pm10": None}
        # Cache the data before returning
        if CACHE_AVAILABLE:
            cache_data(cache_key, fallback_data)
        return fallback_data
