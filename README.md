# Air Quality Index Prediction System

## Project Overview
This is a comprehensive AQI prediction system using machine learning regression models, integrating real-time data from CPCB, OpenWeather, and IQAir APIs for 56 Indian cities.

## Features
- ✅ Multi-source data integration (CPCB, OpenWeather, IQAir)
- ✅ Four ML models (Linear Regression, Random Forest, XGBoost, LSTM)
- ✅ Ensemble model selection with performance tracking
- ✅ 1-48 hour forecasting capability
- ✅ Interactive web dashboard with real-time visualizations
- ✅ Real-time health alerts based on AQI levels
- ✅ PostgreSQL time-series storage with connection pooling
- ✅ RESTful API endpoints
- ✅ Docker containerization for easy deployment
- ✅ Automated scheduling for data collection and model retraining

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
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=aqi_db
DB_USER=postgres
DB_PASSWORD=postgres123

# API Keys
CPCB_API_KEY=your_cpcb_api_key
OPENWEATHER_API_KEY=your_openweather_api_key
IQAIR_API_KEY=your_iqair_api_key
```

2. **Initialize database:**
```bash
python database/reset_db.py
```

### Running the System

**Data Collection:**
```bash
python main.py
```

**Train Models (after collecting 24+ hours of data):**
```bash
python train_models.py
```

**Start Backend Server:**
```bash
python backend/app.py
```

**Access Frontend:**
Open http://localhost:5000 in your browser

**Automated Scheduler (optional):**
```bash
python scheduler.py
```

## Project Structure

```
AQI_Prediction_Regression_RealTime/
├── api_handlers/              # API integration modules
│   ├── cpcb_handler.py       # CPCB API integration
│   ├── openweather_handler.py # OpenWeather API
│   └── iqair_handler.py      # IQAir API
├── backend/                   # Flask backend
│   ├── app.py                # Flask application
│   └── routes.py             # API endpoints
├── config/                    # Configuration files
│   ├── settings.py           # App settings
│   └── logging_config.py     # Logging configuration
├── database/                  # Database operations
│   ├── db_config.py          # Database configuration
│   ├── db_operations.py      # CRUD operations
│   └── reset_db.py           # Database initialization
├── feature_engineering/       # Feature processing
│   └── feature_processor.py  # Feature engineering pipeline
├── frontend/                  # Web dashboard
│   ├── index.html            # Main dashboard
│   ├── styles.css            # Styling
│   └── script.js             # Frontend logic
├── ml_models/                 # ML model implementations
│   ├── linear_regression_model.py
│   ├── random_forest_model.py
│   ├── xgboost_model.py
│   └── lstm_model.py
├── models/                    # Trained models storage
│   ├── model_utils.py        # Model selection utilities
│   └── trained_models/       # Saved model files
├── tests/                     # Unit tests
│   ├── test_api_handlers.py
│   ├── test_database.py
│   ├── test_models.py
│   └── test_complete_pipeline.py
├── logs/                      # Application logs
├── data/                      # Data storage
│   ├── raw/                  # Raw collected data
│   └── processed/            # Processed features
├── main.py                    # Data collection pipeline
├── train_models.py            # Model training script
├── scheduler.py               # Task scheduling
├── Dockerfile                 # Docker configuration
├── docker-compose.yml         # Docker Compose configuration
├── requirements.txt           # Python dependencies
├── runtime.txt               # Python version for deployment
└── README.md                 # This file
```

## API Endpoints

### Base URL: `/api/v1`

| Endpoint | Method | Description | Parameters |
|----------|--------|-------------|------------|
| `/cities` | GET | Get list of supported cities | None |
| `/aqi/current/<city>` | GET | Current AQI data for city | city (path) |
| `/aqi/history/<city>` | GET | Historical AQI data | city (path), days (query, default=7) |
| `/forecast/<city>` | GET | AQI forecast data | city (path) |
| `/metrics/<city>` | GET | Model performance metrics | city (path), model (query, optional) |
| `/health` | GET | API health check | None |

### Example Requests

**Get current AQI for Delhi:**
```bash
curl http://localhost:5000/api/v1/aqi/current/Delhi
```

**Get 7-day history:**
```bash
curl http://localhost:5000/api/v1/aqi/history/Mumbai?days=7
```

**Get forecast:**
```bash
curl http://localhost:5000/api/v1/forecast/Bangalore
```

## Performance Targets

- **R² Score**: > 0.85
- **RMSE**: < 25 µg/m³
- **MAE**: < 15 µg/m³
- **Cities Covered**: 56 Indian cities
- **Forecast Horizon**: 1-48 hours
- **Data Collection Frequency**: Every 1 hour
- **Model Retraining**: Daily at 2:00 AM

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

## 56 Indian Cities Covered

Delhi, Mumbai, Bangalore, Chennai, Kolkata, Hyderabad, Pune, Ahmedabad, Jaipur, Lucknow, Kanpur, Nagpur, Indore, Bhopal, Visakhapatnam, Patna, Vadodara, Ludhiana, Agra, Nashik, Faridabad, Meerut, Rajkot, Varanasi, Srinagar, Amritsar, Allahabad, Ranchi, Howrah, Jabalpur, Gwalior, Vijayawada, Jodhpur, Madurai, Raipur, Kota, Chandigarh, Guwahati, Solapur, Hubli, Mysore, Tiruchirappalli, Bareilly, Aligarh, Moradabad, Jalandhar, Bhubaneswar, Salem, Warangal, Guntur, Bhiwandi, Saharanpur, Gorakhpur, Bikaner, Amravati, Noida

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

**Last Updated**: November 2025  
**Version**: 1.0.0  
**Status**: Production Ready ✅
