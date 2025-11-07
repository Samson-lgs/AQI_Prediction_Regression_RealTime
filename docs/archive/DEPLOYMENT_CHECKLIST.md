# Deployment Checklist - Separate Services Architecture

This checklist ensures successful deployment of all services to Render with GitHub Actions scheduling.

## Pre-Deployment Checklist

### 1. Code Ready ✓
- [ ] All code pushed to GitHub main branch
- [ ] `.env` file NOT committed (in `.gitignore`)
- [ ] `requirements.txt` up to date
- [ ] `runtime.txt` specifies Python 3.9.18
- [ ] `render.yaml` configured for separate services
- [ ] GitHub Actions workflows created (`.github/workflows/`)

### 2. Configuration Files ✓
- [ ] `render.yaml` - Render Blueprint configuration
- [ ] `render-build.sh` - Build script (executable)
- [ ] `frontend/config.js` - API URL configuration
- [ ] `.github/workflows/data_collection.yml` - Hourly data collection
- [ ] `.github/workflows/model_training.yml` - Daily model training

### 3. Documentation ✓
- [ ] `README.md` - Updated with deployment options
- [ ] `RENDER_DEPLOYMENT.md` - Detailed Render deployment guide
- [ ] `QUICK_DEPLOY_GUIDE.md` - Quick start guide
- [ ] `GITHUB_ACTIONS_SETUP.md` - GitHub Actions setup guide
- [ ] `PREDICTION_FEATURES.md` - Feature documentation

## Render Deployment Steps

### Step 1: Deploy to Render (15 minutes)

1. **Push code to GitHub:**
```bash
git add .
git commit -m "Ready for production deployment"
git push origin main
```

2. **Go to Render Dashboard:**
   - Visit: https://dashboard.render.com/
   - Sign in with GitHub account

3. **Create new Blueprint:**
   - Click **New** → **Blueprint**
   - Select repository: `AQI_Prediction_Regression_RealTime`
   - Click **Connect**
   - Render will detect `render.yaml`
   - Click **Apply**

4. **Wait for deployment:**
   - **Database** (`aqi-database`): ~3-5 minutes
   - **Backend API** (`aqi-backend-api`): ~8-10 minutes
   - **Frontend** (`aqi-frontend`): ~2-3 minutes
   - Total: ~15 minutes

5. **Verify deployment:**
   - All services should show **Live** status (green)
   - Check service logs for errors

### Step 2: Get Service URLs (2 minutes)

1. **Backend API URL:**
   - Go to `aqi-backend-api` service
   - Copy the URL (e.g., `https://aqi-backend-api.onrender.com`)

2. **Frontend URL:**
   - Go to `aqi-frontend` service
   - Copy the URL (e.g., `https://aqi-frontend.onrender.com`)

3. **Database Internal URL:**
   - Go to `aqi-database` service
   - Click **Info** tab
   - Copy **Internal Database URL**
   - Example: `postgres://aqi_user:pass@dpg-xxx.oregon-postgres.render.com/aqi_db`

### Step 3: Update Frontend Configuration (2 minutes)

1. **Update `frontend/config.js`:**
```javascript
// Replace with your actual backend URL
API_BASE_URL: 'https://aqi-backend-api.onrender.com/api/v1',
```

2. **Commit and push:**
```bash
git add frontend/config.js
git commit -m "Update API URL for production"
git push origin main
```

3. **Render will auto-deploy** frontend with new configuration

### Step 4: Initialize Database (5 minutes)

**Option A: Using Render Shell (Recommended)**
1. Go to `aqi-backend-api` service
2. Click **Shell** tab
3. Run:
```bash
python database/reset_db.py
```

**Option B: Using Local Terminal**
1. Set environment variables:
```bash
# Windows PowerShell
$env:DATABASE_URL="postgres://aqi_user:pass@dpg-xxx.oregon-postgres.render.com/aqi_db"
python database/reset_db.py
```

4. **Verify database initialized:**
   - Check logs for "Database initialized successfully"
   - Tables created: cities, pollution_data, weather_data, predictions, model_performance

### Step 5: Test Backend API (3 minutes)

