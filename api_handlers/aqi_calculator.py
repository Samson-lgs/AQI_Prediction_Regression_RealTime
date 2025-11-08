"""
AQI Calculation Utilities
Implements EPA AQI calculation from pollutant concentrations
"""
import logging

logger = logging.getLogger(__name__)


def calculate_aqi_from_pm25(pm25: float) -> int:
    """
    Calculate AQI from PM2.5 concentration (μg/m³) using EPA breakpoints
    
    Args:
        pm25: PM2.5 concentration in μg/m³
        
    Returns:
        int: Calculated AQI value (0-500)
    """
    if pm25 is None or pm25 < 0:
        return 0
    
    # EPA AQI breakpoints for PM2.5 (24-hour)
    breakpoints = [
        (0, 12.0, 0, 50),        # Good
        (12.1, 35.4, 51, 100),   # Moderate
        (35.5, 55.4, 101, 150),  # Unhealthy for Sensitive Groups
        (55.5, 150.4, 151, 200), # Unhealthy
        (150.5, 250.4, 201, 300),# Very Unhealthy
        (250.5, 500.4, 301, 500) # Hazardous
    ]
    
    for bp_lo, bp_hi, aqi_lo, aqi_hi in breakpoints:
        if bp_lo <= pm25 <= bp_hi:
            # Linear interpolation formula
            aqi = ((aqi_hi - aqi_lo) / (bp_hi - bp_lo)) * (pm25 - bp_lo) + aqi_lo
            return round(aqi)
    
    # If PM2.5 is above 500.4, return max AQI
    if pm25 > 500.4:
        return 500
    
    return 0


def calculate_aqi_from_pm10(pm10: float) -> int:
    """
    Calculate AQI from PM10 concentration (μg/m³) using EPA breakpoints
    
    Args:
        pm10: PM10 concentration in μg/m³
        
    Returns:
        int: Calculated AQI value (0-500)
    """
    if pm10 is None or pm10 < 0:
        return 0
    
    # EPA AQI breakpoints for PM10 (24-hour)
    breakpoints = [
        (0, 54, 0, 50),         # Good
        (55, 154, 51, 100),     # Moderate
        (155, 254, 101, 150),   # Unhealthy for Sensitive Groups
        (255, 354, 151, 200),   # Unhealthy
        (355, 424, 201, 300),   # Very Unhealthy
        (425, 604, 301, 500)    # Hazardous
    ]
    
    for bp_lo, bp_hi, aqi_lo, aqi_hi in breakpoints:
        if bp_lo <= pm10 <= bp_hi:
            aqi = ((aqi_hi - aqi_lo) / (bp_hi - bp_lo)) * (pm10 - bp_lo) + aqi_lo
            return round(aqi)
    
    # If PM10 is above 604, return max AQI
    if pm10 > 604:
        return 500
    
    return 0


def calculate_india_aqi_from_pm25(pm25: float) -> int:
    """
    Calculate AQI from PM2.5 using India National AQI (NAQI) breakpoints
    
    Args:
        pm25: PM2.5 concentration in μg/m³
        
    Returns:
        int: India AQI value (0-500)
    """
    if pm25 is None or pm25 < 0:
        return 0
    
    # India NAQI breakpoints for PM2.5 (24-hour)
    breakpoints = [
        (0, 30, 0, 50),          # Good
        (31, 60, 51, 100),       # Satisfactory
        (61, 90, 101, 200),      # Moderately Polluted
        (91, 120, 201, 300),     # Poor
        (121, 250, 301, 400),    # Very Poor
        (251, 380, 401, 500)     # Severe
    ]
    
    for bp_lo, bp_hi, aqi_lo, aqi_hi in breakpoints:
        if bp_lo <= pm25 <= bp_hi:
            aqi = ((aqi_hi - aqi_lo) / (bp_hi - bp_lo)) * (pm25 - bp_lo) + aqi_lo
            return round(aqi)
    
    if pm25 > 380:
        return 500
    
    return 0


def calculate_india_aqi_from_pm10(pm10: float) -> int:
    """
    Calculate AQI from PM10 using India National AQI (NAQI) breakpoints
    
    Args:
        pm10: PM10 concentration in μg/m³
        
    Returns:
        int: India AQI value (0-500)
    """
    if pm10 is None or pm10 < 0:
        return 0
    
    # India NAQI breakpoints for PM10 (24-hour)
    breakpoints = [
        (0, 50, 0, 50),          # Good
        (51, 100, 51, 100),      # Satisfactory
        (101, 250, 101, 200),    # Moderately Polluted
        (251, 350, 201, 300),    # Poor
        (351, 430, 301, 400),    # Very Poor
        (431, 550, 401, 500)     # Severe
    ]
    
    for bp_lo, bp_hi, aqi_lo, aqi_hi in breakpoints:
        if bp_lo <= pm10 <= bp_hi:
            aqi = ((aqi_hi - aqi_lo) / (bp_hi - bp_lo)) * (pm10 - bp_lo) + aqi_lo
            return round(aqi)
    
    if pm10 > 550:
        return 500
    
    return 0


