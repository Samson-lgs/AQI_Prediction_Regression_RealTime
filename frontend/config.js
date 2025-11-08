// Frontend Configuration
// Update API_BASE_URL after deploying backend to Render

const config = {
  // Auto-detect environment: use production backend if deployed on GitHub Pages
  API_BASE_URL: window.location.hostname.includes('github.io') 
    ? 'https://aqi-backend-api.onrender.com/api/v1'  // Render backend URL
    : 'http://localhost:5000/api/v1',
  
  // Manual override: Uncomment to force production URL
  // API_BASE_URL: 'https://aqi-backend-api.onrender.com/api/v1',
  
  // Configuration
  DEFAULT_CITY: 'Delhi',
  FORECAST_HOURS: 48,
  HISTORY_DAYS: 7,
  REFRESH_INTERVAL: 300000, // 5 minutes in milliseconds
  
  // AQI Standard
  AQI_STANDARD: 'India NAQI', // India National AQI (CPCB Standard)
  SHOW_AQI_STANDARD: true, // Display AQI standard badge
  
  // AQI Category Thresholds (India NAQI)
  AQI_CATEGORIES: {
    GOOD: { min: 0, max: 50, label: 'Good', color: '#00e400' },
    SATISFACTORY: { min: 51, max: 100, label: 'Satisfactory', color: '#ffff00' },
    MODERATE: { min: 101, max: 200, label: 'Moderately Polluted', color: '#ff7e00' },
    POOR: { min: 201, max: 300, label: 'Poor', color: '#ff0000' },
    VERY_POOR: { min: 301, max: 400, label: 'Very Poor', color: '#8f3f97' },
    SEVERE: { min: 401, max: 500, label: 'Severe', color: '#7e0023' }
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
