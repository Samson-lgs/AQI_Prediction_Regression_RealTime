import requests
from datetime import datetime
import logging
from typing import Dict, List, Optional, Any, Tuple
from config.settings import OPENWEATHER_API_KEY, OPENWEATHER_BASE_URL, CITIES
from api_handlers.aqi_calculator import calculate_aqi, get_aqi_category

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
    # ALL INDIAN CITIES COORDINATES
    # ==========================================
    CITY_COORDINATES = {
        # North India
        'Delhi': (28.7041, 77.1025),
        'Noida': (28.5921, 77.1845),
        'Ghaziabad': (28.6692, 77.4538),
        'Gurugram': (28.4595, 77.0266),
        'Faridabad': (28.4089, 77.3178),
        'Greater Noida': (28.4744, 77.5040),
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
        'Meerut': (28.9845, 77.7064),
        'Aligarh': (27.8974, 78.0880),
        'Allahabad': (25.4358, 81.8463),
        'Jalandhar': (31.3260, 75.5762),
        'Bareilly': (28.3670, 79.4304),
        'Moradabad': (28.8389, 78.7765),
        'Sonipat': (28.9931, 77.0151),
        'Panipat': (29.3909, 76.9635),
        'Alwar': (27.5530, 76.6346),
        'Bharatpur': (27.2152, 77.4883),
        'Mathura': (27.4924, 77.6737),
        'Rohtak': (28.8955, 76.5893),
        'Rewari': (28.1990, 76.6189),
        'Bhiwani': (28.7930, 76.1395),
        'Bhiwadi': (28.2091, 76.8633),
        'Srinagar': (34.0837, 74.7973),
        
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
        'Warangal': (17.9784, 79.6005),
        
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
        'Navi Mumbai': (19.0330, 73.0297),
        'Pimpri-Chinchwad': (18.6298, 73.7997),
        'Solapur': (17.6599, 75.9064),
        'Hubli-Dharwad': (15.3647, 75.1240),
        
        # East India
        'Kolkata': (22.5726, 88.3639),
        'Patna': (25.5941, 85.1376),
        'Ranchi': (23.3441, 85.3096),
        'Guwahati': (26.1445, 91.7362),
        'Raipur': (21.2514, 81.6296),
        'Bhubaneswar': (20.2961, 85.8245),
        'Jamshedpur': (22.8046, 86.1855),
        'Asansol': (23.6840, 86.9640),
        'Dhanbad': (23.7957, 86.4304),
        'Howrah': (22.5958, 88.2636),
        
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
        'Silchar': (24.8333, 92.7789),
        'Kohima': (25.6747, 94.1086),
        'Aizawl': (23.7367, 92.7173),
        
        # Additional Important Cities
        'Dehradun': (30.3165, 78.0322),
        'Shimla': (31.1048, 77.1734),
        'Jammu': (32.7266, 74.8570),
        'Mangalore': (12.9141, 74.8560),
        'Tiruchirappalli': (10.7905, 78.7047),
        'Puducherry': (11.9416, 79.8083),
        'Guntur': (16.3067, 80.4365),
        'Nellore': (14.4426, 79.9865),
        'Belgaum': (15.8497, 74.4977),
        'Amravati': (20.9374, 77.7796),
        'Kolhapur': (16.7050, 74.2433),
        'Ajmer': (26.4499, 74.6399),
        'Bikaner': (28.0229, 73.3119),
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
            logger.warning(f"OpenWeather city name lookup failed for {city}: {str(e)}. Attempting geocode fallback...")
            # Fallback: try geocoding the city name to get lat/lon
            try:
                coords = self.geocode_city(city)
                if coords:
                    lat, lon = coords
                    weather_url = 'https://api.openweathermap.org/data/2.5/weather'
                    params = {
                        'lat': lat,
                        'lon': lon,
                        'appid': self.api_key,
                        'units': 'metric'
                    }
                    response = requests.get(weather_url, params=params, timeout=self.timeout)
                    response.raise_for_status()
                    data = response.json()
                    logger.debug(f"OpenWeather weather data fetched by coords for {city} ({lat},{lon})")
                    return self._parse_weather_data(data)
                else:
                    logger.error(f"Geocoding returned no results for {city}")
                    return None
            except Exception as ge:
                logger.error(f"OpenWeather geocode/weather fallback failed for {city}: {str(ge)}")
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

    def geocode_city(self, city: str) -> Optional[Tuple[float, float]]:
        """
        Use OpenWeather Geo API to translate a city name into coordinates.
        Returns (lat, lon) or None.
        """
        try:
            url = 'https://api.openweathermap.org/geo/1.0/direct'
            params = {
                'q': f"{city},IN",
                'limit': 1,
                'appid': self.api_key
            }
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            results = response.json() or []
            if len(results) > 0:
                lat = results[0].get('lat')
                lon = results[0].get('lon')
                if lat is not None and lon is not None:
                    return (lat, lon)
            return None
        except Exception as e:
            logger.error(f"Geocoding error for {city}: {str(e)}")
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
                
                # Get pollutant concentrations
                pm25 = pollution.get('pm2_5')
                pm10 = pollution.get('pm10')
                no2 = pollution.get('no2')
                so2 = pollution.get('so2')
                co = pollution.get('co')
                o3 = pollution.get('o3')
                
                # Calculate proper AQI from pollutant concentrations (0-500 scale)
                from api_handlers.aqi_calculator import calculate_aqi, calculate_india_aqi, get_aqi_category
                
                # Convert CO from μg/m³ to mg/m³ for India NAQI
                # OpenWeather returns CO in μg/m³, but India NAQI expects mg/m³
                co_mg = co / 1000 if co else None
                
                # Calculate both EPA and India NAQI
                epa_aqi = calculate_aqi(pm25=pm25, pm10=pm10, no2=no2, so2=so2, co=co, o3=o3)
                india_result = calculate_india_aqi(pm25=pm25, pm10=pm10, no2=no2, so2=so2, co=co_mg, o3=o3)
                
                # Use India AQI as primary for Indian cities
                aqi_value = india_result['aqi']
                category = get_aqi_category(aqi_value)
                
                return {
                    'timestamp': datetime.now(),
                    'pm25': pm25,
                    'pm10': pm10,
                    'no2': no2,
                    'so2': so2,
                    'co': co_mg,  # Store CO in mg/m³ for consistency with India NAQI
                    'o3': o3,
                    'data_source': 'OpenWeather',
                    'aqi_value': aqi_value,
                    'aqi_epa': epa_aqi,
                    'aqi_india': india_result['aqi'],
                    'dominant_pollutant': india_result.get('dominant_pollutant'),
                    'sub_index': india_result.get('sub_index', {}),
                    'quality': category['category']
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