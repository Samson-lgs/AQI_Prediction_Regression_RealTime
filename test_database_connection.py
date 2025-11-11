"""
Quick database connection test
Tests if we can connect to PostgreSQL and if tables exist
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from database.db_config import DatabaseManager
from database.db_operations import DatabaseOperations

def test_database():
    print("🔍 Testing Database Connection...")
    print("=" * 60)
    
    try:
        # Test 1: Connection pool creation
        print("\n1️⃣  Creating database connection pool...")
        db_manager = DatabaseManager()
        print("✅ Connection pool created successfully")
        
        # Test 2: Health check
        print("\n2️⃣  Running health check...")
        is_healthy = db_manager.health_check()
        if is_healthy:
            print("✅ Database health check passed")
        else:
            print("❌ Database health check failed")
            return
        
        # Test 3: Check if tables exist
        print("\n3️⃣  Checking if tables exist...")
        check_tables_query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_type = 'BASE TABLE'
        ORDER BY table_name;
        """
        
        tables = db_manager.execute_query(check_tables_query)
        if tables:
            print(f"✅ Found {len(tables)} tables:")
            for table in tables:
                print(f"   - {table[0]}")
        else:
            print("⚠️  No tables found. You may need to create them.")
            print("\n   Run: python -c \"from database.db_operations import DatabaseOperations; db = DatabaseOperations(); db.create_tables()\"")
        
        # Test 4: Check pollution_data table
        print("\n4️⃣  Checking pollution_data table...")
        count_query = "SELECT COUNT(*) FROM pollution_data;"
        try:
            result = db_manager.execute_query(count_query)
            count = result[0][0] if result else 0
            print(f"✅ pollution_data table exists with {count} records")
            
            # Check date range
            date_range_query = """
            SELECT 
                MIN(timestamp) as earliest,
                MAX(timestamp) as latest,
                COUNT(DISTINCT city) as cities
            FROM pollution_data;
            """
            date_info = db_manager.execute_query_dicts(date_range_query)
            if date_info and date_info[0]:
                info = date_info[0]
                print(f"   📅 Date range: {info['earliest']} to {info['latest']}")
                print(f"   🏙️  Cities: {info['cities']}")
                
        except Exception as e:
            print(f"❌ Error accessing pollution_data: {e}")
            print("   Table may not exist. Run create_tables() first.")
        
        # Test 5: Check recent data for Delhi
        print("\n5️⃣  Checking recent data for Delhi...")
        delhi_query = """
        SELECT city, timestamp, pm25, pm10, aqi_value, data_source
        FROM pollution_data
        WHERE city = 'Delhi'
        ORDER BY timestamp DESC
        LIMIT 3;
        """
        try:
            delhi_data = db_manager.execute_query_dicts(delhi_query)
            if delhi_data:
                print(f"✅ Found {len(delhi_data)} recent records for Delhi:")
                for record in delhi_data:
                    print(f"   {record['timestamp']} | AQI: {record['aqi_value']} | PM2.5: {record['pm25']} | Source: {record['data_source']}")
            else:
                print("⚠️  No data found for Delhi")
                print("   You may need to run data collection: python backend/main.py")
        except Exception as e:
            print(f"❌ Error checking Delhi data: {e}")
        
        print("\n" + "=" * 60)
        print("✅ Database test completed!")
        
    except Exception as e:
        print(f"\n❌ Database test failed: {e}")
        print("\n🔧 Troubleshooting:")
        print("   1. Check if .env file has correct DATABASE_URL")
        print("   2. Verify PostgreSQL service is running")
        print("   3. Check if you can connect via psql or pgAdmin")
        print("   4. Verify network connectivity to Render database")

if __name__ == "__main__":
    test_database()
