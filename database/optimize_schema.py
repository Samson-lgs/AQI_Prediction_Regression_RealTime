"""
Database Schema Optimization for Time-Series Data
Implements TimescaleDB hypertables, materialized views, and partitioning
"""
import logging
from database.db_config import DatabaseManager
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseOptimizer:
    """Optimize PostgreSQL database for time-series queries"""
    
    def __init__(self):
        self.db = DatabaseManager()
    
    def check_timescaledb_extension(self):
        """Check if TimescaleDB extension is available"""
        try:
            query = "SELECT * FROM pg_extension WHERE extname = 'timescaledb';"
            result = self.db.execute_query(query)
            return len(result) > 0
        except Exception as e:
            logger.error(f"Error checking TimescaleDB: {str(e)}")
            return False
    
    def enable_timescaledb(self):
        """Enable TimescaleDB extension"""
        try:
            query = "CREATE EXTENSION IF NOT EXISTS timescaledb;"
            self.db.execute_query(query)
            logger.info("✓ TimescaleDB extension enabled")
            return True
        except Exception as e:
            logger.warning(f"Could not enable TimescaleDB: {str(e)}")
            logger.info("Continuing with standard PostgreSQL optimizations...")
            return False
    
    def create_hypertables(self):
        """Convert tables to TimescaleDB hypertables"""
        try:
            # Convert pollution_data to hypertable
            hypertable_query = """
            SELECT create_hypertable(
                'pollution_data',
                'timestamp',
                if_not_exists => TRUE,
                chunk_time_interval => INTERVAL '1 day'
            );
            """
            self.db.execute_query(hypertable_query)
            logger.info("✓ pollution_data converted to hypertable")
            
            # Convert weather_data to hypertable
            hypertable_query = """
            SELECT create_hypertable(
                'weather_data',
                'timestamp',
                if_not_exists => TRUE,
                chunk_time_interval => INTERVAL '1 day'
            );
            """
            self.db.execute_query(hypertable_query)
            logger.info("✓ weather_data converted to hypertable")
            
            # Convert predictions to hypertable
            hypertable_query = """
            SELECT create_hypertable(
                'predictions',
                'forecast_timestamp',
                if_not_exists => TRUE,
                chunk_time_interval => INTERVAL '1 week'
            );
            """
            self.db.execute_query(hypertable_query)
            logger.info("✓ predictions converted to hypertable")
            
            return True
        except Exception as e:
            logger.warning(f"Hypertable creation skipped: {str(e)}")
            return False
    
    def create_continuous_aggregates(self):
        """Create continuous aggregates (TimescaleDB materialized views)"""
        try:
            # Hourly aggregates
            hourly_agg = """
            CREATE MATERIALIZED VIEW IF NOT EXISTS pollution_data_hourly
            WITH (timescaledb.continuous) AS
            SELECT 
                city,
                time_bucket('1 hour', timestamp) AS hour,
                AVG(aqi_value) AS avg_aqi,
                MAX(aqi_value) AS max_aqi,
                MIN(aqi_value) AS min_aqi,
                AVG(pm25) AS avg_pm25,
                AVG(pm10) AS avg_pm10,
                COUNT(*) AS data_points
            FROM pollution_data
            GROUP BY city, hour
            WITH NO DATA;
            
            SELECT add_continuous_aggregate_policy('pollution_data_hourly',
                start_offset => INTERVAL '3 hours',
                end_offset => INTERVAL '1 hour',
                schedule_interval => INTERVAL '1 hour',
                if_not_exists => TRUE
            );
            """
            self.db.execute_query(hourly_agg)
            logger.info("✓ Hourly continuous aggregate created")
            
            # Daily aggregates
            daily_agg = """
            CREATE MATERIALIZED VIEW IF NOT EXISTS pollution_data_daily
            WITH (timescaledb.continuous) AS
            SELECT 
                city,
                time_bucket('1 day', timestamp) AS day,
                AVG(aqi_value) AS avg_aqi,
                MAX(aqi_value) AS max_aqi,
                MIN(aqi_value) AS min_aqi,
                AVG(pm25) AS avg_pm25,
                AVG(pm10) AS avg_pm10,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY aqi_value) AS median_aqi,
                COUNT(*) AS data_points
            FROM pollution_data
            GROUP BY city, day
            WITH NO DATA;
            
            SELECT add_continuous_aggregate_policy('pollution_data_daily',
                start_offset => INTERVAL '2 days',
                end_offset => INTERVAL '1 day',
                schedule_interval => INTERVAL '1 day',
                if_not_exists => TRUE
            );
            """
            self.db.execute_query(daily_agg)
            logger.info("✓ Daily continuous aggregate created")
            
            return True
        except Exception as e:
            logger.warning(f"Continuous aggregates creation skipped: {str(e)}")
            return False
    
    def create_materialized_views(self):
        """Create standard materialized views (fallback if TimescaleDB not available)"""
        try:
            # Hourly city statistics
            hourly_stats = """
            CREATE MATERIALIZED VIEW IF NOT EXISTS mv_hourly_city_stats AS
            SELECT 
                city,
                DATE_TRUNC('hour', timestamp) AS hour,
                AVG(aqi_value) AS avg_aqi,
                MAX(aqi_value) AS max_aqi,
                MIN(aqi_value) AS min_aqi,
                AVG(pm25) AS avg_pm25,
                AVG(pm10) AS avg_pm10,
                COUNT(*) AS data_points
            FROM pollution_data
            WHERE timestamp >= NOW() - INTERVAL '30 days'
            GROUP BY city, DATE_TRUNC('hour', timestamp);
            
            CREATE INDEX IF NOT EXISTS idx_mv_hourly_city_hour 
            ON mv_hourly_city_stats(city, hour DESC);
            """
            self.db.execute_query(hourly_stats)
            logger.info("✓ Hourly statistics materialized view created")
            
            # Daily city statistics
            daily_stats = """
            CREATE MATERIALIZED VIEW IF NOT EXISTS mv_daily_city_stats AS
            SELECT 
                city,
                DATE_TRUNC('day', timestamp) AS day,
                AVG(aqi_value) AS avg_aqi,
                MAX(aqi_value) AS max_aqi,
                MIN(aqi_value) AS min_aqi,
                AVG(pm25) AS avg_pm25,
                AVG(pm10) AS avg_pm10,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY aqi_value) AS median_aqi,
                COUNT(*) AS data_points
            FROM pollution_data
            WHERE timestamp >= NOW() - INTERVAL '90 days'
            GROUP BY city, DATE_TRUNC('day', timestamp);
            
            CREATE INDEX IF NOT EXISTS idx_mv_daily_city_day 
            ON mv_daily_city_stats(city, day DESC);
            """
            self.db.execute_query(daily_stats)
            logger.info("✓ Daily statistics materialized view created")
            
            # City comparison view
            comparison_view = """
            CREATE MATERIALIZED VIEW IF NOT EXISTS mv_city_comparison AS
            SELECT 
                city,
                AVG(aqi_value) AS avg_aqi_7d,
                MAX(aqi_value) AS max_aqi_7d,
                MIN(aqi_value) AS min_aqi_7d,
                STDDEV(aqi_value) AS stddev_aqi_7d,
                AVG(pm25) AS avg_pm25_7d,
                COUNT(*) AS data_points_7d,
                MAX(timestamp) AS last_updated
            FROM pollution_data
            WHERE timestamp >= NOW() - INTERVAL '7 days'
            GROUP BY city;
            
            CREATE INDEX IF NOT EXISTS idx_mv_comparison_aqi 
            ON mv_city_comparison(avg_aqi_7d DESC);
            """
            self.db.execute_query(comparison_view)
            logger.info("✓ City comparison materialized view created")
            
            return True
        except Exception as e:
            logger.error(f"Materialized views creation failed: {str(e)}")
            return False
    
    def create_partitions(self):
        """Create table partitions for better query performance"""
        try:
            # Note: Partitioning should be done at table creation time
            # This is a reference for future implementations
            logger.info("Partition creation would be done at table creation time")
            logger.info("Current tables use indexing for optimization")
            return True
        except Exception as e:
            logger.error(f"Partition creation failed: {str(e)}")
            return False
    
    def optimize_indexes(self):
        """Create additional optimized indexes"""
        try:
            # Composite indexes for common queries
            indexes = [
                # Pollution data indexes
                """CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_pollution_city_time_aqi 
                   ON pollution_data(city, timestamp DESC, aqi_value);""",
                
                """CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_pollution_time_city 
                   ON pollution_data(timestamp DESC, city);""",
                
                """CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_pollution_source_time 
                   ON pollution_data(data_source, timestamp DESC);""",
                
                # Weather data indexes
                """CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_weather_city_time_temp 
                   ON weather_data(city, timestamp DESC, temperature);""",
                
                # Predictions indexes
                """CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_predictions_city_forecast_model 
                   ON predictions(city, forecast_timestamp DESC, model_used);""",
                
                """CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_predictions_accuracy 
                   ON predictions(city, mape_error) 
                   WHERE actual_aqi IS NOT NULL;""",
                
                # Model performance indexes
                """CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_perf_city_model_date 
                   ON model_performance(city, model_name, metric_date DESC);""",
                
                """CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_perf_best_models 
                   ON model_performance(r2_score DESC, rmse ASC) 
                   WHERE r2_score IS NOT NULL;""",
            ]
            
            for idx_query in indexes:
                try:
                    self.db.execute_query(idx_query)
                except Exception as idx_error:
                    logger.warning(f"Index creation warning: {str(idx_error)}")
            
            logger.info("✓ Optimized indexes created")
            return True
        except Exception as e:
            logger.error(f"Index optimization failed: {str(e)}")
            return False
    
    def create_retention_policy(self):
        """Create data retention policy (TimescaleDB)"""
        try:
            # Keep raw data for 90 days
            retention_query = """
            SELECT add_retention_policy(
                'pollution_data',
                INTERVAL '90 days',
                if_not_exists => TRUE
            );
            """
            self.db.execute_query(retention_query)
            logger.info("✓ Data retention policy created (90 days)")
            return True
        except Exception as e:
            logger.warning(f"Retention policy creation skipped: {str(e)}")
            return False
    
    def create_compression_policy(self):
        """Enable compression for older data (TimescaleDB)"""
        try:
            # Enable compression on pollution_data
            compression_query = """
            ALTER TABLE pollution_data SET (
                timescaledb.compress,
                timescaledb.compress_segmentby = 'city'
            );
            
            SELECT add_compression_policy(
                'pollution_data',
                INTERVAL '7 days',
                if_not_exists => TRUE
            );
            """
            self.db.execute_query(compression_query)
            logger.info("✓ Compression policy enabled (7 days)")
            return True
        except Exception as e:
            logger.warning(f"Compression policy creation skipped: {str(e)}")
            return False
    
    def refresh_materialized_views(self):
        """Refresh all materialized views"""
        try:
            views = [
                'mv_hourly_city_stats',
                'mv_daily_city_stats',
                'mv_city_comparison'
            ]
            
            for view in views:
                try:
                    query = f"REFRESH MATERIALIZED VIEW CONCURRENTLY {view};"
                    self.db.execute_query(query)
                    logger.info(f"✓ Refreshed {view}")
                except Exception as view_error:
                    logger.warning(f"Could not refresh {view}: {str(view_error)}")
            
            return True
        except Exception as e:
            logger.error(f"View refresh failed: {str(e)}")
            return False
    
    def analyze_tables(self):
        """Update table statistics for query optimizer"""
        try:
            tables = [
                'pollution_data',
                'weather_data',
                'predictions',
                'model_performance'
            ]
            
            for table in tables:
                query = f"ANALYZE {table};"
                self.db.execute_query(query)
            
            logger.info("✓ Table statistics updated")
            return True
        except Exception as e:
            logger.error(f"Table analysis failed: {str(e)}")
            return False
    
    def optimize_all(self):
        """Run all optimization steps"""
        logger.info("=" * 70)
        logger.info("DATABASE OPTIMIZATION - Starting...")
        logger.info("=" * 70)
        
        # Check TimescaleDB availability
        has_timescaledb = self.check_timescaledb_extension()
        
        if not has_timescaledb:
            logger.info("Attempting to enable TimescaleDB...")
            has_timescaledb = self.enable_timescaledb()
        
        if has_timescaledb:
            logger.info("✓ TimescaleDB is available")
            logger.info("\n--- TimescaleDB Optimizations ---")
            self.create_hypertables()
            self.create_continuous_aggregates()
            self.create_retention_policy()
            self.create_compression_policy()
        else:
            logger.info("⚠ TimescaleDB not available - using standard PostgreSQL")
        
        logger.info("\n--- Standard Optimizations ---")
        self.create_materialized_views()
        self.optimize_indexes()
        self.analyze_tables()
        
        logger.info("\n--- Final Steps ---")
        self.refresh_materialized_views()
        
        logger.info("=" * 70)
        logger.info("DATABASE OPTIMIZATION - Completed!")
        logger.info("=" * 70)

if __name__ == '__main__':
    optimizer = DatabaseOptimizer()
    optimizer.optimize_all()
