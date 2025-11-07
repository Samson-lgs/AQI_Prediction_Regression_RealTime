"""
Export Air Quality Data to CSV
Fetches complete pollution and weather data from database and exports to CSV files
"""

import pandas as pd
from datetime import datetime, timedelta
from database.db_operations import DatabaseOperations
from config.settings import CITIES
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataExporter:
    def __init__(self):
        self.db = DatabaseOperations()
    
    def export_pollution_data(self, output_file='pollution_data_export.csv', 
                              days=30, city_filter=None):
        """
        Export pollution data to CSV file
        
        Args:
            output_file (str): Output CSV filename
            days (int): Number of days of historical data to export (default: 30)
            city_filter (str or list): Specific city/cities to export, or None for all
        
        Returns:
            str: Path to exported CSV file
        """
        try:
            logger.info(f"Starting pollution data export for last {days} days...")
            
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            logger.info(f"Date range: {start_date.date()} to {end_date.date()}")
            
            # Query to fetch all pollution data
            if city_filter:
                if isinstance(city_filter, str):
                    city_filter = [city_filter]
                
                placeholders = ', '.join(['%s'] * len(city_filter))
                query = f"""
                    SELECT 
                        id,
                        city,
                        timestamp,
                        pm25,
                        pm10,
                        no2,
                        so2,
                        co,
                        o3,
                        aqi_value,
                        data_source,
                        created_at
                    FROM pollution_data
                    WHERE timestamp BETWEEN %s AND %s
                      AND city IN ({placeholders})
                    ORDER BY city, timestamp DESC;
                """
                params = (start_date, end_date) + tuple(city_filter)
            else:
                query = """
                    SELECT 
                        id,
                        city,
                        timestamp,
                        pm25,
                        pm10,
                        no2,
                        so2,
                        co,
                        o3,
                        aqi_value,
                        data_source,
                        created_at
                    FROM pollution_data
                    WHERE timestamp BETWEEN %s AND %s
                    ORDER BY city, timestamp DESC;
                """
                params = (start_date, end_date)
            
            # Fetch data as list of dictionaries
            data = self.db.db.execute_query_dicts(query, params)
            
            if not data:
                logger.warning("No pollution data found in the specified date range")
                return None
            
            logger.info(f"Fetched {len(data)} pollution data records")
            
            # Convert to DataFrame
            df = pd.DataFrame(data)
            
            # Format timestamp columns
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['created_at'] = pd.to_datetime(df['created_at'])
            
            # Add calculated columns
            df['date'] = df['timestamp'].dt.date
            df['time'] = df['timestamp'].dt.time
            df['hour'] = df['timestamp'].dt.hour
            df['day_of_week'] = df['timestamp'].dt.day_name()
            
            # Reorder columns for better readability
            column_order = [
                'id', 'city', 'timestamp', 'date', 'time', 'hour', 'day_of_week',
                'aqi_value', 'pm25', 'pm10', 'no2', 'so2', 'co', 'o3',
                'data_source', 'created_at'
            ]
            df = df[column_order]
            
            # Export to CSV
            df.to_csv(output_file, index=False, encoding='utf-8')
            logger.info(f"✅ Pollution data exported to: {output_file}")
            logger.info(f"   Total records: {len(df)}")
            logger.info(f"   Cities covered: {df['city'].nunique()}")
            logger.info(f"   Date range: {df['date'].min()} to {df['date'].max()}")
            
            return output_file
            
        except Exception as e:
            logger.error(f"Error exporting pollution data: {str(e)}")
            raise
    
    def export_weather_data(self, output_file='weather_data_export.csv', 
                           days=30, city_filter=None):
        """
        Export weather data to CSV file
        
        Args:
            output_file (str): Output CSV filename
            days (int): Number of days of historical data
            city_filter (str or list): Specific city/cities to export
        
        Returns:
            str: Path to exported CSV file
        """
        try:
            logger.info(f"Starting weather data export for last {days} days...")
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            if city_filter:
                if isinstance(city_filter, str):
                    city_filter = [city_filter]
                
                placeholders = ', '.join(['%s'] * len(city_filter))
                query = f"""
                    SELECT 
                        id,
                        city,
                        timestamp,
                        temperature,
                        humidity,
                        wind_speed,
                        atmospheric_pressure,
                        precipitation,
                        cloudiness,
                        created_at
                    FROM weather_data
                    WHERE timestamp BETWEEN %s AND %s
                      AND city IN ({placeholders})
                    ORDER BY city, timestamp DESC;
                """
                params = (start_date, end_date) + tuple(city_filter)
            else:
                query = """
                    SELECT 
                        id,
                        city,
                        timestamp,
                        temperature,
                        humidity,
                        wind_speed,
                        atmospheric_pressure,
                        precipitation,
                        cloudiness,
                        created_at
                    FROM weather_data
                    WHERE timestamp BETWEEN %s AND %s
                    ORDER BY city, timestamp DESC;
                """
                params = (start_date, end_date)
            
            data = self.db.db.execute_query_dicts(query, params)
            
            if not data:
                logger.warning("No weather data found in the specified date range")
                return None
            
            logger.info(f"Fetched {len(data)} weather data records")
            
            df = pd.DataFrame(data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['created_at'] = pd.to_datetime(df['created_at'])
            
            df.to_csv(output_file, index=False, encoding='utf-8')
            logger.info(f"✅ Weather data exported to: {output_file}")
            logger.info(f"   Total records: {len(df)}")
            
            return output_file
            
        except Exception as e:
            logger.error(f"Error exporting weather data: {str(e)}")
            raise
    
    def export_combined_data(self, output_file='combined_aqi_weather_export.csv', 
                            days=30, city_filter=None):
        """
        Export combined pollution and weather data (joined by city and timestamp)
        
        Args:
            output_file (str): Output CSV filename
            days (int): Number of days of historical data
            city_filter (str or list): Specific city/cities to export
        
        Returns:
            str: Path to exported CSV file
        """
        try:
            logger.info(f"Starting combined data export for last {days} days...")
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            if city_filter:
                if isinstance(city_filter, str):
                    city_filter = [city_filter]
                
                placeholders = ', '.join(['%s'] * len(city_filter))
                query = f"""
                    SELECT 
                        p.id as pollution_id,
                        p.city,
                        p.timestamp,
                        p.pm25,
                        p.pm10,
                        p.no2,
                        p.so2,
                        p.co,
                        p.o3,
                        p.aqi_value,
                        p.data_source,
                        w.temperature,
                        w.humidity,
                        w.wind_speed,
                        w.atmospheric_pressure,
                        w.precipitation,
                        w.cloudiness,
                        p.created_at
                    FROM pollution_data p
                    LEFT JOIN weather_data w 
                        ON p.city = w.city 
                        AND DATE_TRUNC('hour', p.timestamp) = DATE_TRUNC('hour', w.timestamp)
                    WHERE p.timestamp BETWEEN %s AND %s
                      AND p.city IN ({placeholders})
                    ORDER BY p.city, p.timestamp DESC;
                """
                params = (start_date, end_date) + tuple(city_filter)
            else:
                query = """
                    SELECT 
                        p.id as pollution_id,
                        p.city,
                        p.timestamp,
                        p.pm25,
                        p.pm10,
                        p.no2,
                        p.so2,
                        p.co,
                        p.o3,
                        p.aqi_value,
                        p.data_source,
                        w.temperature,
                        w.humidity,
                        w.wind_speed,
                        w.atmospheric_pressure,
                        w.precipitation,
                        w.cloudiness,
                        p.created_at
                    FROM pollution_data p
                    LEFT JOIN weather_data w 
                        ON p.city = w.city 
                        AND DATE_TRUNC('hour', p.timestamp) = DATE_TRUNC('hour', w.timestamp)
                    WHERE p.timestamp BETWEEN %s AND %s
                    ORDER BY p.city, p.timestamp DESC;
                """
                params = (start_date, end_date)
            
            data = self.db.db.execute_query_dicts(query, params)
            
            if not data:
                logger.warning("No combined data found in the specified date range")
                return None
            
            logger.info(f"Fetched {len(data)} combined data records")
            
            df = pd.DataFrame(data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['created_at'] = pd.to_datetime(df['created_at'])
            
            # Add time-based features
            df['date'] = df['timestamp'].dt.date
            df['time'] = df['timestamp'].dt.time
            df['hour'] = df['timestamp'].dt.hour
            df['day_of_week'] = df['timestamp'].dt.day_name()
            
            df.to_csv(output_file, index=False, encoding='utf-8')
            logger.info(f"✅ Combined data exported to: {output_file}")
            logger.info(f"   Total records: {len(df)}")
            logger.info(f"   Cities covered: {df['city'].nunique()}")
            
            return output_file
            
        except Exception as e:
            logger.error(f"Error exporting combined data: {str(e)}")
            raise
    
    def export_all_current_data(self, output_file='current_aqi_all_cities.csv'):
        """
        Export latest AQI reading for each city
        
        Returns:
            str: Path to exported CSV file
        """
        try:
            logger.info("Exporting current AQI data for all cities...")
            
            query = """
                SELECT DISTINCT ON (city) 
                    city,
                    timestamp,
                    aqi_value,
                    pm25,
                    pm10,
                    no2,
                    so2,
                    co,
                    o3,
                    data_source,
                    created_at
                FROM pollution_data
                ORDER BY city, timestamp DESC;
            """
            
            data = self.db.db.execute_query_dicts(query)
            
            if not data:
                logger.warning("No current data found")
                return None
            
            df = pd.DataFrame(data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['created_at'] = pd.to_datetime(df['created_at'])
            
            # Sort by AQI value (worst first)
            df = df.sort_values('aqi_value', ascending=False)
            
            df.to_csv(output_file, index=False, encoding='utf-8')
            logger.info(f"✅ Current data exported to: {output_file}")
            logger.info(f"   Cities: {len(df)}")
            
            return output_file
            
        except Exception as e:
            logger.error(f"Error exporting current data: {str(e)}")
            raise
    
    def print_summary(self):
        """Print summary statistics of available data"""
        try:
            query = """
                SELECT 
                    COUNT(*) as total_records,
                    COUNT(DISTINCT city) as total_cities,
                    MIN(timestamp) as earliest_date,
                    MAX(timestamp) as latest_date,
                    COUNT(DISTINCT data_source) as data_sources
                FROM pollution_data;
            """
            
            result = self.db.db.execute_query_dicts(query)
            if result:
                stats = result[0]
                print("\n" + "="*60)
                print("DATABASE SUMMARY")
                print("="*60)
                print(f"Total Records:     {stats['total_records']:,}")
                print(f"Total Cities:      {stats['total_cities']}")
                print(f"Earliest Date:     {stats['earliest_date']}")
                print(f"Latest Date:       {stats['latest_date']}")
                print(f"Data Sources:      {stats['data_sources']}")
                print("="*60 + "\n")
                
        except Exception as e:
            logger.error(f"Error printing summary: {str(e)}")


def main():
    """Main function to run data export"""
    print("\n" + "="*60)
    print("AIR QUALITY DATA EXPORT TOOL")
    print("="*60 + "\n")
    
    exporter = DataExporter()
    
    # Print database summary
    exporter.print_summary()
    
    # Export options
    print("Select export option:")
    print("1. Export pollution data (last 30 days)")
    print("2. Export weather data (last 30 days)")
    print("3. Export combined data (pollution + weather)")
    print("4. Export current AQI for all cities")
    print("5. Export pollution data (custom days)")
    print("6. Export specific city data")
    print("7. Export ALL pollution data (entire database)")
    
    try:
        choice = input("\nEnter choice (1-7): ").strip()
        
        if choice == '1':
            file = exporter.export_pollution_data(days=30)
            print(f"\n✅ Export complete: {file}")
            
        elif choice == '2':
            file = exporter.export_weather_data(days=30)
            print(f"\n✅ Export complete: {file}")
            
        elif choice == '3':
            file = exporter.export_combined_data(days=30)
            print(f"\n✅ Export complete: {file}")
            
        elif choice == '4':
            file = exporter.export_all_current_data()
            print(f"\n✅ Export complete: {file}")
            
        elif choice == '5':
            days = int(input("Enter number of days: "))
            file = exporter.export_pollution_data(days=days)
            print(f"\n✅ Export complete: {file}")
            
        elif choice == '6':
            city = input("Enter city name: ").strip()
            days = int(input("Enter number of days: "))
            filename = f"{city.replace(' ', '_')}_pollution_data.csv"
            file = exporter.export_pollution_data(
                output_file=filename,
                days=days,
                city_filter=city
            )
            print(f"\n✅ Export complete: {file}")
            
        elif choice == '7':
            days = int(input("Enter number of days (e.g., 365 for 1 year, 730 for 2 years): "))
            file = exporter.export_pollution_data(
                output_file='pollution_data_complete_export.csv',
                days=days
            )
            print(f"\n✅ Export complete: {file}")
            
        else:
            print("Invalid choice!")
            return
            
    except KeyboardInterrupt:
        print("\n\nExport cancelled by user")
    except Exception as e:
        logger.error(f"Export failed: {str(e)}")
        print(f"\n❌ Export failed: {str(e)}")


if __name__ == "__main__":
    main()
