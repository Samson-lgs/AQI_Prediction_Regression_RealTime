# GitHub Actions DATABASE_URL Secret Setup

## Quick Setup (2 minutes)

### Step 1: Go to GitHub Secrets Page
Open this URL in your browser:
```
https://github.com/Samson-lgs/AQI_Prediction_Regression_RealTime/settings/secrets/actions
```

### Step 2: Add New Repository Secret

1. Click the **"New repository secret"** button (top right)

2. Fill in the form:
   - **Name**: `DATABASE_URL`
   - **Secret**: 
     ```
     postgresql://aqi_user:u2I3Xl9kBvUj1xCXGJaeSFHczxNgzdFJ@dpg-d452eqn5r7bs73ba6o7g-a.oregon-postgres.render.com/aqi_db_gr7o
     ```

3. Click **"Add secret"**

### Step 3: Verify Setup

Once added, you should see `DATABASE_URL` in the list of repository secrets.

### Step 4: Test the Workflow

You can manually trigger the retraining workflow:

1. Go to: https://github.com/Samson-lgs/AQI_Prediction_Regression_RealTime/actions
2. Click on "Weekly Model Retraining" workflow
3. Click "Run workflow" button
4. (Optional) Set parameters:
   - `min_samples`: 50 (default: 100)
   - `specific_city`: Leave empty for all cities
5. Click green "Run workflow" button

### What This Enables

✅ **Automated weekly retraining** every Sunday at 2 AM UTC  
✅ **Manual retraining** anytime via GitHub Actions UI  
✅ **Data coverage checks** before training  
✅ **Automatic commit** of new trained models to repository  
✅ **Artifact storage** of training logs for 30 days

### Workflow Schedule

The workflow runs automatically:
- **When**: Every Sunday at 2:00 AM UTC (7:30 AM IST)
- **What**: Trains all cities with 100+ samples
- **Output**: New model files committed to `models/trained_models/`

### Manual Trigger Parameters

When manually triggering:
- `min_samples`: Minimum data points required (default: 100, can set to 50 for faster testing)
- `specific_city`: Train only one city (e.g., "Delhi") or leave empty for all cities

### Monitoring

Check workflow runs at:
```
https://github.com/Samson-lgs/AQI_Prediction_Regression_RealTime/actions
```

Each run shows:
- Data coverage report
- Cities trained
- Model performance metrics
- Training logs (downloadable as artifacts)

---

**Status**: ✅ Workflow file created and committed  
**Next**: Add DATABASE_URL secret using steps above  
**Time**: ~2 minutes