Test each endpoint:

1. **Health check:**
```bash
curl https://aqi-backend-api.onrender.com/api/v1/health
```
Expected: `{"status": "healthy"}`

2. **Get cities:**
```bash
curl https://aqi-backend-api.onrender.com/api/v1/cities
```
Expected: Array of 56 cities

3. **Get current AQI (will be empty initially):**
```bash
curl https://aqi-backend-api.onrender.com/api/v1/aqi/current/Delhi
```
Expected: Empty data (no data collected yet)

### Step 6: Test Frontend (2 minutes)

1. **Open frontend URL in browser:**
   - Example: `https://aqi-frontend.onrender.com`

2. **Verify UI loads:**
   - [ ] City dropdown shows 56 cities
   - [ ] Dashboard layout displays correctly
   - [ ] No JavaScript errors in console

3. **Expected behavior:**
   - "No data available" message (data not collected yet)
   - City selection works
   - UI is responsive

## GitHub Actions Setup

### Step 7: Add Repository Secrets (5 minutes)

1. **Go to GitHub repository:**
   - Settings → Secrets and variables → Actions

2. **Add these secrets:**

| Secret Name | Value | Where to Get |
|------------|-------|--------------|
| `DB_HOST` | `dpg-xxx.oregon-postgres.render.com` | Database Internal URL hostname |
| `DB_PORT` | `5432` | Standard PostgreSQL port |
| `DB_NAME` | `aqi_db` | From render.yaml |
| `DB_USER` | `aqi_user` | From render.yaml |
| `DB_PASSWORD` | `your_password_here` | Render Dashboard → Database → Info → Password |

3. **Parse database Internal URL:**
```
postgres://aqi_user:PASSWORD@dpg-xxx.oregon-postgres.render.com:5432/aqi_db
         ├────────┤├──────┤├──────────────────────────────────────┤├───┤├──────┤
         DB_USER   PASSWORD           DB_HOST                      PORT  DB_NAME
```

### Step 8: Enable GitHub Actions (2 minutes)

1. **Go to Actions tab:**
   - Your repository → Actions

2. **Enable workflows:**
   - If disabled, click **I understand my workflows, go ahead and enable them**

3. **Verify workflows listed:**
   - [ ] Hourly Data Collection
   - [ ] Daily Model Training

### Step 9: Test Workflows Manually (10 minutes)

1. **Test data collection:**
   - Actions → Hourly Data Collection
   - Click **Run workflow** → **Run workflow**
   - Wait 2-3 minutes
   - Check if succeeds (green checkmark)
   - View logs for any errors

2. **Test model training:**
   - Actions → Daily Model Training
   - Click **Run workflow** → **Run workflow**
   - Wait 5-10 minutes
   - Check if succeeds
   - Note: May fail if no data collected yet (expected)

3. **Check database has data:**
```bash
curl https://aqi-backend-api.onrender.com/api/v1/aqi/current/Delhi
```
Should now return AQI data!

### Step 10: Verify Full System (5 minutes)

1. **Frontend displays data:**
   - Refresh `https://aqi-frontend.onrender.com`
   - Select a city (e.g., Delhi)
   - Should show current AQI, pollutants, predictions

2. **Predictions work:**
   - Change prediction hours (1-48)
   - Verify forecast chart updates
   - Check hourly predictions table

3. **Model performance:**
   - Scroll to "Model Performance" section
   - Should show metrics (after training runs)

## Post-Deployment Monitoring

### Day 1: Initial Data Collection
- [ ] Data collection runs every hour (check Actions tab)
- [ ] Database populates with pollution data
- [ ] Frontend shows current AQI for cities

### Day 2: Model Training
- [ ] Model training runs at 2 AM UTC
- [ ] Check logs for training completion
- [ ] Verify model performance metrics appear

### Week 1: System Health
- [ ] Monitor GitHub Actions usage (< 2000 min/month)
- [ ] Check Render service logs for errors
- [ ] Verify predictions improve as more data collected

## Troubleshooting

### Issue: Backend API returns 500 errors

**Symptoms:**
- API health check fails
- Frontend shows "Failed to load data"
- Render logs show database connection errors

