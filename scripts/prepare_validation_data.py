"""
Prepare validation data from Render PostgreSQL database

Fetches pollution and weather data for Delhi, Mumbai, and Bangalore,
merges them, performs feature engineering, and saves to CSV for validation.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from pathlib import Path

# Import feature engineering
from feature_engineering.data_cleaner import DataCleaner
from feature_engineering.feature_processor import FeatureProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Render Database URL
DATABASE_URL = "postgresql://aqi_user:u2I3Xl9kBvUj1xCXGJaeSFHczxNgzdFJ@dpg-d452eqn5r7bs73ba6o7g-a.oregon-postgres.render.com/aqi_db_gr7o"

VALIDATION_CITIES = ['Delhi', 'Mumbai', 'Bangalore']


def fetch_pollution_data(cities: list = VALIDATION_CITIES) -> pd.DataFrame:
    """Fetch pollution data from Render database"""
    logger.info(f"Fetching pollution data for {cities}...")
    
    conn = psycopg2.connect(DATABASE_URL)
    
    # Build query
    city_placeholders = ','.join(['%s'] * len(cities))
    query = f"""
        SELECT 
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
        WHERE city IN ({city_placeholders})
        ORDER BY timestamp
    """
    
    df = pd.read_sql_query(query, conn, params=cities)
    conn.close()
    
    logger.info(f"Fetched {len(df)} pollution records")
    return df


def fetch_weather_data(cities: list = VALIDATION_CITIES) -> pd.DataFrame:
    """Fetch weather data from Render database"""
    logger.info(f"Fetching weather data for {cities}...")
    
    conn = psycopg2.connect(DATABASE_URL)
    
    city_placeholders = ','.join(['%s'] * len(cities))
    query = f"""
        SELECT 
            city,
            timestamp,
            temperature,
            humidity,
            wind_speed,
            wind_direction,
            pressure,
            precipitation,
            cloud_cover,
            visibility,
            created_at
        FROM weather_data
        WHERE city IN ({city_placeholders})
        ORDER BY timestamp
    """
    
    df = pd.read_sql_query(query, conn, params=cities)
    conn.close()
    
    logger.info(f"Fetched {len(df)} weather records")
    return df


def merge_pollution_weather(pollution_df: pd.DataFrame, weather_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge pollution and weather data on city and timestamp
    
    Uses nearest timestamp match within 30 minutes
    """
    logger.info("Merging pollution and weather data...")
    
    # Convert timestamps
    pollution_df['timestamp'] = pd.to_datetime(pollution_df['timestamp'])
    weather_df['timestamp'] = pd.to_datetime(weather_df['timestamp'])
    
    merged_records = []
    
    for city in VALIDATION_CITIES:
        city_pollution = pollution_df[pollution_df['city'] == city].copy()
        city_weather = weather_df[weather_df['city'] == city].copy()
        
        if city_pollution.empty or city_weather.empty:
            logger.warning(f"No data for {city}, skipping...")
            continue
        
        # Sort by timestamp
        city_pollution = city_pollution.sort_values('timestamp')
        city_weather = city_weather.sort_values('timestamp')
        
        for _, poll_row in city_pollution.iterrows():
            # Find closest weather record within 30 minutes
            time_diff = (city_weather['timestamp'] - poll_row['timestamp']).abs()
            
            if time_diff.min() <= pd.Timedelta(minutes=30):
                closest_idx = time_diff.idxmin()
                weather_row = city_weather.loc[closest_idx]
                
                # Merge
                merged_row = {
                    'city': city,
                    'timestamp': poll_row['timestamp'],
                    'aqi_value': poll_row['aqi_value'],
                    'pm25': poll_row['pm25'],
                    'pm10': poll_row['pm10'],
                    'no2': poll_row['no2'],
                    'so2': poll_row['so2'],
                    'co': poll_row['co'],
                    'o3': poll_row['o3'],
                    'temperature': weather_row['temperature'],
                    'humidity': weather_row['humidity'],
                    'wind_speed': weather_row['wind_speed'],
                    'wind_direction': weather_row['wind_direction'],
                    'pressure': weather_row['pressure'],
                    'precipitation': weather_row['precipitation'],
                    'cloud_cover': weather_row['cloud_cover'],
                    'visibility': weather_row['visibility'],
                    'data_source': poll_row['data_source']
                }
                
                merged_records.append(merged_row)
    
    merged_df = pd.DataFrame(merged_records)
    logger.info(f"Merged dataset: {len(merged_df)} records")
    
    return merged_df


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply feature engineering to the merged dataset
    """
    logger.info("Applying feature engineering...")
    
    # Clean data
    cleaner = DataCleaner()
    df_cleaned = cleaner.clean_data(df)
    
    # Process features
    processor = FeatureProcessor()
    df_processed = processor.create_features(df_cleaned)
    
    logger.info(f"Final dataset: {len(df_processed)} records with {len(df_processed.columns)} features")
    
    return df_processed


def main():
    """Main data preparation pipeline"""
    logger.info("="*80)
    logger.info("PREPARING VALIDATION DATA FROM RENDER DATABASE")
    logger.info("="*80)
    
    try:
        # Fetch data
        pollution_df = fetch_pollution_data()
        weather_df = fetch_weather_data()
        
        # Merge
        merged_df = merge_pollution_weather(pollution_df, weather_df)
        
        if merged_df.empty:
            logger.error("No merged data available!")
            return
        
        # Engineer features
        final_df = engineer_features(merged_df)
        
        # Save to CSV
        output_dir = Path("data/processed")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_path = output_dir / f"validation_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        final_df.to_csv(output_path, index=False)
        
        logger.info(f"\n✅ Validation data saved to: {output_path}")
        
        # Summary statistics
        logger.info("\n" + "="*80)
        logger.info("DATA SUMMARY")
        logger.info("="*80)
        
        for city in VALIDATION_CITIES:
            city_data = final_df[final_df['city'] == city]
            logger.info(f"\n{city}:")
            logger.info(f"  Records: {len(city_data)}")
            logger.info(f"  AQI Range: {city_data['aqi_value'].min():.1f} - {city_data['aqi_value'].max():.1f}")
            logger.info(f"  AQI Mean: {city_data['aqi_value'].mean():.1f}")
            logger.info(f"  Date Range: {city_data['timestamp'].min()} to {city_data['timestamp'].max()}")
        
        logger.info(f"\nTotal Features: {len(final_df.columns)}")
        logger.info(f"Feature Columns: {list(final_df.columns)}")
        
        logger.info("\n" + "="*80)
        logger.info("Ready for validation! Run:")
        logger.info(f"python models/run_step6_validation.py --data-path {output_path}")
        logger.info("="*80)
        
    except Exception as e:
        logger.error(f"Data preparation failed: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
