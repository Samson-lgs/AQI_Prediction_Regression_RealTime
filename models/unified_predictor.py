"""
Unified Predictor with Feature Engineering
Loads models trained with engineered features and applies same transformations at inference.
"""

import logging
from pathlib import Path
import pickle
import json
import numpy as np
import pandas as pd
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class UnifiedPredictor:
    """Predictor using unified models with feature engineering."""
    
    def __init__(self, models_dir: str = "models/saved_models"):
        self.models_dir = Path(models_dir)
        self.models = {}
        self.medians = {}
        self.feature_metadata = None
        self.load_models()
        self.load_feature_metadata()
    
    def load_models(self):
        """Load the latest saved models."""
        logger.info("📦 Loading unified models with feature engineering...")
        
        model_types = [
            ("linear_regression", "pkl"),
            ("random_forest", "pkl"),
            ("xgboost", "json")
        ]
        
        for model_name, ext in model_types:
            try:
                model_file = self.models_dir / f"{model_name}_latest.{ext}"
                
                if not model_file.exists():
                    logger.warning(f"  ⚠️  {model_name}: not found")
                    continue
                
                # Load based on type
                if model_name == "xgboost":
                    import xgboost as xgb
                    model = xgb.XGBRegressor()
                    model.load_model(str(model_file))
                else:
                    with open(model_file, 'rb') as f:
                        model = pickle.load(f)
                
                self.models[model_name] = model
                
                # Load metrics if available
                metrics_files = list(self.models_dir.glob(f"{model_name}_*_metrics.json"))
                if metrics_files:
                    latest_metrics = sorted(metrics_files, reverse=True)[0]
                    with open(latest_metrics) as f:
                        metrics = json.load(f)
                        r2 = metrics.get('r2', 0)
                        logger.info(f"  ✅ {model_name}: R² = {r2:.4f}")
                else:
                    logger.info(f"  ✅ {model_name}: loaded")
                
            except Exception as e:
                logger.error(f"  ❌ {model_name}: {e}")
        
        logger.info(f"📊 Loaded {len(self.models)} models")
        
        # Load median imputation values
        try:
            median_file = self.models_dir / 'median_imputation.json'
            if median_file.exists():
                with open(median_file) as mf:
                    self.medians = json.load(mf)
                    logger.info(f"  ✅ Loaded median imputation values")
            else:
                self.medians = {}
                logger.warning("  ⚠️ median_imputation.json not found")
        except Exception as e:
            self.medians = {}
            logger.warning(f"  ⚠️ Could not load medians: {e}")
    
    def load_feature_metadata(self):
        """Load feature metadata (column names and order)."""
        try:
            metadata_file = self.models_dir / 'feature_metadata.json'
            if metadata_file.exists():
                with open(metadata_file) as f:
                    self.feature_metadata = json.load(f)
                    logger.info(f"  ✅ Loaded feature metadata: {len(self.feature_metadata['feature_columns'])} features")
            else:
                logger.warning("  ⚠️ feature_metadata.json not found - using basic features only")
                self.feature_metadata = None
        except Exception as e:
            logger.warning(f"  ⚠️ Could not load feature metadata: {e}")
            self.feature_metadata = None
    
    def engineer_features(self, pollutants: Dict[str, float], city: str = None, 
                         timestamp: datetime = None) -> np.ndarray:
        """
        Apply same feature engineering as training.
        
        Note: Without historical data, lag and rolling features will be filled with base values.
        This is a limitation for single-point predictions.
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        # Import feature engineering module
        try:
            from feature_engineering.advanced_features import AdvancedFeatureEngineer
        except ImportError:
            logger.warning("Could not import AdvancedFeatureEngineer - using base features only")
            return self._prepare_base_features(pollutants)
        
        # If no feature metadata, use base features only
        if self.feature_metadata is None:
            return self._prepare_base_features(pollutants)
        
        # Create DataFrame with single row
        data = pollutants.copy()
        data['timestamp'] = timestamp
        if city:
            data['city'] = city
        
        df = pd.DataFrame([data])
        
        # Apply feature engineering (without lag/rolling since we don't have history)
        engineer = AdvancedFeatureEngineer()
        
        # Add only features that don't require historical data
        df = engineer.add_temporal_features(df)
        df = engineer.add_interaction_features(df)
        df = engineer.add_ratio_features(df)
        
        # For missing lag/rolling features, fill with base pollutant values or 0
        expected_features = self.feature_metadata['feature_columns']
        
        for feature in expected_features:
            if feature not in df.columns:
                # For lag features, use current value
                if '_lag' in feature:
                    base_pollutant = feature.split('_lag')[0]
                    if base_pollutant in pollutants:
                        df[feature] = pollutants[base_pollutant]
                    else:
                        df[feature] = 0
                # For rolling mean features, use current value
                elif '_rolling' in feature and '_mean' in feature:
                    base_pollutant = feature.split('_rolling')[0]
                    if base_pollutant in pollutants:
                        df[feature] = pollutants[base_pollutant]
                    else:
                        df[feature] = 0
                # For rolling std features, use 0 (no volatility for single point)
                elif '_rolling' in feature and '_std' in feature:
                    df[feature] = 0
                # For city mean features, use global median
                elif '_city_mean' in feature:
                    base_pollutant = feature.split('_city_mean')[0]
                    df[feature] = self.medians.get(base_pollutant, 0)
                # For deviation features, use 0
                elif '_dev_from_city_mean' in feature:
                    df[feature] = 0
                else:
                    df[feature] = 0
        
        # Extract features in correct order
        X = df[expected_features].values
        return X
    
    def _prepare_base_features(self, pollutants: Dict[str, float]) -> np.ndarray:
        """Prepare basic features without engineering (fallback)."""
        def _fill(name, val):
            if val is None:
                return float(self.medians.get(name, 0))
            return float(val)
        
        X = np.array([[
            _fill('pm25', pollutants.get('pm25', 0)),
            _fill('pm10', pollutants.get('pm10', 0)),
            _fill('no2', pollutants.get('no2', 0)),
            _fill('so2', pollutants.get('so2', 0)),
            _fill('co', pollutants.get('co', 0)),
            _fill('o3', pollutants.get('o3', 0))
        ]])
        return X
    
    def predict(
        self,
        pollutants: Dict[str, float],
        model: str = "xgboost",
        city: str = None,
        timestamp: datetime = None
    ) -> Optional[float]:
        """
        Predict AQI from pollutant values.
        
        Args:
            pollutants: Dict with keys pm25, pm10, no2, so2, co, o3
            model: Model to use (linear_regression, random_forest, xgboost)
            city: City name (optional, used for city-specific features)
            timestamp: Datetime for temporal features (default: now)
        
        Returns:
            Predicted AQI value
        """
        if model not in self.models:
            logger.error(f"Model '{model}' not loaded")
            return None
        
        try:
            # Engineer features
            X = self.engineer_features(pollutants, city=city, timestamp=timestamp)
            
            # Predict
            prediction = self.models[model].predict(X)
            aqi = max(0, float(prediction[0]))
            
            return aqi
            
        except Exception as e:
            logger.error(f"Prediction error: {e}", exc_info=True)
            return None
    
    def predict_all_models(
        self,
        pollutants: Dict[str, float],
        city: str = None,
        timestamp: datetime = None
    ) -> Dict[str, Optional[float]]:
        """
        Get predictions from all available models.
        
        Returns:
            Dict mapping model_name -> predicted AQI
        """
        predictions = {}
        for model_name in self.models.keys():
            aqi = self.predict(pollutants, model=model_name, city=city, timestamp=timestamp)
            predictions[model_name] = aqi
        return predictions
    
    def get_best_prediction(
        self,
        city: str,
        pollutants: Dict[str, float],
        timestamp: datetime = None
    ) -> Dict[str, any]:
        """
        Get prediction from the best model (XGBoost by default).
        
        Args:
            city: City name
            pollutants: Dict with pollutant values
            timestamp: Optional timestamp
        
        Returns:
            Dict with 'model', 'aqi', 'all_predictions'
        """
        all_preds = self.predict_all_models(pollutants, city=city, timestamp=timestamp)
        
        # Prefer XGBoost (typically best R²), then Random Forest, then Linear Regression
        best_model = None
        for preferred in ["xgboost", "random_forest", "linear_regression"]:
            if preferred in all_preds and all_preds[preferred] is not None:
                best_model = preferred
                break
        
        return {
            "model": best_model,
            "aqi": all_preds.get(best_model) if best_model else None,
            "all_predictions": all_preds
        }
    
    def available_models(self) -> list:
        """Get list of available model names."""
        return list(self.models.keys())


# Singleton instance
_predictor = None

def get_predictor() -> UnifiedPredictor:
    """Get or create singleton predictor."""
    global _predictor
    if _predictor is None:
        _predictor = UnifiedPredictor()
    return _predictor


if __name__ == "__main__":
    # Test the predictor
    logging.basicConfig(level=logging.INFO)
    
    predictor = get_predictor()
    
    # Example prediction
    test_pollutants = {
        'pm25': 55.0,
        'pm10': 95.0,
        'no2': 42.0,
        'so2': 12.0,
        'co': 1.2,
        'o3': 38.0
    }
    
    result = predictor.get_best_prediction("Delhi", test_pollutants)
    print(f"\nTest Prediction:")
    print(f"  Best model: {result['model']}")
    print(f"  Predicted AQI: {result['aqi']:.1f}")
    print(f"  All predictions: {result['all_predictions']}")
