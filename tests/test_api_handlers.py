"""Tests for API handlers"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from api_handlers import CPCBHandler, OpenWeatherHandler, IQAirHandler
from config.settings import CITIES, PRIORITY_CITIES

@pytest.fixture
def mock_responses():
    """Mock API responses"""
    return {
        'cpcb': {
            'records': [{
                'City': 'Delhi',
                'AQI': '156',
                'PM2.5': '45.6',
                'PM10': '89.4',
                'NO2': '42.3',
                'SO2': '8.5',
                'CO': '1.2',
                'O3': '31.4',
                'Dominant_Parameter': 'PM2.5',
                'Station': 'RK Puram'
            }]
        },
        'openweather_weather': {
            'main': {
                'temp': 25.6,
                'feels_like': 26.2,
                'temp_min': 24.1,
                'temp_max': 27.3,
                'pressure': 1012,
                'humidity': 65
            },
            'wind': {
                'speed': 3.6,
                'deg': 180
            },
            'clouds': {
                'all': 40
            },
            'rain': {
                '1h': 0,
                '3h': 0.2
            },
            'sys': {
                'sunrise': 1635730200,
                'sunset': 1635771000
            },
            'visibility': 8000,
            'name': 'Delhi'
        },
        'openweather_pollution': {
            'list': [{
                'main': {'aqi': 3},
                'components': {
                    'pm2_5': 42.5,
                    'pm10': 85.7,
                    'no2': 38.9,
                    'so2': 7.8,
                    'co': 1.1,
                    'o3': 28.6
                }
            }]
        },
        'iqair': {
            'status': 'success',
            'data': {
                'current': {
                    'pollution': {
                        'aqius': 158,
                        'pm25': 44.8,
                        'pm10': 87.2
                    },
                    'weather': {
                        'tp': 26,
                        'hu': 62,
                        'ws': 3.2,
                        'wd': 175,
                        'pr': 1011
                    }
                }
            }
        }
    }

class TestAPIHandlers:
    """Test suite for API handlers"""
    
    def test_cpcb_handler_with_mocks(self, mock_responses):
        """Test CPCB handler with mock responses"""
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_responses['cpcb']
            mock_get.return_value = mock_response
            
            handler = CPCBHandler()
            data = handler.fetch_aqi_data('Delhi')
            
            assert data is not None
            assert isinstance(data, list)
            assert len(data) > 0
            
            data_point = data[0]
            assert data_point['city'] == 'Delhi'
            assert isinstance(data_point['timestamp'], datetime)
            assert data_point['data_source'] == 'CPCB'
            assert data_point['pm25'] == 45.6
            assert data_point['aqi_value'] == 156.0
            
            # Test non-priority city
            data = handler.fetch_aqi_data('NonPriorityCity')
            assert data is None
    
    def test_openweather_handler_with_mocks(self, mock_responses):
        """Test OpenWeather handler with mock responses"""
        with patch('requests.get') as mock_get:
            def mock_response_by_url(*args, **kwargs):
                mock_response = MagicMock()
                if 'weather' in kwargs['url']:
                    mock_response.json.return_value = mock_responses['openweather_weather']
                else:
                    mock_response.json.return_value = mock_responses['openweather_pollution']
                return mock_response
            
            mock_get.side_effect = mock_response_by_url
            
            handler = OpenWeatherHandler()
            
            # Test weather data
            weather = handler.fetch_weather_data('Delhi')
            assert weather is not None
            assert isinstance(weather, dict)
            assert weather['data_source'] == 'OpenWeather'
            assert weather['temperature'] == 25.6
            assert weather['humidity'] == 65
            
            # Test pollution data
            coords = handler.CITY_COORDINATES['Delhi']
            pollution = handler.fetch_air_pollution_data(coords[0], coords[1])
            assert pollution is not None
            assert isinstance(pollution, dict)
            assert pollution['data_source'] == 'OpenWeather'
            assert pollution['pm25'] == 42.5
            assert pollution['aqi_value'] == 3
    
    def test_iqair_handler_with_mocks(self, mock_responses):
        """Test IQAir handler with mock responses"""
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_responses['iqair']
            mock_get.return_value = mock_response
            
            handler = IQAirHandler()
            data = handler.fetch_aqi_data('Delhi')
            
            assert data is not None
            assert isinstance(data, dict)
            assert data['city'] == 'Delhi'
            assert data['data_source'] == 'IQAir'
            assert data['pm25'] == 44.8
            assert data['aqi_value'] == 158
            
            # Test non-priority city
            data = handler.fetch_aqi_data('NonPriorityCity')
            assert data is None
    
    def test_city_coordinates_consistency(self):
        """Test coordinate consistency across handlers"""
        openweather = OpenWeatherHandler()
        iqair = IQAirHandler()
        
        # All handlers should have same city list
        assert set(openweather.CITY_COORDINATES.keys()) == \
               set(iqair.CITY_COORDINATES.keys())
        
        # Test coordinate values match
        for city in openweather.CITY_COORDINATES:
            ow_coords = openweather.CITY_COORDINATES[city]
            iq_coords = iqair.CITY_COORDINATES[city]
            assert ow_coords == iq_coords, f"Coordinates mismatch for {city}"
    
    def test_error_handling(self):
        """Test error handling in handlers"""
        with patch('requests.get') as mock_get:
            # Simulate connection error
            mock_get.side_effect = Exception("Connection failed")
            
            handlers = [
                CPCBHandler(),
                OpenWeatherHandler(),
                IQAirHandler()
            ]
            
            for handler in handlers:
                if isinstance(handler, OpenWeatherHandler):
                    # Test both weather and pollution endpoints
                    weather = handler.fetch_weather_data('Delhi')
                    pollution = handler.fetch_air_pollution_data(28.7041, 77.1025)
                    assert weather is None
                    assert pollution is None
                elif isinstance(handler, IQAirHandler):
                    data = handler.fetch_aqi_data('Delhi')
                    assert data is None
                else:
                    data = handler.fetch_aqi_data('Delhi')
                    assert data is None

if __name__ == "__main__":
    pytest.main([__file__, "-v"])