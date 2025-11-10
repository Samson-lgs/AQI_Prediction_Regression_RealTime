# AQI Prediction System (India)

Real-time air quality monitoring and 48-hour AQI forecasting across Indian cities using a unified ML approach, with a Flask API backend and a lightweight, modern web dashboard.

Last updated: November 10, 2025

## Overview

This project ingests air quality and weather data from multiple sources (CPCB, OpenWeather, IQAir) and serves:
- A REST API with Swagger docs, rate limiting, and caching-ready hooks
- A single-page web dashboard with map, rankings, trends, comparisons, alerts, and forecasts
- Unified ML predictions that blend multiple model outputs and apply realistic diurnal adjustments

Highlights in the current version:
- Batch-first endpoints to minimize calls and avoid rate limits
- Forecasts based on the median across models and diurnal patterns, with sensible floors/ceilings
- Frontend resilience: cache, retry/backoff on 429, batch-first with graceful fallback
- Production-ready run mode (debug and reloader disabled unless FLASK_DEBUG=1)

## Architecture

- Backend: Flask app (RESTX-style routes) serving JSON API and static frontend assets
- ML: Linear Regression, Random Forest, XGBoost; unified (city-agnostic) inference with median-of-models rule
- Storage: PostgreSQL (optional for historical/monitoring); local run works without DB
- Frontend: Static HTML + CSS + JS (Leaflet for map, Plotly for charts)
- Deployment: Render.com (recommended) and Docker Compose for local/dev

## Features

- Multi-source AQI and weather integration (CPCB, OpenWeather, IQAir)
- Batch endpoint for current AQI to reduce API pressure: `/api/v1/aqi/batch?cities=...`
- 48-hour forecast per city with bounded, realistic hourly trajectory
- Health recommendations and alert scaffolding (email endpoint stubs)
- Rate limiting (500/day, 100/hour) with key endpoints exempted
- Auto-generated API docs at `/api/v1/docs`

## Quick start (Windows PowerShell)

Prerequisites:
- Python 3.9+
- Optional: PostgreSQL 13+ (for historical storage and some scripts)

Setup:
```powershell
# 1) Clone
git clone https://github.com/Samson-lgs/AQI_Prediction_Regression_RealTime.git
cd AQI_Prediction_Regression_RealTime

# 2) Create & activate venv
python -m venv .venv
.venv\Scripts\activate

# 3) Install deps
pip install -r requirements.txt

# 4) (Optional) create .env and set keys (see Configuration)

# 5) Run backend (serves API + frontend)
$env:FLASK_DEBUG='0'
python backend/app.py
```

Open the dashboard at http://localhost:5000 and the API docs at http://localhost:5000/api/v1/docs

## Configuration

Create a `.env` in the project root (only variables you need):

```env
# API Keys (use whichever sources you enable)
CPCB_API_KEY=...
OPENWEATHER_API_KEY=...
IQAIR_API_KEY=...

# Flask
SECRET_KEY=change_this_in_production
FLASK_DEBUG=0

# Database (optional)
DATABASE_URL=postgresql://user:pass@host:5432/dbname
```

Notes:
- Rate limiting is in-memory by default. You can point `REDIS_URL` to enable distributed rate limits.
- Production deployments should set `FLASK_DEBUG=0` and a strong `SECRET_KEY`.

## Running (alternative options)

Docker Compose (dev/local):
```powershell
docker-compose up --build
# Access: http://localhost:5000
```

Gunicorn (production-style locally):
```powershell
.venv\Scripts\activate
gunicorn --bind 0.0.0.0:5000 --workers 1 wsgi:app
```

Render.com (recommended):
- The repo includes `render.yaml`, `render-build.sh`, `Procfile`, and `Dockerfile` for easy deploys
- Create a new Render web service from this repo, set environment variables, and deploy

## Frontend

- Served by the backend from `/`
- Entry file: `frontend/index_new.html`
- Assets: `frontend/unified-app.js`, `frontend/unified-styles.css`, `frontend/config.js`
- Environment auto-detection in `config.js`:
   - On localhost it uses `http://localhost:5000/api/v1`
   - On vercel.app/github.io it uses the Render API base

Resilience features:
- Batch-first has priority; falls back to all-cities or limited sequential fetches
- Shared cache for recent AQI reads (TTL ~2 minutes)
- Global cooldown after a 429 response to avoid hammering the backend

## Machine learning (prediction logic)