def calculate_india_aqi_from_no2(no2: float) -> int:
    """
    Calculate AQI from NO2 using India National AQI breakpoints
    
    Args:
        no2: NO2 concentration in μg/m³
        
    Returns:
        int: India AQI value (0-500)
    """
    if no2 is None or no2 < 0:
        return 0
    
    # India NAQI breakpoints for NO2 (24-hour)
    breakpoints = [
        (0, 40, 0, 50),          # Good
        (41, 80, 51, 100),       # Satisfactory
        (81, 180, 101, 200),     # Moderately Polluted
        (181, 280, 201, 300),    # Poor
        (281, 400, 301, 400),    # Very Poor
        (401, 550, 401, 500)     # Severe
    ]
    
    for bp_lo, bp_hi, aqi_lo, aqi_hi in breakpoints:
        if bp_lo <= no2 <= bp_hi:
            aqi = ((aqi_hi - aqi_lo) / (bp_hi - bp_lo)) * (no2 - bp_lo) + aqi_lo
            return round(aqi)
    
    if no2 > 550:
        return 500
    
    return 0


def calculate_india_aqi_from_so2(so2: float) -> int:
    """
    Calculate AQI from SO2 using India National AQI breakpoints
    
    Args:
        so2: SO2 concentration in μg/m³
        
    Returns:
        int: India AQI value (0-500)
    """
    if so2 is None or so2 < 0:
        return 0
    
    # India NAQI breakpoints for SO2 (24-hour)
    breakpoints = [
        (0, 40, 0, 50),          # Good
        (41, 80, 51, 100),       # Satisfactory
        (81, 380, 101, 200),     # Moderately Polluted
        (381, 800, 201, 300),    # Poor
        (801, 1600, 301, 400),   # Very Poor
        (1601, 2100, 401, 500)   # Severe
    ]
    
    for bp_lo, bp_hi, aqi_lo, aqi_hi in breakpoints:
        if bp_lo <= so2 <= bp_hi:
            aqi = ((aqi_hi - aqi_lo) / (bp_hi - bp_lo)) * (so2 - bp_lo) + aqi_lo
            return round(aqi)
    
    if so2 > 2100:
        return 500
    
    return 0


def calculate_india_aqi_from_co(co: float) -> int:
    """
    Calculate AQI from CO using India National AQI breakpoints
    
    Args:
        co: CO concentration in mg/m³
        
    Returns:
        int: India AQI value (0-500)
    """
    if co is None or co < 0:
        return 0
    
    # India NAQI breakpoints for CO (8-hour)
    breakpoints = [
        (0, 1.0, 0, 50),         # Good
        (1.1, 2.0, 51, 100),     # Satisfactory
        (2.1, 10, 101, 200),     # Moderately Polluted
        (10.1, 17, 201, 300),    # Poor
        (17.1, 34, 301, 400),    # Very Poor
        (34.1, 50, 401, 500)     # Severe
    ]
    
    for bp_lo, bp_hi, aqi_lo, aqi_hi in breakpoints:
        if bp_lo <= co <= bp_hi:
            aqi = ((aqi_hi - aqi_lo) / (bp_hi - bp_lo)) * (co - bp_lo) + aqi_lo
            return round(aqi)
    
    if co > 50:
        return 500
    
    return 0


def calculate_india_aqi_from_o3(o3: float) -> int:
    """
    Calculate AQI from O3 using India National AQI breakpoints
    
    Args:
        o3: O3 concentration in μg/m³
        
    Returns:
        int: India AQI value (0-500)
    """
    if o3 is None or o3 < 0:
        return 0
    
    # India NAQI breakpoints for O3 (8-hour)
    breakpoints = [
        (0, 50, 0, 50),          # Good
        (51, 100, 51, 100),      # Satisfactory
        (101, 168, 101, 200),    # Moderately Polluted
        (169, 208, 201, 300),    # Poor
        (209, 748, 301, 400),    # Very Poor
        (749, 1000, 401, 500)    # Severe
    ]
    
    for bp_lo, bp_hi, aqi_lo, aqi_hi in breakpoints:
        if bp_lo <= o3 <= bp_hi:
            aqi = ((aqi_hi - aqi_lo) / (bp_hi - bp_lo)) * (o3 - bp_lo) + aqi_lo
            return round(aqi)
    
    if o3 > 1000:
        return 500
    
    return 0


