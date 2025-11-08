import xgboost as xgb
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import numpy as np
import logging
import pickle

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class XGBoostAQI:
    def __init__(self, max_depth=6, learning_rate=0.1, n_estimators=100):
        self.params = {
            'max_depth': max_depth,
            'learning_rate': learning_rate,
            'n_estimators': n_estimators,
            'random_state': 42,
            'tree_method': 'hist'
        }
        self.model = None
        self.is_trained = False
    
    def train(self, X_train, y_train, X_val=None, y_val=None):
        """Train XGBoost model"""
        try:
            eval_set = None
            if X_val is not None and y_val is not None:
                eval_set = [(X_val, y_val)]
            
            self.model = xgb.XGBRegressor(**self.params, eval_metric='rmse')
            
            self.model.fit(
                X_train, y_train,
                eval_set=eval_set,
                verbose=False
            )
            
            self.is_trained = True
            logger.info("XGBoost model trained successfully")
            return True
        except Exception as e:
            logger.error(f"Error training XGBoost: {str(e)}")
            return False
    
    def predict(self, X):
        """Make predictions"""
        if not self.is_trained:
            logger.error("Model not trained yet")
            return None
        
        try:
            predictions = self.model.predict(X)
            return np.maximum(predictions, 0)
        except Exception as e:
            logger.error(f"Error making predictions: {str(e)}")
            return None
    
    def evaluate(self, X_test, y_test):
        """Evaluate model performance"""
        try:
            predictions = self.predict(X_test)
            
            mse = mean_squared_error(y_test, predictions)
            rmse = np.sqrt(mse)
            mae = mean_absolute_error(y_test, predictions)
            r2 = r2_score(y_test, predictions)
            safe_y = np.where(y_test == 0, 1e-6, y_test)
            mape = np.mean(np.abs((y_test - predictions) / safe_y)) * 100
            
            metrics = {
                'mse': mse,
                'rmse': rmse,
                'mae': mae,
                'r2': r2,
                'mape': mape
            }
            
            logger.info(f"XGBoost Metrics: {metrics}")
            return metrics
        except Exception as e:
            logger.error(f"Error evaluating model: {str(e)}")
            return None
    
    def save_model(self, filepath):
        """Save model to disk"""
        try:
            self.model.save_model(filepath)
            logger.info(f"Model saved to {filepath}")
        except Exception as e:
            logger.error(f"Error saving model: {str(e)}")
    
    def load_model(self, filepath):
        """Load model from disk"""
        try:
            self.model = xgb.XGBRegressor()
            self.model.load_model(filepath)
            self.is_trained = True
            logger.info(f"Model loaded from {filepath}")
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")