"""Test cases for API handlers"""

import unittest
from unittest.mock import patch, MagicMock
from api_handlers.cpcb_handler import CPCBHandler
from api_handlers.openweather_handler import OpenWeatherHandler
from api_handlers.iqair_handler import IQAirHandler

class TestAPIHandlers(unittest.TestCase):
    def setUp(self):
        self.cpcb_handler = CPCBHandler()
        self.openweather_handler = OpenWeatherHandler()
        self.iqair_handler = IQAirHandler()
        
    @patch('requests.get')
    def test_cpcb_handler(self, mock_get):
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {"aqi": 100}
        mock_get.return_value = mock_response
        
        result = self.cpcb_handler.get_aqi_data("Delhi")
        self.assertEqual(result["aqi"], 100)
        
    @patch('requests.get')
    def test_openweather_handler(self, mock_get):
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {"temp": 25}
        mock_get.return_value = mock_response
        
        result = self.openweather_handler.get_weather_data("Delhi")
        self.assertEqual(result["temp"], 25)
        
    @patch('requests.get')
    def test_iqair_handler(self, mock_get):
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {"aqi": 150}
        mock_get.return_value = mock_response
        
        result = self.iqair_handler.get_air_quality_data("Delhi", "India")
        self.assertEqual(result["aqi"], 150)

if __name__ == '__main__':
    unittest.main()