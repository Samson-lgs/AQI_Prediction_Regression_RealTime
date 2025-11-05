"""Quick script to check what data has been collected in the database"""

import os
from dotenv import load_dotenv
from database.db_operations import DatabaseOperations
from datetime import datetime, timedelta

load_dotenv()

def main():
    print("=" * 60)
    print("DATABASE DATA CHECKER")
    print("=" * 60)
    
    try:
        db = DatabaseOperations()
        
        # 1. Check pollution_data table
        print("\n📊 POLLUTION DATA SUMMARY")
        print("-" * 60)
        
        query = """
        SELECT 
            data_source,
            COUNT(*) as total_records,
            COUNT(DISTINCT city) as unique_cities,
            MIN(timestamp) as earliest_data,
            MAX(timestamp) as latest_data
        FROM pollution_data
        GROUP BY data_source
        ORDER BY total_records DESC;
        """
        results = db.db.execute_query(query)
        
        if results:
            for row in results:
                print(f"\nSource: {row[0]}")
                print(f"  Total Records: {row[1]:,}")
                print(f"  Unique Cities: {row[2]}")
                print(f"  Earliest: {row[3]}")
                print(f"  Latest: {row[4]}")
        else:
            print("⚠️  No pollution data found yet!")
        
        # 2. Check weather_data table
        print("\n\n🌤️  WEATHER DATA SUMMARY")
        print("-" * 60)
        
        query = """
        SELECT 
            COUNT(*) as total_records,
            COUNT(DISTINCT city) as unique_cities,
            MIN(timestamp) as earliest_data,
            MAX(timestamp) as latest_data
        FROM weather_data;
        """
        results = db.db.execute_query(query)
        
        if results and results[0][0] > 0:
            row = results[0]
            print(f"Total Records: {row[0]:,}")
            print(f"Unique Cities: {row[1]}")
            print(f"Earliest: {row[2]}")
            print(f"Latest: {row[3]}")
        else:
            print("⚠️  No weather data found yet!")
        
        # 3. List top 10 cities by data volume
        print("\n\n🏙️  TOP 10 CITIES BY DATA VOLUME")
        print("-" * 60)
        
        query = """
        SELECT 
            city,
            COUNT(*) as records,
            MAX(timestamp) as latest_reading
        FROM pollution_data
        GROUP BY city
        ORDER BY records DESC
        LIMIT 10;
        """
        results = db.db.execute_query(query)
        
        if results:
            print(f"{'City':<20} {'Records':<10} {'Latest Reading'}")
            print("-" * 60)
            for row in results:
                print(f"{row[0]:<20} {row[1]:<10} {row[2]}")
        else:
            print("⚠️  No data to display")
        
        # 4. Check recent data (last 24 hours)
        print("\n\n⏰ RECENT DATA (Last 24 Hours)")
        print("-" * 60)
        
        query = """
        SELECT 
            city,
            COUNT(*) as records
        FROM pollution_data
        WHERE timestamp >= NOW() - INTERVAL '24 hours'
        GROUP BY city
        ORDER BY records DESC
        LIMIT 10;
        """
        results = db.db.execute_query(query)
        
        if results:
            print(f"{'City':<20} {'Records (24h)'}")
            print("-" * 40)
            for row in results:
                print(f"{row[0]:<20} {row[1]}")
        else:
            print("⚠️  No data in last 24 hours")
        
        # 5. Sample data from a city
        print("\n\n📝 SAMPLE DATA (Latest 5 Records)")
        print("-" * 60)
        
        query = """
        SELECT 
            city,
            timestamp,
            aqi_value,
            pm25,
            pm10,
            data_source
        FROM pollution_data
        ORDER BY timestamp DESC
        LIMIT 5;
        """
        results = db.db.execute_query(query)
        
        if results:
            for row in results:
                print(f"\nCity: {row[0]}")
                print(f"  Time: {row[1]}")
                print(f"  AQI: {row[2]}")
                print(f"  PM2.5: {row[3]}, PM10: {row[4]}")
                print(f"  Source: {row[5]}")
        else:
            print("⚠️  No records found")
        
        print("\n" + "=" * 60)
        print("✅ Check complete!")
        print("=" * 60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure DATABASE_URL or DB_* environment variables are set!")

if __name__ == "__main__":
    main()
