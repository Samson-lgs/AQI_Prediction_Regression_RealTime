#!/usr/bin/env python3
"""
Unified Model Training - Trains one model per algorithm using ALL data
City selection happens at prediction time, not training time.

Usage:
  python models/train_unified_models.py --days 3650 --min-samples 10000 --models lr,rf,xgb,lstm

This approach:
- Trains ONE unified model per algorithm (not per city)
- Uses ALL available data from ALL cities
- City becomes a feature (one-hot encoded)
- Predictions filter by city at runtime
- More data = better generalization
"""

import argparse
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
import json

import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder

# Project root setup
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import CITIES
from database.db_operations import DatabaseOperations
from ml_models.linear_regression_model import LinearRegressionAQI
from ml_models.random_forest_model import RandomForestAQI
from ml_models.xgboost_model import XGBoostAQI

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("train_unified_models")

SUPPORTED_MODELS = {
    "lr": "linear_regression",
    "rf": "random_forest",
    "xgb": "xgboost",
    "lstm": "lstm",
}

MODEL_CLASSES = {
    "linear_regression": LinearRegressionAQI,
    "random_forest": RandomForestAQI,
    "xgboost": XGBoostAQI,
}

# Lazy load LSTM only if requested
def get_lstm_class():
    from ml_models.lstm_model import LSTMAQI
    return LSTMAQI

SAVE_DIR = Path("models/trained_models")
SAVE_DIR.mkdir(parents=True, exist_ok=True)


def fetch_all_data(db: DatabaseOperations, days: int) -> pd.DataFrame:
    """Fetch pollution data for ALL cities and combine into one DataFrame."""
    logger.info(f"Fetching data for ALL cities (last {days} days)...")
    
    all_dfs = []
    end = datetime.utcnow()
    start = end - timedelta(days=days)
    
    for city in CITIES:
        try:
            rows = db.get_pollution_data(city, start, end) or []
            if rows:
                df = pd.DataFrame(rows)
                df['city'] = city  # Add city column
                all_dfs.append(df)
                logger.info(f"  {city}: {len(df)} samples")
        except Exception as e:
            logger.warning(f"  {city}: Error fetching data - {e}")
    
    if not all_dfs:
        logger.error("No data found for any city!")
        return pd.DataFrame()
    
    # Combine all cities
    combined_df = pd.concat(all_dfs, ignore_index=True)
    
    # Normalize column names
    combined_df.rename(columns={"aqi_value": "aqi"}, inplace=True)
    
    # Sort by timestamp
    if "timestamp" in combined_df.columns:
        combined_df["timestamp"] = pd.to_datetime(combined_df["timestamp"])
        combined_df.sort_values("timestamp", inplace=True)
        combined_df.reset_index(drop=True, inplace=True)
    
    logger.info(f"Total combined samples: {len(combined_df)}")
    return combined_df


def prepare_features_with_city(df: pd.DataFrame) -> tuple:
    """Prepare features including city as one-hot encoded feature."""
    feature_cols = ["pm25", "pm10", "no2", "so2", "co", "o3"]
    
    # Ensure all pollutant columns exist
    for col in feature_cols:
        if col not in df.columns:
            df[col] = np.nan
    
    # One-hot encode city
    city_dummies = pd.get_dummies(df['city'], prefix='city')
    
    # Combine pollutant features with city features
    X = pd.concat([df[feature_cols], city_dummies], axis=1)
    y = df["aqi"] if "aqi" in df.columns else None
    
    # Drop rows with missing target or features
    mask = y.notna()
    X = X[mask]
    y = y[mask]
    X = X.dropna()
    y = y.loc[X.index]
    
    # Store city column names for later use
    city_columns = city_dummies.columns.tolist()
    
    return X, y, city_columns


def chronological_train_test_split(X: pd.DataFrame, y: pd.Series, test_ratio: float = 0.2):
    """Chronological split - train on older data, test on newer data."""
    n = len(X)
    if n < 5:
        return None, None, None, None
    split = max(1, int(n * (1 - test_ratio)))
    X_train = X.iloc[:split]
    y_train = y.iloc[:split]
    X_test = X.iloc[split:]
    y_test = y.iloc[split:]
    return X_train, X_test, y_train, y_test


def save_model_artifact(model_name: str, model_obj, city_columns: list):
    """Save unified model with metadata."""
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    
    # Save model
    if model_name == "xgboost":
        model_path = SAVE_DIR / f"unified_{model_name}_{ts}.json"
        model_obj.save_model(str(model_path))
    elif model_name == "lstm":
        model_path = SAVE_DIR / f"unified_{model_name}_{ts}.h5"
        model_obj.save_model(str(model_path))
    else:
        model_path = SAVE_DIR / f"unified_{model_name}_{ts}.pkl"
        model_obj.save_model(str(model_path))
    
    # Save metadata (city columns for prediction)
    metadata_path = SAVE_DIR / f"unified_{model_name}_{ts}_metadata.json"
    metadata = {
        "model_name": model_name,
        "city_columns": city_columns,
        "trained_at": ts,
        "feature_order": ["pm25", "pm10", "no2", "so2", "co", "o3"] + city_columns
    }
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"✅ Saved unified {model_name} model -> {model_path}")
    logger.info(f"   Metadata -> {metadata_path}")


