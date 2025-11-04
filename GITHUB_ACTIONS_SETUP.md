# GitHub Actions Setup Guide

This guide explains how to configure GitHub Actions workflows for automated data collection and model training.

## Overview

The project uses **GitHub Actions free tier** (2000 minutes/month) to run scheduled tasks:
- **Hourly Data Collection**: Collects AQI data from APIs every hour
- **Daily Model Training**: Trains ML models every day at 2 AM UTC

## Architecture

```
GitHub Actions (Scheduler)
    ↓
    ├── Hourly: data_collection.yml → main.py
    └── Daily: model_training.yml → train_models.py
         ↓
    Render Database (PostgreSQL)
         ↓
    Render Backend API (Flask)
         ↓
    Render Frontend (Static Site)
```

## Required GitHub Secrets

Before the workflows can run, you need to add the following secrets to your GitHub repository:

### 1. Navigate to GitHub Secrets
1. Go to your GitHub repository
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**

### 2. Database Connection Secrets

These secrets are available after deploying the database to Render:

| Secret Name | Description | Where to Find |
|------------|-------------|---------------|
| `DB_HOST` | PostgreSQL host | Render Dashboard → Database → Internal Database URL (hostname) |
| `DB_PORT` | PostgreSQL port | Usually `5432` |
| `DB_NAME` | Database name | `aqi_db` (configured in render.yaml) |
| `DB_USER` | Database user | `aqi_user` (configured in render.yaml) |
| `DB_PASSWORD` | Database password | Render Dashboard → Database → Info → Password |

**How to get database connection details from Render:**
1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click on your database service (`aqi-database`)
3. Click **Info** tab
4. Copy the following:
   - **Internal Database URL**: Extract hostname for `DB_HOST`
   - **Password**: Copy for `DB_PASSWORD`
   - **Port**: Usually `5432` for `DB_PORT`

Example Internal Database URL:
```
postgres://aqi_user:password123@dpg-abc123xyz.oregon-postgres.render.com/aqi_db
```
- `DB_HOST`: `dpg-abc123xyz.oregon-postgres.render.com`
- `DB_USER`: `aqi_user`
- `DB_PASSWORD`: `password123`
- `DB_NAME`: `aqi_db`
- `DB_PORT`: `5432`

### 3. API Key Secrets (Optional)

If you want to use different API keys for GitHub Actions:

| Secret Name | Description | Default Value |
|------------|-------------|---------------|
| `OPENWEATHER_API_KEY` | OpenWeather API key | `528f129d20a5e514729cbf24b2449e44` |
| `IQAIR_API_KEY` | IQAir API key | `102c31e0-0f3c-4865-b4f3-2b4a57e78c40` |
| `CPCB_API_KEY` | CPCB API key | `579b464db66ec23bdd000001eed35a78497b4993484cd437724fd5dd` |

**Note**: The workflows currently use API keys from code. To use secrets instead, update the workflow files to include these environment variables.

## Step-by-Step Setup

### Step 1: Deploy to Render First

Before setting up GitHub Actions, deploy your application to Render:

