"""
Quick Data Export - Simple Script
Export AQI data without interactive menu
"""

from export_data_to_csv import DataExporter
import sys

def quick_export_all():
    """Export all common formats quickly"""
    print("🚀 Quick Export Starting...\n")
    
    exporter = DataExporter()
    
    # 1. Current AQI snapshot
    print("📊 Exporting current AQI for all cities...")
    exporter.export_all_current_data('current_aqi_all_cities.csv')
    
    # 2. Last 30 days pollution data
    print("📊 Exporting pollution data (30 days)...")
    exporter.export_pollution_data('pollution_data_export.csv', days=30)
    
    # 3. Combined pollution + weather
    print("📊 Exporting combined data...")
    exporter.export_combined_data('combined_aqi_weather_export.csv', days=30)
    
    print("\n✅ All exports complete!")
    print("\nFiles created:")
    print("  • current_aqi_all_cities.csv")
    print("  • pollution_data_export.csv")
    print("  • combined_aqi_weather_export.csv")

def quick_export_city(city_name, days=90):
    """Export data for a specific city"""
    exporter = DataExporter()
    filename = f"{city_name.replace(' ', '_')}_data.csv"
    
    print(f"📊 Exporting {city_name} data ({days} days)...")
    exporter.export_pollution_data(filename, days=days, city_filter=city_name)
    print(f"✅ Export complete: {filename}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Export specific city
        city = sys.argv[1]
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 90
        quick_export_city(city, days)
    else:
        # Export all
        quick_export_all()
