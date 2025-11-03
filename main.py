"""Main entry point for the AQI Prediction System"""

import schedule
import time
from datetime import datetime
from api_handlers import CPCBHandler, OpenWeatherHandler, IQAirHandler
from database.db_operations import DatabaseOperations
from config.settings import CITIES, PRIORITY_CITIES, EXTENDED_CITIES, PARALLEL_WORKERS
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
            futures = []
            
            # Submit priority cities (use all 3 APIs)
            logger.info(f"Submitting {len(self.priority_cities)} priority cities...")
            for city in self.priority_cities:
                future = executor.submit(self.collect_priority_city_data, city)
                futures.append((city, future, 'priority'))
            
            # Submit extended cities (use OpenWeather only)
            logger.info(f"Submitting {len(self.extended_cities)} extended cities...")
            for city in self.extended_cities:
                future = executor.submit(self.collect_extended_city_data, city)
                futures.append((city, future, 'extended'))
            
            # Wait for all to complete
            completed = 0
            failed = 0
            results = {'success': [], 'failed': []}
            
            for city, future, city_type in as_completed(futures):
                try:
                    result = future.result()
                    if result:
                        completed += 1
                        results['success'].append(city)
                        logger.info(f"✓ {city} ({city_type}): Completed [{completed}/{len(self.cities)}]")
                    else:
                        failed += 1
                        results['failed'].append(city)
                        logger.warning(f"✗ {city}: No data collected")
                except Exception as e:
                    failed += 1
                    results['failed'].append(city)
                    logger.error(f"✗ {city}: Error - {str(e)}")
        
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
                    logger.debug(f"  CPCB data: {city}")
                    data_collected = True
            except Exception as e:
                logger.debug(f"  CPCB failed for {city}: {str(e)}")
            
            # 2. IQAir (if available)
            try:
                iqair_data = self.iqair.fetch_aqi_data(city)
                if iqair_data:
                    with self.lock:
                        self.db.insert_pollution_data(
                            city, iqair_data['timestamp'], iqair_data, 'IQAir'
                        )
                    logger.debug(f"  IQAir data: {city}")
                    data_collected = True
            except Exception as e:
                logger.debug(f"  IQAir failed for {city}: {str(e)}")
            
            # 3. OpenWeather (always available)
            try:
                coords = self.openweather.CITY_COORDINATES.get(city)
                if coords:
                    # Weather data
                    weather_data = self.openweather.fetch_weather_data(city)
                    if weather_data:
                        with self.lock:
                            self.db.insert_weather_data(
                                city, weather_data['timestamp'], weather_data
                            )
                        logger.debug(f"  OpenWeather weather: {city}")
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
                        logger.debug(f"  OpenWeather pollution: {city}")
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
    
    # Run first collection immediately
    logger.info("Running initial data collection...")
    pipeline.collect_data_all_cities_parallel()
    
    # Schedule for hourly collection
    logger.info("Scheduling data collection...")
    pipeline.schedule_collection()