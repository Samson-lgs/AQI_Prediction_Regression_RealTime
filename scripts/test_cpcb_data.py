"""Test CPCB API to get actual Delhi AQI data"""

from api_handlers.cpcb_handler import CPCBHandler
import json

def main():
    print("=" * 80)
    print("TESTING CPCB API FOR DELHI")
    print("=" * 80)
    
    cpcb = CPCBHandler()
    
    print("\n📡 Fetching Delhi data from CPCB...")
    delhi_data = cpcb.fetch_aqi_data('Delhi')
    
    if delhi_data:
        print(f"\n✅ Found {len(delhi_data)} monitoring stations in Delhi:\n")
        
        for i, station in enumerate(delhi_data, 1):
            print(f"\n{'='*80}")
            print(f"Station {i}: {station.get('location', 'Unknown')}")
            print(f"{'='*80}")
            print(f"  AQI Value: {station.get('aqi_value', 'N/A')}")
            print(f"  Quality: {station.get('quality', 'N/A')}")
            print(f"  Dominant Pollutant: {station.get('pollutant_dominant', 'N/A')}")
            print(f"\n  Pollutant Concentrations:")
            print(f"    PM2.5: {station.get('pm25', 'N/A')} μg/m³")
            print(f"    PM10:  {station.get('pm10', 'N/A')} μg/m³")
            print(f"    NO2:   {station.get('no2', 'N/A')} μg/m³")
            print(f"    SO2:   {station.get('so2', 'N/A')} μg/m³")
            print(f"    CO:    {station.get('co', 'N/A')} mg/m³")
            print(f"    O3:    {station.get('o3', 'N/A')} μg/m³")
        
        # Find station with highest AQI
        max_station = max(delhi_data, key=lambda x: x.get('aqi_value', 0) or 0)
        print(f"\n{'='*80}")
        print(f"🔴 HIGHEST AQI STATION: {max_station.get('location')}")
        print(f"   AQI: {max_station.get('aqi_value')} - {max_station.get('quality')}")
        print(f"{'='*80}")
        
        # Calculate average AQI
        valid_aqis = [s['aqi_value'] for s in delhi_data if s.get('aqi_value')]
        if valid_aqis:
            avg_aqi = sum(valid_aqis) / len(valid_aqis)
            print(f"\n📊 Average AQI across all stations: {avg_aqi:.1f}")
        
    else:
        print("\n❌ No data received from CPCB API")
        print("Possible reasons:")
        print("  1. CPCB API might be down")
        print("  2. API key might be invalid")
        print("  3. City name format might not match")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
