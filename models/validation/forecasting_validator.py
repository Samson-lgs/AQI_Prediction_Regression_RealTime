"""
Forecasting Validation Module

Assesses 1–48 hour forecasting accuracy using time-series hold-out strategies.
Evaluates model performance across different forecast horizons.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ForecastingValidator:
    """
    Validates models for multi-horizon forecasting (1-48 hours ahead)
    
    Key Features:
    - Rolling forecast validation
    - Multiple forecast horizons (1h, 6h, 12h, 24h, 48h)
    - Walk-forward validation (train → predict → update)
    - Horizon-specific metrics
    """
    
    def __init__(self, horizons: List[int] = None):
        """
        Initialize Forecasting Validator
        
        Args:
            horizons: List of forecast horizons in hours
                     Default: [1, 6, 12, 24, 48]
        """
        self.horizons = horizons or [1, 6, 12, 24, 48]
        self.results = {}
        
        logger.info(f"ForecastingValidator initialized for horizons: {self.horizons} hours")
    
    def prepare_forecast_data(
        self,
        data: pd.DataFrame,
        horizon: int,
        feature_cols: List[str],
        target_col: str = 'aqi_value'
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Prepare data for specific forecast horizon
        
        Creates features at time t to predict target at time t+horizon
        
        Args:
            data: Time-series dataframe (sorted by timestamp)
            horizon: Number of hours ahead to forecast
            feature_cols: List of feature column names
            target_col: Target column name
        
        Returns:
            X (features at time t), y (target at time t+horizon)
        """
        # Ensure data is sorted by timestamp
        if 'timestamp' in data.columns:
            data = data.sort_values('timestamp').reset_index(drop=True)
        
        # Create shifted target (future value)
        y = data[target_col].shift(-horizon)
        
        # Remove last 'horizon' rows (no future target available)
        X = data[feature_cols].iloc[:-horizon]
        y = y.iloc[:-horizon]
        
        # Remove any NaN values
        mask = ~y.isna()
        X = X[mask]
        y = y[mask]
        
        logger.info(f"Prepared forecast data for horizon={horizon}h: {len(X)} samples")
        
        return X, y
    
    def rolling_forecast_validation(
        self,
        model: Any,
        data: pd.DataFrame,
        horizon: int,
        feature_cols: List[str],
        target_col: str = 'aqi_value',
        initial_train_size: int = 500,
        step_size: int = 24
    ) -> Dict[str, Any]:
        """
        Perform rolling (walk-forward) forecast validation
        
        Process:
        1. Train on initial window
        2. Forecast next horizon
        3. Move window forward
        4. Repeat
        
        Args:
            model: Model to validate
            data: Time-series dataframe
            horizon: Forecast horizon in hours
            feature_cols: Feature columns
            target_col: Target column
            initial_train_size: Initial training window size
            step_size: How many samples to advance at each step
        
        Returns:
            Dictionary with metrics and predictions
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"Rolling Forecast Validation - Horizon: {horizon}h")
        logger.info(f"{'='*60}")
        
        # Prepare forecast data
        X, y = self.prepare_forecast_data(data, horizon, feature_cols, target_col)
        
        if len(X) < initial_train_size + step_size:
            raise ValueError(f"Not enough data for rolling validation. "
                           f"Need at least {initial_train_size + step_size} samples")
        
        # Initialize tracking
        y_true_list = []
        y_pred_list = []
        forecast_times = []
        
        # Get timestamps if available
        if 'timestamp' in data.columns:
            timestamps = data['timestamp'].iloc[:-horizon].values
        else:
            timestamps = None
        
        # Rolling window iteration
        current_pos = initial_train_size
        n_forecasts = 0
        
        while current_pos + step_size <= len(X):
            # Define train window
            train_start = max(0, current_pos - initial_train_size)
            train_end = current_pos
            
            # Define test window (next step_size samples)
            test_start = current_pos
            test_end = min(current_pos + step_size, len(X))
            
            # Get train and test data
            X_train = X.iloc[train_start:train_end]
            y_train = y.iloc[train_start:train_end]
            X_test = X.iloc[test_start:test_end]
            y_test = y.iloc[test_start:test_end]
            
            # Train model (clone for each iteration)
            from sklearn.base import clone
            model_clone = clone(model)
            
            if hasattr(model_clone, 'fit'):
                model_clone.fit(X_train, y_train)
            elif hasattr(model_clone, 'train'):
                model_clone.train(X_train, y_train)
            
            # Forecast
            y_pred = model_clone.predict(X_test)
            y_pred = np.maximum(y_pred, 0)  # Ensure non-negative
            
            # Store results
            y_true_list.extend(y_test.values)
            y_pred_list.extend(y_pred)
            
            if timestamps is not None:
                forecast_times.extend(timestamps[test_start:test_end])
            
            n_forecasts += len(y_test)
            
            # Move window forward
            current_pos += step_size
            
            if n_forecasts % 100 == 0:
                logger.info(f"  Processed {n_forecasts} forecasts...")
        
        # Convert to arrays
        y_true = np.array(y_true_list)
        y_pred = np.array(y_pred_list)
        
        # Calculate metrics
        metrics = self._calculate_forecast_metrics(y_true, y_pred, horizon)
        metrics['n_forecasts'] = n_forecasts
        metrics['forecast_times'] = forecast_times
        metrics['predictions'] = y_pred
        metrics['actuals'] = y_true
        
        logger.info(f"\nRolling Forecast Results ({horizon}h ahead):")
        logger.info(f"  Total Forecasts: {n_forecasts}")
        logger.info(f"  R² Score:  {metrics['r2']:.4f}")
        logger.info(f"  RMSE:      {metrics['rmse']:.2f}")
        logger.info(f"  MAE:       {metrics['mae']:.2f}")
        logger.info(f"  MAPE:      {metrics['mape']:.2f}%")
        
        return metrics
    
    def multi_horizon_validation(
        self,
        models: Dict[str, Any],
        data: pd.DataFrame,
        feature_cols: List[str],
        target_col: str = 'aqi_value',
        city: str = None
    ) -> Dict[str, Dict[int, Dict[str, Any]]]:
        """
        Validate all models across all forecast horizons
        
        Args:
            models: Dictionary of {model_name: model}
            data: Time-series dataframe
            feature_cols: Feature columns
            target_col: Target column
            city: Optional city name for filtering
        
        Returns:
            Nested dictionary: {model_name: {horizon: metrics}}
        """
        # Filter by city if specified
        if city and 'city' in data.columns:
            data = data[data['city'] == city].copy()
            logger.info(f"Filtered data for city: {city}")
        
        # Ensure temporal ordering
        if 'timestamp' in data.columns:
            data = data.sort_values('timestamp').reset_index(drop=True)
        
        results = {}
        
        for model_name, model in models.items():
            logger.info(f"\n{'#'*60}")
            logger.info(f"# VALIDATING MODEL: {model_name.upper()}")
            logger.info(f"{'#'*60}")
            
            model_results = {}
            
            for horizon in self.horizons:
                try:
                    # Validate for this horizon
                    horizon_metrics = self.rolling_forecast_validation(
                        model, data, horizon, feature_cols, target_col
                    )
                    
                    model_results[horizon] = horizon_metrics
                    
                except Exception as e:
                    logger.error(f"Error validating {model_name} at horizon {horizon}h: {str(e)}")
                    model_results[horizon] = {'error': str(e)}
            
            results[model_name] = model_results
        
        self.results = results
        return results
    
    def validate_single_horizon(
        self,
        model: Any,
        data: pd.DataFrame,
        horizon: int,
        feature_cols: List[str],
        target_col: str = 'aqi_value',
        test_size: float = 0.2
    ) -> Dict[str, Any]:
        """
        Simple train/test split validation for a single horizon
        
        Args:
            model: Model to validate
            data: Time-series dataframe
            horizon: Forecast horizon in hours
            feature_cols: Feature columns
            target_col: Target column
            test_size: Fraction of data for testing
        
        Returns:
            Dictionary with metrics
        """
        # Prepare forecast data
        X, y = self.prepare_forecast_data(data, horizon, feature_cols, target_col)
        
        # Temporal split
        split_idx = int(len(X) * (1 - test_size))
        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
        
        logger.info(f"Single horizon validation: {len(X_train)} train, {len(X_test)} test")
        
        # Train
        if hasattr(model, 'fit'):
            model.fit(X_train, y_train)
        elif hasattr(model, 'train'):
            model.train(X_train, y_train)
        
        # Predict
        y_pred = model.predict(X_test)
        y_pred = np.maximum(y_pred, 0)
        
        # Calculate metrics
        metrics = self._calculate_forecast_metrics(
            y_test.values, y_pred, horizon
        )
        
        return metrics
    
    def _calculate_forecast_metrics(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        horizon: int
    ) -> Dict[str, float]:
        """
        Calculate comprehensive forecast metrics
        
        Args:
            y_true: Actual values
            y_pred: Predicted values
            horizon: Forecast horizon (for context)
        
        Returns:
            Dictionary of metrics
        """
        # Handle NaN values
        mask = ~(np.isnan(y_true) | np.isnan(y_pred))
        y_true = y_true[mask]
        y_pred = y_pred[mask]
        
        # Basic metrics
        r2 = r2_score(y_true, y_pred)
        rmse = np.sqrt(mean_squared_error(y_true, y_pred))
        mae = mean_absolute_error(y_true, y_pred)
        
        # MAPE (handle zeros)
        mask_nonzero = y_true != 0
        if np.sum(mask_nonzero) > 0:
            mape = np.mean(np.abs((y_true[mask_nonzero] - y_pred[mask_nonzero]) / 
                                  y_true[mask_nonzero])) * 100
        else:
            mape = np.nan
        
        # Forecast-specific metrics
        # Directional accuracy (did we predict increase/decrease correctly?)
        if len(y_true) > 1:
            true_direction = np.diff(y_true) > 0
            pred_direction = np.diff(y_pred) > 0
            directional_accuracy = np.mean(true_direction == pred_direction) * 100
        else:
            directional_accuracy = np.nan
        
        # Bias (systematic over/under prediction)
        bias = np.mean(y_pred - y_true)
        
        # Skill score (vs. persistence model)
        # Persistence: predict that next value = current value
        if len(y_true) > horizon:
            persistence_pred = y_true[:-horizon]
            persistence_actual = y_true[horizon:]
            persistence_rmse = np.sqrt(mean_squared_error(persistence_actual, persistence_pred))
            skill_score = (1 - rmse / persistence_rmse) * 100 if persistence_rmse > 0 else np.nan
        else:
            skill_score = np.nan
        
        return {
            'horizon': horizon,
            'r2': float(r2),
            'rmse': float(rmse),
            'mae': float(mae),
            'mape': float(mape) if not np.isnan(mape) else None,
            'directional_accuracy': float(directional_accuracy) if not np.isnan(directional_accuracy) else None,
            'bias': float(bias),
            'skill_score': float(skill_score) if not np.isnan(skill_score) else None,
            'n_samples': len(y_true)
        }
    
    def generate_summary(self) -> pd.DataFrame:
        """
        Generate summary table of forecast validation results
        
        Returns:
            DataFrame with model x horizon performance matrix
        """
        if not self.results:
            logger.warning("No results available. Run multi_horizon_validation() first.")
            return pd.DataFrame()
        
        summary_data = []
        
        for model_name, horizon_results in self.results.items():
            for horizon, metrics in horizon_results.items():
                if 'error' not in metrics:
                    summary_data.append({
                        'Model': model_name,
                        'Horizon (h)': horizon,
                        'R²': metrics['r2'],
                        'RMSE': metrics['rmse'],
                        'MAE': metrics['mae'],
                        'MAPE': metrics.get('mape'),
                        'Dir. Accuracy': metrics.get('directional_accuracy'),
                        'Bias': metrics['bias'],
                        'Skill Score': metrics.get('skill_score'),
                        'Forecasts': metrics['n_samples']
                    })
        
        df = pd.DataFrame(summary_data)
        
        # Sort by Model and Horizon
        if not df.empty:
            df = df.sort_values(['Model', 'Horizon (h)'])
        
        return df
    
    def plot_forecast_performance(self, model_name: str = None):
        """
        Plot forecast performance across horizons
        
        Args:
            model_name: Specific model to plot (None = all models)
        """
        try:
            import matplotlib.pyplot as plt
            
            fig, axes = plt.subplots(2, 2, figsize=(14, 10))
            fig.suptitle('Forecast Performance Across Horizons', fontsize=16)
            
            models_to_plot = [model_name] if model_name else list(self.results.keys())
            
            for model in models_to_plot:
                if model not in self.results:
                    continue
                
                horizons = []
                rmse_vals = []
                mae_vals = []
                r2_vals = []
                
                for horizon, metrics in sorted(self.results[model].items()):
                    if 'error' not in metrics:
                        horizons.append(horizon)
                        rmse_vals.append(metrics['rmse'])
                        mae_vals.append(metrics['mae'])
                        r2_vals.append(metrics['r2'])
                
                # Plot RMSE
                axes[0, 0].plot(horizons, rmse_vals, marker='o', label=model)
                axes[0, 0].set_xlabel('Forecast Horizon (hours)')
                axes[0, 0].set_ylabel('RMSE')
                axes[0, 0].set_title('RMSE vs. Forecast Horizon')
                axes[0, 0].legend()
                axes[0, 0].grid(True)
                
                # Plot MAE
                axes[0, 1].plot(horizons, mae_vals, marker='o', label=model)
                axes[0, 1].set_xlabel('Forecast Horizon (hours)')
                axes[0, 1].set_ylabel('MAE')
                axes[0, 1].set_title('MAE vs. Forecast Horizon')
                axes[0, 1].legend()
                axes[0, 1].grid(True)
                
                # Plot R²
                axes[1, 0].plot(horizons, r2_vals, marker='o', label=model)
                axes[1, 0].set_xlabel('Forecast Horizon (hours)')
                axes[1, 0].set_ylabel('R² Score')
                axes[1, 0].set_title('R² vs. Forecast Horizon')
                axes[1, 0].legend()
                axes[1, 0].grid(True)
            
            # Remove empty subplot
            fig.delaxes(axes[1, 1])
            
            plt.tight_layout()
            plt.savefig('models/validation/forecast_performance.png', dpi=300, bbox_inches='tight')
            logger.info("Forecast performance plot saved to models/validation/forecast_performance.png")
            plt.close()
            
        except ImportError:
            logger.warning("Matplotlib not available for plotting")


if __name__ == "__main__":
    # Test with synthetic time-series data
    print("Testing ForecastingValidator...")
    print("=" * 60)
    
    # Create synthetic time-series data
    np.random.seed(42)
    n_samples = 1000
    
    timestamps = pd.date_range('2025-01-01', periods=n_samples, freq='H')
    hours = timestamps.hour.values
    
    # Create temporal pattern
    data = pd.DataFrame({
        'timestamp': timestamps,
        'pm25': 50 + 30 * np.sin(hours * 2 * np.pi / 24) + np.random.randn(n_samples) * 10,
        'pm10': 70 + 40 * np.sin(hours * 2 * np.pi / 24) + np.random.randn(n_samples) * 15,
        'temperature': 20 + 10 * np.sin(hours * 2 * np.pi / 24) + np.random.randn(n_samples) * 3,
        'humidity': 60 + 20 * np.cos(hours * 2 * np.pi / 24) + np.random.randn(n_samples) * 5,
    })
    
    # Target = function of features + temporal pattern
    data['aqi_value'] = (
        0.5 * data['pm25'] + 
        0.3 * data['pm10'] + 
        20 * np.sin(hours * 2 * np.pi / 24) +
        np.random.randn(n_samples) * 5
    )
    
    feature_cols = ['pm25', 'pm10', 'temperature', 'humidity']
    
    # Initialize validator
    validator = ForecastingValidator(horizons=[1, 6, 12])
    
    # Test prepare_forecast_data
    print("\n1. Testing prepare_forecast_data...")
    X, y = validator.prepare_forecast_data(data, horizon=6, feature_cols=feature_cols)
    print(f"   ✓ Data prepared: {len(X)} samples for 6h forecast")
    
    # Test with a simple model
    print("\n2. Testing validation with LinearRegression...")
    from sklearn.linear_model import LinearRegression
    
    model = LinearRegression()
    metrics = validator.validate_single_horizon(
        model, data, horizon=6, feature_cols=feature_cols
    )
    print(f"   ✓ Validation complete: R²={metrics['r2']:.4f}, RMSE={metrics['rmse']:.2f}")
    
    print("\n✅ ForecastingValidator test complete!")
