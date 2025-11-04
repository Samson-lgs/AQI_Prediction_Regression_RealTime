import numpy as np
from sklearn.model_selection import train_test_split
from feature_engineering.feature_processor import FeatureProcessor
from ml_models.linear_regression_model import LinearRegressionAQI
from ml_models.random_forest_model import RandomForestAQI
from ml_models.xgboost_model import XGBoostAQI
from ml_models.lstm_model import LSTMAQI
from config.settings import CITIES
from models.model_utils import ModelSelector
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelTrainer:
    def __init__(self):
        self.processor = FeatureProcessor()
        self.models = {
            'linear_regression': LinearRegressionAQI(),
            'random_forest': RandomForestAQI(),
            'xgboost': XGBoostAQI(),
            'lstm': LSTMAQI()
        }
        self.selector = ModelSelector()
    
    def train_all_models(self, city):
        """Train all models for a city"""
        logger.info(f"Starting training for {city}...")
        
        # Prepare data
        df = self.processor.prepare_training_data(city, days=90)
        if df is None or df.empty:
            logger.error(f"No data available for {city}")
            return False
        
        # Prepare features and target
        feature_cols = [col for col in df.columns 
                       if col not in ['timestamp', 'city', 'data_source', 'id', 'created_at', 'aqi_value']]
        X = df[feature_cols].values
        y = df['aqi_value'].values
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        X_train, X_val, y_train, y_val = train_test_split(
            X_train, y_train, test_size=0.2, random_state=42
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
        
        # LSTM
        logger.info("Training LSTM...")
        X_train_lstm, y_train_lstm = self.models['lstm'].create_sequences(X_train, y_train, 24)
        X_test_lstm, y_test_lstm = self.models['lstm'].create_sequences(X_test, y_test, 24)
        
        self.models['lstm'].train(X_train_lstm, y_train_lstm, X_test_lstm, y_test_lstm)
        metrics_lstm = self.models['lstm'].evaluate(X_test_lstm, y_test_lstm)
        results['lstm'] = metrics_lstm
        self.models['lstm'].save_model(f"models/trained_models/{city}_lstm.h5")
        if metrics_lstm:
            self.selector.save_performance(city, 'lstm', metrics_lstm)
        
        logger.info(f"Training completed for {city}. Results: {results}")
        return results

if __name__ == "__main__":
    trainer = ModelTrainer()
    for city in CITIES:
        trainer.train_all_models(city)
