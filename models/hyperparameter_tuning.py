"""
Hyperparameter Tuning for AQI Prediction Models

Implements both Grid Search and Bayesian Optimization (Optuna)
with time-series cross-validation for proper model tuning.
"""

import numpy as np
import pandas as pd
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import make_scorer, mean_squared_error, r2_score
import logging
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

# Try to import optuna for Bayesian optimization
try:
    import optuna
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    OPTUNA_AVAILABLE = True
except ImportError:
    OPTUNA_AVAILABLE = False
    logger.warning("Optuna not available. Install with: pip install optuna")


class HyperparameterTuner:
    """
    Hyperparameter tuning with Grid Search and Bayesian Optimization
    
    Features:
    - Grid Search: Exhaustive search over parameter grid
    - Bayesian Optimization (Optuna): Smart search using TPE algorithm
    - Time-series cross-validation: Respects temporal ordering
    - Multiple optimization metrics: RMSE, R², MAE
    """
    
    def __init__(self, model_type='random_forest'):
        """
        Initialize tuner
        
        Args:
            model_type: 'random_forest', 'xgboost', or 'stacked_ensemble'
        """
        self.model_type = model_type
        self.best_params = None
        self.best_score = None
        self.tuning_history = []
        
        logger.info(f"HyperparameterTuner initialized for {model_type}")
    
    def get_param_grid(self):
        """Get parameter grid for grid search"""
        if self.model_type == 'random_forest':
            return {
                'n_estimators': [50, 100, 200],
                'max_depth': [10, 20, 30, None],
                'min_samples_split': [2, 5, 10],
                'min_samples_leaf': [1, 2, 4],
                'max_features': ['sqrt', 'log2']
            }
        
        elif self.model_type == 'xgboost':
            return {
                'n_estimators': [50, 100, 200],
                'max_depth': [3, 6, 9],
                'learning_rate': [0.01, 0.1, 0.3],
                'subsample': [0.6, 0.8, 1.0],
                'colsample_bytree': [0.6, 0.8, 1.0],
                'gamma': [0, 0.1, 0.5]
            }
        
        elif self.model_type == 'stacked_ensemble':
            return {
                'final_estimator__alpha': [0.1, 1.0, 10.0],
                'random_forest__n_estimators': [50, 100, 200],
                'random_forest__max_depth': [10, 20, 30],
                'xgboost__n_estimators': [50, 100, 200],
                'xgboost__max_depth': [3, 6, 9]
            }
        
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")
    
    def get_search_space(self, trial):
        """
        Get Optuna search space for Bayesian optimization
        
        Args:
            trial: Optuna trial object
            
        Returns:
            Dictionary of hyperparameters
        """
        if self.model_type == 'random_forest':
            return {
                'n_estimators': trial.suggest_int('n_estimators', 50, 300),
                'max_depth': trial.suggest_int('max_depth', 5, 50),
                'min_samples_split': trial.suggest_int('min_samples_split', 2, 20),
                'min_samples_leaf': trial.suggest_int('min_samples_leaf', 1, 10),
                'max_features': trial.suggest_categorical('max_features', ['sqrt', 'log2', None]),
                'random_state': 42,
                'n_jobs': -1
            }
        
        elif self.model_type == 'xgboost':
            return {
                'n_estimators': trial.suggest_int('n_estimators', 50, 300),
                'max_depth': trial.suggest_int('max_depth', 3, 12),
                'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
                'subsample': trial.suggest_float('subsample', 0.5, 1.0),
                'colsample_bytree': trial.suggest_float('colsample_bytree', 0.5, 1.0),
                'gamma': trial.suggest_float('gamma', 0, 1.0),
                'reg_alpha': trial.suggest_float('reg_alpha', 0, 1.0),
                'reg_lambda': trial.suggest_float('reg_lambda', 0, 1.0),
                'random_state': 42,
                'n_jobs': -1
            }
        
        elif self.model_type == 'stacked_ensemble':
            return {
                'meta_alpha': trial.suggest_float('meta_alpha', 0.01, 10.0, log=True),
                'rf_n_estimators': trial.suggest_int('rf_n_estimators', 50, 200),
                'rf_max_depth': trial.suggest_int('rf_max_depth', 5, 30),
                'xgb_n_estimators': trial.suggest_int('xgb_n_estimators', 50, 200),
                'xgb_max_depth': trial.suggest_int('xgb_max_depth', 3, 9),
                'xgb_learning_rate': trial.suggest_float('xgb_learning_rate', 0.01, 0.3, log=True)
            }
        
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")
    
    def grid_search(self, model, X, y, cv, scoring='neg_root_mean_squared_error'):
        """
        Perform grid search with cross-validation
        
        Args:
            model: Base model to tune
            X: Training features
            y: Training targets
            cv: Cross-validation splitter (use TimeSeriesCV)
            scoring: Scoring metric
            
        Returns:
            Best parameters and score
        """
        logger.info("=" * 60)
        logger.info("Starting Grid Search Hyperparameter Tuning")
        logger.info("=" * 60)
        
        param_grid = self.get_param_grid()
        
        # Calculate total combinations
        total_combinations = np.prod([len(v) for v in param_grid.values()])
        logger.info(f"Searching {total_combinations} parameter combinations...")
        
        # Create GridSearchCV
        grid_search = GridSearchCV(
            estimator=model,
            param_grid=param_grid,
            cv=cv,
            scoring=scoring,
            n_jobs=-1,
            verbose=1,
            return_train_score=True
        )
        
        # Fit
        grid_search.fit(X, y)
        
        # Store results
        self.best_params = grid_search.best_params_
        self.best_score = -grid_search.best_score_  # Convert back from negative
        
        logger.info("=" * 60)
        logger.info("Grid Search Results:")
        logger.info(f"  Best RMSE: {self.best_score:.2f}")
        logger.info(f"  Best Parameters:")
        for param, value in self.best_params.items():
            logger.info(f"    {param}: {value}")
        logger.info("=" * 60)
        
        return {
            'best_params': self.best_params,
            'best_score': self.best_score,
            'cv_results': grid_search.cv_results_
        }
    
    def bayesian_optimization(self, model_class, X, y, cv, n_trials=50, 
                             metric='rmse', direction='minimize'):
        """
        Perform Bayesian optimization using Optuna
        
        Args:
            model_class: Model class (not instance) to instantiate with params
            X: Training features
            y: Training targets
            cv: Cross-validation splitter
            n_trials: Number of optimization trials
            metric: Optimization metric ('rmse', 'r2', 'mae')
            direction: 'minimize' or 'maximize'
            
        Returns:
            Best parameters and score
        """
        if not OPTUNA_AVAILABLE:
            logger.error("Optuna not available. Install with: pip install optuna")
            return None
        
        logger.info("=" * 60)
        logger.info("Starting Bayesian Optimization (Optuna)")
        logger.info("=" * 60)
        logger.info(f"Trials: {n_trials}, Metric: {metric}, Direction: {direction}")
        
        def objective(trial):
            """Objective function for Optuna"""
            # Get hyperparameters for this trial
            params = self.get_search_space(trial)
            
            # Handle stacked ensemble separately
            if self.model_type == 'stacked_ensemble':
                from ml_models.stacked_ensemble import StackedEnsembleAQI
                from sklearn.ensemble import RandomForestRegressor
                from xgboost import XGBRegressor
                from sklearn.linear_model import LinearRegression, Ridge
                
                base_models = {
                    'linear_regression': LinearRegression(),
                    'random_forest': RandomForestRegressor(
                        n_estimators=params['rf_n_estimators'],
                        max_depth=params['rf_max_depth'],
                        random_state=42,
                        n_jobs=-1
                    ),
                    'xgboost': XGBRegressor(
                        n_estimators=params['xgb_n_estimators'],
                        max_depth=params['xgb_max_depth'],
                        learning_rate=params['xgb_learning_rate'],
                        random_state=42,
                        n_jobs=-1
                    )
                }
                meta_learner = Ridge(alpha=params['meta_alpha'])
                model = StackedEnsembleAQI(base_models=base_models, meta_learner=meta_learner)
            else:
                # Create model with hyperparameters
                model = model_class(**params)
            
            # Cross-validation scores
            scores = []
            for train_idx, val_idx in cv.split(X, y):
                if isinstance(X, pd.DataFrame):
                    X_train_fold = X.iloc[train_idx]
                    X_val_fold = X.iloc[val_idx]
                else:
                    X_train_fold = X[train_idx]
                    X_val_fold = X[val_idx]
                
                y_train_fold = y[train_idx]
                y_val_fold = y[val_idx]
                
                # Train and predict
                if hasattr(model, 'fit'):
                    model.fit(X_train_fold, y_train_fold)
                else:
                    model.train(X_train_fold, y_train_fold)
                
                y_pred = model.predict(X_val_fold)
                
                # Calculate metric
                if metric == 'rmse':
                    score = np.sqrt(mean_squared_error(y_val_fold, y_pred))
                elif metric == 'r2':
                    score = r2_score(y_val_fold, y_pred)
                elif metric == 'mae':
                    from sklearn.metrics import mean_absolute_error
                    score = mean_absolute_error(y_val_fold, y_pred)
                else:
                    raise ValueError(f"Unknown metric: {metric}")
                
                scores.append(score)
            
            # Return mean score
            return np.mean(scores)
        
        # Create Optuna study
        study = optuna.create_study(direction=direction)
        study.optimize(objective, n_trials=n_trials, show_progress_bar=True)
        
        # Store results
        self.best_params = study.best_params
        self.best_score = study.best_value
        self.tuning_history = [(trial.params, trial.value) for trial in study.trials]
        
        logger.info("=" * 60)
        logger.info("Bayesian Optimization Results:")
        logger.info(f"  Best {metric}: {self.best_score:.4f}")
        logger.info(f"  Best Parameters:")
        for param, value in self.best_params.items():
            logger.info(f"    {param}: {value}")
        logger.info(f"  Total trials: {len(study.trials)}")
        logger.info("=" * 60)
        
        return {
            'best_params': self.best_params,
            'best_score': self.best_score,
            'study': study,
            'history': self.tuning_history
        }


