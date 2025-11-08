import numpy as np
import logging
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error

try:
    import lightgbm as lgb
except ImportError:  # fallback stub
    lgb = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LightGBMAQI:
    def __init__(self, num_leaves=31, learning_rate=0.1, n_estimators=200):
        self.params = dict(num_leaves=num_leaves, learning_rate=learning_rate, n_estimators=n_estimators, random_state=42)
        self.model = None
        self.is_trained = False
    
    def train(self, X_train, y_train, X_val=None, y_val=None):
        if lgb is None:
            logger.error("lightgbm not installed")
            return False
        try:
            self.model = lgb.LGBMRegressor(**self.params)
            if X_val is not None and y_val is not None:
                # Suppress logging by setting verbose to -1 if available, otherwise rely on callbacks
                try:
                    self.model.fit(X_train, y_train, eval_set=[(X_val, y_val)], eval_metric='rmse')
                except TypeError:
                    self.model.fit(X_train, y_train, eval_set=[(X_val, y_val)])
            else:
                self.model.fit(X_train, y_train)
            self.is_trained = True
            return True
        except Exception as e:
            logger.error(f"Error training LightGBM: {e}")
            return False
    
    def predict(self, X):
        if not self.is_trained:
            logger.error("Model not trained yet")
            return None
        preds = self.model.predict(X)
        return np.maximum(preds, 0)
    
    def evaluate(self, X, y):
        try:
            preds = self.predict(X)
            mse = mean_squared_error(y, preds)
            rmse = np.sqrt(mse)
            mae = mean_absolute_error(y, preds)
            r2 = r2_score(y, preds)
            safe_y = np.where(y == 0, 1e-6, y)
            mape = np.mean(np.abs((y - preds) / safe_y)) * 100
            metrics = dict(mse=mse, rmse=rmse, mae=mae, r2=r2, mape=mape)
            logger.info(f"LightGBM Metrics: {metrics}")
            return metrics
        except Exception as e:
            logger.error(f"Error evaluating LightGBM: {e}")
            return None
    
    def save_model(self, filepath):
        try:
            self.model.booster_.save_model(filepath)
            logger.info(f"LightGBM model saved to {filepath}")
        except Exception as e:
            logger.error(f"Error saving LightGBM: {e}")
    
    def load_model(self, filepath):
        try:
            booster = lgb.Booster(model_file=filepath)
            self.model = lgb.LGBMRegressor(**self.params)
            self.model._Booster = booster
            self.is_trained = True
            logger.info(f"LightGBM model loaded from {filepath}")
        except Exception as e:
            logger.error(f"Error loading LightGBM: {e}")
