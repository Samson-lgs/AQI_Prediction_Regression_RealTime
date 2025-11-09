from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
import logging
import numpy as np

logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

@api_bp.route('/cities', methods=['GET'])
def get_cities():
    """Get list of supported cities"""
    from config.settings import CITIES
    return jsonify({'cities': CITIES}), 200

@api_bp.route('/aqi/current/<city>', methods=['GET'])
def get_current_aqi(city):
    """Get current AQI for a city"""
    try:
        from database.db_operations import DatabaseOperations
        db = DatabaseOperations()
        
        end_date = datetime.now()
        # Try last 1 hour first
        start_date = end_date - timedelta(hours=1)
        data = db.get_pollution_data(city, start_date, end_date)

        # If no recent reading found, widen window to last 24 hours
        if not data or len(data) == 0:
            start_date = end_date - timedelta(hours=24)
            data = db.get_pollution_data(city, start_date, end_date)
        
        if data:
            # get_pollution_data orders by timestamp DESC; pick the first as latest
            latest = data[0]
            return jsonify({
                'city': city,
                'timestamp': str(latest['timestamp']),
                'aqi': latest['aqi_value'],
                'pm25': latest['pm25'],
                'pm10': latest['pm10'],
                'no2': latest['no2'],
                'so2': latest['so2'],
                'co': latest['co'],
                'o3': latest['o3']
            }), 200
        else:
            return jsonify({'error': f'No data for {city}'}), 404
    
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/aqi/history/<city>', methods=['GET'])
def get_aqi_history(city):
    """Get AQI history for a city"""
    try:
        from database.db_operations import DatabaseOperations
        db = DatabaseOperations()
        
        days = request.args.get('days', 7, type=int)
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        data = db.get_pollution_data(city, start_date, end_date)
        
        if data:
            return jsonify({
                'city': city,
                'data': data
            }), 200
        else:
            return jsonify({'error': f'No data for {city}'}), 404
    
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/forecast/<city>', methods=['GET'])
def get_forecast(city):
    """Get AQI forecast/prediction for a city using unified models with feature engineering"""
    try:
        from database.db_operations import DatabaseOperations
        from models.unified_predictor import get_predictor
        
        db = DatabaseOperations()
        predictor = get_predictor()
        
        # Get most recent pollutant data for this city
        end_date = datetime.now()
        start_date = end_date - timedelta(hours=24)
        data = db.get_pollution_data(city, start_date, end_date)
        
        if not data or len(data) == 0:
            return jsonify({'error': f'No recent data for {city}'}), 404
        
        # Use latest data as baseline
        latest = data[0]
        pollutants = {
            # Use None for missing values and let the predictor perform median imputation
            'pm25': float(latest['pm25']) if latest.get('pm25') is not None else None,
            'pm10': float(latest['pm10']) if latest.get('pm10') is not None else None,
            'no2': float(latest['no2']) if latest.get('no2') is not None else None,
            'so2': float(latest['so2']) if latest.get('so2') is not None else None,
            'co': float(latest['co']) if latest.get('co') is not None else None,
            'o3': float(latest['o3']) if latest.get('o3') is not None else None,
        }
        
        # Get predictions from all models with feature engineering
        # Pass city and timestamp for proper temporal feature generation
        from datetime import datetime as dt
        timestamp = dt.fromisoformat(latest['timestamp'].replace('Z', '+00:00')) if isinstance(latest['timestamp'], str) else latest['timestamp']
        result = predictor.get_best_prediction(city, pollutants, timestamp=timestamp)
        
        # Generate hourly forecast (simple trend-based for now)
        hours = request.args.get('hours', 48, type=int)
        forecasts = []
        base_aqi = result['aqi'] if result['aqi'] else float(latest.get('aqi_value', 100))
        
        for h in range(1, min(hours + 1, 49)):
            # Simple trend variation
            variation = np.sin(h / 6) * 10 + np.random.normal(0, 3)
            predicted_aqi = max(0, int(base_aqi + variation))
            confidence = max(50, 95 - (h * 0.8))
            
            forecasts.append({
                'hour': h,
                'timestamp': (end_date + timedelta(hours=h)).isoformat(),
                'predicted_aqi': predicted_aqi,
                'confidence': round(confidence, 1)
            })
        
        return jsonify({
            'city': city,
            'current_aqi': base_aqi,
            'predicted_aqi': result['aqi'],
            'best_model': result['model'],
            'all_model_predictions': result['all_predictions'],
            'available_models': predictor.available_models(),
            'forecast': forecasts[:hours],
            'pollutants_used': pollutants,
            'note': 'Model trained on ALL cities combined - works for any city!',
            'timestamp': datetime.now().isoformat()
        }), 200
    
    except Exception as e:
        logger.error(f"Forecast error for {city}: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@api_bp.route('/metrics/<city>', methods=['GET'])
def get_metrics(city):
    """Get model metrics for a city"""
    try:
        from database.db_operations import DatabaseOperations
        db = DatabaseOperations()
        
        model_name = request.args.get('model', 'xgboost')
        
        metrics = db.get_model_performance(city, model_name, days=30)
        
        return jsonify({
            'city': city,
            'model': model_name,
            'metrics': metrics
        }), 200
    
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'}), 200
