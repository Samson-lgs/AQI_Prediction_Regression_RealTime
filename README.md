# Air Quality Index Prediction System

## Project Overview
A comprehensive, production-ready AQI prediction system leveraging machine learning regression models and integrating real-time data from CPCB, OpenWeather, and IQAir APIs for 67 Indian cities. Features automated data collection, model training, and deployment on Render.com with GitHub Actions CI/CD.

## ✨ Key Features

### Data Collection & Processing
- ✅ **Multi-source data integration** (CPCB, OpenWeather, IQAir)
- ✅ **Parallel data collection** for 67 cities (4 workers, ~0.42s/city)
- ✅ **Advanced data cleaning** with outlier detection and imputation
- ✅ **100+ engineered features** (temporal, cyclical, lag, rolling windows)
- ✅ **PostgreSQL time-series storage** with optimized indexes

### Machine Learning
- ✅ **Four ML models**: Linear Regression, Random Forest, XGBoost, LSTM
- ✅ **Time-series aware training** (no data leakage, chronological splits)
- ✅ **Auto model selection** based on performance metrics
- ✅ **42+ cities trained** with models ready for predictions
- ✅ **Performance tracking** with R², RMSE, MAE, MAPE metrics

### Web Application
- ✅ **Interactive dashboard** with real-time visualizations (Plotly.js)
- ✅ **RESTful API** with Swagger documentation (/api/v1/docs)
- ✅ **Real-time WebSocket updates** for live data streaming
- ✅ **Alert system** with email/SMS notifications
- ✅ **Mobile-responsive design** for all devices

### Deployment & Automation
- ✅ **Deployed on Render.com** (backend + frontend + database)
- ✅ **GitHub Actions workflows** for automated retraining
- ✅ **Docker containerization** for local development
- ✅ **Weekly auto-retraining** (every Sunday at 2 AM UTC)
- ✅ **Continuous data collection** (hourly updates)

## Quick Start

### Prerequisites
- Python 3.9+
- PostgreSQL 13+
- 8GB RAM minimum
- Docker (optional, for containerized deployment)

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/Samson-lgs/AQI_Prediction_Regression_RealTime.git
cd AQI_Prediction_Regression_RealTime
```

2. **Create virtual environment:**
```bash
python -m venv aqi_env
# Windows:
aqi_env\Scripts\activate
# Linux/Mac:
source aqi_env/bin/activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

### Configuration

1. **Create `.env` file in project root:**
```env
# Database Configuration (for local development)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=aqi_db
DB_USER=postgres
DB_PASSWORD=your_password

# Or use DATABASE_URL for Render deployment
DATABASE_URL=postgresql://user:password@host:port/database

# API Keys
CPCB_API_KEY=your_cpcb_api_key
OPENWEATHER_API_KEY=your_openweather_api_key
IQAIR_API_KEY=your_iqair_api_key

# Flask Configuration
FLASK_ENV=production
FLASK_DEBUG=0
SECRET_KEY=your_secret_key_here
```

2. **Initialize database:**
```bash
# Set DATABASE_URL first
export DATABASE_URL="postgresql://user:password@host:port/database"
# Windows PowerShell:
$env:DATABASE_URL="postgresql://user:password@host:port/database"

# Then initialize
python database/reset_db.py
```

### Running the System

#### 1. Data Collection (Continuous)
```bash
# Start background data collector
python backend/main.py

# Or run once and exit
python backend/main.py --once
```
This collects hourly data for all 67 cities from multiple APIs.

#### 2. Train Models
```bash
# Check data coverage first
python scripts/report_data_coverage.py

# Train all cities with sufficient data (100+ samples)
python models/train_all_models.py --all --min-samples 100

# Or train specific city
python models/train_all_models.py --city "Delhi" --min-samples 50
```
**Note**: Need 48+ hours of continuous data for R² > 0.70

#### 3. Start Backend API Server
```bash
# Development
python backend/app.py

# Production (with Gunicorn)
gunicorn --bind 0.0.0.0:5000 --workers 1 wsgi:app
```

#### 4. Access Applications
- **Frontend Dashboard**: http://localhost:5000
- **API Documentation**: http://localhost:5000/api/v1/docs
- **API Endpoints**: http://localhost:5000/api/v1/

