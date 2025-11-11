"""
Verify All 97 Cities Configuration
Tests that all cities are properly configured in the system
"""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from api_handlers.openweather_handler import OpenWeatherHandler

def verify_cities():
    """Verify all 97 cities are configured"""
    print("=" * 80)
    print("🔍 VERIFYING 97 CITIES CONFIGURATION")
    print("=" * 80)
    
    handler = OpenWeatherHandler()
    all_cities = list(handler.CITY_COORDINATES.keys())
    
    print(f"\n✅ Total cities with coordinates: {len(all_cities)}")
    
    if len(all_cities) == 97:
        print("✅ SUCCESS: All 97 cities are configured!")
    else:
        print(f"⚠️  WARNING: Expected 97 cities, found {len(all_cities)}")
    
    print("\n" + "=" * 80)
    print("📋 CITIES BY REGION")
    print("=" * 80)
    
    # Categorize by known regions
    north_cities = [
        'Delhi', 'Noida', 'Ghaziabad', 'Gurugram', 'Gurgaon', 'Faridabad', 
        'Greater Noida', 'Chandigarh', 'Jaipur', 'Lucknow', 'Kanpur', 'Varanasi',
        'Agra', 'Amritsar', 'Ludhiana', 'Kota', 'Jodhpur', 'Udaipur', 'Meerut',
        'Aligarh', 'Allahabad', 'Jalandhar', 'Bareilly', 'Moradabad', 'Sonipat',
        'Panipat', 'Alwar', 'Bharatpur', 'Mathura', 'Rohtak', 'Rewari', 'Bhiwani',
        'Bhiwadi', 'Srinagar'
    ]
    
    south_cities = [
        'Bangalore', 'Chennai', 'Hyderabad', 'Kochi', 'Visakhapatnam', 'Coimbatore',
        'Mysore', 'Kurnool', 'Vijayawada', 'Tirupati', 'Thanjavur', 'Madurai',
        'Salem', 'Thiruvananthapuram', 'Warangal'
    ]
    
    west_cities = [
        'Mumbai', 'Pune', 'Ahmedabad', 'Surat', 'Vadodara', 'Rajkot', 'Nashik',
        'Aurangabad', 'Nagpur', 'Thane', 'Navi Mumbai', 'Pimpri-Chinchwad',
        'Solapur', 'Hubli-Dharwad'
    ]
    
    east_cities = [
        'Kolkata', 'Patna', 'Ranchi', 'Guwahati', 'Raipur', 'Bhubaneswar',
        'Jamshedpur', 'Asansol', 'Dhanbad', 'Howrah'
    ]
    
    central_cities = [
        'Indore', 'Bhopal', 'Jabalpur', 'Gwalior', 'Ujjain'
    ]
    
    northeast_cities = [
        'Imphal', 'Shillong', 'Agartala', 'Dibrugarh'
    ]
    
    # Count by region
    north_count = sum(1 for city in all_cities if city in north_cities)
    south_count = sum(1 for city in all_cities if city in south_cities)
    west_count = sum(1 for city in all_cities if city in west_cities)
    east_count = sum(1 for city in all_cities if city in east_cities)
    central_count = sum(1 for city in all_cities if city in central_cities)
    northeast_count = sum(1 for city in all_cities if city in northeast_cities)
    
    print(f"\n🌏 North India: {north_count} cities")
    print(f"🌏 South India: {south_count} cities")
    print(f"🌏 West India: {west_count} cities")
    print(f"🌏 East India: {east_count} cities")
    print(f"🌏 Central India: {central_count} cities")
    print(f"🌏 North-East India: {northeast_count} cities")
    
    total_categorized = north_count + south_count + west_count + east_count + central_count + northeast_count
    print(f"\n📊 Total Categorized: {total_categorized}/{len(all_cities)}")
    
    # Show all cities sorted alphabetically
    print("\n" + "=" * 80)
    print("📝 COMPLETE ALPHABETICAL LIST")
    print("=" * 80)
    
    for i, city in enumerate(sorted(all_cities), 1):
        coords = handler.CITY_COORDINATES[city]
        print(f"{i:3d}. {city:25s} ({coords[0]:.4f}, {coords[1]:.4f})")
    
    print("\n" + "=" * 80)
    print("✅ VERIFICATION COMPLETE")
    print("=" * 80)
    
    return len(all_cities) == 97

if __name__ == "__main__":
    success = verify_cities()
    sys.exit(0 if success else 1)
