"""
Time Series Cross-Validation for AQI Prediction

Implements rolling window cross-validation that respects temporal ordering
and prevents data leakage for time-series model validation.
"""

import numpy as np
import pandas as pd
from typing import Generator, Tuple
import logging

logger = logging.getLogger(__name__)


class TimeSeriesCV:
    """
    Rolling window cross-validation for time-series data
    
    Unlike standard k-fold CV, this:
    - Respects temporal ordering (no shuffling)
    - Training data always precedes validation data
    - Uses expanding or rolling window approach
    - Prevents future data leakage
    
    Example with 5 splits (expanding window):
        Split 1: Train [0:100]  → Val [100:120]
        Split 2: Train [0:120]  → Val [120:140]
        Split 3: Train [0:140]  → Val [140:160]
        Split 4: Train [0:160]  → Val [160:180]
        Split 5: Train [0:180]  → Val [180:200]
    """
    
    def __init__(self, n_splits=5, test_size=None, gap=0, expanding=True):
        """
        Initialize Time Series Cross-Validator
        
        Args:
            n_splits: Number of CV splits
            test_size: Size of validation set (if None, auto-calculated)
            gap: Number of samples to skip between train and validation
                 (useful to account for autocorrelation)
            expanding: If True, training window expands (default)
                      If False, uses fixed rolling window
        """
        self.n_splits = n_splits
        self.test_size = test_size
        self.gap = gap
        self.expanding = expanding
        
        logger.info(f"TimeSeriesCV initialized: {n_splits} splits, "
                   f"{'expanding' if expanding else 'rolling'} window, gap={gap}")
    
    def split(self, X, y=None, timestamps=None) -> Generator[Tuple[np.ndarray, np.ndarray], None, None]:
        """
        Generate train/validation indices for time-series CV
        
        Args:
            X: Feature array or DataFrame
            y: Target array (optional)
            timestamps: Timestamp array for logging (optional)
            
        Yields:
            train_indices, val_indices for each split
        """
        n_samples = len(X)
        
        # Calculate test size if not provided
        if self.test_size is None:
            # Use approximately 15% of data for each validation set
            test_size = max(1, n_samples // (self.n_splits + 5))
        else:
            test_size = self.test_size
        
        # Calculate minimum training size
        min_train_size = n_samples - (self.n_splits * test_size) - (self.n_splits * self.gap)
        
        if min_train_size < 1:
            raise ValueError(f"Not enough data for {self.n_splits} splits. "
                           f"Need at least {self.n_splits * (test_size + self.gap)} samples")
        
        logger.info(f"Time Series CV: {n_samples} samples, {test_size} val samples per split")
        
        for i in range(self.n_splits):
            # Calculate validation set boundaries
            val_end = n_samples - (self.n_splits - i - 1) * test_size
            val_start = val_end - test_size
            
            # Calculate training set end (considering gap)
            train_end = val_start - self.gap
            
            # Calculate training set start
            if self.expanding:
                # Expanding window: use all data from beginning
                train_start = 0
            else:
                # Rolling window: use fixed window size
                train_start = max(0, train_end - min_train_size)
            
            # Create indices
            train_indices = np.arange(train_start, train_end)
            val_indices = np.arange(val_start, val_end)
            
            # Log split information
            if timestamps is not None and len(timestamps) == n_samples:
                logger.info(f"\nSplit {i+1}/{self.n_splits}:")
                logger.info(f"  Train: {train_start} to {train_end-1} "
                          f"({len(train_indices)} samples) "
                          f"[{timestamps[train_start]} to {timestamps[train_end-1]}]")
                logger.info(f"  Val:   {val_start} to {val_end-1} "
                          f"({len(val_indices)} samples) "
                          f"[{timestamps[val_start]} to {timestamps[val_end-1]}]")
            else:
                logger.info(f"Split {i+1}/{self.n_splits}: "
                          f"Train [{train_start}:{train_end}], "
                          f"Val [{val_start}:{val_end}]")
            
            yield train_indices, val_indices
    
    def get_n_splits(self, X=None, y=None, groups=None):
        """Return the number of splits"""
        return self.n_splits


def validate_with_time_series_cv(model, X, y, timestamps=None, n_splits=5, 
                                   gap=0, expanding=True):
    """
    Perform time-series cross-validation and return metrics
    
    Args:
        model: Model with fit() and predict() methods
        X: Features
        y: Target values
        timestamps: Optional timestamps for logging
        n_splits: Number of CV splits
        gap: Gap between train and validation
        expanding: Use expanding window (True) or rolling window (False)
        
    Returns:
        Dictionary with mean and std of metrics across folds
    """
    from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
    
    cv = TimeSeriesCV(n_splits=n_splits, gap=gap, expanding=expanding)
    
    # Store metrics for each fold
    r2_scores = []
    rmse_scores = []
    mae_scores = []
    
    logger.info("=" * 60)
    logger.info("Starting Time Series Cross-Validation")
    logger.info("=" * 60)
    
    for fold, (train_idx, val_idx) in enumerate(cv.split(X, y, timestamps), 1):
        # Split data
        if isinstance(X, pd.DataFrame):
            X_train_fold = X.iloc[train_idx]
            X_val_fold = X.iloc[val_idx]
        else:
            X_train_fold = X[train_idx]
            X_val_fold = X[val_idx]
        
        y_train_fold = y[train_idx]
        y_val_fold = y[val_idx]
        
        # Clone and train model
        from sklearn.base import clone
        model_fold = clone(model)
        
        # Train
        if hasattr(model_fold, 'fit'):
            model_fold.fit(X_train_fold, y_train_fold)
        else:
            # For custom models with train() method
            model_fold.train(X_train_fold, y_train_fold)
        
        # Predict
        y_pred = model_fold.predict(X_val_fold)
        
        # Calculate metrics
        r2 = r2_score(y_val_fold, y_pred)
        rmse = np.sqrt(mean_squared_error(y_val_fold, y_pred))
        mae = mean_absolute_error(y_val_fold, y_pred)
        
        r2_scores.append(r2)
        rmse_scores.append(rmse)
        mae_scores.append(mae)
        
        logger.info(f"  Fold {fold}: R²={r2:.4f}, RMSE={rmse:.2f}, MAE={mae:.2f}")
    
    # Calculate mean and std
    results = {
        'r2_mean': np.mean(r2_scores),
        'r2_std': np.std(r2_scores),
        'rmse_mean': np.mean(rmse_scores),
        'rmse_std': np.std(rmse_scores),
        'mae_mean': np.mean(mae_scores),
        'mae_std': np.std(mae_scores),
        'fold_scores': {
            'r2': r2_scores,
            'rmse': rmse_scores,
            'mae': mae_scores
        }
    }
    
    logger.info("=" * 60)
    logger.info("Cross-Validation Results:")
    logger.info(f"  R² Score:  {results['r2_mean']:.4f} ± {results['r2_std']:.4f}")
    logger.info(f"  RMSE:      {results['rmse_mean']:.2f} ± {results['rmse_std']:.2f}")
    logger.info(f"  MAE:       {results['mae_mean']:.2f} ± {results['mae_std']:.2f}")
    logger.info("=" * 60)
    
    return results


if __name__ == "__main__":
    # Test with synthetic time-series data
    from datetime import datetime, timedelta
    from sklearn.linear_model import LinearRegression
    
    print("Testing Time Series Cross-Validation...")
    print("=" * 60)
    
    # Generate synthetic time-series data
    n_samples = 500
    start_date = datetime.now() - timedelta(days=500)
    timestamps = [start_date + timedelta(hours=i) for i in range(n_samples)]
    
    # Create features with temporal patterns
    hours = np.array([t.hour for t in timestamps])
    X = np.column_stack([
        hours,
        np.sin(hours * 2 * np.pi / 24),
        np.cos(hours * 2 * np.pi / 24)
    ])
    y = 50 + 20 * np.sin(hours * 2 * np.pi / 24) + np.random.randn(n_samples) * 5
    
    # Test expanding window CV
    print("\n1. Testing Expanding Window CV:")
    cv = TimeSeriesCV(n_splits=5, gap=0, expanding=True)
    splits = list(cv.split(X, y, timestamps))
    print(f"   Generated {len(splits)} splits")
    
    # Test rolling window CV
    print("\n2. Testing Rolling Window CV:")
    cv_rolling = TimeSeriesCV(n_splits=5, gap=12, expanding=False)
    splits_rolling = list(cv_rolling.split(X, y, timestamps))
    print(f"   Generated {len(splits_rolling)} splits")
    
    # Test with actual model validation
    print("\n3. Testing with Linear Regression:")
    model = LinearRegression()
    results = validate_with_time_series_cv(
        model, X, y, timestamps=timestamps, 
        n_splits=5, gap=0, expanding=True
    )
    
    print("\n✅ Time Series CV test complete!")
