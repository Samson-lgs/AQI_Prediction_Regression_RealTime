"""
Quick script to test all Render backend endpoints
Run this to see which endpoints are working
"""
import requests
import json

BASE_URL = "https://aqi-backend-api.onrender.com"

endpoints = [
    "/",
    "/health", 
    "/api/v1/cities",
    "/api/v1/health",
    "/api/v1/docs",
]

print("="*70)
print("TESTING RENDER BACKEND ENDPOINTS")
print("="*70)
print(f"Base URL: {BASE_URL}\n")

for endpoint in endpoints:
    url = BASE_URL + endpoint
    print(f"Testing: {url}")
    try:
        response = requests.get(url, timeout=10)
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                if len(str(data)) < 200:
                    print(f"  Response: {json.dumps(data, indent=2)}")
                else:
                    print(f"  Response: {str(data)[:200]}...")
            except:
                print(f"  Response: {response.text[:200]}")
        else:
            print(f"  Error: {response.text}")
    except requests.exceptions.Timeout:
        print(f"  ERROR: Request timed out (backend may be cold starting)")
    except requests.exceptions.ConnectionError:
        print(f"  ERROR: Connection failed (backend may be down)")
    except Exception as e:
        print(f"  ERROR: {str(e)}")
    print()

print("="*70)
print("RECOMMENDATIONS:")
print("="*70)

print("""
If ALL endpoints return 404:
  → Render hasn't redeployed yet with latest code
  → Go to https://dashboard.render.com/
  → Click on 'aqi-backend-api'
  → Click 'Manual Deploy' → 'Deploy latest commit'

If /health returns 404 but /api/v1/cities works:
  → Backend deployed but using old code
  → Wait 1-2 minutes and retry

If you see timeout errors:
  → Backend is cold starting (free tier)
  → Wait 30 seconds and retry

If /api/v1/cities returns data:
  → Backend is working! ✅
  → Update frontend config if needed
""")