1. Push your code to GitHub
2. Go to [Render Dashboard](https://dashboard.render.com/)
3. Click **New** → **Blueprint**
4. Connect your GitHub repository
5. Render will automatically deploy database, backend API, and frontend

### Step 2: Get Database Connection Details

1. Wait for database deployment to complete (2-3 minutes)
2. Go to Render Dashboard → Database service
3. Click **Info** tab
4. Copy the password and internal database URL

### Step 3: Add Secrets to GitHub

For each secret listed above:

1. Go to your GitHub repository
2. **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Enter the secret name (e.g., `DB_HOST`)
5. Paste the value
6. Click **Add secret**

Repeat for all required secrets:
- ✅ DB_HOST
- ✅ DB_PORT
- ✅ DB_NAME
- ✅ DB_USER
- ✅ DB_PASSWORD

### Step 4: Enable GitHub Actions

1. Go to your GitHub repository
2. Click **Actions** tab
3. You should see two workflows:
   - **Hourly Data Collection** (`.github/workflows/data_collection.yml`)
   - **Daily Model Training** (`.github/workflows/model_training.yml`)
4. If workflows are disabled, click **Enable workflows**

### Step 5: Test Workflows Manually

Test each workflow before waiting for scheduled runs:

**Test Data Collection:**
1. Go to **Actions** tab
2. Click **Hourly Data Collection**
3. Click **Run workflow** → **Run workflow**
4. Wait 2-3 minutes
5. Check if workflow succeeds (green checkmark)

**Test Model Training:**
1. Go to **Actions** tab
2. Click **Daily Model Training**
3. Click **Run workflow** → **Run workflow**
4. Wait 5-10 minutes (training takes longer)
5. Check if workflow succeeds

### Step 6: Monitor Scheduled Runs

**Data Collection Schedule:**
- Runs every hour at minute 0
- Examples: 1:00 AM, 2:00 AM, 3:00 AM, etc.

**Model Training Schedule:**
- Runs daily at 2:00 AM UTC
- Convert to your timezone if needed

**View workflow runs:**
1. Go to **Actions** tab
2. Click on a workflow
3. See all past runs with status
4. Click on a run to see detailed logs

## Troubleshooting

### Workflow Fails with Database Connection Error

**Problem**: Cannot connect to database

**Solution**:
1. Verify database secrets are correct
2. Check database is deployed and running on Render
3. Use internal database URL (ends with `.render.com`), not external URL

### Workflow Fails with Module Import Error

**Problem**: `ModuleNotFoundError: No module named 'X'`

**Solution**:
1. Verify `requirements.txt` includes all dependencies
2. Check Python version (should be 3.9)
3. Workflows automatically install from `requirements.txt`

### Workflow Doesn't Run at Scheduled Time

**Problem**: Workflow doesn't execute automatically

**Solution**:
1. Check workflow file syntax (YAML must be valid)
2. GitHub Actions may delay up to 15 minutes during high load
3. Manually trigger workflow to test if it works

### How to View Workflow Logs

1. Go to **Actions** tab
2. Click on workflow name
3. Click on a specific run
4. Click on the job name (e.g., `collect-data`)
5. Expand each step to see output

## Cost Analysis

### GitHub Actions Free Tier
- **Free minutes**: 2,000 minutes/month
- **Data collection**: ~2 min/run × 24 runs/day = 48 min/day = 1,440 min/month
- **Model training**: ~10 min/run × 1 run/day = 10 min/day = 300 min/month
- **Total usage**: ~1,740 min/month
- **Remaining**: ~260 min/month (buffer for manual runs)

✅ **Well within free tier limits!**

### Render Free Tier
- **Database**: Free (256 MB RAM, 1 GB storage, auto-sleeps after 15 min inactivity)
- **Backend API**: Free (512 MB RAM, auto-sleeps after 15 min inactivity)
- **Frontend**: Free (static site, always on)

⚠️ **Note**: Render free tier has limitations:
- Services sleep after 15 minutes of inactivity
- First request after sleep takes 30-60 seconds to wake up
- No always-on cron jobs (that's why we use GitHub Actions!)

## Workflow Files

### data_collection.yml
```yaml
Schedule: Hourly (cron: '0 * * * *')
Command: python main.py
Purpose: Collect AQI data from APIs
Duration: ~2 minutes
```

### model_training.yml
```yaml
Schedule: Daily at 2 AM UTC (cron: '0 2 * * *')
Command: python train_models.py
Purpose: Train ML models for all cities
Duration: ~10 minutes
```

## Advanced Configuration

### Change Schedule Times

Edit the cron expression in workflow files:

**Cron syntax**: `minute hour day month weekday`

Examples:
- `'0 * * * *'` - Every hour at minute 0
- `'0 2 * * *'` - Every day at 2 AM UTC
- `'0 */2 * * *'` - Every 2 hours
- `'0 0 * * 0'` - Every Sunday at midnight

**Useful cron resources**:
- [Crontab Guru](https://crontab.guru/) - Cron expression editor
- [Cron Calculator](https://cron.help/) - Visual cron builder

### Add API Keys to Workflows

To use GitHub secrets for API keys instead of hardcoded values:

1. Add API keys as secrets (see Step 3 above)
2. Update workflow files to include environment variables:

```yaml
- name: Collect data
  env:
    DB_HOST: ${{ secrets.DB_HOST }}
    DB_PORT: ${{ secrets.DB_PORT }}
    DB_NAME: ${{ secrets.DB_NAME }}
    DB_USER: ${{ secrets.DB_USER }}
    DB_PASSWORD: ${{ secrets.DB_PASSWORD }}
    OPENWEATHER_API_KEY: ${{ secrets.OPENWEATHER_API_KEY }}
    IQAIR_API_KEY: ${{ secrets.IQAIR_API_KEY }}
    CPCB_API_KEY: ${{ secrets.CPCB_API_KEY }}
  run: |
    python main.py
```

### Disable Workflows Temporarily

To temporarily stop scheduled runs without deleting workflows:

1. Go to **Actions** tab
2. Click on workflow name
3. Click **...** (three dots) → **Disable workflow**
4. To re-enable: Click **Enable workflow**

## Next Steps

After setting up GitHub Actions:

1. ✅ Monitor first few scheduled runs
2. ✅ Check database is being populated with data
3. ✅ Verify model training completes successfully
4. ✅ Test frontend dashboard displays predictions correctly
5. ✅ Set up error notifications (optional)

## Support

If you encounter issues:
1. Check workflow logs in GitHub Actions tab
2. Verify all secrets are added correctly
3. Test database connection manually
4. Review Render service logs
5. Check this guide's troubleshooting section

---

**Documentation Created**: January 2025  
**Last Updated**: January 2025  
**Version**: 1.0
