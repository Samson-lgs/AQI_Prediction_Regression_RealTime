# AQI Prediction System - GitHub Pages Setup

This frontend is deployed to GitHub Pages and connects to the backend API.

## Quick Setup

1. **Update Backend URL**: 
   - Edit `config.js` and replace `'https://your-backend-url.onrender.com/api/v1'` with your actual backend URL
   
2. **Enable GitHub Pages**:
   - Go to your repository settings
   - Navigate to "Pages" section
   - Set source to "GitHub Actions"
   
3. **Push Changes**:
   - Commit and push your code
   - GitHub Actions will automatically deploy

## URLs
- **GitHub Pages**: `https://samson-lgs.github.io/AQI_Prediction_Regression_RealTime/`
- **Backend API**: Update in `config.js`

## Files
- `index_new.html` - Main unified dashboard (served at root)
- `config.js` - Auto-detects environment (local vs GitHub Pages)
- `unified-app.js` - All frontend functionality
- `unified-styles.css` - Styling

## Features
✅ Auto-detection of deployment environment
✅ Fallback to localhost for local development
✅ All 5 dashboards working
✅ API error handling
✅ Responsive design
