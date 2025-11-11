#!/usr/bin/env python3
"""
Simple Unified Training - Train ONE model per algorithm using ALL city data combined
No city-specific features - just pure pollutant values -> AQI prediction

This is the simplest approach:
- Combine all data from all cities
- Train on: pm25, pm10, no2, so2, co, o3 -> aqi
- No city encoding needed
- At prediction time: just pass pollutant values, any city
"""

import argparse
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
import json
import pickle

import numpy as np
import pandas as pd

# Project root setup
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from database.db_operations import DatabaseOperations
from ml_models.linear_regression_model import LinearRegressionAQI
from ml_models.random_forest_model import RandomForestAQI
from ml_models.xgboost_model import XGBoostAQI

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

SAVE_DIR = Path("models/saved_models")
SAVE_DIR.mkdir(parents=True, exist_ok=True)


def fetch_all_data(db: DatabaseOperations, days: int) -> pd.DataFrame:
    """Fetch ALL pollution data from ALL cities and combine."""
    logger.info(f"📥 Fetching data from ALL cities (last {days} days)...")
    
    # Get all cities that have coordinates defined
    from api_handlers.openweather_handler import OpenWeatherHandler
    handler = OpenWeatherHandler()
    ALL_CITIES = list(handler.CITY_COORDINATES.keys())
    logger.info(f"   Training on {len(ALL_CITIES)} cities with defined coordinates")
    
    all_dfs = []
    end = datetime.utcnow()
    start = end - timedelta(days=days)
    
    total_samples = 0
    for city in ALL_CITIES:
        try:
            rows = db.get_pollution_data(city, start, end) or []
            if rows:
                df = pd.DataFrame(rows)
                all_dfs.append(df)
                total_samples += len(df)
                logger.info(f"  ✓ {city}: {len(df):,} samples")
        except Exception as e:
            logger.warning(f"  ✗ {city}: {e}")
    
    if not all_dfs:
        logger.error("❌ No data found!")
        return pd.DataFrame()
    
    # Combine everything
    combined = pd.concat(all_dfs, ignore_index=True)
    combined.rename(columns={"aqi_value": "aqi"}, inplace=True)
    
    # Sort by timestamp
    if "timestamp" in combined.columns:
        combined["timestamp"] = pd.to_datetime(combined["timestamp"])
        combined.sort_values("timestamp", inplace=True)
        combined.reset_index(drop=True, inplace=True)
    
    logger.info(f"✅ Total combined: {len(combined):,} samples")
    return combined


def prepare_features(df: pd.DataFrame) -> tuple:
    """Extract features: pm25, pm10, no2, so2, co, o3 -> aqi with smart imputation"""
    feature_cols = ["pm25", "pm10", "no2", "so2", "co", "o3"]
    
    # Ensure columns exist
    for col in feature_cols:
        if col not in df.columns:
            df[col] = np.nan
    
    X = df[feature_cols].copy()
    y = df["aqi"] if "aqi" in df.columns else None
    
    # SMART DATA HANDLING - Don't just drop!
    logger.info(f"  📊 Data quality before imputation:")
    logger.info(f"     Total rows: {len(X):,}")
    
    # Only remove rows where AQI is missing (can't train without target)
    if y is not None:
        mask = y.notna()
        X = X[mask]
        y = y[mask]
        logger.info(f"     Rows with valid AQI: {len(X):,}")
    
    # Handle missing pollutant values using MEDIAN IMPUTATION
    # (better than dropping - preserves data!)
    missing_before = X.isnull().sum().sum()
    
    if missing_before > 0:
        logger.info(f"     Missing pollutant values: {missing_before:,}")
        logger.info(f"     Using MEDIAN imputation (better than dropping rows!)")
        
        # Use median of each pollutant to fill missing values
        # Median is robust to outliers (better than mean)
        for col in feature_cols:
            missing_count = X[col].isnull().sum()
            if missing_count > 0:
                median_val = X[col].median()
                X[col].fillna(median_val, inplace=True)
                logger.info(f"       • {col}: filled {missing_count:,} values with median {median_val:.2f}")
        
        logger.info(f"     ✅ All missing values imputed!")
    else:
        logger.info(f"     ✅ No missing values found!")
    
    return X, y


def train_test_split(X, y, test_ratio=0.2):
    """Chronological split - train on old data, test on new data."""
    n = len(X)
    if n < 10:
        return None, None, None, None
    split_idx = int(n * (1 - test_ratio))
    return (
        X.iloc[:split_idx],
        X.iloc[split_idx:],
        y.iloc[:split_idx],
        y.iloc[split_idx:]
    )


