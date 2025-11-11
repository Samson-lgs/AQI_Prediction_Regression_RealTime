# TESTING INSTRUCTIONS FOR AQI PREDICTIONS

## Issue
The dashboard predictions are not changing according to city/forecast period and may not be using the actual XGBoost model predictions.

## Changes Made

1. **Added detailed logging** to track what the model is predicting
2. **Fixed base_aqi calculation** to ensure XGBoost model output is used
3. **Added logging** for every prediction request showing:
   - Current AQI from database
   - Model name used (should be "xgboost")
   - Predicted AQI from the model
   - First and last hourly predictions

## Testing Steps

### Step 1: Test the Model Directly
Run this to verify the XGBoost model is working:

```powershell
python test_prediction.py
```

**Expected output:**
- Should show predictions for Delhi, Mumbai, Bangalore
- Predicted AQI values should be DIFFERENT for each city
- Best Model should be "xgboost"
- All three models (linear_regression, random_forest, xgboost) should show values

### Step 2: Restart Backend with Logging
```powershell
.\restart_dashboard.ps1
```

Watch the terminal output. When the server starts, you should see:
```
📦 Loading unified models with feature engineering...
  ✅ linear_regression: R² = ...
  ✅ random_forest: R² = ...
  ✅ xgboost: R² = 0.9392
📊 Loaded 3 models
```

### Step 3: Test API Directly
Open PowerShell and test the API:

```powershell
# Test Delhi
Invoke-RestMethod "http://localhost:5000/api/v1/forecast/Delhi?hours=24"

# Test Mumbai
Invoke-RestMethod "http://localhost:5000/api/v1/forecast/Mumbai?hours=24"

# Test with different hours
Invoke-RestMethod "http://localhost:5000/api/v1/forecast/Delhi?hours=6"
Invoke-RestMethod "http://localhost:5000/api/v1/forecast/Delhi?hours=48"
```

**Check in the backend terminal logs** - you should see lines like:
```
INFO: Forecast for Delhi: Current AQI=136.0, Model=xgboost, Predicted=142.3
INFO: Generated 24 predictions for Delhi: First=145, Last=152
```

### Step 4: Test in Dashboard
1. Open http://localhost:5000
2. Go to "Forecast" section
3. Select different cities (Delhi, Mumbai, Bangalore)
4. Change forecast period (6h, 12h, 24h, 48h)

**What should happen:**
- Current AQI should change for different cities
- Predicted AQI should be different for different cities
- Predicted AQI should change when you change forecast hours
- The hourly forecast table should show progressive values

### Step 5: Check Logs
Look at the backend terminal for log messages showing:
```
INFO: Forecast for [CITY]: Current AQI=XXX, Model=xgboost, Predicted=YYY
```

## What to Report Back

If it's still not working, please send me:

1. **Output of test_prediction.py**
2. **The log messages** when you request a forecast (from backend terminal)
3. **Screenshot** of what you see in the dashboard
4. **Tell me**: Are the values changing at all, or are they still stuck at 136/381?

## Expected Behavior

✅ **Delhi** (high pollution): Should predict AQI around 150-250
✅ **Mumbai** (moderate): Should predict AQI around 80-120
✅ **Bangalore** (better air): Should predict AQI around 50-90
✅ **6h forecast**: Should be close to current AQI
✅ **48h forecast**: Should show more variation from current AQI
