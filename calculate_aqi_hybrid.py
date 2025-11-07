"""
Hybrid AQI Calculation System
Uses OpenWeather pollutant breakpoints but outputs traditional 0-500 AQI scale
This matches online portals while using standardized OpenWeather thresholds
"""

def calculate_aqi_from_pollutants(so2, no2, pm10, pm25, o3, co):
    """
    Calculate AQI (0-500) using OpenWeather breakpoints
    
    OpenWeather Index → Traditional AQI Mapping:
    Index 1 (Good) → AQI 0-50
    Index 2 (Fair) → AQI 51-100
    Index 3 (Moderate) → AQI 101-200
    Index 4 (Poor) → AQI 201-300
    Index 5 (Very Poor) → AQI 301-500
    
    Args:
        so2: Sulfur dioxide (μg/m³)
        no2: Nitrogen dioxide (μg/m³)
        pm10: Particulate matter 10 (μg/m³)
        pm25: Particulate matter 2.5 (μg/m³)
        o3: Ozone (μg/m³)
        co: Carbon monoxide (μg/m³)
    
    Returns:
        int: AQI value (0-500)
    """
    
    # Calculate index for each pollutant using OpenWeather breakpoints
    so2_aqi = calculate_pollutant_aqi(so2, 'so2')
    no2_aqi = calculate_pollutant_aqi(no2, 'no2')
    pm10_aqi = calculate_pollutant_aqi(pm10, 'pm10')
    pm25_aqi = calculate_pollutant_aqi(pm25, 'pm25')
    o3_aqi = calculate_pollutant_aqi(o3, 'o3')
    co_aqi = calculate_pollutant_aqi(co, 'co')
    
    # Take the maximum (worst) AQI
    final_aqi = max(so2_aqi, no2_aqi, pm10_aqi, pm25_aqi, o3_aqi, co_aqi)
    
    return int(final_aqi)


def calculate_pollutant_aqi(concentration, pollutant_type):
    """
    Calculate AQI for a single pollutant using OpenWeather breakpoints
    
    Args:
        concentration: Pollutant concentration in μg/m³
        pollutant_type: 'so2', 'no2', 'pm10', 'pm25', 'o3', or 'co'
    
    Returns:
        float: AQI value (0-500)
    """
    if concentration is None or concentration < 0:
        return 0
    
    # OpenWeather breakpoints with corresponding AQI ranges
    # Format: (concentration_low, concentration_high, aqi_low, aqi_high)
    breakpoints = {
        'so2': [
            (0, 20, 0, 50),           # Good
            (20, 80, 51, 100),        # Fair
            (80, 250, 101, 200),      # Moderate
            (250, 350, 201, 300),     # Poor
            (350, 1000, 301, 500)     # Very Poor
        ],
        'no2': [
            (0, 40, 0, 50),
            (40, 70, 51, 100),
            (70, 150, 101, 200),
            (150, 200, 201, 300),
            (200, 1000, 301, 500)
        ],
        'pm10': [
            (0, 20, 0, 50),
            (20, 50, 51, 100),
            (50, 100, 101, 200),
            (100, 200, 201, 300),
            (200, 600, 301, 500)
        ],
        'pm25': [
            (0, 10, 0, 50),
            (10, 25, 51, 100),
            (25, 50, 101, 200),
            (50, 75, 201, 300),
            (75, 500, 301, 500)
        ],
        'o3': [
            (0, 60, 0, 50),
            (60, 100, 51, 100),
            (100, 140, 101, 200),
            (140, 180, 201, 300),
            (180, 1000, 301, 500)
        ],
        'co': [
            (0, 4400, 0, 50),
            (4400, 9400, 51, 100),
            (9400, 12400, 101, 200),
            (12400, 15400, 201, 300),
            (15400, 50000, 301, 500)
        ]
    }
    
    pollutant_breakpoints = breakpoints.get(pollutant_type, [])
    
    # Find the appropriate breakpoint range
    for bp_lo, bp_hi, aqi_lo, aqi_hi in pollutant_breakpoints:
        if bp_lo <= concentration < bp_hi:
            # Linear interpolation
            aqi = ((aqi_hi - aqi_lo) / (bp_hi - bp_lo)) * (concentration - bp_lo) + aqi_lo
            return aqi
    
    # If concentration exceeds all ranges, return maximum AQI
    return 500


def get_aqi_category(aqi):
    """
    Get category name for AQI value
    
    Args:
        aqi: AQI value (0-500)
    
    Returns:
        str: Category name
    """
    if aqi <= 50:
        return 'Good'
    elif aqi <= 100:
        return 'Satisfactory'
    elif aqi <= 200:
        return 'Moderate'
    elif aqi <= 300:
        return 'Poor'
    elif aqi <= 400:
        return 'Very Poor'
    else:
        return 'Severe'


def get_aqi_description(aqi):
    """
    Get health implications for AQI value
    
    Args:
        aqi: AQI value (0-500)
    
    Returns:
        str: Health implications
    """
    if aqi <= 50:
        return 'Minimal impact'
    elif aqi <= 100:
        return 'Minor breathing discomfort to sensitive people'
    elif aqi <= 200:
        return 'Breathing discomfort to people with lung, heart disease'
    elif aqi <= 300:
        return 'Breathing discomfort to most people on prolonged exposure'
    elif aqi <= 400:
        return 'Respiratory illness on prolonged exposure'
    else:
        return 'Affects healthy people and seriously impacts those with existing diseases'


# Test the calculation
if __name__ == "__main__":
    print("\n" + "="*80)
    print("HYBRID AQI SYSTEM TEST")
    print("OpenWeather Breakpoints → Traditional 0-500 AQI Scale")
    print("="*80 + "\n")
    
    test_cases = [
        {
            'city': 'Delhi',
            'so2': 2.34,
            'no2': 5.76,
            'pm10': 69.49,
            'pm25': 43.11,
            'o3': 84.16,
            'co': 373.29
        },
        {
            'city': 'Mumbai',
            'so2': 3.45,
            'no2': 8.92,
            'pm10': 78.34,
            'pm25': 52.67,
            'o3': 92.45,
            'co': 456.78
        },
        {
            'city': 'Bangalore',
            'so2': 1.89,
            'no2': 4.23,
            'pm10': 45.67,
            'pm25': 28.34,
            'o3': 76.89,
            'co': 289.45
        }
    ]
    
    for test in test_cases:
        aqi = calculate_aqi_from_pollutants(
            test['so2'], test['no2'], test['pm10'],
            test['pm25'], test['o3'], test['co']
        )
        category = get_aqi_category(aqi)
        description = get_aqi_description(aqi)
        
        print(f"City: {test['city']}")
        print(f"  Pollutants:")
        print(f"    SO₂: {test['so2']:.2f} μg/m³")
        print(f"    NO₂: {test['no2']:.2f} μg/m³")
        print(f"    PM10: {test['pm10']:.2f} μg/m³")
        print(f"    PM2.5: {test['pm25']:.2f} μg/m³")
        print(f"    O₃: {test['o3']:.2f} μg/m³")
        print(f"    CO: {test['co']:.2f} μg/m³")
        print(f"  AQI: {aqi} ({category})")
        print(f"  Health: {description}")
        print()
    
    print("="*80 + "\n")
