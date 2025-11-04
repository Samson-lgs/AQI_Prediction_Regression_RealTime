# 🚀 Quick Render Deployment Steps

## ✅ Prerequisites Complete
- [x] All code committed to GitHub
- [x] Deployment files created (render.yaml, render-build.sh)
- [x] Environment configuration ready

## 📋 Step-by-Step Deployment

### **Step 1: Sign Up / Log In to Render**
👉 Go to: https://render.com
- Click "Get Started" or "Sign In"
- Use GitHub to sign in (recommended)

---

### **Step 2: Deploy Using Blueprint (Easiest!)**

1. **Go to Dashboard:**
   https://dashboard.render.com

2. **Create New Blueprint:**
   - Click the **"New +"** button (top right)
   - Select **"Blueprint"**

3. **Connect Repository:**
   - Select **"Connect a repository"**
   - Choose: **Samson-lgs/AQI_Prediction_Regression_RealTime**
   - Click **"Connect"**

4. **Configure Blueprint:**
   - Render will detect `render.yaml` automatically
   - Review the configuration:
     - ✅ PostgreSQL Database: `aqi-db`
     - ✅ Web Service: `aqi-backend`
   - Click **"Apply"**

5. **Wait for Deployment:**
   - Database creation: ~2-3 minutes
   - Backend deployment: ~5-10 minutes
   - Watch the logs for progress

---

### **Step 3: Get Your Deployment URLs**

After deployment completes:

1. **Backend API URL:**
   ```
   https://aqi-backend-xxxx.onrender.com
   ```

2. **Frontend Dashboard:**
   ```
   https://aqi-backend-xxxx.onrender.com
   ```

3. **API Health Check:**
   ```
   https://aqi-backend-xxxx.onrender.com/api/v1/health
   ```

---

### **Step 4: Initialize Database (IMPORTANT!)**

Once deployed, initialize the database schema:

1. **Open Shell:**
   - In Render Dashboard
   - Go to your `aqi-backend` service
   - Click **"Shell"** tab (top right)

2. **Run Database Setup:**
   ```bash
   python database/reset_db.py
   ```

3. **Start Data Collection:**
   ```bash
   python main.py
   ```
   (Press Ctrl+C after it collects data for all cities)

---

### **Step 5: Set Up Automated Data Collection**

#### Option A: Using Cron Job (Recommended for Free Tier)

1. **Create Cron Job:**
   - Click **"New +"** → **"Cron Job"**
   - Connect same repository

2. **Configure:**
   - **Name:** `aqi-data-collection`
   - **Command:** `python main.py`
   - **Schedule:** `0 * * * *` (every hour)
   - **Environment:** Same as web service

3. **Add Environment Variables:**
   Copy all environment variables from web service:
   - DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, DB_PORT
   - OPENWEATHER_API_KEY, IQAIR_API_KEY, CPCB_API_KEY

#### Option B: Using scheduler.py (Continuous)

In the Shell:
```bash
python scheduler.py &
```

---

### **Step 6: Test Your Deployment**

#### Test API Endpoints:

```bash
# Health check
curl https://aqi-backend-xxxx.onrender.com/api/v1/health

# Get all cities
curl https://aqi-backend-xxxx.onrender.com/api/v1/cities

# Get Mumbai AQI
curl https://aqi-backend-xxxx.onrender.com/api/v1/aqi/current/Mumbai

# Get Delhi history
curl https://aqi-backend-xxxx.onrender.com/api/v1/aqi/history/Delhi?days=7
```

#### Test Frontend:
- Open `https://aqi-backend-xxxx.onrender.com` in browser
- Select a city from dropdown
- Verify AQI displays correctly
- Check charts are rendering

---

## 🎉 Deployment Complete!

Your AQI Prediction System is now live at:
```
https://aqi-backend-xxxx.onrender.com
```

### What's Working:
✅ Backend API with 6 endpoints
✅ Frontend dashboard with interactive charts
✅ PostgreSQL database with connection pooling
✅ Data collection for 56 Indian cities
✅ Real-time AQI monitoring

### Next Steps:
1. ⏰ Wait 24+ hours for data accumulation
2. 🤖 Train ML models: `python train_models.py`
3. 📊 Monitor performance in Render Dashboard
4. 🔄 Set up automatic model retraining (optional)

---

## 🆘 Troubleshooting

### Build Fails
- Check logs in Render Dashboard
- Verify `render-build.sh` syntax
- Ensure Python version is 3.9.18

### Database Connection Issues
- Verify environment variables are set
- Check DATABASE_URL format
- Ensure database is running

### Frontend Not Loading
- Clear browser cache
- Check browser console for errors
- Verify API endpoints are accessible

### Need Help?
- Check `RENDER_DEPLOYMENT.md` for detailed guide
- View logs in Render Dashboard
- GitHub Issues: https://github.com/Samson-lgs/AQI_Prediction_Regression_RealTime/issues

---

## 📝 Important Notes

### Free Tier Limitations:
- ⚠️ Web service spins down after 15 min inactivity
- ⚠️ First request takes 30-60 sec to wake up
- ⚠️ 750 hours/month (shared across services)
- ⚠️ Database expires after 90 days

### Cost Optimization:
- Use Cron Jobs instead of continuous scheduler
- Implement data retention policy
- Upgrade to paid plan for production

### Security:
- Never commit `.env` file
- Use Render's environment variables
- Enable CORS restrictions for production

---

**Your deployment is ready! Share your dashboard URL with others! 🚀**

