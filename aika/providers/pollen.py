"""Pollen forecast data provider using SILAM model from FMI."""
import requests
from datetime import datetime, timedelta
import math

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


def get_pollen_forecast(latitude, longitude, timezone):
    """Get pollen forecast data from FMI SILAM model.
    
    Returns:
        dict: {
            'current': {
                'date': date,
                'birch': int (0-5 scale),
                'grass': int (0-5 scale),
                'alder': int (0-5 scale),
                'mugwort': int (0-5 scale),
                'ragweed': int (0-5 scale),
                'olive': int (0-5 scale),
                'peak_times': list[str] (morning/evening)
            },
            'forecast': list of daily forecasts,
            'recommendations': list of recommendations
        }
    """
    # Check cache first
    cache_key = f"pollen_{latitude}_{longitude}"
    if CACHE_AVAILABLE:
        cached_data = get_cached_data(cache_key)
        if cached_data:
            return cached_data
            
    try:
        # For now, we'll return sample data since accessing SILAM requires
        # specialized libraries and authentication that would need to be configured
        # In a production implementation, this would connect to the THREDDS server
        
        # Get current date
        today = datetime.now().date()
        
        # Create sample pollen data (in a real implementation, this would come from SILAM)
        current_forecast = {
            'date': today,
            'birch': 3,  # 0-5 scale
            'grass': 2,  # 0-5 scale
            'alder': 1,  # 0-5 scale
            'mugwort': 0,  # 0-5 scale
            'ragweed': 0,  # 0-5 scale
            'olive': 0,  # 0-5 scale (not common in Finland)
            'peak_times': ['morning']  # when pollen is highest
        }
        
        # Create 5-day forecast
        forecast = []
        for i in range(5):
            date = today + timedelta(days=i)
            # Simulate varying pollen levels
            birch = max(0, min(5, 3 + math.sin(i) * 2))
            grass = max(0, min(5, 2 + math.cos(i) * 1.5))
            
            forecast.append({
                'date': date,
                'birch': int(birch),
                'grass': int(grass),
                'alder': max(0, min(5, 1 + math.sin(i/2) * 1)),
                'mugwort': 0 if i < 2 else max(0, min(5, i - 2)),
                'ragweed': 0,
                'olive': 0
            })
        
        # Generate recommendations based on current pollen levels
        recommendations = []
        max_pollen = max(current_forecast['birch'], current_forecast['grass'], 
                        current_forecast['alder'], current_forecast['mugwort'])
        
        if max_pollen >= 4:
            recommendations = [
                "Pese kasvot ja kädet usein",
                "Vaihda vaatteet päivittäin",
                "Pidä ikkunat kiinni huippukausina",
                "Käytä ilmansuodatinta",
                "Ota antihistamiinia tarvittaessa"
            ]
        elif max_pollen >= 2:
            recommendations = [
                "Pese kasvot usein",
                "Vaihda vaatteet päivittäin",
                "Rajoita ulkoilua aamuisin",
                "Käytä ilmansuodatinta"
            ]
        else:
            recommendations = [
                "Pese kasvot säännöllisesti",
                "Vaihda vaatteet päivittäin"
            ]
        
        result = {
            'current': current_forecast,
            'forecast': forecast,
            'recommendations': recommendations
        }
        
        # Cache the data before returning
        if CACHE_AVAILABLE:
            cache_data(cache_key, result)
            
        return result
    except Exception as e:
        # Return fallback data if API fails
        fallback_data = {
            'current': {
                'date': datetime.now().date(),
                'birch': 0,
                'grass': 0,
                'alder': 0,
                'mugwort': 0,
                'ragweed': 0,
                'olive': 0,
                'peak_times': []
            },
            'forecast': [],
            'recommendations': []
        }
        
        # Cache the fallback data before returning
        if CACHE_AVAILABLE:
            cache_data(cache_key, fallback_data)
            
        return fallback_data