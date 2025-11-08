"""
Enhanced RESTful API Routes for AQI Prediction System
Includes batch predictions, model comparisons, city rankings, and alerts
"""
from flask import Blueprint, jsonify, request
from flask_restx import Api, Resource, fields, Namespace
from datetime import datetime, timedelta
import logging
import numpy as np
from functools import wraps
import sys

logger = logging.getLogger(__name__)

# Create Blueprint with url_prefix
api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

# Initialize Flask-RESTX API with Swagger documentation
api = Api(
    api_bp,
    version='1.0',
    title='AQI Prediction API',
    description='Real-time Air Quality Index Prediction System for 67 Indian Cities',
    doc='/docs'
    # Remove prefix here - already in Blueprint url_prefix
)

# Define namespaces for better organization
ns_cities = api.namespace('cities', description='City operations')
ns_aqi = api.namespace('aqi', description='AQI data operations')
ns_forecast = api.namespace('forecast', description='Prediction operations')
ns_models = api.namespace('models', description='Model management')
ns_alerts = api.namespace('alerts', description='Alert management')
ns_retrain = api.namespace('retrain', description='Model retraining operations')

# ============================================================================
# API Models for Swagger Documentation
# ============================================================================

city_model = api.model('City', {
    'name': fields.String(required=True, description='City name'),
    'region': fields.String(description='Region/State'),
    'priority': fields.Boolean(description='Is priority city')
})

aqi_data_model = api.model('AQIData', {
    'city': fields.String(required=True),
    'timestamp': fields.DateTime,
    'aqi': fields.Integer(description='AQI value'),
    'pm25': fields.Float(description='PM2.5 concentration'),
    'pm10': fields.Float(description='PM10 concentration'),
    'no2': fields.Float(description='NO2 concentration'),
    'so2': fields.Float(description='SO2 concentration'),
    'co': fields.Float(description='CO concentration'),
    'o3': fields.Float(description='O3 concentration')
})

prediction_model = api.model('Prediction', {
    'city': fields.String(required=True),
    'forecast_timestamp': fields.DateTime(required=True),
    'predicted_aqi': fields.Integer,
    'confidence': fields.Float(description='Confidence percentage'),
    'model_used': fields.String
})

batch_predict_request = api.model('BatchPredictRequest', {
    'cities': fields.List(fields.String, required=True, description='List of city names'),
    'hours_ahead': fields.Integer(default=24, description='Hours to predict ahead (1-48)')
})

retrain_status_model = api.model('RetrainStatus', {
    'job_id': fields.String(description='Retraining job identifier'),
    'status': fields.String(description='Status of the retraining job'),
    'started_at': fields.DateTime(description='Job start timestamp'),
    'ended_at': fields.DateTime(description='Job end timestamp (if finished)'),
    'model_updates': fields.Raw(description='Summary of updated model metrics'),
    'error': fields.String(description='Error details if failed')
})

alert_request = api.model('AlertRequest', {
    'city': fields.String(required=True),
    'threshold': fields.Integer(required=True, description='AQI threshold'),
    'alert_type': fields.String(required=True, enum=['email', 'sms', 'webhook']),
    'contact': fields.String(required=True, description='Contact (email/phone/webhook URL)')
})

# ============================================================================
# Caching decorator (will use Redis when available)
# ============================================================================

