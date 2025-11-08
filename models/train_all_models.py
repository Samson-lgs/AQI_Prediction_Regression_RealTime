#!/usr/bin/env python3
"""
Batch training script for AQI prediction models.

Usage:
  python models/train_all_models.py --all [--days 7] [--min-samples 100] [--models lr,rf,xgb]
  python models/train_all_models.py --city Delhi [--days 7] [--min-samples 100] [--models lr,rf,xgb]

Notes:
- Pulls data from the configured PostgreSQL database (env vars or DATABASE_URL)
- Trains light-weight models by default (Linear Regression, Random Forest, XGBoost)
- Skips LSTM by default to keep CI runs fast; can be added later
- Saves models under models/trained_models/
- Writes model performance into database.model_performance
"""

import argparse
import logging
import os
import json
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

# Project imports
from config.settings import CITIES
from database.db_operations import DatabaseOperations
from ml_models.linear_regression_model import LinearRegressionAQI
from ml_models.random_forest_model import RandomForestAQI
from ml_models.xgboost_model import XGBoostAQI

# Optional heavy model disabled by default
# from ml_models.lstm_model import LSTMAQI

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("train_all_models")

SUPPORTED_MODELS = {
    "lr": "linear_regression",
    "rf": "random_forest",
    "xgb": "xgboost",
    # "lstm": "lstm",  # add later if needed
}

MODEL_CLASSES = {
    "linear_regression": LinearRegressionAQI,
    "random_forest": RandomForestAQI,
    "xgboost": XGBoostAQI,
    # "lstm": LSTMAQI,
}

SAVE_DIR = Path("models/trained_models")
SAVE_DIR.mkdir(parents=True, exist_ok=True)


def fetch_city_dataframe(db: DatabaseOperations, city: str, days: int) -> pd.DataFrame:
    """Fetch last N days of pollution data for a city and return DataFrame."""
    end = datetime.utcnow()
    start = end - timedelta(days=days)

    rows = db.get_pollution_data(city, start, end) or []
    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    # Normalize column names
    df.rename(columns={
        "aqi_value": "aqi",
    }, inplace=True)

    # Ensure timestamp sorting ascending for chronological split
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df.sort_values("timestamp", inplace=True)
        df.reset_index(drop=True, inplace=True)

    return df


