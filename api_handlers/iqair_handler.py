"""Handler for IQAir API"""

import requests
from typing import Dict, Any
from config.settings import IQAIR_API_KEY

class IQAirHandler:
    def __init__(self):
        self.api_key = IQAIR_API_KEY
        self.base_url = "https://api.iqair.com/v2"
    
    def get_air_quality_data(self, city: str, country: str) -> Dict[str, Any]:
        """
        Fetch air quality data from IQAir for a specific city
        
        Args:
            city: Name of the city
            country: Name of the country
            
        Returns:
            Dict containing air quality data
        """
        endpoint = f"{self.base_url}/city"
        params = {
            "city": city,
            "country": country,
            "key": self.api_key
        }
        
        response = requests.get(endpoint, params=params)
        response.raise_for_status()
        return response.json()