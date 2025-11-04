"""Main entry point for the AQI Prediction System"""

import schedule
import time
from datetime import datetime
from api_handlers import CPCBHandler, OpenWeatherHandler, IQAirHandler
from database.db_operations import DatabaseOperations
from config.settings import CITIES, PRIORITY_CITIES, EXTENDED_CITIES, PARALLEL_WORKERS
from config.logging_config import setup_logger, get_city_logger, log_error
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import os
import sys

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
        Collect data from ALL 56 cities in parallel
        Priority cities use CPCB + IQAir + OpenWeather
        Extended cities use OpenWeather only
        """
        logger.info(f"Starting parallel data collection for {len(self.cities)} Indian cities...")
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=PARALLEL_WORKERS) as executor:
            # Create dictionaries to track futures and their metadata
            futures_dict = {}
            
            # Submit priority cities (use all 3 APIs)
            logger.info(f"Submitting {len(self.priority_cities)} priority cities...")
            for city in self.priority_cities:
                future = executor.submit(self.collect_priority_city_data, city)
                futures_dict[future] = (city, 'priority')
            
            # Submit extended cities (use OpenWeather only)
            logger.info(f"Submitting {len(self.extended_cities)} extended cities...")
            for city in self.extended_cities:
                future = executor.submit(self.collect_extended_city_data, city)
                futures_dict[future] = (city, 'extended')
            
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
                        city_logger.info(f"✓ Collection completed ({city_type}) [{completed}/{len(self.cities)}]")
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
        logger.info(f"  Successful: {completed}/{len(self.cities)} cities")
        logger.info(f"  Failed: {failed}/{len(self.cities)} cities")
        logger.info(f"  Time taken: {elapsed_time:.2f} seconds")
        logger.info(f"  Avg time per city: {elapsed_time/len(self.cities):.2f} seconds")
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
                    city_logger = get_city_logger('main', city)
                    city_logger.debug("IQAir data collected and stored")
                    data_collected = True
            except Exception as e:
                city_logger = get_city_logger('main', city)
                city_logger.warning(f"IQAir data collection failed: {str(e)}")
            
            # 3. OpenWeather (always available)
            try:
                coords = self.openweather.CITY_COORDINATES.get(city)
                if coords:
                    city_logger = get_city_logger('main', city)
                    
                    # Weather data
                    weather_data = self.openweather.fetch_weather_data(city)
                    if weather_data:
                        with self.lock:
                            self.db.insert_weather_data(
                                city, weather_data['timestamp'], weather_data
                            )
                        city_logger.debug("OpenWeather weather data collected and stored")
                        data_collected = True
                    
                    # Pollution data
                    pollution_data = self.openweather.fetch_air_pollution_data(
                        coords[0], coords[1]
                    )
                    if pollution_data:
                        with self.lock:
                            self.db.insert_pollution_data(
                                city, pollution_data['timestamp'], 
                                pollution_data, 'OpenWeather'
                            )
                        city_logger.debug("OpenWeather pollution data collected and stored")
                        data_collected = True
            except Exception as e:
                logger.debug(f"  OpenWeather failed for {city}: {str(e)}")
            
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
            
            coords = self.openweather.CITY_COORDINATES.get(city)
            if coords:
                # Weather data
                weather_data = self.openweather.fetch_weather_data(city)
                if weather_data:
                    with self.lock:
                        self.db.insert_weather_data(
                            city, weather_data['timestamp'], weather_data
                        )
                    data_collected = True
                
                # Pollution data
                pollution_data = self.openweather.fetch_air_pollution_data(
                    coords[0], coords[1]
                )
                if pollution_data:
                    with self.lock:
                        self.db.insert_pollution_data(
                            city, pollution_data['timestamp'], 
                            pollution_data, 'OpenWeather'
                        )
                    data_collected = True
            
            return data_collected
        
        except Exception as e:
            logger.error(f"Error collecting extended data for {city}: {str(e)}")
            return False
    
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