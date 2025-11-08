from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import numpy as np
import logging
import pickle

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RandomForestAQI:
    def __init__(self, n_estimators=100, max_depth=20, random_state=42):
        self.model = RandomForestRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=random_state,
            n_jobs=-1
        )
        self.is_trained = False
    
    def train(self, X_train, y_train):
        """Train random forest model"""
        try:
            self.model.fit(X_train, y_train)
            self.is_trained = True
            
            # Feature importance
            importances = self.model.feature_importances_
            logger.info(f"Top 5 important features: {importances}")
            
            logger.info("Random Forest model trained successfully")
            return True
        except Exception as e:
            logger.error(f"Error training Random Forest: {str(e)}")
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
            
            logger.info(f"Random Forest Metrics: {metrics}")
            return metrics
        except Exception as e:
            logger.error(f"Error evaluating model: {str(e)}")
            return None
    
    def save_model(self, filepath):
        """Save model to disk"""
        try:
            with open(filepath, 'wb') as f:
                pickle.dump(self.model, f)
            logger.info(f"Model saved to {filepath}")
        except Exception as e:
            logger.error(f"Error saving model: {str(e)}")
    
    def load_model(self, filepath):
        """Load model from disk"""
        try:
            with open(filepath, 'rb') as f:
                self.model = pickle.load(f)
            self.is_trained = True
            logger.info(f"Model loaded from {filepath}")
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")