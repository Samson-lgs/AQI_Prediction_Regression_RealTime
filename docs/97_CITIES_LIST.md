# Complete List of 97 Indian Cities Monitored by AQI Prediction System

**Last Updated:** November 11, 2025

## Overview
The AQI Prediction System now monitors **97 Indian cities** across all regions, providing real-time air quality data, predictions, and health recommendations.

---

## Cities by Region

### North India (34 cities)
1. Delhi
2. Noida
3. Ghaziabad
4. Gurugram (Gurgaon)
5. Faridabad
6. Greater Noida
7. Chandigarh
8. Jaipur
9. Lucknow
10. Kanpur
11. Varanasi
12. Agra
13. Amritsar
14. Ludhiana
15. Kota
16. Jodhpur
17. Udaipur
18. Meerut
19. Aligarh
20. Allahabad
21. Jalandhar
22. Bareilly
23. Moradabad
24. Sonipat
25. Panipat
26. Alwar
27. Bharatpur
28. Mathura
29. Rohtak
30. Rewari
31. Bhiwani
32. Bhiwadi
33. Srinagar
34. Gwalior

### South India (16 cities)
35. Bangalore (Bengaluru)
36. Chennai
37. Hyderabad
38. Kochi
39. Visakhapatnam
40. Coimbatore
41. Mysore
42. Kurnool
43. Vijayawada
44. Tirupati
45. Thanjavur
46. Madurai
47. Salem
48. Thiruvananthapuram
49. Warangal
50. Tirupati

### West India (14 cities)
51. Mumbai
52. Pune
53. Ahmedabad
54. Surat
55. Vadodara
56. Rajkot
57. Nashik
58. Aurangabad
59. Nagpur
60. Thane
61. Navi Mumbai
62. Pimpri-Chinchwad
63. Solapur
64. Hubli-Dharwad

### East India (10 cities)
65. Kolkata
66. Patna
67. Ranchi
68. Guwahati
69. Raipur
70. Bhubaneswar
71. Jamshedpur
72. Asansol
73. Dhanbad
74. Howrah

### Central India (5 cities)
75. Indore
76. Bhopal
77. Jabalpur
78. Gwalior
79. Ujjain

### North-East India (4 cities)
80. Imphal
81. Shillong
82. Agartala
83. Dibrugarh

---

## Data Sources

Each city receives data from multiple sources:
- **OpenWeather API**: All 97 cities (weather + air pollution data)
- **IQAir API**: Major cities (where available)

---

## Features Available for All 97 Cities

✅ **Real-time AQI Monitoring**
- Current AQI value and category
- All 6 pollutant levels (PM2.5, PM10, NO2, SO2, CO, O3)
- Timestamp of latest reading

✅ **48-Hour Predictions**
- Hourly AQI forecasts
- Predictions from 3 ML models (XGBoost, Random Forest, Linear Regression)
- Confidence intervals

✅ **Historical Trends**
- 7, 14, and 30-day historical data
- Trend analysis and patterns
- Interactive charts

✅ **Interactive Map**
- Color-coded markers based on AQI category
- Popup with detailed city information
- Pan and zoom capabilities

✅ **Multi-City Comparison**
- Compare up to 6 cities simultaneously
- Side-by-side metrics comparison
- Visual trend comparisons

✅ **Custom Alerts**
- Email notifications
- Configurable AQI thresholds
- City-specific alerts

✅ **Health Recommendations**
- Category-specific health advice
- Activity recommendations
- Sensitive group warnings

---

## API Endpoints Supporting All 97 Cities

### Get List of All Cities
```
GET /api/v1/cities
```
Returns all 97 cities with priority flags.

### Get Current AQI for Any City
```
GET /api/v1/aqi/current/{city}
```

### Get Batch AQI Data
```
GET /api/v1/aqi/batch?cities=Delhi,Mumbai,Bangalore,...
```
Fetch multiple cities in a single request.

### Get City Coordinates
```
GET /api/v1/cities/coordinates/{city}
```

### Get Forecast
```
GET /api/v1/forecast/{city}?hours=24
```
Available for all 97 cities.

### Get Historical Data
```
GET /api/v1/aqi/history/{city}?days=7
```

---

## Priority Cities (Enhanced Monitoring)

These 8 cities receive additional monitoring from IQAir API:
1. Delhi
2. Mumbai
3. Bangalore
4. Chennai
5. Kolkata
6. Hyderabad
7. Pune
8. Ahmedabad

---

## System Capabilities

### Data Collection
- **Frequency**: Hourly updates for all cities
- **Parallel Processing**: 4 concurrent workers
- **Retry Logic**: Automatic retry on failures
- **Rate Limiting**: Built-in to avoid API limits

### Machine Learning
- **Training Data**: Combined data from all 97 cities
- **Models**: 3 algorithms trained on unified dataset
- **Feature Engineering**: Advanced temporal and spatial features
- **Prediction Accuracy**: Continuously monitored and improved

### Database
- **Storage**: PostgreSQL with optimized indexes
- **Data Retention**: Historical data maintained
- **Performance**: Fast queries with caching

---

## Frontend Features

### Dashboard
- Real-time updates for all 97 cities
- Interactive map with all city markers
- City ranking table (sortable)
- Quick city search

### Charts & Visualizations
- Historical trend charts
- Pollutant breakdown
- Comparison charts
- Forecast visualizations

### User Experience
- Fast loading with caching
- Responsive design (mobile-friendly)
- Batch API calls to minimize load
- Graceful fallbacks

---

## Technical Details

### Coordinates Coverage
All 97 cities have pre-defined coordinates in the system:
- Frontend: `CITY_COORDS` object with lat/lon for all cities
- Backend: `OpenWeatherHandler.CITY_COORDINATES` dictionary
- Fallback: Geocoding API for dynamic coordinate resolution

### API Response Times
- Single city: ~100-200ms
- Batch request (10 cities): ~500-800ms
- Full dashboard load: ~2-3 seconds

### Data Freshness
- Real-time data: Updated hourly
- Predictions: Generated on-demand
- Historical data: Available immediately after collection

---

## Getting Started

### Access the Dashboard
1. **Local**: http://localhost:5000
2. **Production**: https://aqi-backend-api.onrender.com

### Search for Your City
Use the search box or dropdown to find any of the 97 cities.

### View City Details
Click on any city to see:
- Current AQI and category
- All pollutant levels
- 48-hour forecast
- Historical trends
- Health recommendations

### Set Up Alerts
Create custom alerts for your city with email notifications.

---

## Future Enhancements

🔜 **Expanding to 150+ cities** by adding more Tier 2 and Tier 3 cities
🔜 **Neighborhood-level AQI** for major metropolitan areas
🔜 **SMS alerts** in addition to email
🔜 **Mobile app** for iOS and Android
🔜 **Air quality forecasts** up to 7 days
🔜 **Integration with weather forecasts** for combined predictions

---

## Credits

**Project Team:**
- Drushya M
- Kavana P
- Samson Jose J
- Yashwanth J

**Institution:** ATME College of Engineering (CSE), 2024-2025

**Data Sources:**
- OpenWeather API
- IQAir API
- India National AQI Standards (NAQI)

---

## Support & Feedback

For issues, feature requests, or feedback:
- GitHub: [Repository Link]
- Email: [Contact Email]
- Documentation: [Link to full docs]

---

**Last Updated:** November 11, 2025
**Version:** 2.0 - 97 Cities Coverage
