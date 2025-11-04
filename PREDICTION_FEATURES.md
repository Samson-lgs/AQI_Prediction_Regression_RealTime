# AQI Prediction Dashboard - Feature Overview

## 🎯 Core Prediction Capabilities

This dashboard is specifically designed to showcase **1-48 hour AQI predictions** for 56 Indian cities using multiple machine learning models.

### Key Features

#### 1. **Real-Time Prediction Comparison**
- **Current AQI vs Predicted AQI**: Side-by-side comparison showing how air quality will change
- **Change Indicator**: Visual indicator showing if AQI will increase ↑, decrease ↓, or remain stable →
- **Percentage Change**: Shows the percentage change in AQI value
- **Confidence Level**: Displays prediction confidence (decreases with forecast horizon)

#### 2. **Interactive 48-Hour Forecast**
- **Prediction Timeline**: Full 48-hour forecast with hourly granularity
- **Confidence Intervals**: Shaded regions showing prediction uncertainty
- **AQI Category Zones**: Color-coded background zones (Good, Satisfactory, Moderate, Poor, Very Poor, Severe)
- **Toggleable Views**: 
  - Show/hide historical data
  - Show/hide confidence intervals

#### 3. **Flexible Forecast Horizons**
Select different prediction windows:
- 6 hours ahead
- 12 hours ahead
- 24 hours ahead (default)
- 48 hours ahead

#### 4. **Hourly Predictions Table**
- Next 24 hours in detailed table format
- Time, Predicted AQI, Category, and Change from previous hour
- Easy-to-scan format for quick insights

#### 5. **Current Pollutant Levels**
Real-time display of:
- **PM2.5**: Fine particulate matter (µg/m³)
- **PM10**: Coarse particulate matter (µg/m³)
- **NO₂**: Nitrogen dioxide (µg/m³)
- **SO₂**: Sulfur dioxide (µg/m³)
- **CO**: Carbon monoxide (µg/m³)
- **O₃**: Ozone (µg/m³)

#### 6. **Historical Trend Analysis**
- 7-day historical AQI trend
- Helps identify patterns and validate predictions

#### 7. **Model Performance Metrics**
Real-time display of prediction accuracy:
- **R² Score**: Model accuracy (0-1, higher is better)
- **RMSE**: Root Mean Square Error (lower is better)
- **MAE**: Mean Absolute Error (lower is better)
- **MAPE**: Mean Absolute Percentage Error (lower is better)

### Supported Cities (56 in total)
Delhi, Mumbai, Bangalore, Chennai, Kolkata, Hyderabad, Pune, Ahmedabad, Jaipur, Lucknow, Kanpur, Nagpur, Indore, Thane, Bhopal, Visakhapatnam, and 40 more Indian cities.

### ML Models Used
1. **XGBoost** (Gradient Boosting) - Default
2. **Random Forest**
3. **LSTM** (Deep Learning)
4. **Linear Regression**

### AQI Categories
- **0-50**: Good (Green) 🟢
- **51-100**: Satisfactory (Yellow) 🟡
- **101-200**: Moderately Polluted (Orange) 🟠
- **201-300**: Poor (Red) 🔴
- **301-400**: Very Poor (Purple) 🟣
- **401-500**: Severe (Maroon) 🟤

## Usage Instructions

1. **Select City**: Choose from 56 Indian cities
2. **Select Forecast Horizon**: Choose 6, 12, 24, or 48 hours
3. **View Predictions**: 
   - Compare current vs predicted AQI
   - Analyze the 48-hour forecast chart
   - Check hourly predictions table
4. **Refresh**: Click refresh to get latest predictions

## API Endpoints for Predictions

```
GET /api/v1/aqi/current/{city}      - Get current AQI
GET /api/v1/forecast/{city}          - Get 48-hour forecast
GET /api/v1/metrics/{city}           - Get model performance
GET /api/v1/aqi/history/{city}       - Get historical data
```

## Technical Details

### Prediction Algorithm
1. Load historical data (7 days)
2. Extract weather features
3. Apply trained ML model (XGBoost by default)
4. Generate 1-48 hour predictions with confidence intervals
5. Update dashboard in real-time

### Confidence Calculation
- Confidence = 95% - (0.5% × hours ahead)
- Example: 24-hour forecast has 83% confidence
- Example: 48-hour forecast has 71% confidence

### Update Frequency
- Predictions updated every hour
- Historical data refreshed continuously
- Model retraining: Daily at 2 AM

## Future Enhancements
- [ ] Multi-pollutant predictions
- [ ] Weather-aware forecasting
- [ ] Alert notifications for poor AQI
- [ ] Export predictions to CSV
- [ ] Mobile app version
- [ ] Regional comparisons

---

**Note**: Current predictions are simulated based on realistic patterns. Once models are trained with real data (after 24+ hours of collection), predictions will use actual trained models.
