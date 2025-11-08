import numpy as np
import logging
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error

try:
    from catboost import CatBoostRegressor
except ImportError:
    CatBoostRegressor = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CatBoostAQI:
    def __init__(self, depth=6, learning_rate=0.1, iterations=500):
        self.params = dict(depth=depth, learning_rate=learning_rate, iterations=iterations, random_seed=42, verbose=False)
        self.model = None
        self.is_trained = False
    
    def train(self, X_train, y_train, X_val=None, y_val=None):
        if CatBoostRegressor is None:
            logger.error("catboost not installed")
            return False
        try:
            self.model = CatBoostRegressor(**self.params)
            if X_val is not None and y_val is not None:
                self.model.fit(X_train, y_train, eval_set=(X_val, y_val), use_best_model=False)
            else:
                self.model.fit(X_train, y_train)
            self.is_trained = True
            return True
        except Exception as e:
            logger.error(f"Error training CatBoost: {e}")
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
            logger.info(f"CatBoost Metrics: {metrics}")
            return metrics
        except Exception as e:
            logger.error(f"Error evaluating CatBoost: {e}")
            return None
    
    def save_model(self, filepath):
        try:
            self.model.save_model(filepath)
            logger.info(f"CatBoost model saved to {filepath}")
        except Exception as e:
            logger.error(f"Error saving CatBoost: {e}")
    
    def load_model(self, filepath):
        try:
            from catboost import CatBoostRegressor as CBR
            self.model = CBR()
            self.model.load_model(filepath)
            self.is_trained = True
            logger.info(f"CatBoost model loaded from {filepath}")
        except Exception as e:
            logger.error(f"Error loading CatBoost: {e}")
