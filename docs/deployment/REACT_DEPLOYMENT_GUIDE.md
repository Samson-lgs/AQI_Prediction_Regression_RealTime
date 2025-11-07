# React Frontend Deployment Guide

## Overview

This guide will help you deploy the new React frontend dashboard **alongside** your existing deployment without disrupting current services.

## Current Deployment Status

✅ **Already Deployed:**
- `aqi-backend-api` - Flask backend with REST API & WebSocket
- `aqi-frontend` - Old vanilla JavaScript frontend
- `aqi-database` - PostgreSQL database

🆕 **New Service to Deploy:**
- `aqi-react-dashboard` - Modern React dashboard with real-time updates

## Deployment Strategy: Zero-Downtime Update

We'll deploy the React frontend as a **new separate service** so you can:
- ✅ Keep the old frontend running (backup)
- ✅ Test the React dashboard thoroughly
- ✅ Switch traffic when ready
- ✅ Delete old frontend later

---

## Step 1: Update Backend for WebSocket Support

The React frontend needs WebSocket support. Update your backend:

### 1.1 Add Redis Environment Variable (Optional)

In Render Dashboard → `aqi-backend-api` → Environment:

```
REDIS_URL=redis://localhost:6379
```

**Note:** Redis is optional. If not available, the app will work without caching.

### 1.2 Verify Backend Health

Test that your backend supports all required endpoints:

```bash
# Health check
curl https://aqi-backend-api.onrender.com/api/v1/health

# WebSocket endpoint (should not return 404)
curl https://aqi-backend-api.onrender.com/socket.io/

# Cities endpoint
curl https://aqi-backend-api.onrender.com/api/v1/cities/
```

---

## Step 2: Push Updated Code to GitHub

The `render.yaml` has been updated to include the React frontend.

```powershell
# 1. Add all changes
git add .

# 2. Commit with descriptive message
git commit -m "feat: Add React frontend deployment configuration

- Updated render.yaml to deploy React as separate service
- Added environment variable support for API URLs
- Configured build and serve commands
- Ready for zero-downtime deployment"

# 3. Push to GitHub
git push origin main
```

---

## Step 3: Deploy React Frontend on Render

### Option A: Using Blueprint (Recommended - Auto-deploys all services)

⚠️ **Warning:** This will trigger re-deployment of ALL services in `render.yaml`.

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Your existing Blueprint should auto-detect changes
3. Click **"Sync"** or **"Apply"** on the blueprint
4. Wait 10-15 minutes for `aqi-react-dashboard` to deploy

### Option B: Manual Service Creation (Safer - Deploy only React)

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **New** → **Web Service**
3. Connect your repository
4. Configure:

   **Service Details:**
   - Name: `aqi-react-dashboard`
   - Region: `Oregon` (same as backend)
   - Branch: `main`
   - Root Directory: Leave empty
   - Environment: `Node`

   **Build & Deploy:**
   - Build Command: 
     ```
     cd frontend-react && npm install && npm run build
     ```
   - Start Command:
     ```
     cd frontend-react && npx serve -s dist -l $PORT
     ```

   **Environment Variables:**
   - `NODE_VERSION` = `18.18.0`
   - `VITE_API_URL` = `https://aqi-backend-api.onrender.com/api/v1`
   - `VITE_WS_URL` = `https://aqi-backend-api.onrender.com`

   **Advanced Settings:**
   - Health Check Path: `/`
   - Auto-Deploy: `Yes`

5. Click **Create Web Service**
6. Wait 10-15 minutes for build and deployment

---

## Step 4: Verify React Dashboard

Once deployed, you'll get a URL like:
```
https://aqi-react-dashboard.onrender.com
```

### Test Checklist:

1. ✅ **Dashboard loads without errors**
   - Open URL in browser
   - Check browser console (F12) for errors

2. ✅ **City selector works**
   - Cities dropdown shows 56 cities
   - Can search and select cities

3. ✅ **Data displays correctly**
   - Current AQI card shows data
   - Pollutant metrics display
   - Forecast chart renders

4. ✅ **WebSocket connection works**
   - Header shows "Live" status (green dot)
   - Real-time updates received

5. ✅ **API calls succeed**
   - Check Network tab (F12)
   - All API calls return 200 OK
   - No CORS errors

### Troubleshooting:

**Problem:** Dashboard loads but shows "No data"
- **Solution:** Backend might be sleeping (free tier). Wait 30-60 seconds.

**Problem:** CORS errors in console
- **Solution:** Verify `FRONTEND_ORIGIN` in backend includes React dashboard URL.

**Problem:** WebSocket not connecting
- **Solution:** Check `VITE_WS_URL` environment variable points to correct backend.

**Problem:** 404 on routes (e.g., /city/Delhi)
- **Solution:** Add fallback route in Render dashboard:
  - Go to service → Settings → Redirects/Rewrites
  - Add: `/*` → `/index.html` (SPA mode)

---

## Step 5: Update CORS in Backend (If Needed)

If you see CORS errors, update backend CORS settings:

### 5.1 Edit `backend/app.py`

```python
# Update FRONTEND_ORIGIN to include React dashboard
FRONTEND_ORIGIN = os.getenv('FRONTEND_ORIGIN', 
    'https://aqi-react-dashboard.onrender.com,https://aqi-frontend.onrender.com')
```

