import requests
from datetime import datetime
import logging
from typing import Dict, List, Optional, Any, Tuple
from config.settings import OPENWEATHER_API_KEY, OPENWEATHER_BASE_URL, CITIES

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OpenWeatherHandler:
    def __init__(self):
        self.api_key = OPENWEATHER_API_KEY
        self.base_url = OPENWEATHER_BASE_URL
        self.timeout = 10
        self.cities = CITIES
        
        logger.info(f"OpenWeather Handler initialized for {len(self.CITY_COORDINATES)} cities")
    
    # ==========================================
    # ALL 56 INDIAN CITIES COORDINATES (MODIFIED)
    # ==========================================
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
    
    def fetch_weather_data(self, city: str) -> Optional[Dict[str, Any]]:
        """
        Fetch weather data for a city
        
        Args:
            city (str): Name of the city
            
        Returns:
            Optional[Dict[str, Any]]: Parsed weather data or None if failed
        """
        try:
            weather_url = 'https://api.openweathermap.org/data/2.5/weather'
            params = {
                'q': f"{city},IN",  # Add country code for precision
                'appid': self.api_key,
                'units': 'metric'  # Use metric units
            }
            
            response = requests.get(weather_url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            logger.debug(f"OpenWeather weather data fetched for {city}")
            return self._parse_weather_data(data)
        
        except requests.exceptions.RequestException as e:
            logger.error(f"OpenWeather API error for weather data in {city}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching weather data for {city}: {str(e)}")
            return None
    
    def fetch_air_pollution_data(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """
        Fetch air pollution data using coordinates
        
        Args:
            lat (float): Latitude
            lon (float): Longitude
        
        Returns:
            Optional[Dict[str, Any]]: Parsed pollution data or None if failed
        """
        try:
            url = f"{self.base_url}/air_pollution"
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.api_key
            }
            
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            logger.debug(f"OpenWeather pollution data fetched for coordinates ({lat}, {lon})")
            return self._parse_pollution_data(data)
        
        except requests.exceptions.RequestException as e:
            logger.error(f"OpenWeather API error for pollution data: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching pollution data: {str(e)}")
            return None
    
    def _parse_pollution_data(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parse pollution data from OpenWeather API
        
        Args:
            data (Dict[str, Any]): Raw API response
            
        Returns:
            Optional[Dict[str, Any]]: Parsed pollution data
        """
        try:
            if 'list' in data and data['list']:
                pollution = data['list'][0]['components']
                aqi = data['list'][0].get('main', {}).get('aqi')
                
                return {
                    'timestamp': datetime.now(),
                    'pm25': pollution.get('pm2_5'),
                    'pm10': pollution.get('pm10'),
                    'no2': pollution.get('no2'),
                    'so2': pollution.get('so2'),
                    'co': pollution.get('co'),
                    'o3': pollution.get('o3'),
                    'data_source': 'OpenWeather',
                    'aqi_value': aqi,
                    'quality': self._get_quality_label(aqi)
                }
            return None
        
        except Exception as e:
            logger.error(f"Error parsing OpenWeather pollution data: {str(e)}")
            return None
    
    def _parse_weather_data(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parse weather data from OpenWeather API
        
        Args:
            data (Dict[str, Any]): Raw API response
            
        Returns:
            Optional[Dict[str, Any]]: Parsed weather data
        """
        try:
            main = data.get('main', {})
            wind = data.get('wind', {})
            clouds = data.get('clouds', {})
            rain = data.get('rain', {})
            sys = data.get('sys', {})
            coord = data.get('coord', {})
            
            return {
                'timestamp': datetime.now(),
                'city': data.get('name'),
                'lat': coord.get('lat'),
                'lon': coord.get('lon'),
                'temperature': main.get('temp'),
                'feels_like': main.get('feels_like'),
                'temp_min': main.get('temp_min'),
                'temp_max': main.get('temp_max'),
                'humidity': main.get('humidity'),
                'pressure': main.get('pressure'),
                'wind_speed': wind.get('speed'),
                'wind_direction': wind.get('deg'),
                'cloudiness': clouds.get('all'),
                'rain_1h': rain.get('1h', 0),
                'rain_3h': rain.get('3h', 0),
                'sunrise': datetime.fromtimestamp(sys.get('sunrise', 0)) if sys.get('sunrise') else None,
                'sunset': datetime.fromtimestamp(sys.get('sunset', 0)) if sys.get('sunset') else None,
                'visibility': data.get('visibility'),
                'data_source': 'OpenWeather'
            }
        
        except Exception as e:
            logger.error(f"Error parsing OpenWeather weather data: {str(e)}")
            return None
    
    def fetch_data_batch(self, cities: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Fetch both weather and pollution data for multiple cities in batch
        
        Args:
            cities (List[str]): List of city names
            
        Returns:
            Dict[str, Dict[str, Any]]: Dictionary with city data
        """
        results = {}
        
        for city in cities:
            try:
                city_data = {
                    'weather': None,
                    'pollution': None
                }
                
                # Get weather data
                weather_data = self.fetch_weather_data(city)
                if weather_data:
                    city_data['weather'] = weather_data
                
                # Get pollution data if coordinates exist
                coords = self.CITY_COORDINATES.get(city)
                if coords:
                    pollution_data = self.fetch_air_pollution_data(coords[0], coords[1])
                    if pollution_data:
                        city_data['pollution'] = pollution_data
                
                results[city] = city_data
                
            except Exception as e:
                logger.error(f"Error fetching batch data for {city}: {str(e)}")
                results[city] = {'weather': None, 'pollution': None}
        
        return results
    
    @staticmethod
    def _get_quality_label(aqi: Optional[int]) -> str:
        """
        Get air quality label based on OpenWeather AQI value (1-5 scale)
        
        Args:
            aqi (Optional[int]): AQI value from OpenWeather
            
        Returns:
            str: Air quality label
        """
        if aqi is None:
            return 'Unknown'
            
        labels = {
            1: 'Good',
            2: 'Fair',
            3: 'Moderate',
            4: 'Poor',
            5: 'Very Poor'
        }
        
        return labels.get(aqi, 'Unknown')