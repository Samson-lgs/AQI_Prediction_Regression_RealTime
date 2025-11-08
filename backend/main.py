"""Main entry point for the AQI Prediction System"""

import sys
import os
# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import schedule
import time
from datetime import datetime
from api_handlers.cpcb_handler import CPCBHandler
from api_handlers.openweather_handler import OpenWeatherHandler
from api_handlers.iqair_handler import IQAirHandler
from database.db_operations import DatabaseOperations
from config.settings import CITIES, PRIORITY_CITIES, EXTENDED_CITIES, PARALLEL_WORKERS
from config.logging_config import setup_logger, get_city_logger, log_error
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import os
import sys
from datetime import timedelta

# Email functionality disabled (email_utils module removed)
send_email = None

# Websocket handler doesn't exist yet - stub it out
def broadcast_alert(*args, **kwargs):
    """Placeholder for future websocket alert broadcasting"""
    pass

# Set up main logger
logger = setup_logger(
    'main',
    os.path.join('logs', 'main.log')
)

class DataCollectionPipeline:
    def __init__(self):
        self.cpcb = CPCBHandler()
        self.openweather = OpenWeatherHandler()
        self.iqair = IQAirHandler()
        self.db = DatabaseOperations()
        self.cities = CITIES
        self.priority_cities = PRIORITY_CITIES
        self.extended_cities = EXTENDED_CITIES
        self.lock = threading.Lock()
        
        logger.info(f"Pipeline initialized:")
        logger.info(f"  Total cities: {len(self.cities)}")
        logger.info(f"  Priority cities (3 APIs): {len(self.priority_cities)}")
        logger.info(f"  Extended cities (1 API): {len(self.extended_cities)}")
    
    def collect_data_all_cities_parallel(self):
        """
        Collect data in parallel for the union of CITIES and EXTENDED_CITIES.
        Attempts CPCB + IQAir + OpenWeather for every city (priority gating disabled).
        """
        # Build unique list of cities
        unique_cities = sorted(list(set(self.cities) | set(self.extended_cities)))
        logger.info(f"Starting parallel data collection for {len(unique_cities)} Indian cities (all sources)...")
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=PARALLEL_WORKERS) as executor:
            # Create dictionaries to track futures and their metadata
            futures_dict = {}
            # Submit all cities (attempt all sources per city)
            for city in unique_cities:
                future = executor.submit(self.collect_priority_city_data, city)
                futures_dict[future] = (city, 'all')
            
            # Wait for all to complete
            completed = 0
            failed = 0
            results = {'success': [], 'failed': []}
            
            for future in as_completed(futures_dict.keys()):
                city, city_type = futures_dict[future]
                try:
                    result = future.result()
                    if result:
                        completed += 1
                        results['success'].append(city)
                        city_logger = get_city_logger('main', city)
                        city_logger.info(f"✓ Collection completed ({city_type}) [{completed}/{len(unique_cities)}]")
                    else:
                        failed += 1
                        results['failed'].append(city)
                        city_logger = get_city_logger('main', city)
                        city_logger.warning(f"✗ No data collected")
                except Exception as e:
                    failed += 1
                    results['failed'].append(city)
                    log_error('main', f"✗ {city}: Collection failed", exc_info=e)
        
        elapsed_time = time.time() - start_time
        logger.info(f"\n{'='*60}")
        logger.info(f"Parallel collection completed for ALL CITIES:")
        logger.info(f"  Successful: {completed}/{len(unique_cities)} cities")
        logger.info(f"  Failed: {failed}/{len(unique_cities)} cities")
        logger.info(f"  Time taken: {elapsed_time:.2f} seconds")
        logger.info(f"  Avg time per city: {elapsed_time/len(unique_cities):.2f} seconds")
        logger.info(f"{'='*60}\n")
        
        return results
    
    def collect_priority_city_data(self, city):
        """
        Collect data from all 3 sources for priority cities
        CPCB + IQAir + OpenWeather
        """
        try:
            data_collected = False
            
            # 1. CPCB (if available)
            try:
                cpcb_data = self.cpcb.fetch_aqi_data(city)
                if cpcb_data:
                    for data in cpcb_data:
                        with self.lock:
                            self.db.insert_pollution_data(
                                city, data['timestamp'], data, 'CPCB'
                            )
                            # Evaluate alerts
                            self._process_alerts(city, data)
                    city_logger = get_city_logger('main', city)
                    city_logger.debug("CPCB data collected and stored")
                    data_collected = True
            except Exception as e:
                city_logger = get_city_logger('main', city)
                city_logger.warning(f"CPCB data collection failed: {str(e)}")
            
            # 2. IQAir (if available)
            try:
                iqair_data = self.iqair.fetch_aqi_data(city)
                if iqair_data:
                    with self.lock:
                        self.db.insert_pollution_data(
                            city, iqair_data['timestamp'], iqair_data, 'IQAir'
                        )
                        # Evaluate alerts
                        self._process_alerts(city, iqair_data)
                    city_logger = get_city_logger('main', city)
                    city_logger.debug("IQAir data collected and stored")
                    data_collected = True
            except Exception as e:
                city_logger = get_city_logger('main', city)
                city_logger.warning(f"IQAir data collection failed: {str(e)}")
            
            # 3. OpenWeather (always available)
            try:
                city_logger = get_city_logger('main', city)

                # Weather data (also gives us coordinates when city not in static map)
                weather_data = self.openweather.fetch_weather_data(city)
                if weather_data:
                    with self.lock:
                        self.db.insert_weather_data(
                            city, weather_data['timestamp'], weather_data
                        )
                    city_logger.debug("OpenWeather weather data collected and stored")
                    data_collected = True
                
                logger.info(f"  DEBUG: About to fetch pollution for {city}")

                # Determine coordinates: prefer static map, else derive from weather response
                coords = self.openweather.CITY_COORDINATES.get(city)
                if not coords and weather_data and weather_data.get('lat') and weather_data.get('lon'):
                    coords = (weather_data['lat'], weather_data['lon'])
                # Fallback: geocode if still no coords
                if not coords:
                    gc = self.openweather.geocode_city(city)
                    if gc:
                        coords = gc

                # Pollution data if we have coordinates
                if coords:
                    logger.info(f"Fetching pollution data for {city} at coords {coords}")
                    pollution_data = self.openweather.fetch_air_pollution_data(
                        coords[0], coords[1]
                    )
                    if pollution_data:
                        with self.lock:
                            self.db.insert_pollution_data(
                                city, pollution_data['timestamp'], 
                                pollution_data, 'OpenWeather'
                            )
                            # Evaluate alerts
                            self._process_alerts(city, pollution_data)
                        logger.info(f"  ✅ OpenWeather pollution data collected for {city} - AQI: {pollution_data.get('aqi_value', 'N/A')}")
                        data_collected = True
                    else:
                        logger.warning(f"  ⚠️ Pollution data fetch returned None for {city}")
                else:
                    logger.warning(f"  ⚠️  No coordinates found for {city}, skipping pollution data")
            except Exception as e:
                logger.error(f"  ❌ OpenWeather pollution fetch failed for {city}: {str(e)}")
            
            return data_collected
        
        except Exception as e:
            logger.error(f"Error collecting priority data for {city}: {str(e)}")
            return False
    
    def collect_extended_city_data(self, city):
        """
        Collect data from OpenWeather only for extended cities
        """
        try:
            data_collected = False
            
            # Weather data (also provides coordinates for cities missing in static map)
            weather_data = self.openweather.fetch_weather_data(city)
            if weather_data:
                with self.lock:
                    self.db.insert_weather_data(
                        city, weather_data['timestamp'], weather_data
                    )
                data_collected = True

            # Determine coordinates: static map first, else from weather response
            coords = self.openweather.CITY_COORDINATES.get(city)
            if not coords and weather_data and weather_data.get('lat') and weather_data.get('lon'):
                coords = (weather_data['lat'], weather_data['lon'])
            # Fallback: geocode if still no coords
            if not coords:
                gc = self.openweather.geocode_city(city)
                if gc:
                    coords = gc

            # Pollution data
            if coords:
                pollution_data = self.openweather.fetch_air_pollution_data(
                    coords[0], coords[1]
                )
                if pollution_data:
                    with self.lock:
                        self.db.insert_pollution_data(
                            city, pollution_data['timestamp'], 
                            pollution_data, 'OpenWeather'
                        )
                        # Evaluate alerts
                        self._process_alerts(city, pollution_data)
                    data_collected = True
            
            return data_collected
        
        except Exception as e:
            logger.error(f"Error collecting extended data for {city}: {str(e)}")
            return False

    def _process_alerts(self, city, pollution_data):
        """Check and trigger alerts for a given city's latest pollution data."""
        try:
            current_aqi = pollution_data.get('aqi_value')
            if current_aqi is None:
                return

            active_alerts = self.db.get_active_alerts(city) or []
            if not active_alerts:
                return

            now = datetime.now()
            for alert in active_alerts:
                threshold = int(alert.get('threshold') or 0)
                if current_aqi >= threshold:
                    last_notified = alert.get('last_notified')
                    # Throttle: notify again only if > 2 hours since last notification
                    should_notify = True
                    if last_notified:
                        try:
                            if isinstance(last_notified, str):
                                # Some drivers may return string
                                last_dt = datetime.fromisoformat(last_notified)
                            else:
                                last_dt = last_notified
                            if now - last_dt < timedelta(hours=2):
                                should_notify = False
                        except Exception:
                            pass

                    if not should_notify:
                        continue

                    # Compose message
                    severity = 'hazardous' if current_aqi >= 300 else ('very_unhealthy' if current_aqi >= 200 else ('unhealthy' if current_aqi >= 150 else 'moderate'))
                    message = f"AQI alert for {city}: current AQI {current_aqi} crossed threshold {threshold}."

                    # Email if configured
                    if alert.get('alert_type') == 'email' and send_email:
                        try:
                            send_email(
                                to_address=alert.get('contact'),
                                subject=f"AQI Alert: {city} AQI {current_aqi}",
                                body=message
                            )
                        except Exception as e:
                            logger.warning(f"Failed to send email alert: {e}")

                    # Broadcast via websocket (no-op if not initialized)
                    try:
                        broadcast_alert(city, {
                            'alert_type': alert.get('alert_type'),
                            'current_aqi': current_aqi,
                            'threshold': threshold,
                            'message': message,
                            'severity': severity
                        })
                    except Exception:
                        pass

                    # Mark as notified
                    try:
                        self.db.set_alert_notified(alert.get('id'))
                    except Exception as e:
                        logger.debug(f"Failed to update alert notified timestamp: {e}")
        except Exception as e:
            logger.debug(f"Alert processing failed for {city}: {e}")
    
    def schedule_collection(self):
        """Schedule hourly data collection for all cities"""
        schedule.every(1).hours.do(self.collect_data_all_cities_parallel)
        
        logger.info("Data collection scheduler started")
        logger.info(f"Collection will run every 1 hour for all {len(self.cities)} cities")
        
        while True:
            schedule.run_pending()
            time.sleep(60)

if __name__ == "__main__":
    pipeline = DataCollectionPipeline()

    # Create database tables
    logger.info("Creating database tables...")
    pipeline.db.create_tables()

    # One-shot mode for CI/scheduled runs (e.g., GitHub Actions)
    run_once = os.getenv("RUN_ONCE") == "1" or "--once" in sys.argv
    if run_once:
        logger.info("RUN_ONCE enabled; collecting data once and exiting...")
        pipeline.collect_data_all_cities_parallel()
        logger.info("One-shot collection complete. Exiting.")
        sys.exit(0)

    # Default behavior: initial collection then scheduler loop
    logger.info("Running initial data collection...")
    pipeline.collect_data_all_cities_parallel()

    logger.info("Scheduling data collection...")
    pipeline.schedule_collection()