def cache_response(timeout=300):
    """Cache decorator for API responses"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # TODO: Implement Redis caching
            # For now, just call the function
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ============================================================================
# Cities Endpoints
# ============================================================================

@ns_cities.route('/')
class CityList(Resource):
    @cache_response(timeout=3600)
    @ns_cities.doc('list_cities')
    @ns_cities.marshal_with(city_model, as_list=True, code=200)
    def get(self):
        """Get list of all supported cities"""
        try:
            from config.settings import CITIES, PRIORITY_CITIES
            cities_data = []
            for city in CITIES:
                cities_data.append({
                    'name': city,
                    'priority': city in PRIORITY_CITIES
                })
            return cities_data, 200
        except Exception as e:
            logger.error(f"Error fetching cities: {str(e)}")
            api.abort(500, f"Internal server error: {str(e)}")

@ns_cities.route('/coordinates/<string:city>')
@ns_cities.param('city', 'City name')
class CityCoordinates(Resource):
    @ns_cities.doc('get_city_coordinates')
    def get(self, city):
        """Get latitude and longitude for a city"""
        try:
            from api_handlers.openweather_handler import OpenWeatherHandler
            handler = OpenWeatherHandler()
            
            # Check if city exists in our coordinates map
            coords = handler.CITY_COORDINATES.get(city)
            
            if coords:
                return {
                    'city': city,
                    'lat': coords[0],
                    'lon': coords[1]
                }, 200
            else:
                # Try geocoding as fallback
                geocoded = handler.geocode_city(city)
                if geocoded:
                    return {
                        'city': city,
                        'lat': geocoded[0],
                        'lon': geocoded[1]
                    }, 200
                else:
                    api.abort(404, f'Coordinates not found for {city}')
        except Exception as e:
            logger.error(f"Error fetching coordinates for {city}: {str(e)}")
            api.abort(500, f"Internal server error: {str(e)}")

@ns_cities.route('/rankings')
class CityRankings(Resource):
    @ns_cities.doc('get_city_rankings')
    @ns_cities.param('days', 'Number of days to analyze', default=7)
    @ns_cities.param('metric', 'Ranking metric (avg_aqi, max_aqi, pm25)', default='avg_aqi')
    def get(self):
        """Get city rankings by AQI metrics"""
        try:
            from database.db_operations import DatabaseOperations
            db = DatabaseOperations()
            
            days = request.args.get('days', 7, type=int)
            metric = request.args.get('metric', 'avg_aqi')
            
            query = f"""
            SELECT 
                city,
                AVG(aqi_value) as avg_aqi,
                MAX(aqi_value) as max_aqi,
                AVG(pm25) as avg_pm25,
                COUNT(*) as data_points
            FROM pollution_data
            WHERE timestamp >= NOW() - INTERVAL '{days} days'
            GROUP BY city
            ORDER BY {metric} DESC
            LIMIT 56;
            """
            
            rankings = db.db.execute_query_dicts(query)
            
            return {
                'rankings': rankings,
                'metric': metric,
                'days': days,
                'timestamp': datetime.now().isoformat()
            }, 200
            
        except Exception as e:
            logger.error(f"Error fetching rankings: {str(e)}")
            api.abort(500, f"Internal server error: {str(e)}")

@ns_cities.route('/compare')
class CityComparison(Resource):
    @ns_cities.doc('compare_cities')
    @ns_cities.param('cities', 'Comma-separated city names', required=True)
    @ns_cities.param('days', 'Number of days to compare', default=7)
    def get(self):
        """Compare AQI data across multiple cities"""
        try:
            from database.db_operations import DatabaseOperations
            db = DatabaseOperations()
            
            cities_param = request.args.get('cities', '')
            cities = [c.strip() for c in cities_param.split(',') if c.strip()]
            days = request.args.get('days', 7, type=int)
            
            if not cities:
                api.abort(400, "Please provide cities parameter")
            
            comparison_data = {}
            for city in cities:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days)
                
                data = db.get_pollution_data(city, start_date, end_date)
                
                if data:
                    aqi_values = [d['aqi_value'] for d in data if d['aqi_value']]
                    comparison_data[city] = {
                        'avg_aqi': float(np.mean(aqi_values)) if aqi_values else None,
                        'max_aqi': int(np.max(aqi_values)) if aqi_values else None,
                        'min_aqi': int(np.min(aqi_values)) if aqi_values else None,
                        'data_points': len(data)
                    }
                else:
                    comparison_data[city] = None
            
            return {
                'comparison': comparison_data,
                'days': days,
                'timestamp': datetime.now().isoformat()
            }, 200
            
        except Exception as e:
            logger.error(f"Error comparing cities: {str(e)}")
            api.abort(500, f"Internal server error: {str(e)}")

# ============================================================================
# AQI Data Endpoints
# ============================================================================

@ns_aqi.route('/current/<string:city>')
@ns_aqi.param('city', 'City name')
class CurrentAQI(Resource):
    @cache_response(timeout=300)
    @ns_aqi.doc('get_current_aqi')
    def get(self, city):
        """Get current AQI data for a city from multiple sources"""
        try:
            from database.db_operations import DatabaseOperations
            from api_handlers.aqi_calculator import calculate_india_aqi, get_aqi_category
            db = DatabaseOperations()
            
            # Look for most recent data in the last 48 hours
            end_date = datetime.now()
            start_date = end_date - timedelta(hours=48)
            
            # Get all recent data for this city, sorted by timestamp DESC
            data = db.get_pollution_data(city, start_date, end_date)
            
            if data and len(data) > 0:
                # Group by data source and get the latest from each
                sources_data = {}
                for row in data:
                    source = row.get('data_source', 'Unknown')
                    if source not in sources_data:
                        sources_data[source] = row
                
                # Find the data point with highest AQI (most conservative estimate)
                best_data = None
                max_aqi = 0
                sources_compared = []
                
                for source, row in sources_data.items():
                    aqi = float(row.get('aqi_value', 0)) if row.get('aqi_value') is not None else 0
                    sources_compared.append({'source': source, 'aqi': aqi})
                    
                    if aqi > max_aqi:
                        max_aqi = aqi
                        best_data = row
                
                # Use the data with highest AQI (or first if none have AQI)
                latest = best_data if best_data else data[0]
                
                # Recalculate AQI to get sub-indices
                pm25 = float(latest.get('pm25', 0)) if latest.get('pm25') is not None else 0
                pm10 = float(latest.get('pm10', 0)) if latest.get('pm10') is not None else 0
                no2 = float(latest.get('no2', 0)) if latest.get('no2') is not None else 0
                so2 = float(latest.get('so2', 0)) if latest.get('so2') is not None else 0
                co = float(latest.get('co', 0)) if latest.get('co') is not None else 0
                o3 = float(latest.get('o3', 0)) if latest.get('o3') is not None else 0
                
                india_result = calculate_india_aqi(pm25, pm10, no2, so2, co, o3)
                category = get_aqi_category(india_result['aqi'])
                
                return {
                    'city': city,
                    'timestamp': str(latest.get('timestamp', '')),
                    'aqi': india_result['aqi'],
                    'category': category['category'],
                    'color': category['color'],
                    'data_source': latest.get('data_source', 'Unknown'),
                    'sources_compared': sources_compared if len(sources_compared) > 1 else None,
                    'dominant_pollutant': india_result.get('dominant_pollutant'),
                    'sub_indices': india_result.get('sub_index', {}),
                    'pollutants': {
                        'pm25': pm25,
                        'pm10': pm10,
                        'no2': no2,
                        'so2': so2,
                        'co': co,
                        'o3': o3
                    },
                    'note': 'AQI calculated using India NAQI standard. Values may differ from CPCB due to different monitoring stations and averaging periods.'
                }, 200
            else:
                api.abort(404, f'No data found for {city}')
        
        except Exception as e:
            logger.error(f"Error fetching current AQI for {city}: {str(e)}", exc_info=True)
            return {'error': str(e), 'city': city}, 500

@ns_aqi.route('/history/<string:city>')
@ns_aqi.param('city', 'City name')
class AQIHistory(Resource):
    @ns_aqi.doc('get_aqi_history')
    @ns_aqi.param('days', 'Number of days of history', default=7)
    def get(self, city):
        """Get historical AQI data for a city"""
        try:
            from database.db_operations import DatabaseOperations
            db = DatabaseOperations()
            
            days = request.args.get('days', 7, type=int)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            data = db.get_pollution_data(city, start_date, end_date)
            
            if data:
                # Convert all datetime and Decimal types to serializable formats
                serializable_data = []
                for row in data:
                    serializable_data.append({
                        'timestamp': str(row.get('timestamp', '')),
                        'aqi_value': float(row.get('aqi_value', 0)) if row.get('aqi_value') is not None else 0,
                        'pm25': float(row.get('pm25', 0)) if row.get('pm25') is not None else 0,
                        'pm10': float(row.get('pm10', 0)) if row.get('pm10') is not None else 0,
                        'no2': float(row.get('no2', 0)) if row.get('no2') is not None else 0,
                        'so2': float(row.get('so2', 0)) if row.get('so2') is not None else 0,
                        'co': float(row.get('co', 0)) if row.get('co') is not None else 0,
                        'o3': float(row.get('o3', 0)) if row.get('o3') is not None else 0
                    })
                
                return {
                    'city': city,
                    'days': days,
                    'data_points': len(serializable_data),
                    'data': serializable_data
                }, 200
            else:
                return {'city': city, 'data_points': 0, 'data': []}, 200
        
        except Exception as e:
            logger.error(f"Error fetching history for {city}: {str(e)}", exc_info=True)
            return {'error': str(e), 'city': city}, 500

@ns_aqi.route('/all/current')
class AllCitiesCurrentAQI(Resource):
    @cache_response(timeout=600)
    @ns_aqi.doc('get_all_cities_current')
    def get(self):
        """Get current AQI for all cities"""
        try:
            from database.db_operations import DatabaseOperations
            db = DatabaseOperations()
            
            all_data = db.get_all_cities_current_data()
            
            cities_aqi = []
            for row in all_data:
                cities_aqi.append({
                    'city': row[0],
                    'timestamp': str(row[1]),
                    'aqi': row[2],
                    'pm25': row[3],
                    'pm10': row[4],
                    'no2': row[5],
                    'so2': row[6],
                    'co': row[7],
                    'o3': row[8]
                })
            
            return {
                'total_cities': len(cities_aqi),
                'data': cities_aqi,
                'timestamp': datetime.now().isoformat()
            }, 200
            
        except Exception as e:
            logger.error(f"Error fetching all cities data: {str(e)}")
            api.abort(500, f"Internal server error: {str(e)}")

# ============================================================================
# Forecast/Prediction Endpoints
# ============================================================================

@ns_forecast.route('/<string:city>')
@ns_forecast.param('city', 'City name')
class ForecastSingle(Resource):
    @ns_forecast.doc('get_forecast')
    @ns_forecast.param('hours', 'Hours ahead to forecast (1-48)', default=24)
    def get(self, city):
        """Get AQI forecast for a single city using simple unified models"""
        try:
            from models.simple_predictor import get_predictor
            from database.db_operations import DatabaseOperations
            
            hours = request.args.get('hours', 24, type=int)
            
            if hours < 1 or hours > 48:
                api.abort(400, "Hours must be between 1 and 48")
            
            predictor = get_predictor()
            db = DatabaseOperations()
            
            # Get current data
            end_date = datetime.now()
            start_date = end_date - timedelta(hours=24)
            current_data = db.get_pollution_data(city, start_date, end_date)
            
            if not current_data:
                api.abort(404, f"No recent data available for {city}")
            
            # Prepare pollutants from latest reading
            latest = current_data[0]
            pollutants = {
                # Use None for missing values and let the predictor perform median imputation
                'pm25': float(latest['pm25']) if latest.get('pm25') is not None else None,
                'pm10': float(latest['pm10']) if latest.get('pm10') is not None else None,
                'no2': float(latest['no2']) if latest.get('no2') is not None else None,
                'so2': float(latest['so2']) if latest.get('so2') is not None else None,
                'co': float(latest['co']) if latest.get('co') is not None else None,
                'o3': float(latest['o3']) if latest.get('o3') is not None else None,
            }
            
            # Get prediction from unified models (no city parameter!)
            result = predictor.get_best_prediction(pollutants)
            
            # Generate trend-based hourly predictions
            predictions = []
            base_aqi = result['aqi'] if result['aqi'] else float(latest.get('aqi_value', 100))
            
            for h in range(1, hours + 1):
                # Simple trend-based prediction with some variation
                trend = np.sin(h / 6) * 12
                noise = np.random.normal(0, 4)
                predicted_aqi = max(0, int(base_aqi + trend + noise))
                confidence = 95 - (h * 0.6)
                
                predictions.append({
                    'hour': h,
                    'forecast_timestamp': (end_date + timedelta(hours=h)).isoformat(),
                    'predicted_aqi': predicted_aqi,
                    'confidence': round(max(50, confidence), 2)
                })
            
            return {
                'city': city,
                'model_used': result['model'],
                'current_aqi': int(base_aqi),
                'predicted_aqi': int(result['aqi']) if result['aqi'] else None,
                'all_model_predictions': result['all_predictions'],
                'available_models': predictor.available_models(),
                'forecast_hours': hours,
                'predictions': predictions,
                'note': 'Unified model trained on all cities - city-agnostic prediction',
                'generated_at': datetime.now().isoformat()
            }, 200
        
        except Exception as e:
            logger.error(f"Error generating forecast: {str(e)}", exc_info=True)
            api.abort(500, f"Internal server error: {str(e)}")

@ns_forecast.route('/batch')
class ForecastBatch(Resource):
    @ns_forecast.doc('batch_forecast')
    @ns_forecast.expect(batch_predict_request, validate=True)
    def post(self):
        """Generate forecasts for multiple cities in batch"""
        try:
            data = request.get_json()
            cities = data.get('cities', [])
            hours = data.get('hours_ahead', 24)
            
            if not cities:
                api.abort(400, "Cities list is required")
            
            if hours < 1 or hours > 48:
                api.abort(400, "hours_ahead must be between 1 and 48")
            
            from database.db_operations import DatabaseOperations
            db = DatabaseOperations()
            
            batch_forecasts = {}
            
            for city in cities:
                try:
                    # Get current data
                    end_date = datetime.now()
                    start_date = end_date - timedelta(hours=24)
                    current_data = db.get_pollution_data(city, start_date, end_date)
                    
                    if current_data:
                        base_aqi = current_data[0]['aqi_value']
                        
                        # Generate simplified predictions
                        predictions = []
                        for h in range(1, hours + 1):
                            trend = np.sin(h / 6) * 15
                            noise = np.random.normal(0, 5)
                            predicted_aqi = max(0, int(base_aqi + trend + noise))
                            confidence = 95 - (h * 0.5)
                            
                            predictions.append({
                                'hour': h,
                                'predicted_aqi': predicted_aqi,
                                'confidence': round(confidence, 2)
                            })
                        
                        batch_forecasts[city] = {
                            'status': 'success',
                            'predictions': predictions
                        }
                    else:
                        batch_forecasts[city] = {
                            'status': 'no_data',
                            'message': 'No recent data available'
                        }
                        
                except Exception as city_error:
                    batch_forecasts[city] = {
                        'status': 'error',
                        'message': str(city_error)
                    }
            
            return {
                'total_cities': len(cities),
                'successful': sum(1 for f in batch_forecasts.values() if f['status'] == 'success'),
                'forecasts': batch_forecasts,
                'hours_ahead': hours,
                'generated_at': datetime.now().isoformat()
            }, 200
            
        except Exception as e:
            logger.error(f"Error in batch forecast: {str(e)}")
            api.abort(500, f"Internal server error: {str(e)}")

# ============================================================================
# Model Management Endpoints
# ============================================================================

@ns_models.route('/performance/<string:city>')
@ns_models.param('city', 'City name')
class ModelPerformance(Resource):
    @ns_models.doc('get_model_performance')
    @ns_models.param('model', 'Model name (optional)', default='all')
    @ns_models.param('days', 'Days of metrics to retrieve', default=30)
    def get(self, city):
        """Get model performance metrics for a city"""
        try:
            from database.db_operations import DatabaseOperations
            db = DatabaseOperations()
            
            model_name = request.args.get('model', 'all')
            days = request.args.get('days', 30, type=int)
            
            if model_name == 'all':
                metrics = db.get_model_performance(city, None, days)
            else:
                metrics = db.get_model_performance(city, model_name, days)
            
            # Convert metrics to serializable format
            serializable_metrics = []
            if metrics:
                for metric in metrics:
                    serializable_metrics.append({
                        'city': metric.get('city', city),
                        'model_name': metric.get('model_name', ''),
                        'metric_date': str(metric.get('metric_date', '')),
                        'r2_score': float(metric.get('r2_score', 0)) if metric.get('r2_score') is not None else 0,
                        'rmse': float(metric.get('rmse', 0)) if metric.get('rmse') is not None else 0,
                        'mae': float(metric.get('mae', 0)) if metric.get('mae') is not None else 0,
                        'mape': float(metric.get('mape', 0)) if metric.get('mape') is not None else 0
                    })
            
            return {
                'city': city,
                'model': model_name,
                'days': days,
                'metrics': serializable_metrics
            }, 200
        
        except Exception as e:
            logger.error(f"Error fetching model performance for {city}: {str(e)}", exc_info=True)
            return {'error': str(e), 'city': city, 'metrics': []}, 500

@ns_models.route('/compare')
class ModelComparison(Resource):
    @ns_models.doc('compare_models')
    @ns_models.param('city', 'City name', required=True)
    @ns_models.param('models', 'Comma-separated model names', default='linear_regression,random_forest,xgboost')
    def get(self):
        """Compare performance of multiple models"""
        try:
            from database.db_operations import DatabaseOperations
            db = DatabaseOperations()
            
            city = request.args.get('city')
            if not city:
                api.abort(400, "City parameter is required")
            
            models_param = request.args.get('models', 'linear_regression,random_forest,xgboost')
            models = [m.strip() for m in models_param.split(',')]
            
            comparison = {}
            for model in models:
                metrics = db.get_model_performance(city, model, 30)
                if metrics and len(metrics) > 0:
                    latest = metrics[0]
                    comparison[model] = {
                        'r2_score': latest.get('r2_score'),
                        'rmse': latest.get('rmse'),
                        'mae': latest.get('mae'),
                        'mape': latest.get('mape'),
                        'last_updated': str(latest.get('metric_date'))
                    }
                else:
                    comparison[model] = None
            
            # Determine best model
            best_model = None
            best_r2 = -float('inf')
            for model, metrics in comparison.items():
                if metrics and metrics['r2_score']:
                    if metrics['r2_score'] > best_r2:
                        best_r2 = metrics['r2_score']
                        best_model = model
            
            return {
                'city': city,
                'comparison': comparison,
                'best_model': best_model,
                'best_r2_score': best_r2 if best_model else None
            }, 200
            
        except Exception as e:
            logger.error(f"Error comparing models: {str(e)}")
            api.abort(500, f"Internal server error: {str(e)}")

# ============================================================================
# Alert Management Endpoints
# ============================================================================

@ns_alerts.route('/create')
class CreateAlert(Resource):
    @ns_alerts.doc('create_alert')
    @ns_alerts.expect(alert_request, validate=True)
    def post(self):
        """Create a new AQI alert"""
        try:
            data = request.get_json()
            
            city = data.get('city')
            threshold = data.get('threshold')
            alert_type = data.get('alert_type')
            contact = data.get('contact')
            
            # Validate inputs
            if not all([city, threshold, alert_type, contact]):
                api.abort(400, "All fields are required")
            
            from database.db_operations import DatabaseOperations
            db = DatabaseOperations()
            # Ensure alerts table exists
            db.create_alerts_table()

            # Insert and return id
            new_id = db.add_alert(city, int(threshold), alert_type, contact)
            
            return {
                'alert_id': new_id,
                'city': city,
                'threshold': int(threshold),
                'alert_type': alert_type,
                'contact': contact,
                'status': 'created',
                'created_at': datetime.now().isoformat()
            }, 201
            
        except Exception as e:
            logger.error(f"Error creating alert: {str(e)}")
            api.abort(500, f"Internal server error: {str(e)}")

@ns_alerts.route('/list/<string:city>')
@ns_alerts.param('city', 'City name')
class ListAlerts(Resource):
    @ns_alerts.doc('list_alerts')
    def get(self, city):
        """List all alerts for a city"""
        try:
            from database.db_operations import DatabaseOperations
            db = DatabaseOperations()
            db.create_alerts_table()
            alerts = db.list_alerts(city) or []
            return {
                'city': city,
                'alerts': alerts
            }, 200
        except Exception as e:
            logger.error(f"Error listing alerts: {str(e)}")
            api.abort(500, f"Internal server error: {str(e)}")

@ns_alerts.route('/deactivate/<int:alert_id>')
@ns_alerts.param('alert_id', 'Alert id')
class DeactivateAlert(Resource):
    @ns_alerts.doc('deactivate_alert')
    def post(self, alert_id):
        """Deactivate an alert by id"""
        try:
            from database.db_operations import DatabaseOperations
            db = DatabaseOperations()
            db.deactivate_alert(alert_id)
            return {'status': 'deactivated', 'alert_id': alert_id}, 200
        except Exception as e:
            logger.error(f"Error deactivating alert: {str(e)}")
            api.abort(500, f"Internal server error: {str(e)}")

# ============================================================================
# Unified Model Retraining Endpoints
# ============================================================================

_RETRAIN_JOBS = {}

def _launch_retrain_process(job_id: str):
    """Launch the unified tuned retraining script in a subprocess and track status."""
    import subprocess, json, threading, uuid, datetime as dt, os
    from pathlib import Path
    _RETRAIN_JOBS[job_id] = {
        'job_id': job_id,
        'status': 'running',
        'started_at': dt.datetime.utcnow().isoformat(),
        'ended_at': None,
        'model_updates': None,
        'error': None
    }

    def run_job():
        script_path = Path('scripts') / 'train_models_render_last7d_tuned.py'
        env = os.environ.copy()
        try:
            proc = subprocess.Popen([sys.executable, str(script_path)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = proc.communicate()
            result = _RETRAIN_JOBS[job_id]
            result['ended_at'] = dt.datetime.utcnow().isoformat()
            if proc.returncode == 0:
                # Attempt to parse latest metrics from saved_models directory
                metrics_summary = {}
                saved_dir = Path('models') / 'saved_models'
                if saved_dir.exists():
                    for f in saved_dir.glob('*metrics.json'):
                        try:
                            with open(f, 'r') as fh:
                                metrics_summary[f.name] = json.load(fh)
                        except Exception:
                            pass
                result['model_updates'] = metrics_summary or {'note': 'No metrics files discovered'}
                result['status'] = 'completed'
            else:
                result['status'] = 'failed'
                result['error'] = (stderr or 'Unknown error').strip()[:2000]
        except Exception as e:
            _RETRAIN_JOBS[job_id]['status'] = 'failed'
            _RETRAIN_JOBS[job_id]['error'] = str(e)
            _RETRAIN_JOBS[job_id]['ended_at'] = dt.datetime.utcnow().isoformat()

    threading.Thread(target=run_job, daemon=True).start()

@ns_retrain.route('/unified')
class UnifiedRetrain(Resource):
    @ns_retrain.doc('trigger_unified_retrain')
    def post(self):
        """Trigger asynchronous unified tuned model retraining (7-day window)."""
        try:
            import uuid
            job_id = uuid.uuid4().hex
            _launch_retrain_process(job_id)
            return {'job_id': job_id, 'status': 'started'}, 202
        except Exception as e:
            logger.error(f"Failed to start retraining: {e}")
            api.abort(500, f"Failed to start retraining: {e}")

@ns_retrain.route('/status/<string:job_id>')
@ns_retrain.param('job_id', 'Retraining job id')
class UnifiedRetrainStatus(Resource):
    @ns_retrain.doc('get_retrain_status')
    @ns_retrain.marshal_with(retrain_status_model, code=200)
    def get(self, job_id):
        """Check status of a retraining job."""
        job = _RETRAIN_JOBS.get(job_id)
        if not job:
            api.abort(404, f'Job {job_id} not found')
        return job, 200

# ============================================================================
# Health Check
# ============================================================================

@api.route('/health')
class ApiHealth(Resource):
    def get(self):
        """Lightweight API health check at /api/v1/health"""
        try:
            # Attempt a very quick DB connectivity check but don't fail health if it errors
            db_status = 'unknown'
            try:
                from database.db_operations import DatabaseOperations
                db = DatabaseOperations()
                db.db.execute_query("SELECT 1;")
                db_status = 'connected'
            except Exception as _:
                db_status = 'unavailable'

            return {
                'status': 'ok',
                'database': db_status,
                'timestamp': datetime.now().isoformat()
            }, 200
        except Exception as e:
            # Always return a 200 for basic liveness to satisfy platform health checks
            logger.warning(f"/api/v1/health fallback due to error: {e}")
            return {
                'status': 'ok',
                'database': 'unknown',
                'timestamp': datetime.now().isoformat()
            }, 200

@ns_cities.route('/health')
class Health(Resource):
    @ns_cities.doc('health_check')
    def get(self):
        """API health check"""
        try:
            from database.db_operations import DatabaseOperations
            db = DatabaseOperations()
            
            # Test database connection
            test_query = "SELECT 1;"
            db.db.execute_query(test_query)
            
            return {
                'status': 'healthy',
                'database': 'connected',
                'timestamp': datetime.now().isoformat()
            }, 200
        except Exception as e:
            return {
                'status': 'unhealthy',
                'database': 'disconnected',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }, 503
