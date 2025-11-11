// Frontend Configuration
// Update API_BASE_URL after deploying backend to Render

const config = {
  // Auto-detect environment: use local backend for localhost/127.0.0.1, Render for deployed sites
  API_BASE_URL: (window.location.hostname.includes('vercel.app') || 
                 window.location.hostname.includes('github.io'))
    ? 'https://aqi-backend-api.onrender.com/api/v1'  // Render backend URL for production
    : 'http://localhost:5000/api/v1',                // Local backend for development
  
  // Manual override: Uncomment to force production URL
  // API_BASE_URL: 'https://aqi-backend-api.onrender.com/api/v1',
  
  // Configuration
  DEFAULT_CITY: 'Delhi',
  FORECAST_HOURS: 48,
  HISTORY_DAYS: 7,
  REFRESH_INTERVAL: 300000, // 5 minutes in milliseconds
  
  // AQI Standard
  AQI_STANDARD: 'India NAQI', // India National AQI Standard
  SHOW_AQI_STANDARD: true, // Display AQI standard badge
  
  // AQI Category Thresholds (India NAQI)
  AQI_CATEGORIES: {
    GOOD: { min: 0, max: 100, label: 'Good', color: '#00e400' },
    MODERATE: { min: 101, max: 200, label: 'Moderate', color: '#ffff00' },
    UNHEALTHY: { min: 201, max: 300, label: 'Unhealthy', color: '#ff7e00' },
    VERY_UNHEALTHY: { min: 301, max: 400, label: 'Very Unhealthy', color: '#ff0000' },
    HAZARDOUS: { min: 401, max: 500, label: 'Hazardous', color: '#8f3f97' }
  },
  
  // Pollutant Units
  POLLUTANT_UNITS: {
    pm25: 'µg/m³',
    pm10: 'µg/m³',
    no2: 'µg/m³',
    so2: 'µg/m³',
    co: 'mg/m³',
    o3: 'µg/m³'
  },
  
  // Pollutant Display Names
  POLLUTANT_NAMES: {
    pm25: 'PM2.5',
    pm10: 'PM10',
    no2: 'NO₂',
    so2: 'SO₂',
    co: 'CO',
    o3: 'O₃'
  }
};

// Export for use in script.js
if (typeof module !== 'undefined' && module.exports) {
  module.exports = config;
}
