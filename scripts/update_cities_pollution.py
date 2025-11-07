import logging
import os
import sys
from datetime import datetime

# Ensure project root is on sys.path
CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from api_handlers.openweather_handler import OpenWeatherHandler
from database.db_operations import DatabaseOperations

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

TARGET_CITIES = [
    'Aligarh', 'Allahabad', 'Alwar', 'Bareilly', 'Bharatpur', 'Bhiwadi', 'Bhiwani',
    'Dhanbad', 'Faridabad', 'Greater Noida', 'Gurgaon', 'Howrah', 'Jalandhar',
    'Mathura', 'Meerut', 'Moradabad', 'Navi Mumbai', 'Panipat', 'Pimpri-Chinchwad',
    'Rewari', 'Rohtak', 'Solapur', 'Sonipat', 'Srinagar', 'Thiruvananthapuram', 'Warangal'
]

def main():
    db = DatabaseOperations()
    ow = OpenWeatherHandler()

    updated = 0
    skipped = []

    logger.info(f"Updating pollution data for {len(TARGET_CITIES)} target cities...")

    for city in TARGET_CITIES:
        coords = ow.CITY_COORDINATES.get(city)
        if not coords:
            logger.warning(f"No coordinates for {city}; skipping")
            skipped.append(city)
            continue
        try:
            pollution = ow.fetch_air_pollution_data(coords[0], coords[1])
            if not pollution:
                logger.warning(f"No pollution data for {city}")
                continue
            db.insert_pollution_data(
                city,
                pollution.get('timestamp', datetime.now()),
                pollution,
                'OpenWeather'
            )
            updated += 1
            logger.info(f"  ✅ Updated {city} - AQI: {pollution.get('aqi_value')}")
        except Exception as e:
            logger.error(f"Failed to update {city}: {e}")

    logger.info(f"Done. Updated {updated} cities. Skipped (no coords): {skipped}")

if __name__ == '__main__':
    main()
