# Automated Model Retraining Guide

## Overview

This guide covers the automated model retraining system using GitHub Actions for the AQI Prediction project.

## 🎯 What's Been Set Up

### 1. **GitHub Actions Workflow** (`.github/workflows/retrain_models.yml`)

The workflow automates weekly model retraining with the following features:

- **Scheduled Execution**: Runs every Sunday at 2 AM UTC
- **Manual Trigger**: Can be triggered manually via GitHub Actions UI
- **Flexible Training**: Train all cities or specific city
- **Model Artifacts**: Uploads trained models as artifacts
- **Auto-commit**: Automatically commits updated models to repository
- **Data Coverage Check**: Separate job to monitor data availability

### 2. **Current Status** (November 6, 2025)

✅ **Training Complete**: 42 cities successfully trained
- **Best Performers**: 
  - Ahmedabad: R²=0.5016 (Random Forest)
  - Aligarh: R²=0.5603 (XGBoost)
  - Agra: R²=0.6915 (Linear Regression)
  - Amritsar: R²=0.7938 (XGBoost)

⚠️ **14 Cities Skipped**: Insufficient data (need 24+ continuous hours)

✅ **Data Collector Running**: Background process collecting hourly data

## 📋 Setup Instructions

### Step 1: Add GitHub Secret

The workflow requires database credentials stored as a GitHub Secret:

1. Go to your repository on GitHub
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add secret:
   - **Name**: `DATABASE_URL`
   - **Value**: `postgresql://aqi_user:u2I3Xl9kBvUj1xCXGJaeSFHczxNgzdFJ@dpg-d452eqn5r7bs73ba6o7g-a.oregon-postgres.render.com/aqi_db_gr7o`

### Step 2: Enable GitHub Actions

1. Go to **Actions** tab in your repository
2. Enable workflows if not already enabled
3. The workflow will appear as "Weekly Model Retraining"

### Step 3: First Manual Run (Optional)

Test the workflow immediately:

1. Go to **Actions** → **Weekly Model Retraining**
2. Click **Run workflow**
3. Configure parameters:
   - **min_samples**: 50 (default)
   - **specific_city**: Leave empty for all cities or specify one
4. Click **Run workflow**

## 🔄 Workflow Details

### Main Retraining Job

**Triggers:**
- Automatic: Every Sunday at 2 AM UTC
- Manual: Via GitHub Actions UI with custom parameters

**Steps:**
1. Checkout code
2. Set up Python 3.11
3. Install dependencies from `requirements.txt`
4. Run training script with DATABASE_URL from secrets
5. Generate training report summary
6. Upload models as artifacts (30-day retention)
7. Commit and push updated models to repository
8. Notify on failure

**Parameters (Manual Trigger):**
- `min_samples`: Minimum samples required (default: 50)
- `specific_city`: Train specific city or all (default: all)

### Data Coverage Check Job

Runs in parallel to assess data availability:

**Steps:**
1. Checkout code
2. Set up Python 3.11
3. Install dependencies
4. Run `scripts/report_data_coverage.py`
5. Post coverage summary to workflow
6. Upload detailed coverage report (7-day retention)

## 📊 Monitoring Retraining

### View Workflow Runs

1. Go to **Actions** tab
2. Click on **Weekly Model Retraining**
3. See all runs with status (success/failure)

### Check Training Reports

Each workflow run includes a summary showing:
- Trigger type (scheduled/manual)
- Timestamp
- Minimum samples threshold
- Cities trained
- Success/failure status

### Download Artifacts

After successful runs:
1. Go to workflow run page
2. Scroll to **Artifacts** section
3. Download:
   - `trained-models-<run_id>`: All trained model files
   - `coverage-report-<run_id>`: Data coverage analysis

## 🎯 Usage Scenarios

### Scenario 1: Weekly Automatic Retraining

**When**: Every Sunday at 2 AM UTC  
**Action**: None required - runs automatically  
**Result**: Models retrained with past week's data, committed to repo

### Scenario 2: Emergency Retraining (Manual)

