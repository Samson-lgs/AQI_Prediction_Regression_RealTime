"""Handler for fetching data from IQAir API"""

import requests
from datetime import datetime
import logging
from typing import Dict, List, Optional, Any
from config.settings import IQAIR_API_KEY, IQAIR_BASE_URL, CITIES, PRIORITY_CITIES, OPENWEATHER_API_KEY

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IQAirHandler:
    def __init__(self):
        self.api_key = IQAIR_API_KEY
        self.base_url = IQAIR_BASE_URL
        self.timeout = 10
        self.cities = CITIES
        self.priority_cities = PRIORITY_CITIES
        
        logger.info("IQAir Handler initialized; priority gating disabled, will attempt all configured cities")
    
    def fetch_aqi_data(self, city: str) -> Optional[Dict[str, Any]]:
        """
        Fetch AQI data for a city from IQAir
        
        Args:
            city (str): Name of the city
            
        Returns:
            Optional[Dict[str, Any]]: Parsed AQI data or None if failed
        """
        # Priority gating disabled — attempt fetch for any city
            
        try:
            # Get coordinates for the city
            coords = self.CITY_COORDINATES.get(city)
            if not coords:
                # Fallback: try geocoding via OpenWeather Geo API
                coords = self.geocode_city(city)
            if not coords:
                logger.warning(f"No coordinates found for {city}")
                return None
                
            url = f"{self.base_url}/nearest_city"
            params = {
                'lat': coords[0],
                'lon': coords[1],
                'key': self.api_key
            }
            
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status') == 'success':
                logger.debug(f"IQAir data fetched for {city}")
                return self._parse_iqair_data(data.get('data', {}), city)
            else:
                logger.warning(f"IQAir API error for {city}: {data.get('data')}")
                return None
        
        except requests.exceptions.RequestException as e:
            logger.error(f"IQAir API error for {city}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching IQAir data for {city}: {str(e)}")
            return None
    
    def fetch_aqi_data_batch(self, cities: List[str]) -> Dict[str, Any]:
        """
        Fetch AQI data for multiple cities
        
        Args:
            cities (List[str]): List of city names
            
        Returns:
            Dict[str, Any]: Dictionary with city names as keys and their data as values
        """
        results = {}
        
        for city in cities:
            data = self.fetch_aqi_data(city)
            if data:
                results[city] = data
            else:
                results[city] = None
        
        return results
    
    def _parse_iqair_data(self, data: Dict[str, Any], city: str) -> Optional[Dict[str, Any]]:
        """
        Parse IQAir API response into standardized format
        
        Args:
            data (Dict[str, Any]): Raw data from IQAir API
            city (str): City name
            
        Returns:
            Optional[Dict[str, Any]]: Parsed data point or None if parsing fails
        """
        try:
            current = data.get('current', {})
            pollution = current.get('pollution', {})
            weather = current.get('weather', {})
            
            aqi_value = pollution.get('aqius')  # US AQI standard
            
            return {
                'city': city,
                'timestamp': datetime.now(),
                'pm25': pollution.get('pm25'),
                'pm10': pollution.get('pm10'),
                'aqi_value': aqi_value,
                'quality': self._get_quality_label(aqi_value),
                'temperature': weather.get('tp'),
                'humidity': weather.get('hu'),
                'wind_speed': weather.get('ws'),
                'wind_direction': weather.get('wd'),
                'atmospheric_pressure': weather.get('pr'),
                'data_source': 'IQAir'
            }
        
        except Exception as e:
            logger.error(f"Error parsing IQAir data for {city}: {str(e)}")
            return None
    
    @staticmethod
    def _get_quality_label(aqi: Optional[float]) -> str:
        """
        Get air quality label based on US AQI standard
        
        Args:
            aqi (Optional[float]): AQI value
            
        Returns:
            str: Air quality label
        """
        if aqi is None:
            return 'Unknown'
            
        if aqi <= 50:
            return 'Good'
        elif aqi <= 100:
            return 'Moderate'
        elif aqi <= 150:
            return 'Unhealthy for Sensitive Groups'
        elif aqi <= 200:
            return 'Unhealthy'
        elif aqi <= 300:
            return 'Very Unhealthy'
        else:
            return 'Hazardous'
    
    # City coordinates mapping (same as OpenWeather for consistency)
    CITY_COORDINATES = {
        # North India
        'Delhi': (28.7041, 77.1025),
        'Noida': (28.5921, 77.1845),
        'Ghaziabad': (28.6692, 77.4538),
        'Gurugram': (28.4595, 77.0266),
        'Chandigarh': (30.7333, 76.7794),
        'Jaipur': (26.9124, 75.7873),
        'Lucknow': (26.8467, 80.9462),
        'Kanpur': (26.4499, 80.3319),
        'Varanasi': (25.3176, 82.9739),
        'Agra': (27.1767, 78.0081),
        'Amritsar': (31.6340, 74.8723),
        'Ludhiana': (30.9010, 75.8573),
        'Kota': (25.2138, 75.8648),
        'Jodhpur': (26.2389, 73.0243),
        'Udaipur': (24.5854, 73.7125),
        
        # South India
        'Bangalore': (12.9716, 77.5946),
        'Chennai': (13.0827, 80.2707),
        'Hyderabad': (17.3850, 78.4867),
        'Kochi': (9.9312, 76.2673),
        'Visakhapatnam': (17.6869, 83.2185),
        'Coimbatore': (11.0081, 76.9877),
        'Mysore': (12.2958, 76.6394),
        'Kurnool': (15.8281, 78.8353),
        'Vijayawada': (16.5062, 80.6480),
        'Tirupati': (13.1939, 79.8245),
        'Thanjavur': (10.7870, 79.1378),
        'Madurai': (9.9252, 78.1198),
        'Salem': (11.6643, 78.1460),
        'Thiruvananthapuram': (8.5241, 76.9366),
        
        # West India
        'Mumbai': (19.0760, 72.8777),
        'Pune': (18.5204, 73.8567),
        'Ahmedabad': (23.0225, 72.5714),
        'Surat': (21.1702, 72.8311),
        'Vadodara': (22.3072, 73.1812),
        'Rajkot': (22.3039, 70.8022),
        'Nashik': (19.9975, 73.7898),
        'Aurangabad': (19.8762, 75.3433),
        'Nagpur': (21.1458, 79.0882),
        'Thane': (19.2183, 72.9781),
        
        # East India
        'Kolkata': (22.5726, 88.3639),
        'Patna': (25.5941, 85.1376),
        'Ranchi': (23.3441, 85.3096),
        'Guwahati': (26.1445, 91.7362),
        'Raipur': (21.2514, 81.6296),
        'Bhubaneswar': (20.2961, 85.8245),
        'Jamshedpur': (22.8046, 86.1855),
        'Asansol': (23.6840, 86.9640),
        
        # Central India
        'Indore': (22.7196, 75.8577),
        'Bhopal': (23.1815, 79.9864),
        'Jabalpur': (23.1815, 79.9864),
        'Gwalior': (26.2183, 78.1627),
        'Ujjain': (23.1815, 75.7854),
        
        # North-East India
        'Imphal': (24.8170, 94.9042),
        'Shillong': (25.5729, 91.8933),
        'Agartala': (23.8103, 91.2868),
        'Dibrugarh': (27.4728, 94.9103),
    }

    def geocode_city(self, city: str) -> Optional[tuple]:
        """
        Use OpenWeather Geo API to get (lat, lon) for a city name.
        """
        try:
            url = 'https://api.openweathermap.org/geo/1.0/direct'
            params = {
                'q': f"{city},IN",
                'limit': 1,
                'appid': OPENWEATHER_API_KEY
            }
            resp = requests.get(url, params=params, timeout=self.timeout)
            resp.raise_for_status()
            arr = resp.json() or []
            if arr:
                lat = arr[0].get('lat')
                lon = arr[0].get('lon')
                if lat is not None and lon is not None:
                    return (lat, lon)
            return None
        except Exception as e:
            logger.error(f"Geocoding error for {city} (IQAir): {str(e)}")
            return None