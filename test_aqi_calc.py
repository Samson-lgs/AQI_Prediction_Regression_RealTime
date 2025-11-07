"""
Quick test of the new AQI calculation
"""
from api_handlers.openweather_handler import OpenWeatherHandler

handler = OpenWeatherHandler()
data = handler.fetch_weather_data('Delhi')

if data:
    print(f"\n✅ Data returned:")
    print(f"   Keys: {data.keys()}")
    print(f"   Data: {data}")
else:
    print("\n❌ Failed to fetch data")
