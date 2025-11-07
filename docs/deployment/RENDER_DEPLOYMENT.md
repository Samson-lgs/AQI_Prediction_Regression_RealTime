# Render Deployment Guide for AQI Prediction System

## Prerequisites
1. A Render account (sign up at https://render.com)
2. Your GitHub repository connected to Render
3. All code committed and pushed to GitHub

## Deployment Options

### Option 1: Automatic Deployment with render.yaml (Recommended)

1. **Push all changes to GitHub:**
   ```bash
   git add .
   git commit -m "Add Render deployment configuration"
   git push origin main
   ```

2. **Connect to Render:**
   - Go to https://dashboard.render.com
   - Click "New" → "Blueprint"
   - Connect your GitHub repository
   - Render will automatically detect `render.yaml` and set up:
     - PostgreSQL Database (aqi-db)
     - Web Service (aqi-backend)

3. **Wait for deployment:**
   - Render will automatically build and deploy your application
   - PostgreSQL database will be created first
   - Backend will be deployed and connected to the database
   - You'll get a URL like: `https://aqi-backend-xxxx.onrender.com`

### Option 2: Manual Deployment

#### Step 1: Create PostgreSQL Database

1. In Render Dashboard, click "New" → "PostgreSQL"
2. Configure:
   - **Name:** `aqi-db`
   - **Database:** `aqi_db`
   - **User:** `aqi_user`
   - **Region:** Oregon (or closest to you)
   - **Plan:** Free
3. Click "Create Database"
4. Save the connection details (Internal Database URL)

#### Step 2: Deploy Backend Web Service

1. Click "New" → "Web Service"
2. Connect your GitHub repository
3. Configure:
   - **Name:** `aqi-backend`
   - **Region:** Oregon (same as database)
   - **Branch:** `main`
   - **Root Directory:** Leave empty
   - **Environment:** `Python 3`
   - **Build Command:** `./render-build.sh`
   - **Start Command:** `gunicorn --bind 0.0.0.0:$PORT backend.app:create_app()`
   - **Plan:** Free

4. Add Environment Variables:
   Click "Advanced" → "Add Environment Variable"
   
   ```
   PYTHON_VERSION=3.9.18
   DATABASE_URL=[Paste Internal Database URL from Step 1]
   DB_NAME=aqi_db
   DB_USER=aqi_user
   DB_PASSWORD=[From database connection string]
   DB_HOST=[From database connection string]
   DB_PORT=5432
   OPENWEATHER_API_KEY=528f129d20a5e514729cbf24b2449e44
   IQAIR_API_KEY=102c31e0-0f3c-4865-b4f3-2b4a57e78c40
   CPCB_API_KEY=579b464db66ec23bdd000001eed35a78497b4993484cd437724fd5dd
   FLASK_ENV=production
   FLASK_DEBUG=0
   ```

5. Click "Create Web Service"

## Post-Deployment Steps

### 1. Initialize Database Schema

Once deployed, run the database initialization:

```bash
# Using Render Shell (from Dashboard → Shell)
python database/reset_db.py
```

### 2. Start Data Collection

Run initial data collection:

```bash
python main.py
```

### 3. Set Up Scheduled Jobs (Optional)

For automated data collection, create a Cron Job in Render:

1. Click "New" → "Cron Job"
2. Configure:
   - **Name:** `aqi-data-collection`
   - **Command:** `python main.py`
   - **Schedule:** `0 * * * *` (every hour)
   - Use same environment variables as web service

### 4. Train Models (After 24+ Hours of Data)

```bash
python train_models.py
```

## Accessing Your Application

- **Backend API:** `https://aqi-backend-xxxx.onrender.com/api/v1/health`
- **Frontend Dashboard:** `https://aqi-backend-xxxx.onrender.com`
- **API Documentation:** `https://aqi-backend-xxxx.onrender.com/api/v1/cities`

## Testing the Deployment

Test your endpoints:

```bash
# Health check
curl https://aqi-backend-xxxx.onrender.com/api/v1/health

# Get cities
curl https://aqi-backend-xxxx.onrender.com/api/v1/cities

# Get current AQI for Mumbai
curl https://aqi-backend-xxxx.onrender.com/api/v1/aqi/current/Mumbai
```

## Important Notes

### Free Tier Limitations

1. **Web Service:**
   - Spins down after 15 minutes of inactivity
   - First request after spin-down takes 30-60 seconds
   - 750 hours/month free

2. **PostgreSQL:**
   - 256 MB RAM
   - 1 GB storage
   - Expires after 90 days on free plan

3. **Recommendations:**
   - Upgrade to paid plan for production use
   - Keep only recent data to manage storage
   - Implement data archiving strategy

### Database Connection

The database URL format is:
```
postgresql://user:password@host:port/database
```

Render provides this as `DATABASE_URL` environment variable.

### CORS Configuration

The backend already has CORS enabled for all origins. For production, you may want to restrict this:

```python
# In backend/app.py
CORS(app, origins=['https://your-frontend-domain.com'])
```

### Logs

View logs in Render Dashboard:
- Go to your service
- Click "Logs" tab
- Monitor real-time application logs

## Troubleshooting

### Build Fails

1. Check `render-build.sh` has execution permissions
2. Verify `requirements.txt` is valid
3. Check Python version matches `runtime.txt`

### Database Connection Issues

1. Verify all DB environment variables are set
2. Check DATABASE_URL format
3. Ensure database and web service are in same region

### Frontend Not Loading

1. Check frontend files are in the correct directory
2. Verify routes in `backend/app.py`
3. Check browser console for errors

### Data Collection Fails

1. Verify API keys are correct
2. Check internet connectivity
3. Monitor API rate limits

## Updating the Deployment

To update your deployment:

```bash
# Make changes locally
git add .
git commit -m "Your update message"
git push origin main
```

Render will automatically detect the push and redeploy.

## Cost Optimization

1. **Use Cron Jobs instead of continuous scheduler:**
   - Deploy scheduler as Cron Job
   - Saves compute resources
   - Free tier: 400 hours/month

2. **Optimize Database Queries:**
   - Add indexes for frequently queried columns
   - Limit historical data retention
   - Use database connection pooling

3. **Implement Caching:**
   - Cache API responses
   - Store computed results
   - Reduce database queries

## Support

- Render Documentation: https://render.com/docs
- GitHub Issues: [Your Repository]/issues
- Email: [Your Email]

---

**Deployment Status Checklist:**

- [ ] Code pushed to GitHub
- [ ] PostgreSQL database created
- [ ] Web service deployed
- [ ] Environment variables configured
- [ ] Database schema initialized
- [ ] Initial data collected
- [ ] Frontend accessible
- [ ] API endpoints tested
- [ ] Cron jobs configured (optional)
- [ ] Models trained (after 24+ hours)

**Your AQI Prediction System is ready for production! 🚀**
