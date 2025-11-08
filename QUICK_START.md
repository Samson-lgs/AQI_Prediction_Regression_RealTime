# 🌍 AQI System - Quick Start Guide

## What's New! 🎉

Your AQI Prediction System now includes a **complete interactive dashboard** with:

### ✨ Key Features

1. **🗺️ Live Interactive Map**
   - View all 96 Indian cities on a map
   - Color-coded markers by AQI level
   - Click any city for instant details

2. **📈 Historical Analysis**
   - View trends over 7, 14, or 30 days
   - PM2.5 and PM10 concentration graphs
   - Identify patterns and seasonal changes

3. **⚖️ Multi-City Comparison**
   - Compare up to 6 cities side-by-side
   - Real-time metrics and charts
   - See which cities have the best/worst air quality

4. **🔔 Smart Email Alerts**
   - Set custom AQI thresholds
   - Get notified when air quality degrades
   - Manage alerts for multiple cities

5. **💊 Health Recommendations**
   - Real-time health impact assessments
   - Activity guidance (exercise, outdoor activities)
   - At-risk group identification
   - Emergency protocols for hazardous conditions

---

## 🚀 Quick Start (3 Steps)

### Step 1: Start the System
```bash
# Activate virtual environment
.venv\Scripts\Activate.ps1

# Collect latest data (one-time)
python run_complete_system.py collect

# Start the backend server
python run_complete_system.py server
```

### Step 2: Access the Dashboards

**New Interactive Dashboard** (Recommended):
```
http://localhost:5000/frontend/dashboard.html
```

**Original Prediction Dashboard**:
```
http://localhost:5000/frontend/index.html
```

### Step 3: (Optional) Configure Email Alerts

Edit your `.env` file:
```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your.email@gmail.com
SMTP_PASSWORD=your_app_password  # Use Gmail App Password
SMTP_FROM=AQI Alerts <noreply@aqiapp.com>
SMTP_TLS=true
```

---

## 📱 Dashboard Tour

### Tab 1: Live Map 🗺️
- **Purpose**: See air quality across India at a glance
- **Usage**: 
  - Red/purple cities = Poor air quality
  - Green/yellow cities = Good air quality
  - Click markers for details
  - Scroll down for city rankings

### Tab 2: Historical Trends 📈
- **Purpose**: Analyze AQI patterns over time
- **Usage**:
  1. Select a city from dropdown
  2. Choose time period (7/14/30 days)
  3. View AQI trend and pollutant graphs
  - Helps identify: Weekly patterns, seasonal changes, improvement/degradation

### Tab 3: City Comparison ⚖️
- **Purpose**: Compare multiple cities
- **Usage**:
  1. Click city buttons to select (max 6)
  2. View side-by-side cards with all metrics
  3. Compare using bar chart
  - Great for: Relocation decisions, travel planning, regional analysis

### Tab 4: Alerts & Health 🔔
- **Purpose**: Set up monitoring and get health guidance
- **Usage**:
  - **Create Alert**: Enter city, email, threshold → Submit
  - **View Alerts**: See all active alerts below form
  - **Health Info**: Select city → Get recommendations
  - Recommendations adapt to AQI level (Good → Hazardous)

---

## 🎨 Understanding Color Codes

| AQI Range | Color | Category | What it Means |
|-----------|-------|----------|---------------|
| 0-50 | 🟢 Green | Good | Air quality is great! |
| 51-100 | 🟡 Yellow | Moderate | Acceptable for most |
| 101-150 | 🟠 Orange | Unhealthy (Sensitive) | Sensitive groups affected |
| 151-200 | 🔴 Red | Unhealthy | Everyone may feel effects |
| 201-300 | 🟣 Purple | Very Unhealthy | Health alert! |
| 301-500 | 🟤 Maroon | Hazardous | Emergency! Stay indoors |

---

## 🔧 System Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Data Collection                     │
│  OpenWeather API → PostgreSQL → Feature Engineering │
└─────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────┐
│              ML Models (5 Algorithms)                │
│  XGBoost | Random Forest | LSTM | Linear | Ensemble │
└─────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────┐
│                 Flask REST API                       │
│  /cities | /aqi | /forecast | /alerts | /models    │
└─────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────┐
│                Frontend Dashboards                   │
│  dashboard.html (New) | index.html (Predictions)    │
└─────────────────────────────────────────────────────┘
```

---

## 📊 API Endpoints Quick Reference

### Cities
- `GET /api/v1/cities` - List all cities
- `GET /api/v1/cities/coordinates/{city}` - Get lat/lon
- `GET /api/v1/cities/rankings?days=7` - City rankings

### AQI Data
- `GET /api/v1/aqi/current/{city}` - Current AQI
- `GET /api/v1/aqi/history/{city}?days=30` - Historical data

### Predictions
- `GET /api/v1/forecast/{city}?hours=24` - Get predictions
- `GET /api/v1/forecast/batch` - Multi-city predictions

### Alerts
- `POST /api/v1/alerts/create` - Create alert
- `GET /api/v1/alerts/list/{city}` - List alerts
- `POST /api/v1/alerts/deactivate/{id}` - Remove alert

### Models
- `GET /api/v1/models/performance` - Model metrics
- `GET /api/v1/models/compare` - Compare algorithms

---

## 🔄 Data Collection Schedule

**Automatic Schedule** (when server running):
- Every **1 hour**: Collect data for all 96 cities
- Data sources: OpenWeather (primary), IQAir (backup), CPCB (if available)

**Manual Collection**:
```bash
# Collect once
python run_complete_system.py collect

