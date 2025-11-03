"""LSTM model for AQI prediction"""

import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from sklearn.metrics import mean_squared_error, r2_score
import numpy as np
from typing import Tuple

class AQILSTM:
    def __init__(self, sequence_length: int, n_features: int):
        self.sequence_length = sequence_length
        self.n_features = n_features
        self.model = self._build_model()
        
    def _build_model(self) -> Sequential:
        """
        Build LSTM model architecture
        
        Returns:
            Compiled Keras Sequential model
        """
        model = Sequential([
            LSTM(50, activation='relu', input_shape=(self.sequence_length, self.n_features), return_sequences=True),
            Dropout(0.2),
            LSTM(30, activation='relu'),
            Dropout(0.2),
            Dense(1)
        ])
        
        model.compile(optimizer='adam', loss='mse')
        return model
        
    def train(self, X_train: np.ndarray, y_train: np.ndarray, epochs: int = 50, batch_size: int = 32) -> None:
        """
        Train the LSTM model
        
        Args:
            X_train: Training features
            y_train: Training target values
            epochs: Number of training epochs
            batch_size: Batch size for training
        """
        self.model.fit(
            X_train, 
            y_train, 
            epochs=epochs, 
            batch_size=batch_size, 
            validation_split=0.1,
            verbose=1
        )
        
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