def train_unified_model(db: DatabaseOperations, days: int, min_samples: int, models_to_train: list) -> dict:
    """Train unified models using ALL city data."""
    logger.info("=" * 80)
    logger.info("TRAINING UNIFIED MODELS (One model per algorithm, all cities)")
    logger.info("=" * 80)
    
    # Fetch all data
    df = fetch_all_data(db, days)
    if df.empty:
        logger.error("No data available!")
        return {"status": "failed", "reason": "no-data"}
    
    # Prepare features
    X, y, city_columns = prepare_features_with_city(df)
    if X is None or y is None or len(X) < min_samples:
        logger.warning(f"Insufficient samples (have {len(X)} < {min_samples})")
        return {"status": "failed", "reason": "insufficient-samples", "samples": len(X)}
    
    logger.info(f"✅ Total training samples: {len(X)}")
    logger.info(f"   Features: {X.shape[1]} ({len(city_columns)} cities encoded)")
    
    # Split data
    split = chronological_train_test_split(X, y, test_ratio=0.2)
    if split[0] is None:
        logger.error("Split failed!")
        return {"status": "failed", "reason": "split-failed"}
    
    X_train, X_test, y_train, y_test = split
    logger.info(f"   Train: {len(X_train)} samples | Test: {len(X_test)} samples")
    
    results = {"status": "ok", "trained": [], "samples": len(X)}
    
    # Train each model
    for key in models_to_train:
        model_name = SUPPORTED_MODELS.get(key)
        if not model_name:
            logger.warning(f"Unknown model key '{key}', skipping")
            continue
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Training {model_name.upper()}...")
        logger.info(f"{'='*60}")
        
        # Lazy load LSTM if needed
        if model_name == "lstm":
            ModelCls = get_lstm_class()
        else:
            ModelCls = MODEL_CLASSES.get(model_name)
            if not ModelCls:
                logger.warning(f"Model class not found for '{model_name}', skipping")
                continue
        
        model = ModelCls()
        
        # Train
        ok = model.train(
            X_train.values if hasattr(X_train, 'values') else X_train,
            y_train.values if hasattr(y_train, 'values') else y_train
        )
        
        if not ok:
            logger.warning(f"❌ Training failed for {model_name}")
            continue
        
        # Evaluate
        metrics = model.evaluate(
            X_test.values if hasattr(X_test, 'values') else X_test,
            y_test.values if hasattr(y_test, 'values') else y_test
        )
        
        if metrics:
            logger.info(f"✅ {model_name} Metrics:")
            logger.info(f"   R² Score: {metrics.get('r2', 0):.4f}")
            logger.info(f"   RMSE: {metrics.get('rmse', 0):.2f}")
            logger.info(f"   MAE: {metrics.get('mae', 0):.2f}")
            logger.info(f"   MAPE: {metrics.get('mape', 0):.2f}%")
            
            # Insert performance for "ALL" as city
            db.insert_model_performance("ALL", model_name, metrics)
        
        # Save model
        save_model_artifact(model_name, model, city_columns)
        
        results["trained"].append({
            "model": model_name,
            "metrics": metrics
        })
    
    return results


def parse_args():
    p = argparse.ArgumentParser(description="Train unified AQI models (one per algorithm, all cities)")
    p.add_argument("--days", type=int, default=3650, help="How many days of data to use (default: 10 years)")
    p.add_argument("--min-samples", type=int, default=10000, help="Minimum total samples required")
    p.add_argument("--models", type=str, default="lr,rf,xgb", help="Models to train: lr,rf,xgb,lstm")
    p.add_argument("--summary-file", type=str, default=str(SAVE_DIR / "unified_training_summary.json"))
    return p.parse_args()


def main():
    args = parse_args()
    start_time = datetime.utcnow()
    
    models_to_train = [m.strip() for m in args.models.split(",") if m.strip()]
    logger.info(f"Models to train: {models_to_train}")
    
    # Initialize DB
    db = DatabaseOperations()
    db.create_tables()
    
    # Train unified models
    try:
        results = train_unified_model(db, args.days, args.min_samples, models_to_train)
        
        # Write summary
        summary = {
            "run_started": start_time.isoformat(),
            "run_completed": datetime.utcnow().isoformat(),
            "args": {
                "days": args.days,
                "min_samples": args.min_samples,
                "models": models_to_train,
            },
            "results": results
        }
        
        with open(args.summary_file, "w") as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"\n✅ Summary written to {args.summary_file}")
        
        if results.get("status") != "ok":
            raise SystemExit(1)
        
        logger.info("\n" + "=" * 80)
        logger.info("🎉 UNIFIED TRAINING COMPLETE!")
        logger.info("=" * 80)
        logger.info(f"Models trained: {len(results.get('trained', []))}")
        logger.info(f"Total samples used: {results.get('samples', 0):,}")
        logger.info("\nNext steps:")
        logger.info("1. Update backend to load unified models")
        logger.info("2. Predictions will filter by selected city")
        logger.info("3. All cities use the same trained models")
        
    except Exception as e:
        logger.exception(f"Training failed: {e}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
