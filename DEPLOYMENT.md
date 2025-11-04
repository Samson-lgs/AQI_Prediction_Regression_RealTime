# Deployment Guide

## Local Deployment with Docker

1. Build and run containers:
   ```bash
   docker-compose up --build
   ```

2. Initialize database:
   ```bash
   docker exec aqi-prediction-system-web-1 python database/reset_db.py
   ```

3. Access application:
   - Frontend: http://localhost:5000
   - API: http://localhost:5000/api/v1
   - Health Check: http://localhost:5000/api/v1/health

## Render Deployment (Free Alternative to Heroku)

1. Push to GitHub:
   ```bash
   git push origin main
   ```

2. Connect repository to Render:
   - Go to https://render.com
   - Sign up/Login with GitHub
   - Click "New +" → "Web Service"
   - Connect your repository

3. Set environment variables in Render dashboard:
   - `CPCB_API_KEY`
   - `OPENWEATHER_API_KEY`
   - `IQAIR_API_KEY`
   - `DB_HOST`
   - `DB_PORT`
   - `DB_NAME`
   - `DB_USER`
   - `DB_PASSWORD`

4. Deploy:
   - Render will automatically build and deploy
   - Access your app at: `https://your-app-name.onrender.com`

## Container Management

1. Stop containers:
   ```bash
   docker-compose down
   ```

2. View logs:
   ```bash
   docker-compose logs -f web
   ```

## Local Development Setup

1. Create virtual environment:
   ```bash
   python -m venv aqi_env
   ```

2. Activate virtual environment:
   - Windows: `aqi_env\Scripts\activate`
   - Linux/Mac: `source aqi_env/bin/activate`

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   Create a `.env` file in the root directory:
   ```env
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=aqi_db
   DB_USER=postgres
   DB_PASSWORD=postgres123
   
   CPCB_API_KEY=your_cpcb_api_key
   IQAIR_API_KEY=your_iqair_api_key
   OPENWEATHER_API_KEY=your_openweather_api_key
   ```

5. Initialize database:
   ```bash
   python database/reset_db.py
   ```

6. Start data collection:
   ```bash
   python main.py
   ```

7. Run backend server (in separate terminal):
   ```bash
   python backend/app.py
   ```

## Production Deployment

### Prerequisites
- Docker and Docker Compose installed
- PostgreSQL database (managed or self-hosted)
- API keys for data sources

### Deployment Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/Samson-lgs/AQI_Prediction_Regression_RealTime.git
   cd AQI_Prediction_Regression_RealTime
   ```

2. Configure environment variables:
   - Update `docker-compose.yml` with production credentials
   - Set secure passwords for database
   - Add API keys for external services

3. Build Docker image:
   ```bash
   docker-compose build
   ```

4. Run containers:
   ```bash
   docker-compose up -d
   ```

5. Initialize database schema:
   ```bash
   docker-compose exec web python database/reset_db.py
   ```

6. Start data collection:
   ```bash
   docker-compose exec web python main.py &
   ```

7. Verify deployment:
   - Check health endpoint: `curl http://localhost:5000/api/v1/health`
   - View logs: `docker-compose logs -f`

## Cloud Deployment (AWS/GCP/Azure)

### AWS EC2 Deployment

1. Launch EC2 instance (Ubuntu 20.04 or later)
2. Install Docker and Docker Compose
3. Clone repository and configure environment
4. Set up security groups:
   - Allow inbound: 5000 (HTTP), 22 (SSH)
   - PostgreSQL: 5432 (internal only)
5. Run with docker-compose
6. Configure nginx reverse proxy (optional)
7. Set up SSL with Let's Encrypt (recommended)

### Using AWS RDS for Database

1. Create RDS PostgreSQL instance
2. Update `docker-compose.yml`:
   ```yaml
   environment:
     DB_HOST: your-rds-endpoint.amazonaws.com
     DB_PORT: 5432
     DB_NAME: aqi_db
     DB_USER: your_username
     DB_PASSWORD: your_password
   ```
3. Remove postgres service from docker-compose.yml

## Scheduled Tasks

### Automated Data Collection

The application uses Python's `schedule` library for periodic data collection:

- **Data Collection**: Every 1 hour
- **Model Training**: Manual (requires sufficient historical data)

To run as a background service:

1. Using Docker:
   ```bash
   docker-compose up -d
   ```

2. Using systemd (Linux):
   Create `/etc/systemd/system/aqi-collector.service`:
   ```ini
   [Unit]
   Description=AQI Data Collection Service
   After=network.target

   [Service]
   Type=simple
   User=ubuntu
   WorkingDirectory=/path/to/AQI_Prediction_Regression_RealTime
   ExecStart=/path/to/aqi_env/bin/python main.py
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

   Enable and start:
   ```bash
   sudo systemctl enable aqi-collector
   sudo systemctl start aqi-collector
   ```

3. Using Windows Task Scheduler:
   - Create new task
   - Trigger: Daily, repeat every 1 hour
   - Action: Start program `python.exe main.py`

## Model Training

Train models after collecting 24+ hours of data:

```bash
python train_models.py
```

For automated retraining, set up a cron job or scheduled task:
```bash
# Daily at 2 AM
0 2 * * * cd /path/to/project && /path/to/aqi_env/bin/python train_models.py
```

## Monitoring and Maintenance

### Health Checks
- API Health: `GET /api/v1/health`
- Database Connection: Check logs for connection errors
- Data Collection: Monitor logs for API failures

### Logs
- Application logs: `logs/` directory
- Docker logs: `docker-compose logs`
- Database logs: Check PostgreSQL logs

### Backup Database
```bash
docker-compose exec postgres pg_dump -U postgres aqi_db > backup_$(date +%Y%m%d).sql
```

### Restore Database
```bash
cat backup_20250104.sql | docker-compose exec -T postgres psql -U postgres aqi_db
```

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check PostgreSQL is running
   - Verify credentials in `.env`
   - Check network connectivity

2. **API Returns No Data**
   - Ensure data collection is running
   - Check API keys are valid
   - Verify database has data: `SELECT COUNT(*) FROM pollution_data;`

3. **Model Not Found**
   - Run `train_models.py` first
   - Check `models/trained_models/` directory exists

4. **Port Already in Use**
   - Change port in docker-compose.yml
   - Kill process using port: `lsof -ti:5000 | xargs kill`

## Security Best Practices

1. **Never commit sensitive data**
   - Use `.env` files for secrets
   - Add `.env` to `.gitignore`

2. **Use strong passwords**
   - Generate random passwords for production
   - Rotate credentials regularly

3. **Enable HTTPS**
   - Use Let's Encrypt for free SSL
   - Configure nginx with SSL termination

4. **Firewall Configuration**
   - Allow only necessary ports
   - Use VPC/security groups for cloud deployments

5. **API Rate Limiting**
   - Implement rate limiting in Flask
   - Monitor API usage

## Performance Optimization

1. **Database Indexing**
   - Indexes on `city`, `timestamp` columns
   - Regular VACUUM and ANALYZE

2. **Caching**
   - Cache API responses (Redis)
   - Cache model predictions

3. **Load Balancing**
   - Use nginx for load balancing
   - Scale horizontally with multiple containers

4. **Model Optimization**
   - Use model quantization
   - Implement model caching

## Support

For issues and questions:
- GitHub Issues: https://github.com/Samson-lgs/AQI_Prediction_Regression_RealTime/issues
- Documentation: README.md
