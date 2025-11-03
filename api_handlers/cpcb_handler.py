"""Handler for CPCB (Central Pollution Control Board) API"""

import requests
from typing import Dict, Any
from config.settings import CPCB_API_KEY

class CPCBHandler:
    def __init__(self):
        self.api_key = CPCB_API_KEY
        self.base_url = "https://api.cpcb.gov.in/data"
    
    def get_aqi_data(self, city: str) -> Dict[str, Any]:
        """
        Fetch AQI data from CPCB for a specific city
        
        Args:
            city: Name of the city
            
        Returns:
            Dict containing AQI data
        """
        endpoint = f"{self.base_url}/aqi"
        params = {
            "city": city,
            "api_key": self.api_key
        }
        
        response = requests.get(endpoint, params=params)
        response.raise_for_status()
        return response.json()