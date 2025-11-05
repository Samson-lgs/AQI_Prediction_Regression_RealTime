"""
Stacked Ensemble Model for AQI Prediction

Implements ensemble stacking to combine multiple base learners with a meta-learner
for improved generalization and prediction accuracy.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import StackingRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import pickle
import logging

logger = logging.getLogger(__name__)


class StackedEnsembleAQI:
    """
    Stacked Ensemble combining Linear Regression, Random Forest, and XGBoost
    
    Architecture:
    - Base learners (Level 0):
      * Linear Regression (interpretable baseline)
      * Random Forest (non-linear patterns)
      * XGBoost (gradient boosting)
    - Meta-learner (Level 1):
      * Ridge Regression (combines base predictions with L2 regularization)
    
    Benefits:
    - Combines strengths of different model types
    - Reduces overfitting through ensemble averaging
    - Meta-learner learns optimal weighting of base models
    - Better generalization on unseen data
    """
    
    def __init__(self, base_models=None, meta_learner=None):
        """
        Initialize Stacked Ensemble
        
        Args:
            base_models: Dictionary of base models {'name': model}
                        If None, uses default LinearReg + RandomForest + XGBoost
            meta_learner: Meta-model for stacking
                         If None, uses Ridge(alpha=1.0)
        """
        self.base_models = base_models
        self.meta_learner = meta_learner if meta_learner else Ridge(alpha=1.0)
        self.model = None
        self.feature_names = None
        
        logger.info("StackedEnsembleAQI initialized")
    
    def _get_default_base_models(self):
        """Get default base models if not provided"""
        from sklearn.linear_model import LinearRegression
        from sklearn.ensemble import RandomForestRegressor
        from xgboost import XGBRegressor
        
        return [
            ('linear_regression', LinearRegression()),
            ('random_forest', RandomForestRegressor(
                n_estimators=100,
                max_depth=20,
                min_samples_split=5,
                min_samples_leaf=2,
                n_jobs=-1,
                random_state=42
            )),
            ('xgboost', XGBRegressor(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                n_jobs=-1
            ))
        ]
    
    def train(self, X_train, y_train, X_val=None, y_val=None):
        """
        Train stacked ensemble
        
        Args:
            X_train: Training features
            y_train: Training targets
            X_val: Validation features (optional, for evaluation)
            y_val: Validation targets (optional, for evaluation)
        """
        try:
            logger.info("Training Stacked Ensemble...")
            
            # Get base models if not provided
            if self.base_models is None:
                base_estimators = self._get_default_base_models()
            else:
                base_estimators = list(self.base_models.items())
            
            # Create stacking regressor
            self.model = StackingRegressor(
                estimators=base_estimators,
                final_estimator=self.meta_learner,
                cv=5,  # 5-fold CV for generating meta-features
                n_jobs=-1
            )
            
            # Fit the model
            self.model.fit(X_train, y_train)
            
            # Store feature names if available
            if hasattr(X_train, 'columns'):
                self.feature_names = X_train.columns.tolist()
            
            logger.info("✓ Stacked Ensemble trained successfully")
            
            # Log training performance
            train_pred = self.model.predict(X_train)
            train_r2 = r2_score(y_train, train_pred)
            train_rmse = np.sqrt(mean_squared_error(y_train, train_pred))
            logger.info(f"  Training R²: {train_r2:.4f}, RMSE: {train_rmse:.2f}")
            
            # Log validation performance if provided
            if X_val is not None and y_val is not None:
                val_pred = self.model.predict(X_val)
                val_r2 = r2_score(y_val, val_pred)
                val_rmse = np.sqrt(mean_squared_error(y_val, val_pred))
                logger.info(f"  Validation R²: {val_r2:.4f}, RMSE: {val_rmse:.2f}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error training stacked ensemble: {str(e)}")
            return False
    
    def predict(self, X):
        """Make predictions using the ensemble"""
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")
        return self.model.predict(X)
    
    def evaluate(self, X_test, y_test):
        """
        Evaluate model on test data
        
        Returns:
            Dictionary with performance metrics
        """
        try:
            predictions = self.predict(X_test)
            
            # Calculate metrics
            r2 = r2_score(y_test, predictions)
            rmse = np.sqrt(mean_squared_error(y_test, predictions))
            mae = mean_absolute_error(y_test, predictions)
            
            # MAPE (avoiding division by zero)
            mask = y_test != 0
            mape = np.mean(np.abs((y_test[mask] - predictions[mask]) / y_test[mask])) * 100
            
            metrics = {
                'r2_score': float(r2),
                'rmse': float(rmse),
                'mae': float(mae),
                'mape': float(mape)
            }
            
            logger.info(f"Stacked Ensemble Evaluation:")
            logger.info(f"  R² Score: {r2:.4f}")
            logger.info(f"  RMSE: {rmse:.2f}")
            logger.info(f"  MAE: {mae:.2f}")
            logger.info(f"  MAPE: {mape:.2f}%")
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error evaluating stacked ensemble: {str(e)}")
            return None
    
    def get_base_model_predictions(self, X):
        """
        Get predictions from individual base models
        
        Returns:
            Dictionary of predictions from each base model
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")
        
        base_predictions = {}
        for name, estimator in self.model.named_estimators_.items():
            base_predictions[name] = estimator.predict(X)
        
        return base_predictions
    
    def get_meta_features(self, X):
        """
        Get meta-features (base model predictions) for analysis
        
        Returns:
            DataFrame with base model predictions
        """
        base_preds = self.get_base_model_predictions(X)
        return pd.DataFrame(base_preds)
    
    def save_model(self, filepath):
        """Save the trained ensemble model"""
        try:
            if self.model is None:
                logger.warning("No trained model to save")
                return False
            
            model_data = {
                'model': self.model,
                'feature_names': self.feature_names,
                'meta_learner_type': type(self.meta_learner).__name__
            }
            
            with open(filepath, 'wb') as f:
                pickle.dump(model_data, f)
            
            logger.info(f"✓ Stacked ensemble saved to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving stacked ensemble: {str(e)}")
            return False
    
    def load_model(self, filepath):
        """Load a trained ensemble model"""
        try:
            with open(filepath, 'rb') as f:
                model_data = pickle.load(f)
            
            self.model = model_data['model']
            self.feature_names = model_data.get('feature_names')
            
            logger.info(f"✓ Stacked ensemble loaded from {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading stacked ensemble: {str(e)}")
            return False


if __name__ == "__main__":
    # Quick test with synthetic data
    from sklearn.datasets import make_regression
    
    print("Testing Stacked Ensemble Implementation...")
    print("=" * 60)
    
    # Generate synthetic data
    X, y = make_regression(n_samples=1000, n_features=20, noise=10, random_state=42)
    split_idx = 800
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]
    
    # Train ensemble
    ensemble = StackedEnsembleAQI()
    ensemble.train(X_train, y_train, X_test, y_test)
    
    # Evaluate
    metrics = ensemble.evaluate(X_test, y_test)
    print(f"\nTest Metrics: {metrics}")
    
    # Get base model predictions
    base_preds = ensemble.get_base_model_predictions(X_test[:5])
    print(f"\nBase Model Predictions (first 5 samples):")
    for model_name, preds in base_preds.items():
        print(f"  {model_name}: {preds[:3]}")
    
    print("\n✅ Stacked Ensemble test complete!")