**Solutions:**
1. Check database is deployed and **Live**
2. Verify DATABASE_URL environment variable
3. Check database password in Render
4. Restart backend API service

### Issue: Frontend shows "No data available"

**Symptoms:**
- Cities load but no AQI data
- API health check works
- Database is empty

**Solutions:**
1. Run data collection workflow manually
2. Wait 2-3 minutes for data to populate
3. Refresh frontend
4. Check if GitHub Actions workflow succeeded

### Issue: GitHub Actions workflow fails

**Symptoms:**
- Workflow shows red X
- Logs show connection errors
- Database credentials invalid

**Solutions:**
1. Verify all secrets added correctly
2. Check database password from Render
3. Use **Internal Database URL** (not external)
4. Ensure database is not sleeping (wake it up)

### Issue: Predictions not showing

**Symptoms:**
- Current AQI shows but predictions are empty
- Model performance is 0

**Solutions:**
1. Collect data for 24+ hours first
2. Run model training workflow manually
3. Wait 5-10 minutes for training to complete
4. Refresh frontend

### Issue: Services keep sleeping

**Problem:**
- Render free tier services sleep after 15 min inactivity
- First request takes 30-60 seconds to wake up

**Solutions:**
1. Expected behavior on free tier
2. Upgrade to paid plan ($7/month) for always-on
3. Use external monitoring (e.g., UptimeRobot) to ping every 10 min
4. Accept slow first load (not critical for this project)

## Cost Analysis

### Free Tier Resources

**Render:**
- Database: Free (256 MB RAM, 1 GB storage)
- Backend API: Free (512 MB RAM)
- Frontend: Free (static site)
- **Total Render Cost**: $0/month

**GitHub Actions:**
- Free tier: 2,000 minutes/month
- Data collection: 48 min/day × 30 days = 1,440 min/month
- Model training: 10 min/day × 30 days = 300 min/month
- **Total usage**: ~1,740 min/month
- **Remaining**: 260 min/month (buffer)
- **Total GitHub Cost**: $0/month

**Grand Total: $0/month** ✅

### Upgrade Options (Optional)

If you need better performance:

**Render Paid Plans:**
- Starter ($7/month): 512 MB RAM, no sleeping
- Standard ($25/month): 2 GB RAM, better performance
- Pro ($85/month): 4 GB RAM, autoscaling

**GitHub Actions Paid:**
- $0.008 per minute beyond free tier
- For 3,000 min/month: ~$8/month

## Success Criteria

After deployment, verify:

- ✅ All 3 services deployed and **Live** on Render
- ✅ Backend API health check returns 200
- ✅ Frontend loads and displays UI
- ✅ GitHub Actions workflows enabled
- ✅ Data collection runs hourly
- ✅ Model training runs daily at 2 AM UTC
- ✅ Database populates with pollution data
- ✅ Frontend displays current AQI and predictions
- ✅ No errors in service logs
- ✅ Total cost: $0/month

## Maintenance Schedule

**Daily:**
- Check GitHub Actions logs (2 min)
- Verify data collection succeeded

**Weekly:**
- Review model performance metrics
- Check prediction accuracy
- Monitor GitHub Actions usage

**Monthly:**
- Review Render service logs
- Check database storage usage (< 1 GB)
- Verify API response times

## Next Steps After Deployment

1. **Collect data for 7 days** for better predictions
2. **Monitor model performance** and tune if needed
3. **Add more cities** if API limits allow
4. **Implement email alerts** for critical AQI levels (optional)
5. **Setup monitoring** with UptimeRobot (optional)
6. **Consider upgrading** if free tier limits reached

## Support & Documentation

- **README.md** - Project overview
- **RENDER_DEPLOYMENT.md** - Detailed deployment guide
- **GITHUB_ACTIONS_SETUP.md** - GitHub Actions setup
- **PREDICTION_FEATURES.md** - Feature documentation
- **GitHub Issues** - Report bugs or ask questions

---

**Deployment Checklist Version**: 1.0  
**Last Updated**: January 2025  
**Estimated Total Time**: ~60 minutes
