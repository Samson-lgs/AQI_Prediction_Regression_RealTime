# IMPORTANT: Restart Backend Server to See 97 Cities

## The Issue
The dashboard is showing only 56 cities because the backend server is running the old code.

## Solution
You need to **RESTART** the backend server to load the updated code.

## Steps to Restart:

### Option 1: Using PowerShell Script (Recommended)
```powershell
# Run this in a new PowerShell terminal:
cd "c:\Users\Samson Jose\Desktop\AQI_Prediction_Regression_RealTime"
.\start_backend.ps1
```

### Option 2: Manual Restart
```powershell
# 1. Stop any existing backend
$procs = Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
foreach ($p in $procs) { Stop-Process -Id $p -Force }

# 2. Wait a moment
Start-Sleep -Seconds 2

# 3. Start backend
cd "c:\Users\Samson Jose\Desktop\AQI_Prediction_Regression_RealTime"
.\.venv\Scripts\Activate.ps1
$env:FLASK_DEBUG = "0"
python backend/app.py
```

### Option 3: Quick Restart Script
```powershell
cd "c:\Users\Samson Jose\Desktop\AQI_Prediction_Regression_RealTime"
.\restart_dashboard.ps1
```

## Verify After Restart

1. **Check API Response:**
```powershell
$cities = Invoke-RestMethod -Uri "http://localhost:5000/api/v1/cities"
Write-Host "Total cities: $($cities.Count)"
```

Expected output: **Total cities: 97**

2. **Check in Browser:**
   - Open: http://localhost:5000
   - Look at the hero section stats
   - Should show: **"97 Cities Monitored"**

3. **Check Cities Dropdown:**
   - Go to "Live Dashboard" section
   - Open any city dropdown
   - You should see 97 cities in alphabetical order

## What Was Changed

✅ Backend API now returns all 97 cities  
✅ Frontend displays "97 cities"  
✅ Model training uses all 97 cities  
✅ Data collection covers all 97 cities  
✅ All coordinates defined for 97 cities  

## New Cities Added (from 56 to 97)

The additional 41 cities include:
- North-East: Silchar, Kohima, Aizawl
- North: Dehradun, Shimla, Jammu, Bikaner, Ajmer
- South: Mangalore, Tiruchirappalli, Puducherry, Guntur, Nellore
- West/Central: Belgaum, Amravati, Kolhapur
- And many more!

---

**Once restarted, your dashboard will show all 97 cities!** 🚀