def train_model(model_name: str, X_train, y_train, X_test, y_test):
    """Train a single model and return it with metrics."""
    logger.info(f"\n{'='*70}")
    logger.info(f"🚀 Training {model_name.upper()}")
    logger.info(f"{'='*70}")
    
    # Create model instance
    if model_name == "linear_regression":
        model = LinearRegressionAQI()
    elif model_name == "random_forest":
        model = RandomForestAQI()
    elif model_name == "xgboost":
        model = XGBoostAQI()
    else:
        logger.error(f"Unknown model: {model_name}")
        return None, None
    
    # Train
    logger.info(f"  Training on {len(X_train):,} samples...")
    success = model.train(X_train.values, y_train.values)
    
    if not success:
        logger.error(f"  ❌ Training failed!")
        return None, None
    
    # Evaluate
    logger.info(f"  Evaluating on {len(X_test):,} samples...")
    metrics = model.evaluate(X_test.values, y_test.values)
    
    if metrics:
        logger.info(f"  📊 Metrics:")
        logger.info(f"     R² Score: {metrics.get('r2', 0):.4f}")
        logger.info(f"     RMSE:     {metrics.get('rmse', 0):.2f}")
        logger.info(f"     MAE:      {metrics.get('mae', 0):.2f}")
        logger.info(f"     MAPE:     {metrics.get('mape', 0):.2f}%")
    
    return model, metrics


def save_model(model, model_name: str, metrics: dict):
    """Save model to disk."""
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    
    if model_name == "xgboost":
        filepath = SAVE_DIR / f"{model_name}_{timestamp}.json"
        model.save_model(str(filepath))
    else:
        filepath = SAVE_DIR / f"{model_name}_{timestamp}.pkl"
        model.save_model(str(filepath))
    
    # Save metrics alongside
    metrics_file = SAVE_DIR / f"{model_name}_{timestamp}_metrics.json"
    with open(metrics_file, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    # Create "latest" symlink (copy on Windows)
    latest_file = SAVE_DIR / f"{model_name}_latest.{'json' if model_name == 'xgboost' else 'pkl'}"
    if latest_file.exists():
        latest_file.unlink()
    
    import shutil
    shutil.copy(filepath, latest_file)
    
    logger.info(f"  💾 Saved: {filepath.name}")
    logger.info(f"  📋 Metrics: {metrics_file.name}")
    logger.info(f"  🔗 Latest: {latest_file.name}")


def main():
    parser = argparse.ArgumentParser(description="Train unified models on all city data")
    parser.add_argument("--days", type=int, default=3650, help="Days of data to use")
    parser.add_argument("--min-samples", type=int, default=10000, help="Minimum samples required")
    parser.add_argument("--models", type=str, default="lr,rf,xgb", help="Models to train (lr,rf,xgb)")
    args = parser.parse_args()
    
    logger.info("=" * 80)
    logger.info("SIMPLE UNIFIED MODEL TRAINING")
    logger.info("Training on COMBINED data from ALL cities")
    logger.info("=" * 80)
    
    # Load data
    db = DatabaseOperations()
    df = fetch_all_data(db, args.days)
    
    if df.empty:
        logger.error("❌ No data available!")
        return 1
    
    # Prepare features
    X, y = prepare_features(df)
    
    if len(X) < args.min_samples:
        logger.error(f"❌ Insufficient samples: {len(X)} < {args.min_samples}")
        return 1
    
    logger.info(f"\n📊 Dataset Summary:")
    logger.info(f"   Total samples: {len(X):,}")
    logger.info(f"   Features: {list(X.columns)}")
    logger.info(f"   AQI range: {y.min():.1f} - {y.max():.1f}")
    logger.info(f"   AQI mean: {y.mean():.1f}")

    # Save median imputation values so predictors can use the same statistics at inference
    try:
        medians = {col: float(X[col].median()) for col in X.columns}
        median_file = SAVE_DIR / 'median_imputation.json'
        with open(median_file, 'w') as mf:
            json.dump(medians, mf, indent=2)
        logger.info(f"  💾 Saved median imputation values: {median_file.name}")
    except Exception as e:
        logger.warning(f"  ⚠️ Could not save median imputation values: {e}")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_ratio=0.2)
    logger.info(f"\n📈 Split:")
    logger.info(f"   Train: {len(X_train):,} samples (80%)")
    logger.info(f"   Test:  {len(X_test):,} samples (20%)")
    
    # Train models
    models_to_train = [m.strip() for m in args.models.split(",")]
    model_map = {"lr": "linear_regression", "rf": "random_forest", "xgb": "xgboost"}
    
    results = []
    
    for key in models_to_train:
        model_name = model_map.get(key)
        if not model_name:
            logger.warning(f"Unknown model: {key}")
            continue
        
        model, metrics = train_model(model_name, X_train, y_train, X_test, y_test)
        
        if model and metrics:
            save_model(model, model_name, metrics)
            results.append({"model": model_name, "metrics": metrics})
            
            # Store in database
            db.insert_model_performance("ALL_CITIES", model_name, metrics)
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("🎉 TRAINING COMPLETE!")
    logger.info("=" * 80)
    logger.info(f"✅ Models trained: {len(results)}")
    logger.info(f"📁 Saved to: {SAVE_DIR}")
    logger.info(f"\nBest performing model:")
    
    if results:
        best = max(results, key=lambda x: x['metrics'].get('r2', -999))
        logger.info(f"   {best['model']}: R² = {best['metrics']['r2']:.4f}")
    
    logger.info("\n💡 Usage:")
    logger.info("   1. Models work for ANY city")
    logger.info("   2. Just pass pollutant values (pm25, pm10, no2, so2, co, o3)")
    logger.info("   3. Get AQI prediction back")
    logger.info("   4. No city-specific parameters needed!")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
