"""
Test script for enhanced API endpoints
Tests all new features: batch predictions, rankings, WebSocket, caching
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:5000/api/v1"

def print_section(title):
    print("\n" + "=" * 70)
    print(f"{title}")
    print("=" * 70)

def test_health():
    """Test health check endpoint"""
    print_section("TEST 1: Health Check")
    try:
        response = requests.get(f"{BASE_URL}/cities/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_cities_list():
    """Test cities list endpoint"""
    print_section("TEST 2: Cities List")
    try:
        response = requests.get(f"{BASE_URL}/cities/")
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Total cities: {len(data)}")
        print(f"First 5 cities: {data[:5]}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_city_rankings():
    """Test city rankings endpoint"""
    print_section("TEST 3: City Rankings")
    try:
        response = requests.get(f"{BASE_URL}/cities/rankings?days=7&metric=avg_aqi")
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Rankings: {json.dumps(data, indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_city_comparison():
    """Test city comparison endpoint"""
    print_section("TEST 4: City Comparison")
    try:
        cities = "Delhi,Mumbai,Bangalore"
        response = requests.get(f"{BASE_URL}/cities/compare?cities={cities}&days=7")
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Comparison: {json.dumps(data, indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_current_aqi():
    """Test current AQI endpoint"""
    print_section("TEST 5: Current AQI")
    try:
        city = "Delhi"
        response = requests.get(f"{BASE_URL}/aqi/current/{city}")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"City: {data.get('city')}")
            print(f"AQI: {data.get('aqi')}")
            print(f"PM2.5: {data.get('pm25')}")
            print(f"Timestamp: {data.get('timestamp')}")
        else:
            print(f"Response: {response.json()}")
        return response.status_code in [200, 404]  # 404 is acceptable if no data yet
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_all_cities_current():
    """Test all cities current AQI endpoint"""
    print_section("TEST 6: All Cities Current AQI")
    try:
        response = requests.get(f"{BASE_URL}/aqi/all/current")
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Total cities: {data.get('total_cities')}")
        print(f"First city data: {data.get('data', [])[0] if data.get('data') else 'No data'}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_forecast_single():
    """Test single city forecast endpoint"""
    print_section("TEST 7: Single City Forecast")
    try:
        city = "Delhi"
        response = requests.get(f"{BASE_URL}/forecast/{city}?hours=24")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"City: {data.get('city')}")
            print(f"Model: {data.get('model_used')}")
            print(f"Forecast hours: {data.get('forecast_hours')}")
            print(f"Predictions: {len(data.get('predictions', []))}")
            if data.get('predictions'):
                print(f"First prediction: {data['predictions'][0]}")
        else:
            print(f"Response: {response.json()}")
        return response.status_code in [200, 404]
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_batch_forecast():
    """Test batch forecast endpoint"""
    print_section("TEST 8: Batch Forecast")
    try:
        payload = {
            "cities": ["Delhi", "Mumbai", "Bangalore"],
            "hours_ahead": 12
        }
        response = requests.post(
            f"{BASE_URL}/forecast/batch",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Total cities: {data.get('total_cities')}")
            print(f"Successful: {data.get('successful')}")
            print(f"Response: {json.dumps(data, indent=2)[:500]}...")  # First 500 chars
        else:
            print(f"Response: {response.json()}")
        return response.status_code in [200, 404]
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_model_comparison():
    """Test model comparison endpoint"""
    print_section("TEST 9: Model Comparison")
    try:
        response = requests.get(f"{BASE_URL}/models/compare?city=Delhi&models=linear_regression,random_forest,xgboost")
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Comparison: {json.dumps(data, indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_create_alert():
    """Test alert creation endpoint"""
    print_section("TEST 10: Create Alert")
    try:
        payload = {
            "city": "Delhi",
            "threshold": 200,
            "alert_type": "email",
            "contact": "user@example.com"
        }
        response = requests.post(
            f"{BASE_URL}/alerts/create",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Alert created: {json.dumps(data, indent=2)}")
        return response.status_code == 201
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_cache_stats():
    """Test cache statistics endpoint"""
    print_section("TEST 11: Cache Statistics")
    try:
        response = requests.get("http://localhost:5000/api/v1/cache/stats")
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Cache stats: {json.dumps(data, indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_swagger_docs():
    """Test Swagger documentation"""
    print_section("TEST 12: Swagger Documentation")
    try:
        response = requests.get("http://localhost:5000/api/v1/docs")
        print(f"Status: {response.status_code}")
        print(f"Swagger UI available at: http://localhost:5000/api/v1/docs")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def run_all_tests():
    """Run all test cases"""
    print("\n" + "=" * 70)
    print("ENHANCED API TESTING")
    print("=" * 70)
    print(f"Testing API at: {BASE_URL}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    tests = [
        ("Health Check", test_health),
        ("Cities List", test_cities_list),
        ("City Rankings", test_city_rankings),
        ("City Comparison", test_city_comparison),
        ("Current AQI", test_current_aqi),
        ("All Cities Current", test_all_cities_current),
        ("Single Forecast", test_forecast_single),
        ("Batch Forecast", test_batch_forecast),
        ("Model Comparison", test_model_comparison),
        ("Create Alert", test_create_alert),
        ("Cache Stats", test_cache_stats),
        ("Swagger Docs", test_swagger_docs),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ Test '{test_name}' failed with exception: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print_section("TEST SUMMARY")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️ {total - passed} test(s) failed")
    
    print("\n" + "=" * 70)
    print("IMPORTANT: Make sure Flask server is running on http://localhost:5000")
    print("Start server with: python backend/app.py")
    print("=" * 70)

if __name__ == '__main__':
    run_all_tests()
