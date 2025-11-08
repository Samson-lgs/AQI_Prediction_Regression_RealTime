# PythonAnywhere Deployment Guide for AQI Prediction System

## 🎯 Prerequisites
- PythonAnywhere account (FREE): https://www.pythonanywhere.com/registration/register/beginner/
- Your GitHub repo URL: https://github.com/Samson-lgs/AQI_Prediction_Regression_RealTime

## 📋 Step-by-Step Deployment

### 1. Create PythonAnywhere Account
1. Go to https://www.pythonanywhere.com
2. Sign up for **FREE Beginner Account**
3. Verify your email

### 2. Open a Bash Console
1. After login, click **"Consoles"** tab
2. Click **"Bash"** to start a new console

### 3. Clone Your Repository
```bash
git clone https://github.com/Samson-lgs/AQI_Prediction_Regression_RealTime.git
cd AQI_Prediction_Regression_RealTime
```

### 4. Create Virtual Environment
```bash
mkvirtualenv --python=/usr/bin/python3.10 aqi-env
```

### 5. Install Dependencies
```bash
pip install -r requirements.txt
```

### 6. Set Up Environment Variables
```bash
# Create .env file
nano .env
```

Add these lines (replace with your actual keys):
```
OPENWEATHER_API_KEY=your_openweather_key
IQAIR_API_KEY=your_iqair_key
DATABASE_URL=your_postgresql_url
SECRET_KEY=your_secret_key
FLASK_DEBUG=0
```

Press `Ctrl+X`, then `Y`, then `Enter` to save.

### 7. Set Up PostgreSQL Database

**Option A: Use External PostgreSQL (Recommended)**
- Get free PostgreSQL from:
  - Supabase: https://supabase.com (FREE, 500MB)
  - ElephantSQL: https://www.elephantsql.com (FREE, 20MB)
  - Neon: https://neon.tech (FREE, 3GB)

**Option B: Use MySQL (PythonAnywhere provides free MySQL)**
- Go to **"Databases"** tab in PythonAnywhere
- Initialize MySQL database
- Update your `database/db_config.py` to use MySQL instead

### 8. Create WSGI Configuration File

1. Go to **"Web"** tab in PythonAnywhere
2. Click **"Add a new web app"**
3. Choose **"Manual configuration"**
4. Select **Python 3.10**
5. Click on the **WSGI configuration file** link

Replace the content with:

```python
# /var/www/YOUR_USERNAME_pythonanywhere_com_wsgi.py

import sys
import os

# Add your project directory to the sys.path
project_home = '/home/YOUR_USERNAME/AQI_Prediction_Regression_RealTime'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Load environment variables
from dotenv import load_dotenv
env_path = os.path.join(project_home, '.env')
load_dotenv(env_path)

# Import Flask app
from backend.app import create_app
application = create_app()
```

**Replace `YOUR_USERNAME` with your actual PythonAnywhere username!**

### 9. Configure Static Files

In the **"Web"** tab, scroll to **"Static files"**:

| URL | Directory |
|-----|-----------|
| `/static/` | `/home/YOUR_USERNAME/AQI_Prediction_Regression_RealTime/frontend/` |

### 10. Configure Virtual Environment

In the **"Web"** tab:
- **Virtualenv:** `/home/YOUR_USERNAME/.virtualenvs/aqi-env`

### 11. Reload Web App

Click the green **"Reload"** button in the **"Web"** tab.

### 12. Access Your App

Your app will be live at:
```
https://YOUR_USERNAME.pythonanywhere.com
```

## 🔧 Troubleshooting

### View Error Logs
```bash
# In PythonAnywhere Bash console
tail -f /var/log/YOUR_USERNAME.pythonanywhere.com.error.log
```

### Check Server Log
Go to **"Web"** tab → **"Log files"** → Click on error log

### Common Issues

**1. Import Errors**
- Make sure virtual environment is activated
- Reinstall requirements: `pip install -r requirements.txt`

**2. Database Connection Errors**
- Check DATABASE_URL in `.env` file
- Ensure PostgreSQL/MySQL is accessible

**3. Static Files Not Loading**
- Check static files configuration in Web tab
- Verify frontend directory path

**4. 502 Bad Gateway**
- Check WSGI file for syntax errors
- Verify application is importing correctly

## 📊 Database Setup

### Initialize Database Tables
```bash
# In PythonAnywhere Bash console
workon aqi-env
cd ~/AQI_Prediction_Regression_RealTime
python -c "from database.db_operations import DatabaseOperations; db = DatabaseOperations(); print('Database initialized')"
```

### Run Data Collection (Optional)
```bash
# Collect initial data
python -m backend.main
```

## 🔄 Updating Your App

When you push changes to GitHub:

```bash
# In PythonAnywhere Bash console
cd ~/AQI_Prediction_Regression_RealTime
git pull origin main
pip install -r requirements.txt  # if requirements changed
# Go to Web tab and click Reload
```

## 🌐 Custom Domain (Optional - Paid Feature)

Free accounts get: `YOUR_USERNAME.pythonanywhere.com`

To use custom domain:
1. Upgrade to paid account ($5/month)
2. Configure DNS settings
3. Add domain in Web tab

## 📝 Important Notes

### PythonAnywhere Free Tier Limitations:
- ✅ One web app
- ✅ 512MB storage
- ✅ HTTPS enabled
- ❌ No outbound HTTPS (API calls may be limited)
- ❌ No scheduled tasks (need paid account for cron jobs)

### Workarounds:
- For API calls: Upgrade to paid account ($5/month) for whitelist
- For scheduled tasks: Use external cron service or upgrade

## 🎉 Success Checklist

- [ ] Account created
- [ ] Repository cloned
- [ ] Virtual environment created
- [ ] Dependencies installed
- [ ] Environment variables set
- [ ] Database configured
- [ ] WSGI file configured
- [ ] Static files mapped
- [ ] Web app reloaded
- [ ] Site accessible

## 🆘 Need Help?

- PythonAnywhere Help: https://help.pythonanywhere.com/
- Forums: https://www.pythonanywhere.com/forums/
- Your app logs: Web tab → Log files

---

**Your App URL:** `https://YOUR_USERNAME.pythonanywhere.com`

Replace `YOUR_USERNAME` with your actual PythonAnywhere username throughout this guide!
