from flask import Blueprint, jsonify
from ml_models.linear_regression_model import LinearRegressionAQI
from ml_models.random_forest_model import RandomForestAQI
from ml_models.xgboost_model import XGBoostAQI
from ml_models.lstm_model import LSTMAQI
from models.model_utils import ModelSelector
from database.db_operations import DatabaseOperations
import logging

logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__, url_prefix='/api')
db = DatabaseOperations()
selector = ModelSelector()

# Lazy instances; models will be loaded per request
lr_model = LinearRegressionAQI()
rf_model = RandomForestAQI()
xgb_model = XGBoostAQI()
lstm_model = LSTMAQI()

@api_bp.route('/predict/<city>', methods=['GET'])
def predict(city):
    """Get prediction for a city by loading the best model (sanity check endpoint)."""
    try:
        best_model_name = selector.get_best_model(city)

        # Load best model
        if best_model_name == 'linear_regression':
            model = lr_model
            model.load_model(f"models/trained_models/{city}_lr.pkl")
        elif best_model_name == 'random_forest':
            model = rf_model
            model.load_model(f"models/trained_models/{city}_rf.pkl")
        elif best_model_name == 'xgboost':
            model = xgb_model
            model.load_model(f"models/trained_models/{city}_xgb.json")
        elif best_model_name == 'lstm':
            model = lstm_model
            model.load_model(f"models/trained_models/{city}_lstm.h5")
        else:
            return jsonify({'error': f"Unknown model '{best_model_name}' for city {city}"}), 404

        return jsonify({"city": city, "model": best_model_name, "status": "Model loaded successfully"}), 200
    except Exception as e:
        logger.error(f"Error in prediction: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/performance/<city>', methods=['GET'])
def get_performance(city):
    """Get model performance for a city for the last 30 days (default)."""
    try:
        result = db.get_model_performance(city, None, days=30)
        return jsonify(result or []), 200
    except Exception as e:
        logger.error(f"Error getting performance: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'}), 200
