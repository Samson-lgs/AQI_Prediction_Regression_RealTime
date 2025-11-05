"""
Comprehensive Test for Ensemble Stacking and Hyperparameter Tuning

Tests the following features:
1. Stacked ensemble combining multiple base learners
2. Time-series cross-validation with rolling windows
3. Grid search hyperparameter tuning
4. Bayesian optimization with Optuna
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ml_models.stacked_ensemble import StackedEnsembleAQI
from models.time_series_cv import TimeSeriesCV, validate_with_time_series_cv
from models.hyperparameter_tuning import HyperparameterTuner, OPTUNA_AVAILABLE
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor
from sklearn.linear_model import LinearRegression
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def generate_synthetic_aqi_data(n_samples=1000, noise_level=10):
    """
    Generate synthetic time-series AQI data with realistic patterns
    """
    print("\n" + "=" * 80)
    print("GENERATING SYNTHETIC AQI DATA")
    print("=" * 80)
    
    start_date = datetime.now() - timedelta(hours=n_samples)
    timestamps = [start_date + timedelta(hours=i) for i in range(n_samples)]
    
    # Time-based features
    hours = np.array([t.hour for t in timestamps])
    days = np.array([t.day for t in timestamps])
    months = np.array([t.month for t in timestamps])
    
    # Temporal patterns
    hour_sin = np.sin(hours * 2 * np.pi / 24)
    hour_cos = np.cos(hours * 2 * np.pi / 24)
    month_sin = np.sin(months * 2 * np.pi / 12)
    
    # Simulated pollutants with temporal correlation
    pm25 = 50 + 30 * hour_sin + 20 * month_sin + np.random.randn(n_samples) * noise_level
    pm10 = pm25 * 1.8 + np.random.randn(n_samples) * noise_level
    no2 = 30 + 20 * hour_sin + np.random.randn(n_samples) * 5
    temp = 20 + 10 * hour_sin + 15 * month_sin + np.random.randn(n_samples) * 3
    humidity = 60 + 20 * hour_cos + np.random.randn(n_samples) * 10
    
    # Target AQI (complex non-linear relationship)
    aqi = (
        50 +
        0.5 * pm25 +
        0.2 * pm10 +
        0.3 * no2 +
        0.1 * temp -
        0.05 * humidity +
        10 * hour_sin +
        np.random.randn(n_samples) * noise_level
    )
    aqi = np.clip(aqi, 0, 500)
    
    # Create feature matrix
    X = pd.DataFrame({
        'hour': hours,
        'day': days,
        'month': months,
        'hour_sin': hour_sin,
        'hour_cos': hour_cos,
        'month_sin': month_sin,
        'pm25': pm25,
        'pm10': pm10,
        'no2': no2,
        'temperature': temp,
        'humidity': humidity
    })
    
    y = aqi
    
    print(f"✓ Generated {n_samples} samples")
    print(f"  Features: {X.shape[1]}")
    print(f"  AQI range: [{y.min():.1f}, {y.max():.1f}]")
    print(f"  AQI mean: {y.mean():.1f} ± {y.std():.1f}")
    
    return X, y, timestamps


def test_stacked_ensemble(X_train, y_train, X_test, y_test):
    """Test 1: Stacked Ensemble"""
    print("\n" + "=" * 80)
    print("TEST 1: STACKED ENSEMBLE")
    print("=" * 80)
    
    ensemble = StackedEnsembleAQI()
    ensemble.train(X_train, y_train, X_test, y_test)
    
    metrics = ensemble.evaluate(X_test, y_test)
    
    # Compare with base models
    print("\n📊 Model Comparison:")
    base_preds = ensemble.get_base_model_predictions(X_test)
    
    from sklearn.metrics import mean_squared_error, r2_score
    for name, pred in base_preds.items():
        r2 = r2_score(y_test, pred)
        rmse = np.sqrt(mean_squared_error(y_test, pred))
        print(f"  {name:20s}: R²={r2:.4f}, RMSE={rmse:.2f}")
    
    print(f"  {'ENSEMBLE':20s}: R²={metrics['r2_score']:.4f}, RMSE={metrics['rmse']:.2f}")
    
    return ensemble, metrics


def test_time_series_cv(X, y, timestamps):
    """Test 2: Time Series Cross-Validation"""
    print("\n" + "=" * 80)
    print("TEST 2: TIME SERIES CROSS-VALIDATION")
    print("=" * 80)
    
    # Test expanding window
    print("\n2a. Expanding Window CV:")
    model = RandomForestRegressor(n_estimators=50, max_depth=10, random_state=42, n_jobs=-1)
    results_expanding = validate_with_time_series_cv(
        model, X, y, timestamps=timestamps,
        n_splits=5, gap=0, expanding=True
    )
    
    # Test rolling window with gap
    print("\n2b. Rolling Window CV (gap=12):")
    results_rolling = validate_with_time_series_cv(
        model, X, y, timestamps=timestamps,
        n_splits=5, gap=12, expanding=False
    )
    
    return results_expanding, results_rolling


def test_hyperparameter_tuning(X_train, y_train, timestamps):
    """Test 3: Hyperparameter Tuning"""
    print("\n" + "=" * 80)
    print("TEST 3: HYPERPARAMETER TUNING")
    print("=" * 80)
    
    # Create time-series CV
    cv = TimeSeriesCV(n_splits=3, expanding=True)
    
    # Test Random Forest tuning
    print("\n3a. Random Forest Tuning (Bayesian Optimization):")
    if OPTUNA_AVAILABLE:
        tuner_rf = HyperparameterTuner(model_type='random_forest')
        results_rf = tuner_rf.bayesian_optimization(
            RandomForestRegressor,
            X_train, y_train,
            cv=cv,
            n_trials=20,
            metric='rmse',
            direction='minimize'
        )
        print(f"   Best RMSE: {results_rf['best_score']:.2f}")
    else:
        print("   ⚠️  Optuna not available. Install with: pip install optuna")
        results_rf = None
    
    # Test XGBoost tuning
    print("\n3b. XGBoost Tuning (Bayesian Optimization):")
    if OPTUNA_AVAILABLE:
        tuner_xgb = HyperparameterTuner(model_type='xgboost')
        results_xgb = tuner_xgb.bayesian_optimization(
            XGBRegressor,
            X_train, y_train,
            cv=cv,
            n_trials=20,
            metric='rmse',
            direction='minimize'
        )
        print(f"   Best RMSE: {results_xgb['best_score']:.2f}")
    else:
        results_xgb = None
    
    return results_rf, results_xgb


def test_ensemble_tuning(X_train, y_train):
    """Test 4: Ensemble Hyperparameter Tuning"""
    print("\n" + "=" * 80)
    print("TEST 4: STACKED ENSEMBLE TUNING")
    print("=" * 80)
    
    if not OPTUNA_AVAILABLE:
        print("⚠️  Optuna not available. Skipping ensemble tuning.")
        return None
    
    cv = TimeSeriesCV(n_splits=3, expanding=True)
    tuner_ensemble = HyperparameterTuner(model_type='stacked_ensemble')
    
    print("\n4. Tuning Stacked Ensemble (Bayesian Optimization):")
    results_ensemble = tuner_ensemble.bayesian_optimization(
        None,  # Will be handled internally
        X_train, y_train,
        cv=cv,
        n_trials=15,
        metric='rmse',
        direction='minimize'
    )
    
    print(f"   Best RMSE: {results_ensemble['best_score']:.2f}")
    
    return results_ensemble


def run_comprehensive_test():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("COMPREHENSIVE TEST: ENSEMBLE STACKING & HYPERPARAMETER TUNING")
    print("=" * 80)
    print(f"Start Time: {datetime.now()}")
    
    # Generate data
    X, y, timestamps = generate_synthetic_aqi_data(n_samples=800, noise_level=15)
    
    # Split data (time-series aware)
    train_size = 600
    X_train = X[:train_size]
    y_train = y[:train_size]
    X_test = X[train_size:]
    y_test = y[train_size:]
    timestamps_train = timestamps[:train_size]
    
    print(f"\nData Split:")
    print(f"  Training: {len(X_train)} samples ({timestamps_train[0]} to {timestamps_train[-1]})")
    print(f"  Test: {len(X_test)} samples ({timestamps[train_size]} to {timestamps[-1]})")
    
    # Run tests
    results = {}
    
    # Test 1: Stacked Ensemble
    ensemble, ensemble_metrics = test_stacked_ensemble(X_train, y_train, X_test, y_test)
    results['stacked_ensemble'] = ensemble_metrics
    
    # Test 2: Time Series CV
    cv_expanding, cv_rolling = test_time_series_cv(X, y, timestamps)
    results['cv_expanding'] = cv_expanding
    results['cv_rolling'] = cv_rolling
    
    # Test 3: Hyperparameter Tuning
    tuning_rf, tuning_xgb = test_hyperparameter_tuning(X_train, y_train, timestamps_train)
    results['tuning_rf'] = tuning_rf
    results['tuning_xgb'] = tuning_xgb
    
    # Test 4: Ensemble Tuning
    tuning_ensemble = test_ensemble_tuning(X_train, y_train)
    results['tuning_ensemble'] = tuning_ensemble
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"End Time: {datetime.now()}")
    print("\n✅ Test Results:")
    print(f"  1. Stacked Ensemble: R²={ensemble_metrics['r2_score']:.4f}, RMSE={ensemble_metrics['rmse']:.2f}")
    print(f"  2. Time Series CV (Expanding): R²={cv_expanding['r2_mean']:.4f} ± {cv_expanding['r2_std']:.4f}")
    print(f"  3. Time Series CV (Rolling): R²={cv_rolling['r2_mean']:.4f} ± {cv_rolling['r2_std']:.4f}")
    
    if tuning_rf:
        print(f"  4. RF Hyperparameter Tuning: Best RMSE={tuning_rf['best_score']:.2f}")
    if tuning_xgb:
        print(f"  5. XGBoost Hyperparameter Tuning: Best RMSE={tuning_xgb['best_score']:.2f}")
    if tuning_ensemble:
        print(f"  6. Ensemble Hyperparameter Tuning: Best RMSE={tuning_ensemble['best_score']:.2f}")
    
    print("\n✨ All tests completed successfully!")
    print("=" * 80)
    
    return results


if __name__ == "__main__":
    try:
        results = run_comprehensive_test()
    except Exception as e:
        logger.error(f"Test failed: {str(e)}", exc_info=True)
        raise