#### 5. Import Historical Data (Optional - for quick training)
```bash
# Generate 90 days of synthetic historical data
python scripts/import_historical_data.py
```
This creates realistic training data for immediate model training.

## Project Structure

```
AQI_Prediction_Regression_RealTime/
├── .github/workflows/          # GitHub Actions CI/CD
│   └── retrain_models.yml     # Weekly automated retraining
├── api_handlers/              # API integration modules
│   ├── cpcb_handler.py       # CPCB API integration
│   ├── openweather_handler.py # OpenWeather API
│   └── iqair_handler.py      # IQAir API
├── backend/                   # Flask backend
│   ├── app.py                # Flask application factory
│   ├── api_routes.py         # Enhanced API with Swagger
│   ├── routes.py             # Basic API endpoints
│   ├── main.py               # Data collection pipeline
│   ├── cache_manager.py      # Redis caching (optional)
│   ├── email_utils.py        # Email notifications
│   └── websocket_handler.py  # Real-time WebSocket
├── config/                    # Configuration files
│   ├── settings.py           # App settings & city list
│   └── logging_config.py     # Logging configuration
├── database/                  # Database operations
│   ├── db_config.py          # Connection pooling
│   ├── db_operations.py      # CRUD operations
│   ├── reset_db.py           # Database initialization
│   ├── optimize_schema.py    # Schema optimization
│   └── step7_schema_updates.sql # Monitoring tables
├── feature_engineering/       # Feature processing
│   ├── data_cleaner.py       # Advanced cleaning pipeline
│   └── feature_processor.py  # 100+ feature engineering
├── frontend/                  # Web dashboard (HTML/CSS/JS)
│   ├── index.html            # Main dashboard
│   ├── styles.css            # Styling
│   ├── script.js             # Frontend logic
│   └── config.js             # API configuration
├── frontend-react/            # React dashboard (optional)
│   ├── src/                  # React components
│   ├── package.json          # Dependencies
│   └── vite.config.js        # Build configuration
├── ml_models/                 # ML model implementations
│   ├── linear_regression_model.py
│   ├── random_forest_model.py
│   ├── xgboost_model.py
│   └── lstm_model.py
├── models/                    # Training & utilities
│   ├── train_all_models.py   # Batch training script
│   ├── train_models.py       # Core training logic
│   ├── model_utils.py        # Model selection
│   ├── time_series_cv.py     # Time-series validation
│   ├── hyperparameter_tuning.py # Grid search
│   └── trained_models/       # Saved models (168 files)
├── monitoring/                # Step 7: Continuous improvement
│   ├── performance_monitor.py # Track model metrics
│   ├── data_drift_detector.py # Detect distribution shifts
│   ├── auto_model_selector.py # Best model selection
│   ├── alert_manager.py      # Threshold alerts
│   └── documentation_manager.py # Auto-generate docs
├── scripts/                   # Utility scripts
│   ├── report_data_coverage.py # Check data availability
│   ├── import_historical_data.py # Generate training data
│   └── deploy_render.sh      # Deployment helper
├── tests/                     # Unit & integration tests
│   ├── test_api_handlers.py
│   ├── test_database.py
│   ├── test_models.py
│   └── test_complete_pipeline.py
├── logs/                      # Application logs
├── data/                      # Data storage
│   ├── raw/                  # Raw collected data
│   └── processed/            # Processed features
├── wsgi.py                    # Gunicorn WSGI entry point
├── Dockerfile                 # Docker configuration
├── docker-compose.yml         # Multi-container setup
├── render.yaml                # Render deployment config
├── requirements.txt           # Python dependencies
├── runtime.txt               # Python version (3.11)
└── README.md                 # This file
```

## API Endpoints

### Base URL
- **Local**: `http://localhost:5000/api/v1`
- **Production**: `https://aqi-backend-api.onrender.com/api/v1`

### Documentation
- **Swagger UI**: `/api/v1/docs` (Interactive API documentation)

### Endpoints

