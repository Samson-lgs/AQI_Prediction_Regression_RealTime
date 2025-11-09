# Vercel Deployment Guide - AQI Frontend

## Quick Deploy to Vercel

### Option 1: Deploy via Vercel CLI (Recommended)

1. **Install Vercel CLI:**
   ```bash
   npm install -g vercel
   ```

2. **Login to Vercel:**
   ```bash
   vercel login
   ```

3. **Deploy from your project directory:**
   ```bash
   cd "c:\Users\Samson Jose\Desktop\AQI_Prediction_Regression_RealTime"
   vercel
   ```

4. **Follow the prompts:**
   - Set up and deploy? **Y**
   - Which scope? Select your account
   - Link to existing project? **N**
   - What's your project's name? **aqi-prediction-frontend** (or your choice)
   - In which directory is your code located? **./frontend**
   - Want to override the settings? **N**

5. **Deploy to production:**
   ```bash
   vercel --prod
   ```

### Option 2: Deploy via Vercel Dashboard

1. **Go to:** https://vercel.com/new

2. **Import your GitHub repository:**
   - Click "Import Git Repository"
   - Select: `Samson-lgs/AQI_Prediction_Regression_RealTime`

3. **Configure Project:**
   - **Framework Preset:** Other
   - **Root Directory:** `./` (leave as is)
   - **Build Command:** Leave empty (static site)
   - **Output Directory:** `frontend`
   - **Install Command:** Leave empty

4. **Environment Variables:** None needed (frontend only)

5. **Click "Deploy"**

## After Deployment

### Update Backend URL (if needed)

If your Render backend URL is different, update `frontend/config.js`:

```javascript
API_BASE_URL: 'https://YOUR-RENDER-BACKEND.onrender.com/api/v1'
```

Then redeploy:
```bash
vercel --prod
```

### Enable CORS on Backend

Make sure your Render backend allows requests from your Vercel domain:

1. Go to your Render backend code
2. Update CORS settings to include your Vercel URL:
   ```python
   CORS(app, origins=[
       "http://localhost:3000",
       "https://your-vercel-app.vercel.app",
       "https://*.vercel.app"
   ])
   ```

## Vercel Free Tier Limits

✅ **Included:**
- Unlimited static deployments
- 100 GB bandwidth per month
- Automatic HTTPS
- Global CDN
- Custom domains

## Project Structure

```
AQI_Prediction_Regression_RealTime/
├── frontend/                  # Frontend files (deployed to Vercel)
│   ├── config.js             # API configuration
│   ├── unified-app.js        # Main application logic
│   └── unified-styles.css    # Styles
├── index.html                # Main HTML file
├── vercel.json              # Vercel configuration
└── .vercelignore            # Files to ignore during deployment
```

## Troubleshooting

### Issue: API calls failing
**Solution:** Check browser console for CORS errors. Update backend CORS settings.

### Issue: 404 on refresh
**Solution:** The `vercel.json` rewrites are configured to handle this.

### Issue: Old version showing
**Solution:** Clear browser cache or use incognito mode.

## Useful Commands

```bash
# Preview deployment
vercel

# Production deployment
vercel --prod

# View deployment logs
vercel logs

# List deployments
vercel ls

# Remove deployment
vercel remove [deployment-url]
```

## Custom Domain (Optional)

1. Go to your Vercel project dashboard
2. Click "Settings" > "Domains"
3. Add your custom domain
4. Update DNS records as instructed

## Support

- Vercel Docs: https://vercel.com/docs
- Vercel Support: https://vercel.com/support
