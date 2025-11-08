"""Standalone data summary script with local path bootstrap."""
import sys, os
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from database.db_operations import DatabaseOperations

QUERIES = {
    "pollution_sources": """
        SELECT data_source, COUNT(*) AS total_records, COUNT(DISTINCT city) AS unique_cities,
               MIN(timestamp) AS earliest_data, MAX(timestamp) AS latest_data
        FROM pollution_data GROUP BY data_source ORDER BY total_records DESC;""",
    "weather_summary": """
        SELECT COUNT(*) AS total_records, COUNT(DISTINCT city) AS unique_cities,
               MIN(timestamp) AS earliest_data, MAX(timestamp) AS latest_data
        FROM weather_data;""",
    "top_cities": """
        SELECT city, COUNT(*) AS records, MAX(timestamp) AS latest_reading
        FROM pollution_data GROUP BY city ORDER BY records DESC LIMIT 10;""",
    "recent_24h": """
        SELECT city, COUNT(*) AS records
        FROM pollution_data WHERE timestamp >= NOW() - INTERVAL '24 hours'
        GROUP BY city ORDER BY records DESC LIMIT 10;""",
    "latest_samples": """
        SELECT city, timestamp, aqi_value, pm25, pm10, data_source
        FROM pollution_data ORDER BY timestamp DESC LIMIT 5;"""
}

def main():
    print("="*70) 
    print("DATA SUMMARY @", datetime.utcnow().isoformat())
    print("="*70)
    try:
        db = DatabaseOperations()
        # Pollution sources
        print("\n📊 Pollution Data by Source")
        rows = db.db.execute_query(QUERIES["pollution_sources"]) or []
        if not rows:
            print("(no pollution data)")
        for r in rows:
            src, total, cities, earliest, latest = r
            print(f"- {src or 'unknown'}: {total} rows, {cities} cities, {earliest} → {latest}")
        # Weather summary
        print("\n🌤️ Weather Data Summary")
        w = db.db.execute_query(QUERIES["weather_summary"]) or []
        if w and w[0][0] > 0:
            total, cities, earliest, latest = w[0]
            print(f"Rows: {total}, Cities: {cities}, Range: {earliest} → {latest}")
        else:
            print("(no weather data)")
        # Top cities
        print("\n🏙️ Top 10 Cities by Rows")
        t = db.db.execute_query(QUERIES["top_cities"]) or []
        if not t:
            print("(no city data)")
        for city, count, latest in t:
            print(f"- {city}: {count} rows (latest {latest})")
        # Recent 24h
        print("\n⏰ Recent 24h Activity (Top 10)")
        r24 = db.db.execute_query(QUERIES["recent_24h"]) or []
        if not r24:
            print("(no rows in last 24h)")
        for city, count in r24:
            print(f"- {city}: {count} rows")
        # Latest samples
        print("\n📝 Latest 5 Samples")
        samples = db.db.execute_query(QUERIES["latest_samples"]) or []
        if not samples:
            print("(no samples)")
        for city, ts, aqi, pm25, pm10, src in samples:
            print(f"- {city} @ {ts} | AQI={aqi} PM2.5={pm25} PM10={pm10} src={src}")
    except Exception as e:
        print("❌ Error summarizing data:", e)
        print("Ensure DATABASE_URL or DB_* environment variables are set.")
    print("\n" + "="*70)

if __name__ == "__main__":
    main()
