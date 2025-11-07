"""
Comprehensive Frontend API Test
Tests all API endpoints that the React dashboard uses
"""
import requests
import json
from datetime import datetime

BASE_URL = "https://aqi-backend-api.onrender.com/api/v1"

print("\n" + "="*70)
print("🧪 FRONTEND API TESTING")
print("="*70)

# Test 1: Health Check
print("\n1. Testing Health Endpoint...")
try:
    response = requests.get(f"{BASE_URL}/health")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Status: {data['status']}")
        print(f"   ✅ Database: {data['database']}")
        print(f"   ✅ Timestamp: {data['timestamp']}")
    else:
        print(f"   ❌ Failed: {response.status_code}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 2: Cities List
print("\n2. Testing Cities Endpoint...")
try:
    response = requests.get(f"{BASE_URL}/cities/")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Total cities: {len(data['cities'])}")
        print(f"   ✅ First 5 cities: {', '.join(data['cities'][:5])}")
    else:
        print(f"   ❌ Failed: {response.status_code}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 3: Current AQI for All Cities
print("\n3. Testing All Cities Current AQI...")
try:
    response = requests.get(f"{BASE_URL}/aqi/all/current")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Cities with data: {len(data['data'])}")
        if data['data']:
            sample = data['data'][0]
            print(f"   ✅ Sample ({sample['city']}): AQI={sample.get('aqi_value', 'N/A')}, PM2.5={sample.get('pm25', 'N/A')}")
    else:
        print(f"   ❌ Failed: {response.status_code}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 4: Current AQI for Specific City
print("\n4. Testing Single City Current AQI (Delhi)...")
try:
    response = requests.get(f"{BASE_URL}/aqi/current/Delhi")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ City: {data.get('city', 'N/A')}")
        print(f"   ✅ AQI: {data.get('aqi_value', 'N/A')}")
        print(f"   ✅ PM2.5: {data.get('pm25', 'N/A')}")
    else:
        print(f"   ⚠️  Status: {response.status_code} (Using fallback in frontend)")
except Exception as e:
    print(f"   ⚠️  Error: {e} (Using fallback in frontend)")

# Test 5: Historical Data
print("\n5. Testing Historical Data (Delhi, 7 days)...")
try:
    response = requests.get(f"{BASE_URL}/aqi/historical/Delhi?days=7")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Data points: {len(data.get('data', []))}")
        if data.get('data'):
            print(f"   ✅ Date range: {data['data'][0]['timestamp']} to {data['data'][-1]['timestamp']}")
    else:
        print(f"   ❌ Failed: {response.status_code}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 6: Top Polluted Cities
print("\n6. Testing Top Polluted Cities...")
try:
    response = requests.get(f"{BASE_URL}/aqi/top-polluted")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Cities returned: {len(data.get('cities', []))}")
        if data.get('cities'):
            top_city = data['cities'][0]
            print(f"   ✅ Most polluted: {top_city['city']} (AQI: {top_city.get('aqi_value', 'N/A')})")
    else:
        print(f"   ❌ Failed: {response.status_code}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 7: Statistics
print("\n7. Testing Statistics Endpoint...")
try:
    response = requests.get(f"{BASE_URL}/aqi/statistics")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Total cities: {data.get('total_cities', 'N/A')}")
        print(f"   ✅ Average AQI: {data.get('average_aqi', 'N/A')}")
        print(f"   ✅ Data points: {data.get('total_data_points', 'N/A')}")
    else:
        print(f"   ❌ Failed: {response.status_code}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "="*70)
print("✅ API Testing Complete!")
print("="*70)
print("\n📊 Frontend Dashboard Status:")
print("   🌐 Local: http://localhost:3001/")
print("   🚀 Deployed: https://aqi-react-dashboard.onrender.com")
print("\n💡 What to check in the dashboard:")
print("   1. City dropdown loads all cities")
print("   2. Current AQI data displays correctly")
print("   3. Historical charts render")
print("   4. Rankings table shows cities")
print("   5. Statistics update in real-time")
print("="*70 + "\n")
