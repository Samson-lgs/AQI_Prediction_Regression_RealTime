# AQI Interactive Dashboard - Features Guide

## 🎯 Overview
The enhanced AQI Dashboard provides comprehensive real-time air quality monitoring with interactive visualizations, multi-city comparisons, email alerts, and health recommendations.

## 🚀 New Features

### 1. **🗺️ Live Interactive Map**
- **Real-time AQI visualization** across all monitored Indian cities
- **Color-coded markers** indicating air quality levels:
  - 🟢 Green (0-50): Good
  - 🟡 Yellow (51-100): Moderate  
  - 🟠 Orange (101-150): Unhealthy for Sensitive Groups
  - 🔴 Red (151-200): Unhealthy
  - 🟣 Purple (201-300): Very Unhealthy
  - 🟤 Maroon (301+): Hazardous
- **Click markers** for detailed pollution data and timestamps
- **City Rankings Chart** showing top 20 cities by AQI

### 2. **📈 Historical Trends**
- **Time-series charts** for AQI trends over 7, 14, or 30 days
- **Pollutant concentration graphs** for PM2.5 and PM10
- **Interactive Plotly charts** with zoom, pan, and hover tooltips
- Track air quality patterns and seasonal variations

### 3. **⚖️ Multi-City Comparison**
- **Side-by-side comparison** of up to 6 cities
- **Real-time metrics** including:
  - Current AQI value
  - PM2.5, PM10, NO₂, SO₂ levels
  - Air quality category
  - Last update timestamp
- **Comparison bar chart** for visual analysis
- **Quick selection** from 30 major cities

### 4. **🔔 Email Alerts System**
- **Set custom AQI thresholds** (0-500)
- **Email notifications** when air quality degrades
- **City-specific alerts** for personalized monitoring
- **Manage active alerts** - create, view, and remove alerts
- **Automatic throttling** - prevents notification spam

### 5. **💊 Health Impact & Recommendations**
- **Real-time health assessments** based on current AQI
- **Activity recommendations** tailored to air quality levels:
  - Outdoor exercise guidelines
  - Indoor air quality tips
  - Protective measures (masks, air purifiers)
- **At-risk groups identification**:
  - Children and elderly
  - People with respiratory/heart conditions
  - Pregnant women
  - Outdoor workers
- **Emergency guidance** for hazardous conditions

## 📂 File Structure

```
frontend/
├── dashboard.html       # Enhanced interactive dashboard
├── dashboard.js         # Dashboard functionality
├── index.html          # Original prediction interface
├── script.js           # Prediction interface logic
├── styles.css          # Shared styles
└── config.js           # API configuration
```

## 🌐 Accessing the Dashboard

### Local Development
1. Start the backend server:
   ```bash
   python run_complete_system.py server
   ```

2. Open the dashboard:
   ```
   http://localhost:5000/frontend/dashboard.html
   ```

3. Or use the original prediction interface:
   ```
   http://localhost:5000/frontend/index.html
   ```

### Production (Render)
```
https://your-app.onrender.com/frontend/dashboard.html
```

## 🔧 Technical Features

### Map Implementation
- **Leaflet.js** for interactive mapping
- **OpenStreetMap** tiles for base layer
- **Circle markers** with dynamic sizing and coloring
- **Popup information** with real-time data

### Charts & Visualization
- **Plotly.js** for interactive charts
- **Responsive design** adapts to screen sizes
- **Time-series analysis** with date/time axes
- **Bar charts** for comparisons and rankings

### API Integration
All features use the existing REST API:
- `GET /api/v1/cities` - List all cities
- `GET /api/v1/cities/coordinates/{city}` - Get city lat/lon
- `GET /api/v1/aqi/current/{city}` - Current AQI data
- `GET /api/v1/aqi/history/{city}?days=X` - Historical data
- `POST /api/v1/alerts/create` - Create alert
- `GET /api/v1/alerts/list/{city}` - List alerts
- `POST /api/v1/alerts/deactivate/{id}` - Remove alert

### Alert System Configuration

To enable email alerts, configure SMTP settings in `.env`:

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your.email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_FROM=AQI Alerts <noreply@aqiapp.com>
SMTP_TLS=true
```

**Gmail Users**: Generate an App Password from Google Account settings.

## 📱 Responsive Design

The dashboard is fully responsive:
- **Desktop**: Full feature set with side-by-side comparisons
- **Tablet**: Optimized grid layouts
- **Mobile**: Stacked views with touch-friendly controls

## ⚡ Performance

- **Lazy loading** of city data
- **Caching** for frequently accessed data
- **Batch requests** for multi-city comparisons
- **Debounced** API calls to prevent rate limiting

## 🎨 Color-Coding Standards

Following EPA AQI standards:
- **0-50** (Good): #00e400 - Green
- **51-100** (Moderate): #ffff00 - Yellow
- **101-150** (Unhealthy for Sensitive): #ff7e00 - Orange
- **151-200** (Unhealthy): #ff0000 - Red
- **201-300** (Very Unhealthy): #8f3f97 - Purple
- **301-500** (Hazardous): #7e0023 - Maroon

## 🔄 Data Refresh

- **Map markers**: Auto-refresh every 5 minutes
- **Historical charts**: On-demand refresh via dropdown changes
- **Comparison view**: Updates when city selection changes
- **Health recommendations**: Real-time based on current AQI

## 🆘 Troubleshooting

### Map not loading
- Check browser console for errors
- Verify internet connection (requires OpenStreetMap)
- Clear browser cache

### No city data showing
- Ensure backend server is running
- Verify data collection has completed (`python run_complete_system.py collect`)
- Check API endpoint: `http://localhost:5000/api/v1/cities`

### Alerts not working
- Verify SMTP credentials in `.env`
- Check email spam folder
- Review backend logs for delivery errors

### Charts not rendering
- Ensure Plotly.js CDN is accessible
- Check browser console for JavaScript errors
- Try refreshing the page

## 🔮 Future Enhancements

Potential additions:
- **WebSocket support** for real-time updates
- **User authentication** for personalized dashboards
- **Forecast predictions** overlaid on historical charts
- **Export data** as CSV/PDF reports
- **Social sharing** of air quality conditions
- **Mobile app** with push notifications
- **Air quality heatmaps** with interpolation

## 📞 Support

For issues or feature requests:
1. Check existing documentation
2. Review backend logs: `logs/main.log`
3. Test API endpoints directly
4. Report issues via GitHub

---

**Dashboard Version**: 1.0.0  
**Last Updated**: November 2025  
**Powered by**: Flask, Leaflet.js, Plotly.js, OpenStreetMap
