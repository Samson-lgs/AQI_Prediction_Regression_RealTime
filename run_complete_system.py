"""
Complete AQI System Runner
Runs all components in sequence: DB setup, data collection, model training, and server launch
"""

import sys
import os
import time
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def print_banner(text):
    """Print a formatted banner"""
    print("\n" + "="*80)
    print(f"  {text}")
    print("="*80 + "\n")

def step_1_database_setup():
    """Initialize database and create tables"""
    print_banner("STEP 1: DATABASE SETUP")
    
    try:
        from database.db_operations import DatabaseOperations
        
        logger.info("Creating database tables...")
        db = DatabaseOperations()
        db.create_tables()
        logger.info("✅ Database tables created successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Database setup failed: {str(e)}")
        return False

def step_2_collect_data():
    """Collect data from all APIs"""
    print_banner("STEP 2: DATA COLLECTION")
    
    try:
        from api_handlers.openweather_handler import OpenWeatherHandler
        from api_handlers.iqair_handler import IQAirHandler
        from database.db_operations import DatabaseOperations
        from datetime import datetime
        
        db = DatabaseOperations()
        openweather = OpenWeatherHandler()
        iqair = IQAirHandler()
        
        # Get all cities from OpenWeather handler
        all_cities = list(openweather.CITY_COORDINATES.keys())
        
        collected = 0
        
        logger.info(f"Collecting data for {len(all_cities)} cities...")
        
        for city in all_cities:
            logger.info(f"Fetching data for {city}...")
            
            # Try OpenWeather (most reliable)
            try:
                # Fetch weather data
                ow_data = openweather.fetch_weather_data(city)
                if ow_data and isinstance(ow_data, dict):
                    # Insert weather data
                    if 'temperature' in ow_data:
                        weather = {
                            'temperature': ow_data.get('temperature'),
                            'humidity': ow_data.get('humidity'),
                            'wind_speed': ow_data.get('wind_speed'),
                            'atmospheric_pressure': ow_data.get('pressure'),
                            'precipitation': ow_data.get('rain'),
                            'cloudiness': ow_data.get('clouds')
                        }
                        db.insert_weather_data(
                            city,
                            datetime.now(),
                            weather
                        )
                        logger.info(f"  ✅ OpenWeather weather data collected for {city}")
                
                # Fetch pollution data separately
                coords = openweather.CITY_COORDINATES.get(city)
                if not coords and ow_data:
                    coords = (ow_data.get('lat'), ow_data.get('lon'))
                
                if coords:
                    pollution_data = openweather.fetch_air_pollution_data(coords[0], coords[1])
                    if pollution_data and isinstance(pollution_data, dict):
                        db.insert_pollution_data(
                            city,
                            pollution_data.get('timestamp', datetime.now()),
                            pollution_data,
                            'OpenWeather'
                        )
                        collected += 1
                        logger.info(f"  ✅ OpenWeather pollution data collected for {city} - AQI: {pollution_data.get('aqi_value', 'N/A')}")
                else:
                    logger.warning(f"  ⚠️ No coordinates for {city}, skipping pollution data")
                    
            except Exception as e:
                logger.warning(f"  ⚠️ OpenWeather failed for {city}: {str(e)}")
            
            # Try IQAir
            try:
                iq_data = iqair.fetch_aqi_data(city)
                if iq_data and isinstance(iq_data, list):
                    for data_point in iq_data:
                        if isinstance(data_point, dict):
                            db.insert_pollution_data(
                                city,
                                datetime.now(),
                                {
                                    'aqi_value': data_point.get('aqi_value'),
                                    'pm25': data_point.get('pm25'),
                                    'pm10': data_point.get('pm10')
                                },
                                'IQAir'
                            )
                    collected += 1
                    logger.info(f"  ✅ IQAir data collected for {city}")
            except Exception as e:
                logger.warning(f"  ⚠️ IQAir failed for {city}: {str(e)}")
            
            time.sleep(0.5)  # Rate limiting
        
        logger.info(f"✅ Data collection complete: {collected} cities")
        return collected > 0
        
    except Exception as e:
        logger.error(f"❌ Data collection failed: {str(e)}")
        return False

