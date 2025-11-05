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
    """Get AQI forecast for a city"""
    try:
        from models.model_utils import ModelSelector
        selector = ModelSelector()
        
        best_model = selector.get_best_model(city)
        
        return jsonify({
            'city': city,
            'best_model': best_model,
            'forecast_hours': 48,
            'status': 'Forecast model ready'
        }), 200
    
    except Exception as e:
        logger.error(f"Error: {str(e)}")
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