| Endpoint | Method | Description | Parameters |
|----------|--------|-------------|------------|
| `/cities` | GET | Get list of 67 supported cities | None |
| `/cities/rankings` | GET | Get city rankings by AQI | days, metric |
| `/aqi/current/<city>` | GET | Current AQI data for city | city (path) |
| `/aqi/history/<city>` | GET | Historical AQI data | city, days (default=7) |
| `/forecast/<city>` | GET | 48-hour AQI forecast | city (path) |
| `/forecast/batch` | POST | Batch predictions | cities[], hours_ahead |
| `/models/<city>` | GET | Available models for city | city (path) |
| `/metrics/<city>` | GET | Model performance metrics | city, model |
| `/alerts/<city>` | GET/POST | Manage AQI alerts | city, threshold, type |
| `/health` | GET | API health check | None |

### Example Requests

**Get list of cities:**
```bash
curl https://aqi-backend-api.onrender.com/api/v1/cities
```

**Get current AQI for Delhi:**
```bash
curl https://aqi-backend-api.onrender.com/api/v1/aqi/current/Delhi
```

**Get 7-day history for Mumbai:**
```bash
curl https://aqi-backend-api.onrender.com/api/v1/aqi/history/Mumbai?days=7
```

**Get 48-hour forecast for Bangalore:**
```bash
curl https://aqi-backend-api.onrender.com/api/v1/forecast/Bangalore
```

**Batch predictions:**
```bash
curl -X POST https://aqi-backend-api.onrender.com/api/v1/forecast/batch \
  -H "Content-Type: application/json" \
  -d '{"cities": ["Delhi", "Mumbai", "Bangalore"], "hours_ahead": 24}'
```

## Current Performance Status (Nov 6, 2025)

### Data Collection
- **Total Records**: 2,328+ rows and growing
- **Time Span**: 38 hours (Nov 4-6, 2025)
- **Coverage**: 33 distinct hours collected
- **Cities Active**: 66/67 cities (Hubli-Dharwad failed)
- **Best Coverage**: 22/24 hours (91.7%) in last 24h

### Model Training
- **Cities Trained**: 42/67 cities successfully trained
- **Total Models**: 168 model files (42 cities × 4 models)
- **Best Performing Models**:
  - Amritsar: R²=0.7938 (XGBoost) ⭐
  - Agra: R²=0.6915 (Linear Regression)
  - Aligarh: R²=0.5603 (XGBoost)
  - Ahmedabad: R²=0.5016 (Random Forest)

### Performance Targets

| Metric | Current (33h data) | Target (48h+) | Target (168h+) |
|--------|-------------------|---------------|----------------|
| **R² Score** | 0.40-0.79 | > 0.70 | > 0.85 |
| **RMSE** | Variable | < 25 µg/m³ | < 15 µg/m³ |
| **MAE** | Variable | < 15 µg/m³ | < 10 µg/m³ |
| **MAPE** | 50-70% | < 20% | < 12% |
| **Cities Trained** | 42/67 | 60+/67 | 67/67 |
| **Forecast Horizon** | 1-48 hours | 1-48 hours | 1-48 hours |

**Note**: Model accuracy improves with more continuous hourly data. Current performance is expected with only 33 hours of data. Target R² > 0.85 achievable after 7+ days of continuous collection.

## Technologies Used

### Backend
- **Framework**: Flask 2.3.0
- **Database**: PostgreSQL 13+ with psycopg2
- **Web Server**: Gunicorn (production)

### Machine Learning
- **scikit-learn** 1.2.1 - Linear Regression, Random Forest
- **XGBoost** 1.7.4 - Gradient Boosting
- **TensorFlow/Keras** 2.12.0 - LSTM Neural Networks
- **NumPy** 1.23.5 - Numerical computing
- **Pandas** 1.5.3 - Data manipulation

### Frontend
- **HTML5**, **CSS3**, **JavaScript**
- **Plotly.js** - Interactive visualizations
- **Responsive Design** - Mobile-friendly

### Deployment
- **Docker** & **Docker Compose** - Containerization
- **Render.com** - Cloud deployment
- **GitHub Actions** - CI/CD (optional)

### APIs
- **CPCB** - Central Pollution Control Board (India)
- **OpenWeather** - Weather and pollution data
- **IQAir** - Global air quality data

## 67 Indian Cities Covered

**Tier 1 Metro Cities (8 priority):**
Delhi, Mumbai, Bangalore, Chennai, Kolkata, Hyderabad, Pune, Ahmedabad

