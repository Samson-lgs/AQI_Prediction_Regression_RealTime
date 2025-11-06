"""Utility functions for model operations and model selection/ensembling"""

import joblib
import os
import sys
from typing import Any, Optional, Dict
import logging
from datetime import datetime
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.db_config import DatabaseManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def save_model(model: Any, model_name: str, version: str = "1.0.0") -> str:
    """
    Save a trained model to disk
    
    Args:
        model: The trained model object
        model_name: Name of the model
        version: Version of the model
        
    Returns:
        str: Path where the model was saved
    """
    filepath = f"models/trained_models/{model_name}_v{version}.joblib"
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    joblib.dump(model, filepath)
    return filepath

def load_model(model_name: str, version: str = "1.0.0") -> Any:
    """
    Load a trained model from disk
    
    Args:
        model_name: Name of the model to load
        version: Version of the model to load
        
    Returns:
        The loaded model object
    """
    filepath = f"models/trained_models/{model_name}_v{version}.joblib"
    return joblib.load(filepath)


class ModelSelector:
    def __init__(self):
        # Use DatabaseManager directly for query execution
        self.db = DatabaseManager()
        self.model_performances = {}

    def save_performance(self, city: str, model_name: str, metrics: Dict) -> None:
        """Save model performance to database"""
        try:
            query = """
            INSERT INTO model_performance 
            (city, model_name, metric_date, r2_score, rmse, mae, mape)
            VALUES (%s, %s, CURRENT_DATE, %s, %s, %s, %s)
            ON CONFLICT (city, model_name, metric_date) DO UPDATE
            SET r2_score=EXCLUDED.r2_score, rmse=EXCLUDED.rmse, 
                mae=EXCLUDED.mae, mape=EXCLUDED.mape;
            """
            # Convert numpy types to Python native types
            params = (
                city, 
                model_name, 
                float(metrics.get('r2', 0)), 
                float(metrics.get('rmse', 0)), 
                float(metrics.get('mae', 0)), 
                float(metrics.get('mape', 0))
            )
            self.db.execute_query(query, params)
            logger.info(f"Performance saved for {model_name} in {city}")
        except Exception as e:
            logger.error(f"Error saving performance: {str(e)}")

    def get_best_model(self, city: str) -> str:
        """Get best model for a city based on recent performance"""
        try:
            query = """
            SELECT model_name, r2_score, rmse, mae, mape
            FROM model_performance
            WHERE city = %s
            AND metric_date >= CURRENT_DATE - INTERVAL '7 days'
            ORDER BY r2_score DESC NULLS LAST, rmse ASC NULLS LAST
            LIMIT 1;
            """
            result = self.db.execute_query_dicts(query, (city,))

            if result and len(result) > 0:
                best_model = result[0]['model_name']
                logger.info(f"Best model for {city}: {best_model}")
                return best_model
            else:
                logger.warning(f"No performance data for {city}, using default")
                return 'xgboost'  # Default model
        except Exception as e:
            logger.error(f"Error getting best model: {str(e)}")
            return 'xgboost'

    def ensemble_prediction(self, predictions_dict: Dict, weights: Optional[Dict] = None):
        """Combine predictions from multiple models using weighted average"""
        try:
            if not predictions_dict:
                return None

            # Align shapes and convert to numpy arrays
            preds = {k: np.asarray(v) for k, v in predictions_dict.items() if v is not None}
            if not preds:
                return None

            if weights is None:
                weights = {model: 1 / len(preds) for model in preds.keys()}

            # Normalize weights to sum to 1
            w_sum = sum(weights.get(m, 0) for m in preds.keys()) or 1.0
            norm_weights = {m: weights.get(m, 0) / w_sum for m in preds.keys()}

            # Weighted sum
            ensemble_pred = np.sum([
                preds[model] * norm_weights.get(model, 0)
                for model in preds.keys()
            ], axis=0)

            return np.maximum(ensemble_pred, 0)
        except Exception as e:
            logger.error(f"Error in ensemble prediction: {str(e)}")
            return None