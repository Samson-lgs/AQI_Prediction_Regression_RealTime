from database.db_operations import DatabaseOperations

db = DatabaseOperations()
data = db.get_all_cities_current_data()

missing_cities = ['Pimpri-Chinchwad', 'Navi Mumbai', 'Faridabad', 'Greater Noida', 'Gurgaon', 'Meerut', 'Aligarh']

print("\n=== Status of Previously Missing Cities ===\n")
for city_name in missing_cities:
    city_data = [d for d in data if d[0] == city_name]
    if city_data:
        city, timestamp, aqi_value, pm25, pm10 = city_data[0][:5]
        status = "✅ UPDATED" if aqi_value > 10 else "❌ Still old"
        print(f"{city:<20} AQI: {aqi_value:<6.0f}  {status}  (Updated: {str(timestamp)[:19]})")
    else:
        print(f"{city_name:<20} NOT FOUND IN DATABASE")

# Count all cities with old vs new AQI
old_aqi = [d for d in data if d[2] <= 5]
new_aqi = [d for d in data if d[2] > 5]

print(f"\n=== Overall Status ===")
print(f"Total cities in database: {len(data)}")
print(f"Cities with corrected AQI (0-500): {len(new_aqi)}")
print(f"Cities still with old AQI (1-5): {len(old_aqi)}")

if old_aqi:
    print(f"\n=== Cities Still Needing Update ===")
    for city in old_aqi:
        print(f"  {city[0]}: AQI {city[2]}")
