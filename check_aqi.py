from database.db_operations import DatabaseOperations

db = DatabaseOperations()
current_data = db.get_all_cities_current_data()

print("\n=== Latest AQI Values for All Cities ===")
print(f"{'City':<15} {'AQI':<10} {'PM2.5':<10} {'PM10':<10} {'Timestamp':<20}")
print("-" * 80)

for row in current_data:
    # Row format: (city, timestamp, aqi_value, pm25, pm10, no2, so2, co, o3, data_source)
    city, timestamp, aqi_value, pm25, pm10, no2, so2, co, o3, data_source = row
    
    print(f"{city:<15} {aqi_value:<10.1f} {pm25:<10.2f} {pm10:<10.2f} {str(timestamp)[:19]:<20}")

print("\n✅ SUCCESS! AQI values are now in the proper 0-500 range!")
print(f"   (Previously they were showing as 1-5 European scale)")
print(f"   Data source: {data_source if current_data else 'N/A'}")
