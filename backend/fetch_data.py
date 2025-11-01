"""
Step 2: Fetch combined air quality and weather data
Sources: OpenWeather + IQAir
Purpose: Collect pollutants, weather, and AQI for regression model training
"""

import requests
import pandas as pd
from datetime import datetime

# ===============================
# CONFIGURATION
# ===============================
OPENWEATHER_KEY = "528f129d20a5e514729cbf24b2449e44"
IQAIR_KEY = "102c31e0-0f3c-4865-b4f3-2b4a57e78c40"

CITY = "Bangalore"
STATE = "Karnataka"
COUNTRY = "India"
LAT, LON = 12.97, 77.59  # Bangalore coordinates

# ===============================
# FETCH FROM OPENWEATHER
# ===============================
def fetch_openweather():
    """Fetch pollutant concentrations from OpenWeather"""
    url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={LAT}&lon={LON}&appid={OPENWEATHER_KEY}"
    response = requests.get(url)
    data = response.json()

    # Extract main pollutant data
    components = data["list"][0]["components"]
    return {
        "pm2_5": components.get("pm2_5"),
        "pm10": components.get("pm10"),
        "no2": components.get("no2"),
        "so2": components.get("so2"),
        "co": components.get("co"),
        "o3": components.get("o3"),
    }

# ===============================
# FETCH FROM IQAIR
# ===============================
def fetch_iqair():
    """Fetch AQI and weather data from IQAir"""
    url = f"https://api.airvisual.com/v2/city?city={CITY}&state={STATE}&country={COUNTRY}&key={IQAIR_KEY}"
    response = requests.get(url)
    data = response.json()

    if data.get("status") == "success":
        pollution = data["data"]["current"]["pollution"]
        weather = data["data"]["current"]["weather"]
        return {
            "aqi_iqair": pollution.get("aqius"),
            "main_pollutant": pollution.get("mainus"),
            "temperature": weather.get("tp"),
            "humidity": weather.get("hu"),
            "wind_speed": weather.get("ws"),
        }
    else:
        print("⚠️ IQAir data unavailable:", data)
        return None

# ===============================
# COMBINE AND SAVE
# ===============================
def fetch_combined():
    """Fetch data from both APIs and combine"""
    print("🔄 Fetching combined air quality data...")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    openweather = fetch_openweather()
    iqair = fetch_iqair()

    if iqair:
        combined_data = {"datetime": timestamp, **openweather, **iqair}
        df = pd.DataFrame([combined_data])
        df.to_csv("backend/combined_data.csv", mode="a", index=False, header=False)
        print("✅ Combined data saved at", timestamp)
    else:
        print("❌ Skipped saving due to missing IQAir data")

if __name__ == "__main__":
    fetch_combined()