**Tier 2 Major Cities (59):**
Jaipur, Lucknow, Kanpur, Nagpur, Indore, Bhopal, Visakhapatnam, Pimpri-Chinchwad, Patna, Vadodara, Ghaziabad, Ludhiana, Agra, Nashik, Faridabad, Meerut, Rajkot, Varanasi, Srinagar, Aurangabad, Dhanbad, Amritsar, Navi Mumbai, Allahabad, Ranchi, Howrah, Coimbatore, Jabalpur, Gwalior, Vijayawada, Jodhpur, Madurai, Raipur, Kota, Chandigarh, Guwahati, Solapur, Hubli-Dharwad, Bareilly, Moradabad, Mysore, Gurgaon, Aligarh, Jalandhar, Bhubaneswar, Salem, Warangal, Alwar, Bharatpur, Kurnool, Kadapa, Rajahmundry, Ajmer, Jamnagar, Ujujain, Kolhapur, Nanded, Durgapur, Asansol

**Total**: 67 cities across all major Indian states

## Deployment Options

### Option 1: Render.com (Recommended for Production)

**Separate services architecture with GitHub Actions for scheduling:**

1. **Deploy to Render:**
   - See [RENDER_DEPLOYMENT.md](RENDER_DEPLOYMENT.md) for detailed instructions
   - See [QUICK_DEPLOY_GUIDE.md](QUICK_DEPLOY_GUIDE.md) for quick start
   - Uses Render Blueprint for automated deployment
   - Separate services: Database, Backend API, Frontend

2. **Setup GitHub Actions:**
   - See [GITHUB_ACTIONS_SETUP.md](GITHUB_ACTIONS_SETUP.md) for complete guide
   - Configure repository secrets (database credentials)
   - Automated hourly data collection
   - Automated daily model training
   - Free tier: 2000 minutes/month

**Services:**
- **Database**: PostgreSQL on Render (free tier, 256MB RAM)
- **Backend API**: Flask + Gunicorn on Render (free tier, 512MB RAM)
- **Frontend**: Static site on Render (free tier, always on)
- **Scheduler**: GitHub Actions (free tier, 2000 min/month)

**Total Cost**: $0/month (all free tiers!)

### Option 2: Docker Compose (Local/Development)

1. **Build and start:**
```bash
docker-compose up --build
```

2. **Initialize database:**
```bash
docker exec aqi-prediction-system-web-1 python database/reset_db.py
```

3. **Access application:**
- Frontend: http://localhost:5000
- API: http://localhost:5000/api/v1

4. **Stop containers:**
```bash
docker-compose down
```

## Testing

**Run all tests:**
```bash
pytest tests/ -v
```

**Run specific test file:**
```bash
pytest tests/test_complete_pipeline.py -v
```

**Run with coverage:**
```bash
pytest tests/ --cov=. --cov-report=html
```

## Contributors

- **Drushya M** (4AD23CI014)
- **Kavana P** (4AD23CI019)
- **Samson Jose J** (4AD23CI047)
- **Yashwanth J** (4AD23CI062)

## Academic Information

- **Institution**: ATME College of Engineering
- **Department**: Computer Science & Engineering
- **Course**: Machine Learning / Data Science Project
- **Year**: 2024-2025

## License

MIT License - See [LICENSE](LICENSE) file for details

## Acknowledgments

- Central Pollution Control Board (CPCB) for air quality data (optional)
- OpenWeather for weather API services
- IQAir for global air quality monitoring
- scikit-learn, XGBoost, and TensorFlow communities

## Support

For issues and questions:
- **GitHub Issues**: https://github.com/Samson-lgs/AQI_Prediction_Regression_RealTime/issues
- **Documentation**: See DEPLOYMENT.md for detailed deployment instructions

## Future Enhancements

1. **Model Optimization**: Hyperparameter tuning with GridSearchCV
2. **Real-time Alerts**: Email/SMS notifications for critical AQI levels
3. **Mobile App**: React Native or Flutter implementation
4. **Advanced Analytics**: Anomaly detection and causality analysis
5. **Scaling**: Load balancing and horizontal scaling
6. **CI/CD**: GitHub Actions for automated testing and deployment
7. **Monitoring**: Prometheus/Grafana for system monitoring
8. **More Cities**: Expand to all major Indian cities

---

**Last Updated**: November 6, 2025  
**Version**: 1.0.0  
**Status**: Production Ready ✅