def prepare_features(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Select basic features and target for training; drop rows with NaNs."""
    feature_cols = ["pm25", "pm10", "no2", "so2", "co", "o3"]
    for col in feature_cols:
        if col not in df.columns:
            df[col] = np.nan

    X = df[feature_cols].copy()
    y = df["aqi"] if "aqi" in df.columns else None

    # Drop rows with missing target or any missing features
    mask = y.notna()
    X = X[mask]
    y = y[mask]
    X = X.dropna()
    y = y.loc[X.index]

    return X, y


def chronological_train_test_split(X: pd.DataFrame, y: pd.Series, test_ratio: float = 0.2):
    n = len(X)
    if n < 5:
        return None, None, None, None
    split = max(1, int(n * (1 - test_ratio)))
    X_train = X.iloc[:split]
    y_train = y.iloc[:split]
    X_test = X.iloc[split:]
    y_test = y.iloc[split:]
    return X_train, X_test, y_train, y_test


def evaluate_and_record(db: DatabaseOperations, city: str, model_name: str, metrics: dict):
    """Insert performance metrics into DB with expected key names."""
    # Normalize keys to expected ones
    normalized = {
        "r2_score": metrics.get("r2") or metrics.get("r2_score"),
        "rmse": metrics.get("rmse"),
        "mae": metrics.get("mae"),
        "mape": metrics.get("mape"),
    }
    db.insert_model_performance(city, model_name, normalized)


def save_model_artifact(city: str, model_name: str, model_obj):
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    if model_name == "xgboost":
        out_path = SAVE_DIR / f"{city}_{model_name}_{ts}.json"
        model_obj.save_model(str(out_path))
    else:
        out_path = SAVE_DIR / f"{city}_{model_name}_{ts}.pkl"
        model_obj.save_model(str(out_path))
    logger.info(f"Saved {model_name} model for {city} -> {out_path}")


def train_for_city(db: DatabaseOperations, city: str, days: int, min_samples: int, models_to_train: list[str]) -> dict:
    logger.info(f"==== Training models for {city} (last {days} days) ====")
    df = fetch_city_dataframe(db, city, days)
    if df.empty:
        logger.warning(f"No data for {city}; skipping")
        return {"city": city, "status": "skipped", "reason": "no-data"}

    X, y = prepare_features(df)
    if X is None or y is None or len(X) < min_samples:
        logger.warning(f"Insufficient samples for {city} (have {len(X)} < {min_samples}); skipping")
        return {"city": city, "status": "skipped", "reason": "insufficient-samples", "samples": int(len(X))}

    split = chronological_train_test_split(X, y, test_ratio=0.2)
    if split[0] is None:
        logger.warning(f"Not enough data to split for {city}; skipping")
        return {"city": city, "status": "skipped", "reason": "split-failed"}
    X_train, X_test, y_train, y_test = split

    results = {"city": city, "status": "ok", "trained": []}

    for key in models_to_train:
        model_name = SUPPORTED_MODELS.get(key)
        if not model_name:
            logger.warning(f"Unknown model key '{key}', skipping")
            continue
        ModelCls = MODEL_CLASSES[model_name]
        model = ModelCls()
        ok = model.train(X_train.values if hasattr(X_train, 'values') else X_train, y_train.values if hasattr(y_train, 'values') else y_train)
        if not ok:
            logger.warning(f"Training failed for {model_name} on {city}")
            continue
        metrics = model.evaluate(X_test.values if hasattr(X_test, 'values') else X_test, y_test.values if hasattr(y_test, 'values') else y_test)
        if metrics:
            evaluate_and_record(db, city, model_name, metrics)
        save_model_artifact(city, model_name, model)
        results["trained"].append({"model": model_name, "metrics": metrics})

    if not results["trained"]:
        results["status"] = "failed"
    return results


def parse_args():
    p = argparse.ArgumentParser(description="Train AQI models for one or more cities")
    scope = p.add_mutually_exclusive_group(required=True)
    scope.add_argument("--all", action="store_true", help="Train all configured cities")
    scope.add_argument("--city", type=str, help="Train a single city by name")

    p.add_argument("--days", type=int, default=7, help="How many days of data to use")
    p.add_argument("--min-samples", type=int, default=100, help="Minimum samples required to train")
    p.add_argument("--models", type=str, default="lr,rf,xgb", help="Comma-separated model keys: lr,rf,xgb")
    p.add_argument("--summary-file", type=str, default=str(SAVE_DIR / "training_summary.json"), help="Path to write JSON training summary")
    return p.parse_args()


def main():
    args = parse_args()
    global start_time_iso
    start_time_iso = datetime.utcnow().isoformat()

    models_to_train = [m.strip() for m in args.models.split(",") if m.strip()]
    logger.info(f"Models to train: {models_to_train}")

    # Initialize DB (uses env vars or DATABASE_URL inside DatabaseManager)
    db = DatabaseOperations()
    db.create_tables()

    cities = [args.city] if args.city else CITIES

    summary = {"ok": 0, "skipped": 0, "failed": 0}

    for city in cities:
        try:
            res = train_for_city(db, city, args.days, args.min_samples, models_to_train)
            status = res.get("status")
            summary[status] = summary.get(status, 0) + 1
            # Accumulate detailed per-city info
            res["timestamp_utc"] = datetime.utcnow().isoformat()
            res["days"] = args.days
            res["min_samples"] = args.min_samples
            res["models"] = models_to_train
            # Append to existing list in summary
            summary.setdefault("details", []).append(res)
        except Exception as e:
            logger.exception(f"Unexpected error training {city}: {e}")
            summary["failed"] += 1

    logger.info("==== Training Summary ====")
    for k, v in summary.items():
        if k == "details":
            continue
        logger.info(f"{k}: {v}")

    # Write summary JSON
    try:
        summary_out = {
            "run_started": start_time_iso,
            "run_completed": datetime.utcnow().isoformat(),
            "args": {
                "all": args.all,
                "city": args.city,
                "days": args.days,
                "min_samples": args.min_samples,
                "models": models_to_train,
            },
            "summary": {k: v for k, v in summary.items() if k != "details"},
            "details": summary.get("details", [])
        }
        with open(args.summary_file, "w", encoding="utf-8") as f:
            json.dump(summary_out, f, indent=2)
        logger.info(f"Training summary written to {args.summary_file}")
    except Exception as e:
        logger.warning(f"Could not write summary file: {e}")

    # Exit non-zero only if everything failed
    if summary.get("ok", 0) == 0 and summary.get("failed", 0) > 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
