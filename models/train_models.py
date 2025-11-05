import os
import sys
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, TimeSeriesSplit

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from feature_engineering.feature_processor import FeatureProcessor
from ml_models.linear_regression_model import LinearRegressionAQI
from ml_models.random_forest_model import RandomForestAQI
from ml_models.xgboost_model import XGBoostAQI
from config.settings import CITIES
from models.model_utils import ModelSelector
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Optional LSTM import
try:
    from ml_models.lstm_model import LSTMAQI
    LSTM_AVAILABLE = True
except Exception as e:
    LSTM_AVAILABLE = False
    logger.warning(f"LSTM not available: {e}")

class ModelTrainer:
    def __init__(self, train_ratio=0.7, val_ratio=0.15, test_ratio=0.15):
        """
        Initialize ModelTrainer with time-series-aware splitting
        
        Args:
            train_ratio: Proportion of data for training (default: 70%)
            val_ratio: Proportion of data for validation (default: 15%)
            test_ratio: Proportion of data for testing (default: 15%)
        """
        self.processor = FeatureProcessor()
        self.models = {
            'linear_regression': LinearRegressionAQI(),
            'random_forest': RandomForestAQI(),
            'xgboost': XGBoostAQI()
        }
        
        # Add LSTM if available
        if LSTM_AVAILABLE:
            self.models['lstm'] = LSTMAQI()
            logger.info("LSTM model available")
        else:
            logger.warning("Training without LSTM model")
        
        self.selector = ModelSelector()
        
        # Validate ratios
        if not np.isclose(train_ratio + val_ratio + test_ratio, 1.0):
            raise ValueError("Train, validation, and test ratios must sum to 1.0")
        
        self.train_ratio = train_ratio
        self.val_ratio = val_ratio
        self.test_ratio = test_ratio
    
    def time_series_split(self, X, y, timestamps=None):
        """
        Split data using time-series-aware approach
        
        This ensures:
        1. Training data comes before validation data
        2. Validation data comes before test data
        3. No data leakage from future to past
        4. Temporal ordering is preserved
        
        Args:
            X: Feature matrix
            y: Target values
            timestamps: Optional timestamps for logging split points
            
        Returns:
            X_train, X_val, X_test, y_train, y_val, y_test
        """
        n = len(X)
        
        # Calculate split indices based on time order (no shuffling!)
        train_end = int(n * self.train_ratio)
        val_end = int(n * (self.train_ratio + self.val_ratio))
        
        # Split data chronologically
        X_train = X[:train_end]
        y_train = y[:train_end]
        
        X_val = X[train_end:val_end]
        y_val = y[train_end:val_end]
        
        X_test = X[val_end:]
        y_test = y[val_end:]
        
        # Log split information
        logger.info(f"Time-Series Split Summary:")
        logger.info(f"  Total samples: {n}")
        logger.info(f"  Training set: {len(X_train)} samples ({len(X_train)/n*100:.1f}%)")
        logger.info(f"  Validation set: {len(X_val)} samples ({len(X_val)/n*100:.1f}%)")
        logger.info(f"  Test set: {len(X_test)} samples ({len(X_test)/n*100:.1f}%)")
        
        if timestamps is not None and len(timestamps) == n:
            logger.info(f"  Training period: {timestamps[0]} to {timestamps[train_end-1]}")
            logger.info(f"  Validation period: {timestamps[train_end]} to {timestamps[val_end-1]}")
            logger.info(f"  Test period: {timestamps[val_end]} to {timestamps[-1]}")
        
        return X_train, X_val, X_test, y_train, y_val, y_test
    
    def train_all_models(self, city):
        """Train all models for a city using time-series-aware splitting"""
        logger.info(f"Starting training for {city}...")
        
        # Prepare data
        df = self.processor.prepare_training_data(city, days=90)
        if df is None or df.empty:
            logger.error(f"No data available for {city}")
            return False
        
        # Ensure data is sorted by timestamp (critical for time-series split)
        df = df.sort_values('timestamp').reset_index(drop=True)
        logger.info(f"Data sorted by timestamp for {city}")
        
        # Store timestamps for logging
        timestamps = df['timestamp'].values
        
        # Prepare features and target
        feature_cols = [col for col in df.columns 
                       if col not in ['timestamp', 'city', 'data_source', 'id', 'created_at', 'aqi_value']]
        X = df[feature_cols].values
        y = df['aqi_value'].values
        
        # Time-series-aware split (NO SHUFFLING!)
        X_train, X_val, X_test, y_train, y_val, y_test = self.time_series_split(
            X, y, timestamps
        )
        
        # Train models
        results = {}
        
        # Linear Regression
        logger.info("Training Linear Regression...")
        self.models['linear_regression'].train(X_train, y_train)
        metrics_lr = self.models['linear_regression'].evaluate(X_test, y_test)
        results['linear_regression'] = metrics_lr
        self.models['linear_regression'].save_model(f"models/trained_models/{city}_lr.pkl")
        if metrics_lr:
            self.selector.save_performance(city, 'linear_regression', metrics_lr)
        
        # Random Forest
        logger.info("Training Random Forest...")
        self.models['random_forest'].train(X_train, y_train)
        metrics_rf = self.models['random_forest'].evaluate(X_test, y_test)
        results['random_forest'] = metrics_rf
        self.models['random_forest'].save_model(f"models/trained_models/{city}_rf.pkl")
        if metrics_rf:
            self.selector.save_performance(city, 'random_forest', metrics_rf)
        
        # XGBoost
        logger.info("Training XGBoost...")
        self.models['xgboost'].train(X_train, y_train, X_val, y_val)
        metrics_xgb = self.models['xgboost'].evaluate(X_test, y_test)
        results['xgboost'] = metrics_xgb
        self.models['xgboost'].save_model(f"models/trained_models/{city}_xgb.json")
        if metrics_xgb:
            self.selector.save_performance(city, 'xgboost', metrics_xgb)
        
        # LSTM (if available)
        if 'lstm' in self.models:
            logger.info("Training LSTM...")
            X_train_lstm, y_train_lstm = self.models['lstm'].create_sequences(X_train, y_train, 24)
            X_test_lstm, y_test_lstm = self.models['lstm'].create_sequences(X_test, y_test, 24)
            
            self.models['lstm'].train(X_train_lstm, y_train_lstm, X_test_lstm, y_test_lstm)
            metrics_lstm = self.models['lstm'].evaluate(X_test_lstm, y_test_lstm)
            results['lstm'] = metrics_lstm
            self.models['lstm'].save_model(f"models/trained_models/{city}_lstm.h5")
            if metrics_lstm:
                self.selector.save_performance(city, 'lstm', metrics_lstm)
        else:
            logger.info("Skipping LSTM (not available)")
        
        logger.info(f"Training completed for {city}. Results: {results}")
        return results

if __name__ == "__main__":
    trainer = ModelTrainer()
    for city in CITIES:
        trainer.train_all_models(city)