def step_3_export_data():
    """Export collected data to CSV"""
    print_banner("STEP 3: DATA EXPORT")
    
    try:
        # Try multiple import locations to handle different project layouts
        # Attempt multiple import strategies using dynamic import to avoid static linter errors
        import importlib
        DataExporter = None

        # 1) Top-level module
        try:
            module = importlib.import_module('export_data_to_csv')
            DataExporter = getattr(module, 'DataExporter', None)
        except Exception:
            DataExporter = None

        # 2) Common utils subpackage
        if DataExporter is None:
            try:
                module = importlib.import_module('utils.export_data_to_csv')
                DataExporter = getattr(module, 'DataExporter', None)
            except Exception:
                DataExporter = None

        # 3) Package-relative import (when this file is part of a package)
        if DataExporter is None:
            try:
                module = importlib.import_module('.export_data_to_csv', package=__package__)
                DataExporter = getattr(module, 'DataExporter', None)
            except Exception:
                DataExporter = None

        # 4) Fallback: load module file located next to this script
        if DataExporter is None:
            import importlib.util
            module_path = os.path.join(os.path.dirname(__file__), 'export_data_to_csv.py')
            if os.path.isfile(module_path):
                spec = importlib.util.spec_from_file_location("export_data_to_csv", module_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                DataExporter = getattr(module, 'DataExporter', None)

        if DataExporter is None:
            raise ImportError("Could not import DataExporter from export_data_to_csv (tried multiple locations)")

        exporter = DataExporter()
        
        logger.info("Exporting current AQI data...")
        exporter.export_all_current_data()
        
        logger.info("Exporting pollution data...")
        exporter.export_pollution_data(days=30)
        
        logger.info("Exporting combined data...")
        exporter.export_combined_data(days=30)
        
        logger.info("✅ Data export complete")
        return True
        
    except Exception as e:
        logger.error(f"❌ Data export failed: {str(e)}")
        return False

def step_4_start_backend():
    """Start the Flask backend server"""
    print_banner("STEP 4: STARTING BACKEND SERVER")
    
    try:
        logger.info("Starting Flask backend on http://localhost:5000")
        logger.info("Press Ctrl+C to stop the server")
        
        from backend.app import create_app
        
        app = create_app()
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True,
            use_reloader=False
        )
        
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Backend server failed: {str(e)}")
        return False

def run_complete_system():
    """Run the complete AQI system"""
    print_banner("AQI PREDICTION SYSTEM - COMPLETE RUN")
    
    start_time = datetime.now()
    
    # Step 1: Database Setup
    if not step_1_database_setup():
        logger.error("System initialization failed at database setup")
        return False
    
    time.sleep(1)
    
    # Step 2: Data Collection
    if not step_2_collect_data():
        logger.warning("Data collection had issues, but continuing...")
    
    time.sleep(1)
    
    # Step 3: Export Data
    if not step_3_export_data():
        logger.warning("Data export had issues, but continuing...")
    
    time.sleep(1)
    
    # Step 4: Start Backend
    print_banner("SYSTEM READY")
    logger.info(f"Total setup time: {(datetime.now() - start_time).seconds} seconds")
    logger.info("Starting backend server...")
    
    step_4_start_backend()

def quick_data_refresh():
    """Quick refresh: collect data and export"""
    print_banner("QUICK DATA REFRESH")
    
    if step_2_collect_data():
        step_3_export_data()
        logger.info("✅ Data refresh complete!")
    else:
        logger.error("❌ Data refresh failed!")

def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'db':
            step_1_database_setup()
        elif command == 'collect':
            step_2_collect_data()
        elif command == 'export':
            step_3_export_data()
        elif command == 'server':
            step_4_start_backend()
        elif command == 'refresh':
            quick_data_refresh()
        else:
            print("Usage:")
            print("  python run_complete_system.py          # Run complete system")
            print("  python run_complete_system.py db       # Setup database only")
            print("  python run_complete_system.py collect  # Collect data only")
            print("  python run_complete_system.py export   # Export data only")
            print("  python run_complete_system.py server   # Start server only")
            print("  python run_complete_system.py refresh  # Quick data refresh")
    else:
        run_complete_system()

if __name__ == "__main__":
    main()
