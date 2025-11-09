# 🚀 Quick Vercel Deployment Steps

## Method 1: Vercel Dashboard (Easiest - No CLI needed)

### Step 1: Go to Vercel
Visit: https://vercel.com/new

### Step 2: Import Repository
1. Click **"Import Git Repository"**
2. If not connected, authorize Vercel to access your GitHub
3. Select: **`Samson-lgs/AQI_Prediction_Regression_RealTime`**

### Step 3: Configure Project
- **Framework Preset:** Other (or select "Other" from dropdown)
- **Root Directory:** Leave as `./`
- **Build Command:** Leave EMPTY
- **Output Directory:** Enter `frontend`
- **Install Command:** Leave EMPTY

### Step 4: Deploy
Click **"Deploy"** button

### Step 5: Wait
⏳ Vercel will build and deploy (takes ~1-2 minutes)

### Step 6: Done! 🎉
You'll get a URL like: `https://your-project-name.vercel.app`

---

## Method 2: Using Vercel CLI (Advanced)

### Step 1: Install Vercel CLI
```powershell
npm install -g vercel
```

### Step 2: Login
```powershell
vercel login
```

### Step 3: Deploy
```powershell
cd "c:\Users\Samson Jose\Desktop\AQI_Prediction_Regression_RealTime"
vercel
```

Follow the prompts:
- Link to existing project? **N**
- Project name? **aqi-prediction** (or your choice)
- In which directory is your code? **./frontend**
- Override settings? **N**

### Step 4: Production Deploy
```powershell
vercel --prod
```

---

## After Deployment Checklist

### ✅ Test Your Deployment
1. Visit your Vercel URL
2. Open browser DevTools (F12) → Console
3. Check for any errors
4. Test all tabs:
   - Live Dashboard
   - Forecast
   - Compare Cities
   - Alerts

### ✅ Verify Backend Connection
Open Console and look for:
```
Rankings batch response: {requested: 10, returned: 10...}
```

If you see errors about API calls, check next step.

### ⚠️ If API Calls Fail (CORS Error)

Your Render backend needs to allow requests from Vercel.

**Update backend CORS settings:**
1. Find your backend's CORS configuration (usually in `backend/app.py` or `backend/main.py`)
2. Add your Vercel domain:
   ```python
   CORS(app, origins=[
       "http://localhost:3000",
       "http://localhost:5000",
       "https://your-app-name.vercel.app",  # Add this
       "https://*.vercel.app"                # Or use wildcard
   ])
   ```
3. Redeploy your backend on Render

---

## Custom Domain (Optional)

1. Go to: https://vercel.com/dashboard
2. Select your project
3. Click **"Settings"** → **"Domains"**
4. Add your custom domain
5. Update DNS records as instructed

---

## Troubleshooting

### Issue: White screen or 404
**Solution:** Clear browser cache, try incognito mode

### Issue: API calls timeout
**Solution:** Check if Render backend is awake (free tier sleeps after 15 min inactivity)

### Issue: Old version showing
**Solution:** 
```powershell
vercel --prod  # Force redeploy
```

---

## Important Files Created

✅ `vercel.json` - Vercel configuration
✅ `.vercelignore` - Files to ignore during deployment  
✅ `index.html` - Main entry point
✅ `frontend/config.js` - Auto-detects Vercel deployment
✅ `VERCEL_DEPLOY.md` - Detailed documentation

---

## Useful Vercel Commands

```powershell
vercel          # Preview deployment
vercel --prod   # Production deployment
vercel logs     # View logs
vercel ls       # List deployments
vercel domains  # Manage domains
```

---

## What's Deployed?

**Frontend Only:**
- ✅ HTML, CSS, JavaScript files
- ✅ Static assets
- ✅ Client-side code

**Backend (stays on Render):**
- ✅ Python Flask API
- ✅ Database connections
- ✅ ML models
- ✅ Data processing

---

## Free Tier Limits

**Vercel Free Tier includes:**
- ✅ Unlimited deployments
- ✅ 100 GB bandwidth/month
- ✅ Automatic HTTPS
- ✅ Global CDN
- ✅ Custom domains

**This is MORE than enough for your frontend!** 🎉

---

## Need Help?

- Vercel Docs: https://vercel.com/docs
- Vercel Support: https://vercel.com/support
- GitHub Repo: https://github.com/Samson-lgs/AQI_Prediction_Regression_RealTime