**When**: After fixing data issues or API problems  
**Action**: 
```
1. Go to Actions → Weekly Model Retraining
2. Click "Run workflow"
3. Set min_samples: 30 (lower threshold if needed)
4. Leave specific_city empty
5. Click "Run workflow"
```
**Result**: All cities retrained immediately

### Scenario 3: Single City Retraining

**When**: One city has new data or poor performance  
**Action**:
```
1. Go to Actions → Weekly Model Retraining
2. Click "Run workflow"
3. Set specific_city: "Delhi"
4. Set min_samples: 50
5. Click "Run workflow"
```
**Result**: Only Delhi models retrained

### Scenario 4: Check Data Coverage Before Training

**When**: Want to verify data availability  
**Action**: Check the Data Coverage Check job in any workflow run  
**Result**: See which cities have sufficient data

## 📈 Expected Improvements Over Time

As more data accumulates (48-168 hours):

| Week | Expected Coverage | Expected R² Score | Cities Trainable |
|------|------------------|-------------------|------------------|
| 1    | 29 hours         | 0.40-0.60         | 42/66            |
| 2    | 58 hours         | 0.50-0.70         | 50/66            |
| 4    | 116 hours        | 0.60-0.80         | 60/66            |
| 8+   | 168+ hours       | 0.70-0.90         | 66/66            |

## 🔧 Troubleshooting

### Workflow Fails: "No module named 'psycopg2'"

**Cause**: Missing dependencies  
**Fix**: Ensure `requirements.txt` includes all dependencies:
```bash
psycopg2-binary
pandas
numpy
scikit-learn
xgboost
tensorflow
```

### Workflow Fails: "Connection refused" or Database Error

**Cause**: DATABASE_URL secret not set or incorrect  
**Fix**: 
1. Verify secret exists in Settings → Secrets
2. Check database URL is correct
3. Ensure Render database is accessible from GitHub Actions IPs

### No Models Committed

**Cause**: No model changes detected  
**This is normal if:**
- Models already exist and haven't improved
- No cities had sufficient data
- Training failed for all cities

**Action**: Check workflow logs for details

### Training Times Out (>120 minutes)

**Cause**: Too many cities or slow database  
**Fix**: Split into multiple runs:
```yaml
# Option 1: Increase timeout in workflow
timeout-minutes: 240

# Option 2: Train cities in batches manually
```

## 🚀 Advanced Configuration

### Change Retraining Frequency

Edit `.github/workflows/retrain_models.yml`:

```yaml
# Daily at midnight
schedule:
  - cron: '0 0 * * *'

# Twice weekly (Sunday and Wednesday)
schedule:
  - cron: '0 2 * * 0,3'

# Monthly (1st of month)
schedule:
  - cron: '0 2 1 * *'
```

### Adjust Model Retention

Change artifact retention period:

```yaml
retention-days: 60  # Keep models for 60 days instead of 30
```

### Add Slack/Email Notifications

Add notification step:

```yaml
- name: Notify on Slack
  if: always()
  uses: 8398a7/action-slack@v3
  with:
    status: ${{ job.status }}
    webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

## 📝 Best Practices

1. **Let Data Accumulate**: Wait 48-168 hours before expecting high R² scores
2. **Monitor Coverage**: Check data coverage reports to identify problem cities
3. **Review Artifacts**: Download and inspect trained models after each run
4. **Adjust Thresholds**: Lower `min_samples` if too many cities skip
5. **Track Performance**: Compare R² scores across weekly runs to see improvement

## 🔗 Related Files

- **Workflow**: `.github/workflows/retrain_models.yml`
- **Training Script**: `models/train_all_models.py`
- **Coverage Report**: `scripts/report_data_coverage.py`
- **Trained Models**: `models/trained_models/`
- **Backend Server**: `backend/main.py` (data collector)

## 📞 Support

If you encounter issues:

1. Check workflow run logs in Actions tab
2. Verify DATABASE_URL secret is correct
3. Ensure database is accessible
4. Review training script logs for specific errors
5. Check data coverage to identify insufficient data

---

**Last Updated**: November 6, 2025  
**Status**: ✅ Automated retraining active, data collector running
