from database.db_config import DatabaseManager
import json
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseOperations:
    def __init__(self):
        self.db = DatabaseManager()
    
    def create_tables(self):
        """Create tables optimized for multiple cities"""
        
        # Create pollution data table with city partitioning indexes
        pollution_table = """
        CREATE TABLE IF NOT EXISTS pollution_data (
            id SERIAL PRIMARY KEY,
            city VARCHAR(100) NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            pm25 FLOAT,
            pm10 FLOAT,
            no2 FLOAT,
            so2 FLOAT,
            co FLOAT,
            o3 FLOAT,
            aqi_value INT,
            data_source VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(city, timestamp, data_source)
        );
        
        -- Indexes for fast querying across all cities
        CREATE INDEX IF NOT EXISTS idx_pollution_city_time ON pollution_data(city, timestamp DESC);
        CREATE INDEX IF NOT EXISTS idx_pollution_timestamp ON pollution_data(timestamp DESC);
        CREATE INDEX IF NOT EXISTS idx_pollution_city ON pollution_data(city);
        CREATE INDEX IF NOT EXISTS idx_pollution_aqi ON pollution_data(aqi_value);
        CREATE INDEX IF NOT EXISTS idx_pollution_pm25 ON pollution_data(pm25);
        """
        
        # Create weather data table
        weather_table = """
        CREATE TABLE IF NOT EXISTS weather_data (
            id SERIAL PRIMARY KEY,
            city VARCHAR(100) NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            temperature FLOAT,
            humidity FLOAT,
            wind_speed FLOAT,
            atmospheric_pressure FLOAT,
            precipitation FLOAT,
            cloudiness FLOAT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(city, timestamp)
        );
        
        CREATE INDEX IF NOT EXISTS idx_weather_city_time ON weather_data(city, timestamp DESC);
        CREATE INDEX IF NOT EXISTS idx_weather_city ON weather_data(city);
        CREATE INDEX IF NOT EXISTS idx_weather_timestamp ON weather_data(timestamp DESC);
        """
        
        # Create predictions table
        predictions_table = """
        CREATE TABLE IF NOT EXISTS predictions (
            id SERIAL PRIMARY KEY,
            city VARCHAR(100) NOT NULL,
            forecast_timestamp TIMESTAMP NOT NULL,
            predicted_aqi INT,
            confidence_interval FLOAT,
            model_used VARCHAR(50),
            actual_aqi INT,
            mape_error FLOAT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(city, forecast_timestamp, model_used)
        );
        
        CREATE INDEX IF NOT EXISTS idx_predictions_city_time ON predictions(city, forecast_timestamp DESC);
        CREATE INDEX IF NOT EXISTS idx_predictions_city ON predictions(city);
        CREATE INDEX IF NOT EXISTS idx_predictions_model ON predictions(model_used);
        """
        
        # Create model performance table
        performance_table = """
        CREATE TABLE IF NOT EXISTS model_performance (
            id SERIAL PRIMARY KEY,
            city VARCHAR(100) NOT NULL,
            model_name VARCHAR(50) NOT NULL,
            metric_date DATE NOT NULL,
            r2_score FLOAT,
            rmse FLOAT,
            mae FLOAT,
            mape FLOAT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(city, model_name, metric_date)
        );
        
        CREATE INDEX IF NOT EXISTS idx_perf_city_model ON model_performance(city, model_name);
        CREATE INDEX IF NOT EXISTS idx_perf_date ON model_performance(metric_date DESC);
        """
        
        # Create city statistics table (new for multi-city analytics)
        city_stats_table = """
        CREATE TABLE IF NOT EXISTS city_statistics (
            id SERIAL PRIMARY KEY,
            city VARCHAR(100) NOT NULL,
            metric_date DATE NOT NULL,
            avg_aqi FLOAT,
            max_aqi INT,
            min_aqi INT,
            avg_pm25 FLOAT,
            max_pm25 FLOAT,
            data_points INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(city, metric_date)
        );
        
        CREATE INDEX IF NOT EXISTS idx_stats_city_date ON city_statistics(city, metric_date DESC);
        """
        
        # Create region statistics table (new for regional analysis)
        region_stats_table = """
        CREATE TABLE IF NOT EXISTS region_statistics (
            id SERIAL PRIMARY KEY,
            region VARCHAR(50) NOT NULL,
            metric_date DATE NOT NULL,
            avg_aqi FLOAT,
            max_aqi INT,
            min_aqi INT,
            cities_count INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(region, metric_date)
        );
        
        CREATE INDEX IF NOT EXISTS idx_region_stats_date ON region_statistics(region, metric_date DESC);
        """
        
        for table_query in [pollution_table, weather_table, predictions_table, 
                            performance_table, city_stats_table, region_stats_table]:
            self.db.execute_query(table_query)
        
        # Ensure alerts table exists
        try:
            self.create_alerts_table()
        except Exception as e:
            logger.warning(f"Could not create alerts table: {e}")

        logger.info("All tables created successfully for 97 cities!")

    # -------------------------------
    # Alerts table and operations
    # -------------------------------
    def create_alerts_table(self):
        """Create alerts table if it doesn't exist"""
        table = """
        CREATE TABLE IF NOT EXISTS alerts (
            id SERIAL PRIMARY KEY,
            city VARCHAR(100) NOT NULL,
            threshold INT NOT NULL,
            alert_type VARCHAR(20) NOT NULL, -- email, sms, webhook
            contact VARCHAR(255) NOT NULL,   -- email address / phone / url
            active BOOLEAN DEFAULT TRUE,
            last_notified TIMESTAMP NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_alerts_city ON alerts(city);
        CREATE INDEX IF NOT EXISTS idx_alerts_active ON alerts(active);
        """
        self.db.execute_query(table)
        logger.info("Alerts table ensured")

    def add_alert(self, city: str, threshold: int, alert_type: str, contact: str):
        """Insert a new alert and return its id"""
        query = """
        INSERT INTO alerts (city, threshold, alert_type, contact)
        VALUES (%s, %s, %s, %s)
        RETURNING id;
        """
        res = self.db.execute_query(query, (city, threshold, alert_type, contact))
        return res[0][0] if res else None

    def list_alerts(self, city: str):
        """List alerts for a city"""
        query = """
        SELECT id, city, threshold, alert_type, contact, active, last_notified, created_at
        FROM alerts
        WHERE city = %s
        ORDER BY created_at DESC;
        """
        return self.db.execute_query_dicts(query, (city,))

    def get_active_alerts(self, city: str):
        """Get active alerts for a city"""
        query = """
        SELECT id, city, threshold, alert_type, contact, last_notified
        FROM alerts
        WHERE city = %s AND active = TRUE;
        """
        return self.db.execute_query_dicts(query, (city,))

    def set_alert_notified(self, alert_id: int):
        """Update last_notified timestamp"""
        query = """
        UPDATE alerts SET last_notified = NOW() WHERE id = %s;
        """
        self.db.execute_query(query, (alert_id,))

    def deactivate_alert(self, alert_id: int):
        """Deactivate an alert"""
        query = """
        UPDATE alerts SET active = FALSE WHERE id = %s;
        """
        self.db.execute_query(query, (alert_id,))
    
    def insert_pollution_data(self, city, timestamp, pollutants, data_source):
        """Insert pollution data for a city"""
        query = """
        INSERT INTO pollution_data 
        (city, timestamp, pm25, pm10, no2, so2, co, o3, aqi_value, data_source)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (city, timestamp, data_source) DO UPDATE
        SET pm25=EXCLUDED.pm25, pm10=EXCLUDED.pm10, no2=EXCLUDED.no2,
            so2=EXCLUDED.so2, co=EXCLUDED.co, o3=EXCLUDED.o3,
            aqi_value=EXCLUDED.aqi_value;
        """
        params = (city, timestamp, 
                 pollutants.get('pm25'), pollutants.get('pm10'),
                 pollutants.get('no2'), pollutants.get('so2'),
                 pollutants.get('co'), pollutants.get('o3'),
                 pollutants.get('aqi_value'), data_source)
        
        return self.db.execute_query(query, params)
    
    def insert_weather_data(self, city, timestamp, weather):
        """Insert weather data for a city"""
        query = """
        INSERT INTO weather_data 
        (city, timestamp, temperature, humidity, wind_speed, atmospheric_pressure, precipitation, cloudiness)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (city, timestamp) DO UPDATE
        SET temperature=EXCLUDED.temperature, humidity=EXCLUDED.humidity,
            wind_speed=EXCLUDED.wind_speed, atmospheric_pressure=EXCLUDED.atmospheric_pressure,
            precipitation=EXCLUDED.precipitation, cloudiness=EXCLUDED.cloudiness;
        """
        params = (city, timestamp, 
                 weather.get('temperature'), weather.get('humidity'),
                 weather.get('wind_speed'), weather.get('atmospheric_pressure'),
                 weather.get('precipitation'), weather.get('cloudiness'))
        
        return self.db.execute_query(query, params)
    
    def get_pollution_data(self, city, start_date, end_date):
        """Get pollution data for a city in date range as list of dicts"""
        query = """
        SELECT id, city, timestamp, pm25, pm10, no2, so2, co, o3, aqi_value, data_source, created_at
        FROM pollution_data 
        WHERE city = %s AND timestamp BETWEEN %s AND %s
        ORDER BY timestamp DESC;
        """
        return self.db.execute_query_dicts(query, (city, start_date, end_date))
    
    def get_all_cities_current_data(self):
        """Get current data for ALL cities (latest reading per city)"""
        query = """
        SELECT DISTINCT ON (city) 
            city, timestamp, aqi_value, pm25, pm10, no2, so2, co, o3, data_source
        FROM pollution_data
        ORDER BY city, timestamp DESC;
        """
        return self.db.execute_query(query)
    
    def get_regional_data(self, region):
        """Get data for all cities in a region"""
        query = """
        SELECT pd.* FROM pollution_data pd
        WHERE pd.city IN (
            SELECT city FROM city_statistics 
            WHERE region = %s
        )
        ORDER BY pd.timestamp DESC
        LIMIT 1000;
        """
        return self.db.execute_query(query, (region,))
    
    def calculate_city_statistics(self, city, date):
        """Calculate daily statistics for a city"""
        query = """
        INSERT INTO city_statistics 
        (city, metric_date, avg_aqi, max_aqi, min_aqi, avg_pm25, max_pm25, data_points)
        SELECT 
            %s,
            DATE(%s),
            AVG(aqi_value),
            MAX(aqi_value),
            MIN(aqi_value),
            AVG(pm25),
            MAX(pm25),
            COUNT(*)
        FROM pollution_data
        WHERE city = %s AND DATE(timestamp) = DATE(%s)
        ON CONFLICT (city, metric_date) DO UPDATE
        SET avg_aqi=EXCLUDED.avg_aqi, max_aqi=EXCLUDED.max_aqi, 
            min_aqi=EXCLUDED.min_aqi, avg_pm25=EXCLUDED.avg_pm25, 
            max_pm25=EXCLUDED.max_pm25, data_points=EXCLUDED.data_points;
        """
        params = (city, date, city, date)
        return self.db.execute_query(query, params)
    
    def bulk_insert_predictions(self, predictions_list):
        """Insert multiple predictions efficiently"""
        query = """
        INSERT INTO predictions 
        (city, forecast_timestamp, predicted_aqi, confidence_interval, model_used)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (city, forecast_timestamp, model_used) DO UPDATE
        SET predicted_aqi=EXCLUDED.predicted_aqi, 
            confidence_interval=EXCLUDED.confidence_interval;
        """
        
        for pred in predictions_list:
            params = (pred['city'], pred['timestamp'], pred['aqi'], 
                     pred['confidence'], pred['model'])
            self.db.execute_query(query, params)
        
        logger.info(f"Inserted {len(predictions_list)} predictions for all cities")
    
    def get_model_performance(self, city: str, model_name: str = None, days: int = 30):
        """Fetch model performance metrics for a city, optionally filtered by model_name, for recent days."""
        if model_name:
            query = """
            SELECT city, model_name, metric_date, r2_score, rmse, mae, mape
            FROM model_performance
            WHERE city = %s AND model_name = %s
                AND metric_date >= CURRENT_DATE - %s
            ORDER BY metric_date DESC;
            """
            params = (city, model_name, days)
        else:
            query = """
            SELECT city, model_name, metric_date, r2_score, rmse, mae, mape
            FROM model_performance
            WHERE city = %s
                AND metric_date >= CURRENT_DATE - %s
            ORDER BY metric_date DESC;
            """
            params = (city, days)
        
        return self.db.execute_query_dicts(query, params)
    
    def insert_model_performance(self, city: str, model_name: str, metrics: dict, metric_date=None):
        """Insert or update model performance metrics"""
        if metric_date is None:
            metric_date = datetime.now().date()
        
        query = """
        INSERT INTO model_performance 
        (city, model_name, metric_date, r2_score, rmse, mae, mape)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (city, model_name, metric_date) DO UPDATE
        SET r2_score=EXCLUDED.r2_score, rmse=EXCLUDED.rmse, 
            mae=EXCLUDED.mae, mape=EXCLUDED.mape;
        """
        params = (city, model_name, metric_date, 
                 metrics.get('r2_score'), metrics.get('rmse'),
                 metrics.get('mae'), metrics.get('mape'))
        
        return self.db.execute_query(query, params)