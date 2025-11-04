import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LSTMAQI:
    def __init__(self, lookback=24, units=50, dropout_rate=0.2):
        self.lookback = lookback
        self.units = units
        self.dropout_rate = dropout_rate
        self.model = None
        self.is_trained = False
    
    def create_sequences(self, data, target, lookback):
        """Create sequences for LSTM"""
        X, y = [], []
        for i in range(len(data) - lookback):
            X.append(data[i:i+lookback])
            y.append(target[i+lookback])
        return np.array(X), np.array(y)
    
    def build_model(self, input_shape):
        """Build LSTM model"""
        try:
            self.model = Sequential([
                LSTM(self.units, activation='relu', return_sequences=True, input_shape=input_shape),
                Dropout(self.dropout_rate),
                LSTM(self.units, activation='relu', return_sequences=False),
                Dropout(self.dropout_rate),
                Dense(25, activation='relu'),
                Dense(1)
            ])
            
            self.model.compile(optimizer=Adam(learning_rate=0.001), loss='mse', metrics=['mae'])
            logger.info("LSTM model built successfully")
            return True
        except Exception as e:
            logger.error(f"Error building LSTM model: {str(e)}")
            return False
    
    def train(self, X_train, y_train, X_val=None, y_val=None, epochs=50, batch_size=32):
        """Train LSTM model"""
        try:
            if self.model is None:
                self.build_model((X_train.shape[1], X_train.shape[2]))
            
            callbacks = [EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)]
            
            validation_data = None
            if X_val is not None and y_val is not None:
                validation_data = (X_val, y_val)
            
            self.model.fit(
                X_train, y_train,
                epochs=epochs,
                batch_size=batch_size,
                validation_data=validation_data,
                callbacks=callbacks,
                verbose=0
            )
            
            self.is_trained = True
            logger.info("LSTM model trained successfully")
            return True
        except Exception as e:
            logger.error(f"Error training LSTM: {str(e)}")
            return False
    
    def predict(self, X):
        """Make predictions"""
        if not self.is_trained:
            logger.error("Model not trained yet")
            return None
        
        try:
            predictions = self.model.predict(X, verbose=0)
            return np.maximum(predictions.flatten(), 0)
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
            mape = np.mean(np.abs((y_test - predictions) / y_test)) * 100
            
            metrics = {
                'mse': mse,
                'rmse': rmse,
                'mae': mae,
                'r2': r2,
                'mape': mape
            }
            
            logger.info(f"LSTM Metrics: {metrics}")
            return metrics
        except Exception as e:
            logger.error(f"Error evaluating model: {str(e)}")
            return None
    
    def save_model(self, filepath):
        """Save model to disk"""
        try:
            self.model.save(filepath)
            logger.info(f"Model saved to {filepath}")
        except Exception as e:
            logger.error(f"Error saving model: {str(e)}")
    
    def load_model(self, filepath):
        """Load model from disk"""
        try:
            from tensorflow.keras.models import load_model
            self.model = load_model(filepath)
            self.is_trained = True
            logger.info(f"Model loaded from {filepath}")
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")