### 5.2 Add Environment Variable in Render

Backend service → Environment:
```
FRONTEND_ORIGIN=https://aqi-react-dashboard.onrender.com
```

### 5.3 Commit and Push

```powershell
git add backend/app.py
git commit -m "fix: Update CORS for React dashboard"
git push origin main
```

Backend will auto-redeploy (~5 minutes).

---

## Step 6: Performance Optimization (Optional)

### 6.1 Enable Compression

React build already includes:
- ✅ Minified JavaScript
- ✅ Code splitting
- ✅ Tree shaking
- ✅ Asset optimization

### 6.2 Add Custom Domain (Optional)

1. Go to React service → Settings
2. Add custom domain (e.g., `aqi.yourdomain.com`)
3. Update DNS records as instructed
4. SSL certificate auto-generated

### 6.3 Keep Services Awake (Optional - Costs $5/month)

Free tier services sleep after 15 minutes. To prevent:
- Upgrade to **Starter plan** ($7/month per service)
- Or use external monitoring (e.g., UptimeRobot) to ping every 10 minutes

---

## Step 7: Make React Dashboard Primary

Once you've tested thoroughly and are satisfied:

### Option A: Switch Custom Domain
If using custom domain:
1. Point domain to `aqi-react-dashboard` instead of `aqi-frontend`
2. Users automatically get React version

### Option B: Update Links
Update any links in:
- Documentation
- README
- External sites
- Social media

### Option C: Redirect Old Frontend
Add redirect in old frontend's `index.html`:
```html
<script>
  window.location.href = 'https://aqi-react-dashboard.onrender.com';
</script>
```

---

## Step 8: Clean Up (After 1 Week)

After confirming React dashboard works perfectly:

### Delete Old Frontend (Optional)
1. Go to Render Dashboard
2. Select `aqi-frontend` service
3. Settings → Delete Service
4. Saves free tier resources

### Update render.yaml
Remove old frontend section:
```yaml
# Remove this section after deletion:
  - type: web
    name: aqi-frontend
    ...
```

Commit and push:
```powershell
git add render.yaml
git commit -m "chore: Remove old frontend from deployment config"
git push origin main
```

---

## Monitoring & Maintenance

### Check Service Logs
- Render Dashboard → Service → Logs
- Monitor for errors or warnings

### Monitor Performance
- Check response times in Network tab
- Verify WebSocket stability
- Watch for memory issues

### Update Dependencies
Every few months:
```powershell
cd frontend-react
npm update
npm audit fix
git add package.json package-lock.json
git commit -m "chore: Update React dependencies"
git push origin main
```

---

## Cost Breakdown

**Current Setup (After React Deployment):**

| Service | Type | Cost | Notes |
|---------|------|------|-------|
| `aqi-database` | PostgreSQL | Free | 256MB RAM, 1GB storage |
| `aqi-backend-api` | Web Service | Free | Sleeps after 15 min |
| `aqi-frontend` (old) | Static Site | Free | Can delete later |
| `aqi-react-dashboard` | Web Service | Free | Sleeps after 15 min |

**Total: $0/month** ✅

**After deleting old frontend: Still $0/month**

---

## Quick Reference

### Service URLs
```
Backend API:       https://aqi-backend-api.onrender.com
Old Frontend:      https://aqi-frontend.onrender.com
React Dashboard:   https://aqi-react-dashboard.onrender.com
API Docs:          https://aqi-backend-api.onrender.com/api/v1/docs
```

### Key Files Updated
- `render.yaml` - Added React service configuration
- `frontend-react/src/store.js` - Added environment variable support
- `frontend-react/package.json` - Added serve dependency

### Environment Variables (React Service)
```
NODE_VERSION=18.18.0
VITE_API_URL=https://aqi-backend-api.onrender.com/api/v1
VITE_WS_URL=https://aqi-backend-api.onrender.com
```

---

## Rollback Plan

If React dashboard has issues:

1. **Keep old frontend running** - Already deployed, no changes needed
2. **Point users back** - Update links to old frontend URL
3. **Debug React** - Check logs, fix issues
4. **Redeploy** - Push fixes, auto-redeploys

**Zero data loss** - Database unaffected by frontend changes.

---

## Success Criteria

✅ React dashboard loads without errors  
✅ Can select and view data for all 56 cities  
✅ Real-time WebSocket updates working  
✅ Charts and visualizations render correctly  
✅ Mobile responsive (test on phone)  
✅ No CORS or API errors  
✅ Performance acceptable (< 3s load time)  

---

## Next Steps After Deployment

1. **Test thoroughly** - Try all features
2. **Share with users** - Get feedback
3. **Monitor for 1 week** - Check for issues
4. **Delete old frontend** - If satisfied
5. **Celebrate!** 🎉

---

## Support

**Documentation:**
- React Frontend: `frontend-react/README.md`
- Backend API: `STEP3_SYSTEM_DESIGN_COMPLETE.md`
- General Deployment: `DEPLOYMENT_CHECKLIST.md`

**Logs:**
- Render Dashboard → Service → Logs tab

**Issues:**
- Create GitHub issue with error details

---

**Ready to deploy? Follow the steps above!** 🚀
