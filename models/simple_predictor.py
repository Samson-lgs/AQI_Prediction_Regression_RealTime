"""
Simple Predictor - Loads and uses unified models trained on all city data
No city parameter needed - just pass pollutant values!
"""

import logging
from pathlib import Path
import pickle
import json
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class SimplePredictor:
    """Simple predictor using unified models (no city encoding)."""
    
    def __init__(self, models_dir: str = "models/saved_models"):
        self.models_dir = Path(models_dir)
        self.models = {}
        self.load_models()
    
    def load_models(self):
        """Load the latest saved models."""
        logger.info("📦 Loading unified models...")
        
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
                metrics_file = model_file.parent / f"{model_file.stem.replace('_latest', '')}_*_metrics.json"
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
        # Load median imputation values if available
        try:
            median_file = self.models_dir / 'median_imputation.json'
            if median_file.exists():
                with open(median_file) as mf:
                    self.medians = json.load(mf)
                    logger.info(f"  ✅ Loaded median imputation values from {median_file.name}")
            else:
                self.medians = {}
                logger.info("  ⚠️ median_imputation.json not found; predictions will use 0 for missing inputs")
        except Exception as e:
            self.medians = {}
            logger.warning(f"  ⚠️ Could not load medians: {e}")
    
    def predict(
        self,
        pm25: float,
        pm10: float,
        no2: float,
        so2: float,
        co: float,
        o3: float,
        model: str = "xgboost"
    ) -> Optional[float]:
        """
        Predict AQI from pollutant values.
        
        Args:
            pm25: PM2.5 concentration (µg/m³)
            pm10: PM10 concentration (µg/m³)
            no2: NO2 concentration (µg/m³)
            so2: SO2 concentration (µg/m³)
            co: CO concentration (mg/m³)
            o3: O3 concentration (µg/m³)
            model: Model to use (linear_regression, random_forest, xgboost)
        
        Returns:
            Predicted AQI value
        """
        if model not in self.models:
            logger.error(f"Model '{model}' not loaded")
            return None
        
        try:
            # Prepare feature vector
            import numpy as np
            # If any value is None, fall back to stored median (if available)
            def _fill(name, val):
                if val is None:
                    return float(self.medians.get(name, 0))
                return float(val)

            X = np.array([[
                _fill('pm25', pm25),
                _fill('pm10', pm10),
                _fill('no2', no2),
                _fill('so2', so2),
                _fill('co', co),
                _fill('o3', o3)
            ]])
            
            # Predict
            prediction = self.models[model].predict(X)
            aqi = max(0, float(prediction[0]))
            
            return aqi
            
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return None
    
    def predict_from_dict(
        self,
        pollutants: Dict[str, float],
        model: str = "xgboost"
    ) -> Optional[float]:
        """
        Predict AQI from pollutants dictionary.
        
        Args:
            pollutants: Dict with keys pm25, pm10, no2, so2, co, o3
            model: Model to use
        
        Returns:
            Predicted AQI value
        """
        return self.predict(
            pm25=pollutants.get('pm25', 0),
            pm10=pollutants.get('pm10', 0),
            no2=pollutants.get('no2', 0),
            so2=pollutants.get('so2', 0),
            co=pollutants.get('co', 0),
            o3=pollutants.get('o3', 0),
            model=model
        )
    
    def predict_all_models(
        self,
        pollutants: Dict[str, float]
    ) -> Dict[str, Optional[float]]:
        """
        Get predictions from all available models.
        
        Returns:
            Dict mapping model_name -> predicted AQI
        """
        predictions = {}
        for model_name in self.models.keys():
            aqi = self.predict_from_dict(pollutants, model=model_name)
            predictions[model_name] = aqi
        return predictions
    
    def get_best_prediction(
        self,
        pollutants: Dict[str, float]
    ) -> Dict[str, any]:
        """
        Get prediction from the best model (XGBoost by default).
        
        Returns:
            Dict with 'model', 'aqi', 'all_predictions'
        """
        all_preds = self.predict_all_models(pollutants)
        
        # Prefer XGBoost (best R²), then Random Forest, then Linear Regression
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

def get_predictor() -> SimplePredictor:
    """Get or create singleton predictor."""
    global _predictor
    if _predictor is None:
        _predictor = SimplePredictor()
    return _predictor
