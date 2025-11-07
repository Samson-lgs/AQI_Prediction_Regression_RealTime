"""
View current database data in formatted tables
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from tabulate import tabulate

def view_database_data():
    """Display current database data in table format"""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL environment variable not set!")
        return
    
    conn = psycopg2.connect(database_url)
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # 1. Database Summary
        print("\n" + "="*100)
        print("📊 DATABASE SUMMARY")
        print("="*100)
        
        cursor.execute("SELECT COUNT(*) as total FROM pollution_data")
        total = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(DISTINCT city) as cities FROM pollution_data")
        cities_count = cursor.fetchone()['cities']
        
        cursor.execute("SELECT MIN(timestamp) as first, MAX(timestamp) as last FROM pollution_data")
        time_range = cursor.fetchone()
        
        summary_data = [
            ["Total Records", f"{total:,}"],
            ["Unique Cities", f"{cities_count:,}"],
            ["First Record", str(time_range['first'])],
            ["Latest Record", str(time_range['last'])]
        ]
        print(tabulate(summary_data, headers=["Metric", "Value"], tablefmt="grid"))
        
        # 2. Current AQI Distribution
        print("\n" + "="*100)
        print("📈 CURRENT AQI DISTRIBUTION")
        print("="*100)
        
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN aqi_value <= 50 THEN '0-50 (Good)'
                    WHEN aqi_value <= 100 THEN '51-100 (Satisfactory)'
                    WHEN aqi_value <= 200 THEN '101-200 (Moderate)'
                    WHEN aqi_value <= 300 THEN '201-300 (Poor)'
                    WHEN aqi_value <= 400 THEN '301-400 (Very Poor)'
                    ELSE '401-500 (Severe)'
                END as category,
                COUNT(*) as count,
                ROUND(COUNT(*) * 100.0 / %s, 2) as percentage
            FROM pollution_data
            GROUP BY category
            ORDER BY MIN(aqi_value)
        """, (total,))
        
        distribution = cursor.fetchall()
        dist_data = []
        for d in distribution:
            bar = "█" * int(d['percentage'] / 2)
            dist_data.append([
                d['category'],
                f"{d['count']:,}",
                f"{d['percentage']:.2f}%",
                bar
            ])
        
        print(tabulate(dist_data, headers=["AQI Category", "Count", "Percentage", "Distribution"], tablefmt="grid"))
        
        # 3. Recent Data by City (Last 24 hours)
        print("\n" + "="*100)
        print("🌆 RECENT DATA BY CITY (Last 24 Hours)")
        print("="*100)
        
        cursor.execute("""
            SELECT DISTINCT ON (city) 
                city,
                ROUND(aqi_value::numeric, 0) as aqi,
                ROUND(pm25::numeric, 2) as pm25,
                ROUND(pm10::numeric, 2) as pm10,
                ROUND(no2::numeric, 2) as no2,
                ROUND(so2::numeric, 2) as so2,
                ROUND(co::numeric, 2) as co,
                ROUND(o3::numeric, 2) as o3,
                data_source,
                TO_CHAR(timestamp, 'YYYY-MM-DD HH24:MI') as time
            FROM pollution_data
            WHERE timestamp >= NOW() - INTERVAL '24 hours'
            ORDER BY city, timestamp DESC
            LIMIT 20
        """)
        
        recent_data = cursor.fetchall()
        if recent_data:
            recent_table = []
            for r in recent_data:
                recent_table.append([
                    r['city'],
                    r['aqi'],
                    r['pm25'],
                    r['pm10'],
                    r['no2'],
                    r['so2'],
                    r['co'],
                    r['o3'],
                    r['data_source'],
                    r['time']
                ])
            
            print(tabulate(recent_table, 
                         headers=["City", "AQI", "PM2.5", "PM10", "NO2", "SO2", "CO", "O3", "Source", "Timestamp"],
                         tablefmt="grid"))
        else:
            print("⚠️  No data found in last 24 hours")
        
        # 4. All Cities in Database
        print("\n" + "="*100)
        print("🏙️  ALL CITIES IN DATABASE")
        print("="*100)
        
        cursor.execute("""
            SELECT 
                city,
                COUNT(*) as records,
                ROUND(AVG(aqi_value)::numeric, 1) as avg_aqi,
                ROUND(MIN(aqi_value)::numeric, 0) as min_aqi,
                ROUND(MAX(aqi_value)::numeric, 0) as max_aqi,
                TO_CHAR(MAX(timestamp), 'YYYY-MM-DD HH24:MI') as latest
            FROM pollution_data
            GROUP BY city
            ORDER BY city
        """)
        
        cities_data = cursor.fetchall()
        cities_table = []
        for c in cities_data:
            cities_table.append([
                c['city'],
                f"{c['records']:,}",
                c['avg_aqi'],
                c['min_aqi'],
                c['max_aqi'],
                c['latest']
            ])
        
        print(tabulate(cities_table,
                     headers=["City", "Total Records", "Avg AQI", "Min AQI", "Max AQI", "Latest Update"],
                     tablefmt="grid"))
        
        # 5. Sample Records (Random 15)
        print("\n" + "="*100)
        print("📋 RANDOM SAMPLE RECORDS")
        print("="*100)
        
        cursor.execute("""
            SELECT 
                city,
                ROUND(aqi_value::numeric, 0) as aqi,
                ROUND(pm25::numeric, 2) as pm25,
                ROUND(pm10::numeric, 2) as pm10,
                data_source,
                TO_CHAR(timestamp, 'YYYY-MM-DD HH24:MI') as time
            FROM pollution_data
            ORDER BY RANDOM()
            LIMIT 15
        """)
        
        samples = cursor.fetchall()
        sample_table = []
        for s in samples:
            sample_table.append([
                s['city'],
                s['aqi'],
                s['pm25'],
                s['pm10'],
                s['data_source'],
                s['time']
            ])
        
        print(tabulate(sample_table,
                     headers=["City", "AQI", "PM2.5", "PM10", "Source", "Timestamp"],
                     tablefmt="grid"))
        
        print("\n" + "="*100)
        print("✅ Data view complete!")
        print("="*100 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    view_database_data()