def calculate_india_aqi(pm25: float = None, pm10: float = None, no2: float = None, 
                        so2: float = None, co: float = None, o3: float = None) -> dict:
    """
    Calculate overall India National AQI from multiple pollutants
    Returns the maximum AQI value and the dominant pollutant
    
    Args:
        pm25: PM2.5 concentration in μg/m³
        pm10: PM10 concentration in μg/m³
        no2: NO2 concentration in μg/m³
        so2: SO2 concentration in μg/m³
        co: CO concentration in mg/m³
        o3: O3 concentration in μg/m³
        
    Returns:
        dict: {
            'aqi': int (0-500),
            'dominant_pollutant': str,
            'sub_index': dict of individual pollutant AQIs
        }
    """
    sub_index = {}
    
    # Calculate AQI for each available pollutant
    if pm25 is not None and pm25 > 0:
        sub_index['PM2.5'] = calculate_india_aqi_from_pm25(pm25)
    
    if pm10 is not None and pm10 > 0:
        sub_index['PM10'] = calculate_india_aqi_from_pm10(pm10)
    
    if no2 is not None and no2 > 0:
        sub_index['NO2'] = calculate_india_aqi_from_no2(no2)
    
    if so2 is not None and so2 > 0:
        sub_index['SO2'] = calculate_india_aqi_from_so2(so2)
    
    if co is not None and co > 0:
        sub_index['CO'] = calculate_india_aqi_from_co(co)
    
    if o3 is not None and o3 > 0:
        sub_index['O3'] = calculate_india_aqi_from_o3(o3)
    
    # Return maximum AQI (worst pollutant determines overall AQI)
    if sub_index:
        dominant_pollutant = max(sub_index, key=sub_index.get)
        final_aqi = sub_index[dominant_pollutant]
        logger.debug(f"Calculated India AQI: {final_aqi}, dominant: {dominant_pollutant}")
        return {
            'aqi': final_aqi,
            'dominant_pollutant': dominant_pollutant,
            'sub_index': sub_index
        }
    
    return {
        'aqi': 0,
        'dominant_pollutant': None,
        'sub_index': {}
    }


def calculate_aqi(pm25: float = None, pm10: float = None, no2: float = None, 
                  so2: float = None, co: float = None, o3: float = None) -> int:
    """
    Calculate overall AQI from multiple pollutants (EPA standard)
    Returns the maximum AQI value among all pollutants
    
    Args:
        pm25: PM2.5 concentration in μg/m³
        pm10: PM10 concentration in μg/m³
        no2: NO2 concentration in μg/m³
        so2: SO2 concentration in μg/m³
        co: CO concentration in mg/m³
        o3: O3 concentration in μg/m³
        
    Returns:
        int: Overall AQI value (0-500)
    """
    aqi_values = []
    
    # Calculate AQI for each available pollutant
    if pm25 is not None and pm25 > 0:
        aqi_values.append(calculate_aqi_from_pm25(pm25))
    
    if pm10 is not None and pm10 > 0:
        aqi_values.append(calculate_aqi_from_pm10(pm10))
    
    # Return maximum AQI (worst pollutant determines overall AQI)
    if aqi_values:
        final_aqi = max(aqi_values)
        logger.debug(f"Calculated AQI: {final_aqi} from PM2.5={pm25}, PM10={pm10}")
        return final_aqi
    
    return 0


def get_aqi_category(aqi: int) -> dict:
    """
    Get AQI category information based on value
    
    Args:
        aqi: AQI value
        
    Returns:
        dict: Category information with label, color, and health implications
    """
    if aqi <= 50:
        return {
            'category': 'Good',
            'color': '#00e400',
            'level': 'good',
            'health_implications': 'Air quality is satisfactory'
        }
    elif aqi <= 100:
        return {
            'category': 'Moderate',
            'color': '#ffff00',
            'level': 'moderate',
            'health_implications': 'Acceptable for most people'
        }
    elif aqi <= 150:
        return {
            'category': 'Unhealthy for Sensitive Groups',
            'color': '#ff7e00',
            'level': 'unhealthy_sensitive',
            'health_implications': 'Sensitive groups may experience health effects'
        }
    elif aqi <= 200:
        return {
            'category': 'Unhealthy',
            'color': '#ff0000',
            'level': 'unhealthy',
            'health_implications': 'Everyone may begin to experience health effects'
        }
    elif aqi <= 300:
        return {
            'category': 'Very Unhealthy',
            'color': '#8f3f97',
            'level': 'very_unhealthy',
            'health_implications': 'Health alert: everyone may experience serious effects'
        }
    else:
        return {
            'category': 'Hazardous',
            'color': '#7e0023',
            'level': 'hazardous',
            'health_implications': 'Health warnings of emergency conditions'
        }
