"""Handler for fetching data from CPCB API"""

import requests
import pandas as pd
from datetime import datetime
import logging
from config.settings import CPCB_API_KEY, CPCB_BASE_URL, CITIES, PRIORITY_CITIES
from typing import List, Dict, Optional, Union, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CPCBHandler:
    def __init__(self):
        self.api_key = CPCB_API_KEY
        self.base_url = CPCB_BASE_URL
        self.resource_id = '3b01bcb632fd4d27f711f1135cdfdfb0'  # CPCB AQI data
        self.timeout = 10
        self.cities = CITIES
        self.priority_cities = PRIORITY_CITIES
        
        logger.info("CPCB Handler initialized; priority gating disabled, will attempt all configured cities")
    
    def fetch_aqi_data(self, city: str) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch current AQI data for a city from CPCB
        
        Args:
            city (str): Name of the city to fetch data for
            
        Returns:
            Optional[List[Dict[str, Any]]]: List of parsed data points or None if failed
        """
        # Priority gating disabled — attempt fetch for any city
            
        try:
            url = f"{self.base_url}/{self.resource_id}"
            params = {
                'api-key': self.api_key,
                'format': 'json',
                'filters[City]': city,
                'limit': 10
            }
            
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('records'):
                records = data['records']
                logger.debug(f"CPCB data fetched for {city}: {len(records)} records")
                return self._parse_cpcb_data(records, city)
            else:
                logger.warning(f"No CPCB data found for {city}")
                return None
        
        except requests.exceptions.RequestException as e:
            logger.error(f"CPCB API error for {city}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching CPCB data for {city}: {str(e)}")
            return None
    
    def fetch_aqi_data_batch(self, cities: List[str]) -> Dict[str, Any]:
        """
        Fetch AQI data for multiple cities in a batch
        
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
    
    def _parse_cpcb_data(self, records: List[Dict[str, Any]], city: str) -> Optional[List[Dict[str, Any]]]:
        """
        Parse CPCB API response into standardized format
        
        Args:
            records (List[Dict[str, Any]]): Raw records from CPCB API
            city (str): City name for the records
            
        Returns:
            Optional[List[Dict[str, Any]]]: List of parsed data points or None if parsing fails
        """
        try:
            parsed_data = []
            
            for record in records:
                data_point = {
                    'city': city,
                    'timestamp': datetime.now(),
                    'pm25': self._safe_float(record.get('PM2.5')),
                    'pm10': self._safe_float(record.get('PM10')),
                    'no2': self._safe_float(record.get('NO2')),
                    'so2': self._safe_float(record.get('SO2')),
                    'co': self._safe_float(record.get('CO')),
                    'o3': self._safe_float(record.get('O3')),
                    'aqi_value': self._safe_float(record.get('AQI')),
                    'pollutant_dominant': record.get('Dominant_Parameter', '').strip(),
                    'location': record.get('Station', '').strip(),
                    'data_source': 'CPCB',
                    'quality': self._get_quality_label(
                        self._safe_float(record.get('AQI'))
                    )
                }
                parsed_data.append(data_point)
            
            return parsed_data
        
        except Exception as e:
            logger.error(f"Error parsing CPCB data for {city}: {str(e)}")
            return None
    
    @staticmethod
    def _safe_float(value: Union[str, int, float, None]) -> Optional[float]:
        """
        Safely convert value to float, handling various input types
        
        Args:
            value: Input value of any type
            
        Returns:
            Optional[float]: Converted float value or None if conversion fails
        """
        if value is None or value == '':
            return None
            
        try:
            # Handle string preprocessing
            if isinstance(value, str):
                value = value.strip().replace(',', '')
            return float(value)
        except (ValueError, TypeError):
            return None
    
    @staticmethod        
    def _get_quality_label(aqi: Optional[float]) -> str:
        """
        Get air quality label based on AQI value
        
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
            return 'Satisfactory'
        elif aqi <= 200:
            return 'Moderate'
        elif aqi <= 300:
            return 'Poor'
        elif aqi <= 400:
            return 'Very Poor'
        else:
            return 'Severe'