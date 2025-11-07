"""
Recalculate all AQI values using the hybrid system
OpenWeather pollutant breakpoints → Traditional 0-500 AQI scale
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from calculate_aqi_hybrid import calculate_aqi_from_pollutants, get_aqi_category

def recalculate_all_aqi():
    """Update all AQI values in database using hybrid system"""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL environment variable not set!")
        return
    
    conn = psycopg2.connect(database_url)
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Get total count
        cursor.execute("SELECT COUNT(*) as total FROM pollution_data")
        total = cursor.fetchone()['total']
        
        print(f"\n📊 Found {total:,} records to recalculate")
        print("=" * 80)
        print("Using: OpenWeather Breakpoints → Traditional 0-500 AQI Scale")
        print("=" * 80 + "\n")
        
        # Get all records
        cursor.execute("""
            SELECT id, city, so2, no2, pm10, pm25, o3, co, aqi_value
            FROM pollution_data
            ORDER BY id
        """)
        
        records = cursor.fetchall()
        updated = 0
        sample_updates = []
        
        for i, record in enumerate(records, 1):
            old_aqi = record['aqi_value']
            
            # Calculate new AQI using hybrid system
            new_aqi = calculate_aqi_from_pollutants(
                so2=record['so2'] or 0,
                no2=record['no2'] or 0,
                pm10=record['pm10'] or 0,
                pm25=record['pm25'] or 0,
                o3=record['o3'] or 0,
                co=record['co'] or 0
            )
            
            # Update the record
            cursor.execute(
                "UPDATE pollution_data SET aqi_value = %s WHERE id = %s",
                (new_aqi, record['id'])
            )
            
            if old_aqi != new_aqi:
                updated += 1
                
                # Collect first 10 updates as examples
                if len(sample_updates) < 10:
                    category = get_aqi_category(new_aqi)
                    sample_updates.append({
                        'city': record['city'],
                        'old_aqi': old_aqi,
                        'new_aqi': new_aqi,
                        'category': category,
                        'pm25': record['pm25']
                    })
            
            # Show progress every 5000 records
            if i % 5000 == 0:
                print(f"Progress: {i:,}/{total:,} records ({(i/total*100):.1f}%)")
        
        # Commit changes
        conn.commit()
        
        print(f"\n{'='*80}")
        print(f"✅ RECALCULATION COMPLETE!")
        print(f"{'='*80}")
        print(f"Total records: {total:,}")
        print(f"Updated: {updated:,}")
        print(f"Unchanged: {(total - updated):,}")
        print(f"{'='*80}\n")
        
        # Show sample updates
        if sample_updates:
            print("📋 Sample Updates (First 10):")
            print("-" * 80)
            for s in sample_updates:
                print(f"{s['city']:15} | Old: {s['old_aqi']:3.0f} → New: {s['new_aqi']:3} "
                      f"({s['category']:12}) | PM2.5: {s['pm25']:.1f}")
        
        # Show AQI distribution
        print(f"\n{'='*80}")
        print("📊 New AQI Distribution:")
        print(f"{'='*80}")
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
                COUNT(*) as count
            FROM pollution_data
            GROUP BY category
            ORDER BY MIN(aqi_value)
        """)
        
        distribution = cursor.fetchall()
        for d in distribution:
            count = d['count']
            percentage = (count / total * 100)
            bar = "█" * int(percentage / 2)
            print(f"{d['category']:25} | {count:6,} ({percentage:5.1f}%) {bar}")
        
        print(f"{'='*80}\n")
        
        # Show recent data samples
        print("📋 Recent Data Samples:")
        print("-" * 80)
        cursor.execute("""
            SELECT DISTINCT ON (city) 
                city, aqi_value, pm25, pm10, no2, so2, co, o3
            FROM pollution_data
            WHERE timestamp >= NOW() - INTERVAL '24 hours'
            ORDER BY city, timestamp DESC
            LIMIT 10
        """)
        
        samples = cursor.fetchall()
        for s in samples:
            category = get_aqi_category(s['aqi_value'])
            print(f"{s['city']:15} | AQI: {s['aqi_value']:3} ({category:12}) | "
                  f"PM2.5: {s['pm25']:5.1f} | PM10: {s['pm10']:5.1f}")
        
        print(f"{'='*80}\n")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    print("\n🔄 Hybrid AQI Recalculation Script")
    print("=" * 80)
    print("This will recalculate all AQI values using:")
    print("  • OpenWeather pollutant breakpoints")
    print("  • Traditional 0-500 AQI output scale")
    print("  • Matches online portal display standards")
    print("=" * 80)
    
    response = input("\n⚠️  This will modify the database. Continue? (yes/no): ")
    if response.lower() == 'yes':
        recalculate_all_aqi()
        print("\n✅ All AQI values updated to hybrid system!\n")
    else:
        print("\n❌ Operation cancelled.\n")
