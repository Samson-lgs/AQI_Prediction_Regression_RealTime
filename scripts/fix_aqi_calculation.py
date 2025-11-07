"""
Fix AQI calculation in database
Recalculates AQI values based on pollutant concentrations using EPA formula
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor

def calculate_aqi_from_pm25(pm25):
    """Calculate AQI from PM2.5 concentration (μg/m³)"""
    # EPA AQI breakpoints for PM2.5 (24-hour)
    breakpoints = [
        (0, 12.0, 0, 50),       # Good
        (12.1, 35.4, 51, 100),  # Moderate
        (35.5, 55.4, 101, 150), # Unhealthy for Sensitive
        (55.5, 150.4, 151, 200),# Unhealthy
        (150.5, 250.4, 201, 300),# Very Unhealthy
        (250.5, 500.4, 301, 500) # Hazardous
    ]
    
    for bp_lo, bp_hi, aqi_lo, aqi_hi in breakpoints:
        if bp_lo <= pm25 <= bp_hi:
            # Linear interpolation formula
            aqi = ((aqi_hi - aqi_lo) / (bp_hi - bp_lo)) * (pm25 - bp_lo) + aqi_lo
            return round(aqi)
    
    # If PM2.5 is above 500.4, return max AQI
    if pm25 > 500.4:
        return 500
    return 0

def calculate_aqi_from_pm10(pm10):
    """Calculate AQI from PM10 concentration (μg/m³)"""
    # EPA AQI breakpoints for PM10 (24-hour)
    breakpoints = [
        (0, 54, 0, 50),         # Good
        (55, 154, 51, 100),     # Moderate
        (155, 254, 101, 150),   # Unhealthy for Sensitive
        (255, 354, 151, 200),   # Unhealthy
        (355, 424, 201, 300),   # Very Unhealthy
        (425, 604, 301, 500)    # Hazardous
    ]
    
    for bp_lo, bp_hi, aqi_lo, aqi_hi in breakpoints:
        if bp_lo <= pm10 <= bp_hi:
            aqi = ((aqi_hi - aqi_lo) / (bp_hi - bp_lo)) * (pm10 - bp_lo) + aqi_lo
            return round(aqi)
    
    if pm10 > 604:
        return 500
    return 0

def fix_aqi_values():
    """Update all AQI values in the database"""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL environment variable not set!")
        return
    
    conn = psycopg2.connect(database_url)
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Get all records
        cursor.execute("SELECT id, pm25, pm10, aqi_value FROM pollution_data")
        records = cursor.fetchall()
        
        print(f"\n📊 Found {len(records)} records to update")
        print("=" * 50)
        
        updated = 0
        for record in records:
            old_aqi = record['aqi_value']
            pm25 = record['pm25']
            pm10 = record['pm10']
            
            # Calculate AQI from both PM2.5 and PM10, take the higher value
            aqi_from_pm25 = calculate_aqi_from_pm25(pm25) if pm25 else 0
            aqi_from_pm10 = calculate_aqi_from_pm10(pm10) if pm10 else 0
            new_aqi = max(aqi_from_pm25, aqi_from_pm10)
            
            if new_aqi != old_aqi:
                cursor.execute(
                    "UPDATE pollution_data SET aqi_value = %s WHERE id = %s",
                    (new_aqi, record['id'])
                )
                updated += 1
                
                if updated <= 5:  # Show first 5 updates as examples
                    print(f"✓ ID {record['id']}: AQI {old_aqi} → {new_aqi} (PM2.5: {pm25}, PM10: {pm10})")
        
        conn.commit()
        print(f"\n✅ Updated {updated} records")
        print(f"✓ {len(records) - updated} records were already correct")
        
        # Show some sample updated values
        cursor.execute("""
            SELECT city, aqi_value, pm25, pm10 
            FROM pollution_data 
            WHERE timestamp >= NOW() - INTERVAL '1 day'
            ORDER BY city
            LIMIT 5
        """)
        samples = cursor.fetchall()
        
        print("\n📋 Sample updated values:")
        print("=" * 50)
        for s in samples:
            print(f"{s['city']}: AQI={s['aqi_value']}, PM2.5={s['pm25']}, PM10={s['pm10']}")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Error: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    print("\n🔧 AQI Calculation Fix Script")
    print("=" * 50)
    fix_aqi_values()
    print("\n✅ Done!\n")
