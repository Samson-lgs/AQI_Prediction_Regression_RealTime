import psycopg2
import os
from datetime import datetime, timezone, timedelta

conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()

print("\n" + "="*70)
print("HOURLY DATA COLLECTION STATUS CHECK")
print("="*70)

# Get latest data info
cur.execute("""
    SELECT 
        MAX(timestamp) as latest,
        MIN(timestamp) as earliest,
        COUNT(*) as total,
        COUNT(DISTINCT city) as cities,
        COUNT(DISTINCT DATE_TRUNC('hour', timestamp)) as hours
    FROM pollution_data
""")
row = cur.fetchone()

latest, earliest, total, cities, hours = row
now = datetime.now(timezone.utc)

print(f"\n📊 Overall Statistics:")
print(f"   Total records collected: {total:,}")
print(f"   Cities monitored: {cities}")
print(f"   Distinct hours collected: {hours}")
print(f"   Data collection period: {hours / 24:.1f} days")

print(f"\n⏰ Timing:")
print(f"   Earliest data: {earliest} UTC")
print(f"   Latest data:   {latest} UTC")
print(f"   Current time:  {now.replace(microsecond=0)} UTC")

if latest:
    time_since_last = now - latest.replace(tzinfo=timezone.utc)
    minutes_ago = int(time_since_last.total_seconds() / 60)
    print(f"   Time since last collection: {minutes_ago} minutes ago")
    
    if minutes_ago < 70:
        print(f"\n   ✅ HEALTHY - Data collected within last hour")
    elif minutes_ago < 130:
        print(f"\n   ⚠️  DELAYED - Last collection was {minutes_ago} minutes ago")
    else:
        print(f"\n   ❌ ISSUE - No data for {minutes_ago} minutes (expected hourly)")

# Check data collected in last 24 hours
cur.execute("""
    SELECT COUNT(*) 
    FROM pollution_data 
    WHERE timestamp > NOW() - INTERVAL '24 hours'
""")
last_24h = cur.fetchone()[0]

print(f"\n📈 Recent Activity:")
print(f"   Records in last 24 hours: {last_24h:,}")
print(f"   Expected per hour: ~{cities} records (one per city)")
print(f"   Expected in 24 hours: ~{cities * 24:,} records")

if last_24h > 0:
    coverage = (last_24h / (cities * 24)) * 100
    print(f"   Actual coverage: {coverage:.1f}%")

# Check most recent cities
print(f"\n🏙️  Recently Updated Cities (last 10):")
cur.execute("""
    SELECT city, timestamp, aqi_value, data_source
    FROM pollution_data
    ORDER BY timestamp DESC
    LIMIT 10
""")
for city, ts, aqi, source in cur.fetchall():
    mins_ago = int((now - ts.replace(tzinfo=timezone.utc)).total_seconds() / 60)
    print(f"   {city:15} AQI:{aqi or 'N/A':>4}  {mins_ago:3}min ago  ({source})")

# Check for cities without recent data
cur.execute("""
    WITH recent_cities AS (
        SELECT DISTINCT city
        FROM pollution_data
        WHERE timestamp > NOW() - INTERVAL '2 hours'
    ),
    all_cities AS (
        SELECT DISTINCT city
        FROM pollution_data
    )
    SELECT ac.city, MAX(pd.timestamp) as last_seen
    FROM all_cities ac
    LEFT JOIN pollution_data pd ON ac.city = pd.city
    WHERE ac.city NOT IN (SELECT city FROM recent_cities)
    GROUP BY ac.city
    ORDER BY last_seen DESC NULLS LAST
    LIMIT 10
""")

stale = cur.fetchall()
if stale:
    print(f"\n⚠️  Cities Without Recent Data (>2 hours):")
    for city, last_seen in stale:
        if last_seen:
            hours_ago = int((now - last_seen.replace(tzinfo=timezone.utc)).total_seconds() / 3600)
            print(f"   {city:15} last seen {hours_ago} hours ago")
        else:
            print(f"   {city:15} never seen")

print("\n" + "="*70)
if minutes_ago < 70:
    print("✅ CONCLUSION: Hourly data collection is WORKING PROPERLY")
else:
    print("⚠️  CONCLUSION: Data collection may have stopped or delayed")
print("="*70 + "\n")

conn.close()
