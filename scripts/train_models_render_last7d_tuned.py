import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import json

from ml_models.linear_regression_model import LinearRegressionAQI
from ml_models.random_forest_model import RandomForestAQI
from ml_models.xgboost_model import XGBoostAQI

SAVE_DIR = Path('models/saved_models')
SAVE_DIR.mkdir(parents=True, exist_ok=True)

DATA_PATH = Path('render_pollution_last7d.csv')
assert DATA_PATH.exists(), f"{DATA_PATH} not found. Run export_render_pollution_data.py first."

df = pd.read_csv(DATA_PATH)

feature_cols = ["pm25", "pm10", "no2", "so2", "co", "o3"]

def prepare(df: pd.DataFrame):
    df = df.copy()
    # Ensure numeric dtypes
    for c in feature_cols + ["aqi_value"]:
        df[c] = pd.to_numeric(df[c], errors='coerce')
    # Drop rows without target
    df = df[df['aqi_value'].notna()]
    # Median impute features
    medians = {c: float(df[c].median()) for c in feature_cols}
    for c in feature_cols:
        df[c] = df[c].fillna(medians[c])
    # Clip extreme outliers per feature (1st-99th percentiles)
    for c in feature_cols:
        lo, hi = np.percentile(df[c], [1, 99])
        df[c] = df[c].clip(lo, hi)
    X = df[feature_cols].copy()
    y = df['aqi_value'].astype(float).copy()
    return X, y, medians

X, y, medians = prepare(df)

# Save medians for inference consistency
with open(SAVE_DIR / 'median_imputation.json', 'w') as f:
    json.dump(medians, f, indent=2)

n = len(X)
train_end = int(n * 0.6)
val_end = int(n * 0.8)

X_train, y_train = X.iloc[:train_end], y.iloc[:train_end]
X_val, y_val = X.iloc[train_end:val_end], y.iloc[train_end:val_end]
X_test, y_test = X.iloc[val_end:], y.iloc[val_end:]

print(f"Samples: train={len(X_train)}, val={len(X_val)}, test={len(X_test)}")

results = {}

# Linear Regression (baseline)
lin = LinearRegressionAQI()
lin.train(X_train.values, y_train.values)
lin_metrics = lin.evaluate(X_test.values, y_test.values)
results['linear_regression'] = {'metrics': lin_metrics}
with open(SAVE_DIR / 'linear_regression_latest.pkl', 'wb') as f:
    import pickle; pickle.dump(lin, f)
with open(SAVE_DIR / 'linear_regression_latest_metrics.json', 'w') as f:
    json.dump(lin_metrics, f, indent=2)
print('Linear Regression:', lin_metrics)

# Random Forest - simple grid search
rf_grid = {
    'n_estimators': [300, 600, 1000],
    'max_depth': [None, 20, 40]
}

best_rf = None
best_rf_score = -1e9
best_rf_params = None
for ne in rf_grid['n_estimators']:
    for md in rf_grid['max_depth']:
        rf = RandomForestAQI(n_estimators=ne, max_depth=md)
        ok = rf.train(X_train.values, y_train.values)
        if not ok:
            continue
        # Evaluate on validation
        val_metrics = rf.evaluate(X_val.values, y_val.values)
        r2_val = val_metrics['r2']
        print(f"RF val r2={r2_val:.4f} (n_estimators={ne}, max_depth={md})")
        if r2_val > best_rf_score:
            best_rf_score = r2_val
            best_rf = rf
            best_rf_params = {'n_estimators': ne, 'max_depth': md}

# Evaluate best RF on test and save
rf_test_metrics = best_rf.evaluate(X_test.values, y_test.values) if best_rf else None
results['random_forest'] = {'params': best_rf_params, 'metrics': rf_test_metrics}
if best_rf:
    import pickle
    with open(SAVE_DIR / 'random_forest_latest.pkl', 'wb') as f:
        pickle.dump(best_rf, f)
    with open(SAVE_DIR / 'random_forest_latest_metrics.json', 'w') as f:
        json.dump(rf_test_metrics, f, indent=2)
print('Random Forest best:', best_rf_params, rf_test_metrics)

# XGBoost - tuned grid with early stopping
xgb_grid = {
    'n_estimators': [400, 800, 1200],
    'max_depth': [4, 6, 8],
    'learning_rate': [0.05, 0.1],
}

best_xgb = None
best_xgb_score = -1e9
best_xgb_params = None
for ne in xgb_grid['n_estimators']:
    for md in xgb_grid['max_depth']:
        for lr in xgb_grid['learning_rate']:
            xgbm = XGBoostAQI(max_depth=md, learning_rate=lr, n_estimators=ne)
            ok = xgbm.train(X_train.values, y_train.values, X_val.values, y_val.values)
            if not ok:
                continue
            val_metrics = xgbm.evaluate(X_val.values, y_val.values)
            r2_val = val_metrics['r2']
            print(f"XGB val r2={r2_val:.4f} (n_estimators={ne}, max_depth={md}, lr={lr})")
            if r2_val > best_xgb_score:
                best_xgb_score = r2_val
                best_xgb = xgbm
                best_xgb_params = {'n_estimators': ne, 'max_depth': md, 'learning_rate': lr}

xgb_test_metrics = best_xgb.evaluate(X_test.values, y_test.values) if best_xgb else None
results['xgboost'] = {'params': best_xgb_params, 'metrics': xgb_test_metrics}
if best_xgb:
    best_xgb.save_model(str(SAVE_DIR / 'xgboost_latest.json'))
    with open(SAVE_DIR / 'xgboost_latest_metrics.json', 'w') as f:
        json.dump(xgb_test_metrics, f, indent=2)
print('XGBoost best:', best_xgb_params, xgb_test_metrics)

# Summary
summary_path = SAVE_DIR / f"render_last7d_training_summary_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
with open(summary_path, 'w') as f:
    json.dump(results, f, indent=2)
print('Saved summary to', summary_path)

best_model = max([(k, v['metrics']['r2']) for k, v in results.items() if v['metrics']], key=lambda kv: kv[1])
print('Best model R2 on test:', best_model)
