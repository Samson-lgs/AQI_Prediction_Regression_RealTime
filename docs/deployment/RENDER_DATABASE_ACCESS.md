# How to View Data in Render PostgreSQL Database

This guide shows you how to view and query the data stored in your PostgreSQL database on Render.

## Quick Start

### Method 1: Using the Python Script (Recommended)

1. **Get your DATABASE_URL from Render:**
   - Go to [Render Dashboard](https://dashboard.render.com/)
   - Click on your database: `aqi-database`
   - Go to **Info** tab
   - Copy the **Internal Database URL**
     ```
     postgres://aqi_user:password@dpg-xxx.oregon-postgres.render.com/aqi_db
     ```

2. **Run the viewer script:**
   ```powershell
   # Set the DATABASE_URL
   $env:DATABASE_URL='postgres://aqi_user:YOUR_PASSWORD@dpg-xxx.oregon-postgres.render.com/aqi_db'
   
   # Run the script
   .\aqi_env\Scripts\python.exe scripts\view_render_db_data.py
   ```

3. **What you'll see:**
   - All tables with row counts
   - Pollution data summary (total records, coverage by city)
   - Recent pollution data (last 15 records)
   - Predictions summary
   - Alerts summary

### Method 2: Using psql Command Line

1. **Install psql** (if not already installed):
   - Download from [PostgreSQL Downloads](https://www.postgresql.org/download/windows/)
   - Or use WSL with `sudo apt install postgresql-client`

2. **Connect to Render database:**
   ```powershell
   # Using DATABASE_URL
   psql "postgres://aqi_user:YOUR_PASSWORD@dpg-xxx.oregon-postgres.render.com/aqi_db"
   ```

3. **Useful SQL queries:**
   ```sql
   -- List all tables
   \dt
   
   -- View table structure
   \d pollution_data
   
   -- Count total records
   SELECT COUNT(*) FROM pollution_data;
   
   -- View recent data
   SELECT city, timestamp, aqi, pm25, pm10 
   FROM pollution_data 
   ORDER BY timestamp DESC 
   LIMIT 20;
   
   -- Count records per city
   SELECT city, COUNT(*) as count 
   FROM pollution_data 
   GROUP BY city 
   ORDER BY count DESC;
   
   -- View data from last 24 hours
   SELECT city, timestamp, aqi, pm25 
   FROM pollution_data 
   WHERE timestamp > NOW() - INTERVAL '24 hours'
   ORDER BY timestamp DESC;
   ```

### Method 3: Using Render Dashboard (Limited)

1. Go to Render Dashboard → Database → `aqi-database`
2. Click **Connect** → **PSQL Command**
3. This will show you the connection string
4. You can also use the **Shell** tab for basic queries

### Method 4: Using a GUI Tool (pgAdmin, DBeaver, etc.)

1. **Download DBeaver** (free): https://dbeaver.io/download/
2. **Create new connection:**
   - Database: PostgreSQL
   - Host: `dpg-xxx.oregon-postgres.render.com`
   - Port: `5432`
   - Database: `aqi_db`
   - Username: `aqi_user`
   - Password: (from Render Dashboard)

## Understanding Your Data

### Tables in Your Database

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `pollution_data` | Hourly air quality data | city, timestamp, aqi, pm25, pm10, temperature, humidity |
| `predictions` | Model predictions | city, prediction_time, predicted_aqi, model_name |
| `alerts` | User-configured alerts | city, threshold_type, threshold_value, is_active |
| `model_metrics` | Model performance tracking | model_name, accuracy, precision, timestamp |

### Pollution Data Fields

- **id**: Unique identifier
- **city**: City name (e.g., "Delhi", "Mumbai", "Bangalore")
- **timestamp**: UTC timestamp of data collection
- **aqi**: Air Quality Index (0-500)
- **pm25**: PM2.5 concentration (μg/m³)
- **pm10**: PM10 concentration (μg/m³)
- **so2**: Sulfur Dioxide (μg/m³)
- **no2**: Nitrogen Dioxide (μg/m³)
- **co**: Carbon Monoxide (μg/m³)
- **o3**: Ozone (μg/m³)
- **temperature**: Temperature (°C)
- **humidity**: Humidity (%)
- **wind_speed**: Wind speed (m/s)
- **pressure**: Atmospheric pressure (hPa)

## Common Queries

### Check Data Collection Progress

```sql
-- Total hours of data collected
SELECT COUNT(DISTINCT DATE_TRUNC('hour', timestamp)) as hours_collected
FROM pollution_data;

-- Data coverage per city
SELECT 
    city,
    COUNT(*) as total_records,
    COUNT(DISTINCT DATE_TRUNC('hour', timestamp)) as hours_collected,
    MIN(timestamp) as first_record,
    MAX(timestamp) as latest_record
FROM pollution_data
GROUP BY city
ORDER BY hours_collected DESC;

-- Data collected in last 24 hours
SELECT 
    city,
    COUNT(*) as records_last_24h
FROM pollution_data
WHERE timestamp > NOW() - INTERVAL '24 hours'
GROUP BY city
ORDER BY records_last_24h DESC;
```

### Check Data Quality

```sql
-- Find missing values
SELECT 
    COUNT(*) as total,
    COUNT(aqi) as has_aqi,
    COUNT(pm25) as has_pm25,
    COUNT(pm10) as has_pm10
FROM pollution_data;

-- Find cities with highest AQI
SELECT 
    city,
    MAX(aqi) as max_aqi,
    AVG(aqi) as avg_aqi
FROM pollution_data
WHERE timestamp > NOW() - INTERVAL '7 days'
GROUP BY city
ORDER BY max_aqi DESC;
```

### Export Data

```sql
-- Export to CSV (in psql)
\copy (SELECT * FROM pollution_data ORDER BY timestamp DESC LIMIT 1000) TO 'pollution_data.csv' CSV HEADER;
```

## Troubleshooting

### Connection Failed

**Error:** `fe_sendauth: no password supplied`
- **Solution:** Make sure you've set the DATABASE_URL with the correct password

**Error:** `could not connect to server`
- **Solution:** 
  - Check if you're using the **Internal Database URL** (not External)
  - Verify the hostname starts with `dpg-`
  - Make sure your database is running on Render

### No Data Found

If tables are empty:
1. Check if the GitHub Actions workflow is running (hourly data collection)
2. Check Render logs for the backend service
3. Verify API keys are set correctly in Render environment variables

### Database Credentials

To get your credentials from Render:
1. Dashboard → Database → `aqi-database`
2. Info tab → Connection Details
3. Click "Show" to reveal password

## Security Notes

- **Never commit** the DATABASE_URL or password to Git
- Use environment variables for all database credentials
- The Internal Database URL is only accessible from Render services
- For local access, you need the External Database URL (with additional security setup)

## Next Steps

After viewing your data:
- Check data quality and coverage
- Verify all cities are being collected
- Monitor for gaps in hourly collection
- Set up alerts for data collection failures
- Export data for local analysis if needed
