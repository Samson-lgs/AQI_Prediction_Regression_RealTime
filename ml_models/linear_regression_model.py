"""Linear Regression model for AQI prediction"""

from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
import numpy as np
from typing import Tuple

class AQILinearRegression:
    def __init__(self):
        self.model = LinearRegression()
        
    def train(self, X_train: np.ndarray, y_train: np.ndarray) -> None:
        """
        Train the linear regression model
        
        Args:
            X_train: Training features
            y_train: Training target values
        """
        self.model.fit(X_train, y_train)
        
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Make predictions using the trained model
        
        Args:
            X: Input features
            
        Returns:
            Array of predictions
        """
        return self.model.predict(X)
        
    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray) -> Tuple[float, float]:
        """
        Evaluate the model performance
        
        Args:
            X_test: Test features
            y_test: Test target values
            
        Returns:
            Tuple of (RMSE, R² score)
        """
        predictions = self.predict(X_test)
        rmse = np.sqrt(mean_squared_error(y_test, predictions))
        r2 = r2_score(y_test, predictions)
        return rmse, r2