# Export to CSV
python run_complete_system.py export
```

---

## 🎯 Common Use Cases

### Use Case 1: Daily Air Quality Check
1. Open dashboard.html
2. Click "Live Map" tab
3. Find your city on map
4. Click marker for current AQI

### Use Case 2: Planning Outdoor Activities
1. Go to "Alerts & Health" tab
2. Select your city
3. Read activity recommendations
4. Check if it's safe to exercise outdoors

### Use Case 3: Comparing Cities for Relocation
1. Go to "City Comparison" tab
2. Select 4-6 cities you're considering
3. Compare AQI, PM2.5, PM10 levels
4. Check historical trends for seasonal patterns

### Use Case 4: Monitoring Air Quality Trends
1. Go to "Historical Trends" tab
2. Select your city
3. Choose 30-day period
4. Identify patterns (weekday vs weekend, seasonal)

### Use Case 5: Setting Up Alerts
1. Go to "Alerts & Health" tab
2. Fill in: City, Email, Threshold (e.g., 150)
3. Click "Create Alert"
4. You'll get emails when AQI > 150

---

## 🐛 Troubleshooting

### Dashboard shows "Loading..."
**Fix**: 
1. Check if backend is running: `http://localhost:5000/api/v1/cities`
2. Ensure data collection completed: `python run_complete_system.py collect`
3. Check browser console (F12) for errors

### Map not loading
**Fix**:
1. Check internet connection (needs OpenStreetMap tiles)
2. Disable ad blockers temporarily
3. Clear browser cache

### No email alerts received
**Fix**:
1. Verify SMTP settings in `.env`
2. Check spam/junk folder
3. For Gmail: Use App Password, not regular password
4. Check backend logs: `logs/main.log`

### Historical charts empty
**Fix**:
1. System needs 7+ days of data for meaningful charts
2. Run collection multiple times: `python run_complete_system.py collect`
3. Check if selected city has data in database

---

## 📈 Production Deployment (Render)

Your app is deployed at: `https://your-app.onrender.com`

**Access Dashboards**:
- Interactive: `https://your-app.onrender.com/frontend/dashboard.html`
- Predictions: `https://your-app.onrender.com/frontend/index.html`
- API Docs: `https://your-app.onrender.com/api/v1/docs`

**Update config.js** for production:
```javascript
const config = {
    API_BASE_URL: 'https://your-app.onrender.com/api/v1',
    DEFAULT_CITY: 'Delhi',
    FORECAST_HOURS: 48
};
```

---

## 📚 Further Documentation

- **Frontend Features**: `/frontend/DASHBOARD_GUIDE.md`
- **API Documentation**: `http://localhost:5000/api/v1/docs` (Swagger UI)
- **Project Overview**: `/docs/PROJECT_SUMMARY.md`
- **Database Schema**: `/database/create_db.sql`

---

## 🎓 Tips & Best Practices

### For Accurate Predictions
- Run data collection at least **daily**
- Maintain **30+ days** of historical data
- Monitor model performance in dashboard
- Retrain models monthly with new data

### For Effective Alerts
- Set threshold based on your sensitivity (100-150 for sensitive groups)
- Don't set threshold too low (< 50) - too many alerts
- Use different thresholds for different cities
- Check alerts work by testing with current high-AQI city

### For Performance
- Map loads faster with good internet
- Historical charts perform best with ≤ 30 days
- Limit city comparisons to 6 for speed
- Refresh page if charts seem stuck

---

## 🆘 Support

**Get Help**:
1. Check this guide first
2. Review `/frontend/DASHBOARD_GUIDE.md`
3. Check API at: `http://localhost:5000/api/v1/docs`
4. Review logs: `/logs/main.log`
5. GitHub Issues: Report bugs or request features

**Quick Debug Commands**:
```bash
# Check if backend running
curl http://localhost:5000/api/v1/cities

# Test specific city
curl http://localhost:5000/api/v1/aqi/current/Delhi

# View logs
Get-Content logs\main.log -Tail 50

# Restart system
python run_complete_system.py server
```

---

**System Version**: 2.0.0  
**Dashboard Version**: 1.0.0  
**Last Updated**: November 2025  

**Built with** ❤️ using Flask, PostgreSQL, Leaflet, Plotly, and Machine Learning