Current approach:
- Compute predictions from multiple models (Linear Regression, Random Forest, XGBoost)
- Use the median across models as the base forecast to dampen outliers
- Apply diurnal adjustment factors (rush hour bumps, afternoon dips)
- Clamp within 50–150% of the base to avoid unrealistic swings

Outputs:
- `GET /api/v1/forecast/<city>` returns the chosen model, current AQI, all model predictions, and a 24–48h hourly forecast with confidence values

## API

Base URLs:
- Local: `http://localhost:5000/api/v1`
- Production (example): `https://aqi-backend-api.onrender.com/api/v1`

Docs:
- Swagger UI: `/api/v1/docs`

Key endpoints:
- `GET /cities` — list supported cities
- `GET /cities/coordinates/<city>` — lat/lon for a city (if available)
- `GET /aqi/current/<city>` — current AQI and pollutants
- `GET /aqi/history/<city>?days=7` — historical AQI
- `GET /aqi/batch?cities=Delhi,Mumbai,...` — current AQI for many cities in one call
- `GET /forecast/<city>?hours=24` — hourly AQI forecast
- `GET /models/active_training` — shows active model name and training metrics snapshot
- `POST /alerts/create` — create alert (email), `POST /alerts/deactivate/<id>` — remove
- `GET /health` and `GET /api/v1/health` — health checks

Rate limiting:
- Default: 500 requests/day and 100/hour per IP (memory backend)
- Exempt: `/health`, `/api/v1/health`, `/api/v1/cities`, and heavy dashboard paths like `/aqi/current/*`, `/forecast/*`, `/cities/coordinates/*`

Examples (PowerShell):
```powershell
Invoke-RestMethod "http://localhost:5000/api/v1/cities"
Invoke-RestMethod "http://localhost:5000/api/v1/aqi/batch?cities=Delhi,Mumbai,Bengaluru"
Invoke-RestMethod "http://localhost:5000/api/v1/forecast/Delhi?hours=24"
```

## Project structure (current)

```
AQI_Prediction_Regression_RealTime/
├── backend/
│   ├── app.py                 # Flask app (serves API + frontend)
│   ├── api_routes.py          # API v1 routes incl. batch + forecast
│   ├── routes.py              # Basic legacy routes (fallback)
│   ├── scheduler.py           # Optional scheduled tasks
│   ├── email_utils.py         # Alert emails (stubs)
│   └── main.py                # Data collection entry (optional)
├── frontend/
│   ├── index_new.html         # Dashboard entry
│   ├── unified-app.js         # Frontend logic (batch-first, charts, map)
│   ├── unified-styles.css     # Styles
│   └── config.js              # API base auto-detection
├── api_handlers/              # Integrations (CPCB, OpenWeather, IQAir)
├── feature_engineering/       # Data cleaning & feature pipeline
├── ml_models/                 # Model wrappers
├── database/                  # DB config, migrations, utilities
├── monitoring/                # Metrics, feedback, drift (scaffolding)
├── tests/                     # Unit & integration tests
├── Dockerfile
├── docker-compose.yml
├── render.yaml, render-build.sh, Procfile
├── start_server.ps1           # Local Windows launcher
├── requirements.txt, runtime.txt
└── README.md
```

## Testing

Run tests:
```powershell
.venv\Scripts\activate
pytest -q
```

Focus files include `tests/test_api_endpoints.py`, `tests/test_frontend_api.py`, `tests/test_predictions.py`, and more.

## Troubleshooting

- Can’t connect to http://localhost:5000?
   - Ensure the process is running and not restarted by the auto-reloader. Set `$env:FLASK_DEBUG='0'` when running `python backend/app.py`.
   - Check port conflicts: `Test-NetConnection -ComputerName localhost -Port 5000` should show `TcpTestSucceeded: True`.
- Seeing HTTP 429?
   - The frontend will back off automatically. Prefer batch endpoints.
   - If testing manually, space requests or momentarily increase limits in `backend/app.py`.
- Forecast looks unrealistic?
   - The current logic uses median-of-models with diurnal bounds. If you changed models, verify `ml_models/` and the forecast code in `backend/api_routes.py`.

## License

MIT License. See `LICENSE`.

## Credits

Contributors: Drushya M, Kavana P, Samson Jose J, Yashwanth J

Affiliation: ATME College of Engineering (CSE), 2024–2025

## Roadmap

- Extended alerts (SMS/Push), richer health guidance
- Active drift detection and automatic retraining hooks
- Periodic LightGBM/CatBoost comparisons
- Model hot-reload without downtime

---

If you deploy on Render and want me to verify production endpoints (batch + forecast) now, I can do that next.
