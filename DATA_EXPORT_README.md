# Air Quality Data Export Tool

## Overview
This tool exports air quality and pollution data from the database to CSV files in table format with complete records.

## Generated CSV Files

### 1. `pollution_data_export.csv`
Complete pollution data with all historical records (last 30 days by default).

**Columns:**
- `id` - Record ID
- `city` - City name
- `timestamp` - Date and time of measurement
- `date` - Date only
- `time` - Time only
- `hour` - Hour of day (0-23)
- `day_of_week` - Day name (Monday, Tuesday, etc.)
- `aqi_value` - Air Quality Index value
- `pm25` - PM2.5 particulate matter (μg/m³)
- `pm10` - PM10 particulate matter (μg/m³)
- `no2` - Nitrogen dioxide (μg/m³)
- `so2` - Sulfur dioxide (μg/m³)
- `co` - Carbon monoxide (μg/m³)
- `o3` - Ozone (μg/m³)
- `data_source` - Source of data (CPCB, OpenWeather, IQAir)
- `created_at` - Record creation timestamp

**Total Records:** 126  
**Cities Covered:** 66  
**Date Range:** 2025-11-04 to 2025-11-06

### 2. `current_aqi_all_cities.csv`
Latest AQI reading for each city (snapshot).

**Columns:**
- `city` - City name
- `timestamp` - Measurement timestamp
- `aqi_value` - Current AQI
- `pm25`, `pm10`, `no2`, `so2`, `co`, `o3` - Pollutant values
- `data_source` - Data source
- `created_at` - Record creation time

**Cities:** 66 cities sorted by AQI (worst air quality first)

## Usage

### Run the Export Tool

```powershell
# Activate virtual environment
.\.venv\Scripts\activate

# Run the export script
python export_data_to_csv.py
```

### Export Options

1. **Export pollution data (last 30 days)** - Complete pollution records
2. **Export weather data (last 30 days)** - Temperature, humidity, wind, etc.
3. **Export combined data** - Pollution + weather joined by city and timestamp
4. **Export current AQI** - Latest reading for all cities
5. **Export pollution data (custom days)** - Specify number of days
6. **Export specific city data** - Filter by city name
7. **Export ALL pollution data** - Entire database history

### Programmatic Usage

```python
from export_data_to_csv import DataExporter

exporter = DataExporter()

# Print database summary
exporter.print_summary()

# Export last 30 days of pollution data
exporter.export_pollution_data(days=30)

# Export specific city
exporter.export_pollution_data(
    output_file='delhi_data.csv',
    days=90,
    city_filter='Delhi'
)

# Export current AQI for all cities
exporter.export_all_current_data()

# Export combined pollution + weather
exporter.export_combined_data(days=30)
```

## Database Summary

```
============================================================
DATABASE SUMMARY
============================================================
Total Records:     126
Total Cities:      66
Earliest Date:     2025-11-04 20:06:02
Latest Date:       2025-11-06 07:31:36
Data Sources:      2 (OpenWeather, IQAir)
============================================================
```

## Sample Data

### Pollution Data Export Sample
| city | timestamp | aqi_value | pm25 | pm10 | no2 | so2 | co | o3 | data_source |
|------|-----------|-----------|------|------|-----|-----|----|-------|-------------|
| Kolkata | 2025-11-06 07:31:24 | 5 | 97.53 | 128.25 | 7.72 | 6.12 | 567.61 | 79.52 | OpenWeather |
| Dhanbad | 2025-11-06 07:31:19 | 5 | 88.13 | 121.79 | 6.75 | 2.81 | 457.12 | 18.43 | OpenWeather |
| Delhi | 2025-11-06 07:31:17 | 4 | 53.03 | 75.91 | 7.30 | 5.71 | 449.51 | 78.69 | OpenWeather |
| Mumbai | 2025-11-06 07:31:27 | 3 | 36.89 | 45.28 | 34.92 | 8.29 | 468.92 | 36.29 | OpenWeather |

### Current AQI Export Sample
Top 5 cities by AQI:
1. **Kolkata** - AQI: 5 (Very Poor)
2. **Dhanbad** - AQI: 5 (Very Poor)
3. **Ranchi** - AQI: 5 (Very Poor)
4. **Bareilly** - AQI: 5 (Very Poor)
5. **Patna** - AQI: 5 (Very Poor)

## AQI Scale Reference

| AQI Range | Category | Health Impact |
|-----------|----------|---------------|
| 0-50 | Good | Minimal impact |
| 51-100 | Satisfactory | Minor breathing discomfort |
| 101-200 | Moderate | Breathing discomfort for sensitive people |
| 201-300 | Poor | Breathing discomfort to most people |
| 301-400 | Very Poor | Respiratory illness to prolonged exposure |
| 401-500 | Severe | Affects healthy people and seriously impacts those with existing diseases |

## Features

✅ **Multiple Export Formats**
- Pollution data only
- Weather data only
- Combined pollution + weather
- Current snapshot
- Custom date ranges
- City-specific exports

✅ **Complete Data**
- All pollutants (PM2.5, PM10, NO2, SO2, CO, O3)
- AQI values
- Timestamps with timezone
- Data source tracking
- 66 cities covered

✅ **Data Quality**
- Cleaned and validated
- No duplicates (UNIQUE constraints)
- Indexed for fast queries
- Multiple data sources for reliability

## Files Generated

- `pollution_data_export.csv` - Historical pollution data
- `current_aqi_all_cities.csv` - Current AQI snapshot
- `weather_data_export.csv` - Weather data (optional)
- `combined_aqi_weather_export.csv` - Combined data (optional)
- `{city}_pollution_data.csv` - City-specific exports

## Requirements

```
pandas==1.5.3
psycopg2-binary==2.9.6
python-dotenv==1.0.0
```

## Environment Variables

Create a `.env` file with database credentials:

```env
DB_HOST=localhost
DB_NAME=aqi_db
DB_USER=postgres
DB_PASSWORD=your_password
DB_PORT=5432
```

## Notes

- CSV files use UTF-8 encoding
- Timestamps are in ISO 8601 format
- NULL values appear as empty cells in CSV
- Files can be opened in Excel, Google Sheets, or any CSV viewer
- Large exports may take a few seconds to complete

## Support

For issues or questions about data exports, check:
1. Database connection (`.env` file)
2. Python virtual environment activation
3. Required packages installed
4. Database contains data for requested date range

---

**Last Updated:** November 7, 2025  
**Script:** `export_data_to_csv.py`  
**Database:** PostgreSQL (aqi_db)