if __name__ == "__main__":
    # Test with synthetic data
    from sklearn.ensemble import RandomForestRegressor
    from models.time_series_cv import TimeSeriesCV
    from datetime import datetime, timedelta
    
    print("Testing Hyperparameter Tuning...")
    print("=" * 60)
    
    # Generate synthetic time-series data
    n_samples = 500
    start_date = datetime.now() - timedelta(days=500)
    timestamps = [start_date + timedelta(hours=i) for i in range(n_samples)]
    
    hours = np.array([t.hour for t in timestamps])
    X = np.column_stack([
        hours,
        np.sin(hours * 2 * np.pi / 24),
        np.cos(hours * 2 * np.pi / 24),
        np.random.randn(n_samples)
    ])
    y = 50 + 20 * np.sin(hours * 2 * np.pi / 24) + np.random.randn(n_samples) * 5
    
    # Create time-series CV
    cv = TimeSeriesCV(n_splits=3, expanding=True)
    
    # Test Grid Search (small grid for testing)
    print("\n1. Testing Grid Search:")
    tuner_grid = HyperparameterTuner(model_type='random_forest')
    
    # Use smaller grid for testing
    small_param_grid = {
        'n_estimators': [50, 100],
        'max_depth': [10, 20],
        'min_samples_split': [2, 5]
    }
    
    model_rf = RandomForestRegressor(random_state=42, n_jobs=-1)
    # results_grid = tuner_grid.grid_search(model_rf, X, y, cv)
    print("   Grid search test skipped (use full version for actual tuning)")
    
    # Test Bayesian Optimization
    if OPTUNA_AVAILABLE:
        print("\n2. Testing Bayesian Optimization:")
        tuner_bayes = HyperparameterTuner(model_type='random_forest')
        results_bayes = tuner_bayes.bayesian_optimization(
            RandomForestRegressor, X, y, cv, 
            n_trials=10, metric='rmse', direction='minimize'
        )
        print(f"   Best RMSE: {results_bayes['best_score']:.2f}")
    else:
        print("\n2. Bayesian Optimization not available (install optuna)")
    
    print("\n✅ Hyperparameter tuning test complete!")
