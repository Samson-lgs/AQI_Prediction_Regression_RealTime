"""
Unified Model Predictor - Loads and uses unified models for predictions
Filters by city at prediction time rather than using city-specific models.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
import numpy as np
import pandas as pd
import pickle

logger = logging.getLogger(__name__)

class UnifiedPredictor:
    """Predictor that uses unified models (one per algorithm) with city filtering."""
    
    def __init__(self, models_dir: str = "models/trained_models"):
        self.models_dir = Path(models_dir)
        self.models = {}
        self.metadata = {}
        self.load_latest_models()
    
    def load_latest_models(self):
        """Load the most recent unified models."""
        logger.info("Loading unified models...")
        
        model_types = ["linear_regression", "random_forest", "xgboost"]
        
        for model_type in model_types:
            try:
                # Find latest model file for this type
                if model_type == "xgboost":
                    pattern = f"unified_{model_type}_*.json"
                else:
                    pattern = f"unified_{model_type}_*.pkl"
                
                model_files = sorted(self.models_dir.glob(pattern), reverse=True)
                
                if not model_files:
                    logger.warning(f"No unified {model_type} model found")
                    continue
                
                latest_model = model_files[0]
                
                # Load model
                if model_type == "xgboost":
                    import xgboost as xgb
                    model = xgb.XGBRegressor()
                    model.load_model(str(latest_model))
                else:
                    with open(latest_model, 'rb') as f:
                        model = pickle.load(f)
                
                self.models[model_type] = model
                
                # Load metadata
                metadata_file = latest_model.parent / f"{latest_model.stem}_metadata.json"
                if metadata_file.exists():
                    with open(metadata_file, 'r') as f:
                        self.metadata[model_type] = json.load(f)
                
                logger.info(f"✅ Loaded {model_type}: {latest_model.name}")
                
            except Exception as e:
                logger.error(f"Error loading {model_type}: {e}")
    
    def prepare_features(self, city: str, pollutants: Dict[str, float], model_type: str) -> np.ndarray:
        """
        Prepare feature vector for prediction.
        
        Args:
            city: City name
            pollutants: Dict with pm25, pm10, no2, so2, co, o3
            model_type: Which model to prepare for
        
        Returns:
            Feature array ready for prediction
        """
        # Get metadata for this model
        meta = self.metadata.get(model_type, {})
        city_columns = meta.get("city_columns", [])
        
        # Base pollutant features
        features = {
            "pm25": pollutants.get("pm25", 0),
            "pm10": pollutants.get("pm10", 0),
            "no2": pollutants.get("no2", 0),
            "so2": pollutants.get("so2", 0),
            "co": pollutants.get("co", 0),
            "o3": pollutants.get("o3", 0),
        }
        
        # Add city one-hot encoding
        city_feature = f"city_{city}"
        for city_col in city_columns:
            features[city_col] = 1.0 if city_col == city_feature else 0.0
        
        # Convert to array in correct order
        feature_order = meta.get("feature_order", [])
        if feature_order:
            feature_vector = [features.get(col, 0) for col in feature_order]
        else:
            # Fallback: pollutants first, then cities
            feature_vector = [
                features["pm25"], features["pm10"], features["no2"],
                features["so2"], features["co"], features["o3"]
            ] + [features.get(col, 0) for col in city_columns]
        
        return np.array([feature_vector])
    
    def predict(
        self, 
        city: str, 
        pollutants: Dict[str, float], 
        model_type: str = "xgboost"
    ) -> Optional[float]:
        """
        Predict AQI for a city given pollutant values.
        
        Args:
            city: City name
            pollutants: Dict with pm25, pm10, no2, so2, co, o3
            model_type: Model to use (linear_regression, random_forest, xgboost)
        
        Returns:
            Predicted AQI value or None if error
        """
        try:
            if model_type not in self.models:
                logger.error(f"Model {model_type} not loaded")
                return None
            
            # Prepare features
            X = self.prepare_features(city, pollutants, model_type)
            
            # Predict
            model = self.models[model_type]
            prediction = model.predict(X)
            
            # Ensure non-negative AQI
            aqi = max(0, float(prediction[0]))
            
            return aqi
            
        except Exception as e:
            logger.error(f"Prediction error for {city} using {model_type}: {e}")
            return None
    
    def predict_all_models(
        self, 
        city: str, 
        pollutants: Dict[str, float]
    ) -> Dict[str, Optional[float]]:
        """
        Get predictions from all available models.
        
        Returns:
            Dict mapping model_type -> predicted AQI
        """
        predictions = {}
        
        for model_type in self.models.keys():
            aqi = self.predict(city, pollutants, model_type)
            predictions[model_type] = aqi
        
        return predictions
    
    def get_best_prediction(
        self, 
        city: str, 
        pollutants: Dict[str, float]
    ) -> Dict[str, any]:
        """
        Get the best prediction using the most accurate model.
        
        Returns:
            Dict with 'model', 'aqi', and 'all_predictions'
        """
        all_predictions = self.predict_all_models(city, pollutants)
        
        # Use XGBoost as default best (highest R² from training)
        best_model = "xgboost"
        
        # Fallback order: xgboost -> random_forest -> linear_regression
        for preferred in ["xgboost", "random_forest", "linear_regression"]:
            if preferred in all_predictions and all_predictions[preferred] is not None:
                best_model = preferred
                break
        
        return {
            "model": best_model,
            "aqi": all_predictions.get(best_model),
            "all_predictions": all_predictions,
            "city": city
        }
    
    def available_models(self) -> List[str]:
        """Get list of available model types."""
        return list(self.models.keys())


# Singleton instance
_predictor_instance = None

def get_predictor() -> UnifiedPredictor:
    """Get or create the singleton predictor instance."""
    global _predictor_instance
    if _predictor_instance is None:
        _predictor_instance = UnifiedPredictor()
    return _predictor_instance
