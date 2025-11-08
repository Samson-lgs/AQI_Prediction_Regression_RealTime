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
from ml_models.lightgbm_model import LightGBMAQI
from ml_models.catboost_model import CatBoostAQI

DATA_PATH = Path('render_pollution_last7d.csv')
SAVE_DIR = Path('models/saved_models')
SAVE_DIR.mkdir(parents=True, exist_ok=True)

feature_cols = ["pm25", "pm10", "no2", "so2", "co", "o3"]

assert DATA_PATH.exists(), f"Missing {DATA_PATH}. Run export_render_pollution_data.py first."

df = pd.read_csv(DATA_PATH)
# Basic types
for c in feature_cols + ["aqi_value"]:
    df[c] = pd.to_numeric(df[c], errors='coerce')
# Parse timestamp
df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
# Drop rows without target
df = df[df['aqi_value'].notna()].copy()

# Global medians for fallback
global_medians = {c: float(df[c].median()) for c in feature_cols}

# Sanity: percentile clipping to handle extreme units/outliers
for c in feature_cols:
    lo, hi = np.nanpercentile(df[c], [1, 99])
    df[c] = df[c].clip(lo, hi)

# Median imputation
for c in feature_cols:
    df[c] = df[c].fillna(global_medians[c])

# Feature engineering
df['pm_ratio'] = np.where(df['pm10'] == 0, 0, df['pm25'] / df['pm10'])
df['total_pm'] = df['pm25'] + df['pm10']
df['oxidants'] = df['no2'] + df['o3']
df['sulfur_nitrogen'] = df['so2'] + df['no2']
df['pm25_no2'] = df['pm25'] * df['no2']
df['pm10_o3'] = df['pm10'] * df['o3']
# Log transforms (robust)
for c in ["pm25", "pm10", "no2", "so2", "co", "o3", "total_pm", "oxidants"]:
    df[f'log_{c}'] = np.log1p(np.maximum(df[c], 0))

# Temporal smoothing (per city, past-only)
df = df.sort_values(['city', 'timestamp'])
for c in feature_cols:
    df[f'{c}_roll3'] = df.groupby('city')[c].transform(lambda s: s.rolling(window=3, min_periods=1).mean())
# Smoothed target option
df['aqi_roll3'] = df.groupby('city')['aqi_value'].transform(lambda s: s.rolling(window=3, min_periods=1).mean())

all_features = [
    *feature_cols,
    'pm_ratio','total_pm','oxidants','sulfur_nitrogen','pm25_no2','pm10_o3',
    *[f'log_{c}' for c in ["pm25","pm10","no2","so2","co","o3","total_pm","oxidants"]],
    *[f'{c}_roll3' for c in feature_cols]
]

# Train/val/test split chronologically
n = len(df)
train_end = int(n * 0.6)
val_end = int(n * 0.8)

train_df = df.iloc[:train_end]
val_df = df.iloc[train_end:val_end]
test_df = df.iloc[val_end:]

# Per-city normalization using training stats
scaler_stats = {}
for city, sub in train_df.groupby('city'):
    means = sub[all_features].mean()
    stds = sub[all_features].std(ddof=0).replace(0, 1.0)
    scaler_stats[city] = {'mean': means.to_dict(), 'std': stds.to_dict()}

def apply_city_scaling(input_df):
    out = input_df.copy()
    for city, sub in out.groupby('city'):
        stats = scaler_stats.get(city)
        if stats is None:
            # fallback to global
            gmean = train_df[all_features].mean()
            gstd = train_df[all_features].std(ddof=0).replace(0,1.0)
            out.loc[out['city']==city, all_features] = (sub[all_features] - gmean) / gstd
        else:
            mean = pd.Series(stats['mean'])
            std = pd.Series(stats['std']).replace(0,1.0)
            out.loc[out['city']==city, all_features] = (sub[all_features] - mean) / std
    return out

train_df_scaled = apply_city_scaling(train_df)
val_df_scaled = apply_city_scaling(val_df)
test_df_scaled = apply_city_scaling(test_df)

# Targets
y_train_raw = train_df['aqi_value'].values
y_val_raw = val_df['aqi_value'].values
y_test_raw = test_df['aqi_value'].values

y_train_smooth = train_df['aqi_roll3'].values
y_val_smooth = val_df['aqi_roll3'].values
y_test_smooth = test_df['aqi_roll3'].values

X_train = train_df_scaled[all_features].values
X_val = val_df_scaled[all_features].values
X_test = test_df_scaled[all_features].values

results = {}
artifacts = {
    'global_medians': global_medians,
    'scaler_stats': scaler_stats,
    'features': all_features,
}

def record_result(name, params, model, test_metrics):
    results[name] = {'params': params, 'metrics': test_metrics}

# Train on RAW target only (smoothed target kept for future experimentation)
lin = LinearRegressionAQI()
lin.train(X_train, y_train_raw)
lin_test_metrics = lin.evaluate(X_test, y_test_raw)
record_result('linear_regression_advanced', {'target':'raw'}, lin, lin_test_metrics)

# Random Forest grid
rf_candidates = []
for ne in [300, 600]:
    for md in [None, 20, 40]:
        rf = RandomForestAQI(n_estimators=ne, max_depth=md)
        ok = rf.train(X_train, y_train_raw)
        if not ok: continue
        val_metrics = rf.evaluate(X_val, y_val_raw) or {'r2': -1e9}
        rf_candidates.append((rf, val_metrics['r2'], {'n_estimators': ne, 'max_depth': md, 'target': 'raw'}))

best_rf, _, best_rf_params = max(rf_candidates, key=lambda t: t[1]) if rf_candidates else (None, None, None)
rf_test_metrics = None
if best_rf:
    y_te = y_test_raw if best_rf_params['target']=='raw' else y_test_smooth
    rf_test_metrics = best_rf.evaluate(X_test, y_te)
    import pickle
    with open(SAVE_DIR / 'random_forest_advanced.pkl', 'wb') as f:
        pickle.dump(best_rf, f)
    with open(SAVE_DIR / 'random_forest_advanced_metrics.json', 'w') as f:
        json.dump(rf_test_metrics, f, indent=2)
record_result('random_forest_advanced', best_rf_params, best_rf, rf_test_metrics)

# XGBoost grid
xgb_candidates = []
for ne in [400, 800]:
    for md in [4, 6, 8]:
        for lr in [0.05, 0.1]:
            xgbm = XGBoostAQI(max_depth=md, learning_rate=lr, n_estimators=ne)
            ok = xgbm.train(X_train, y_train_raw, X_val, y_val_raw)
            if not ok: continue
            val_metrics = xgbm.evaluate(X_val, y_val_raw) or {'r2': -1e9}
            xgb_candidates.append((xgbm, val_metrics['r2'], {'n_estimators': ne, 'max_depth': md, 'learning_rate': lr, 'target': 'raw'}))

best_xgb, _, best_xgb_params = max(xgb_candidates, key=lambda t: t[1]) if xgb_candidates else (None, None, None)
xgb_test_metrics = None
if best_xgb:
    y_te = y_test_raw if best_xgb_params['target']=='raw' else y_test_smooth
    xgb_test_metrics = best_xgb.evaluate(X_test, y_te)
    best_xgb.save_model(str(SAVE_DIR / 'xgboost_advanced.json'))
    with open(SAVE_DIR / 'xgboost_advanced_metrics.json', 'w') as f:
        json.dump(xgb_test_metrics, f, indent=2)
record_result('xgboost_advanced', best_xgb_params, best_xgb, xgb_test_metrics)

# LightGBM grid
lgb_candidates = []
for nl in [31, 63]:
    for ne in [400, 800]:
        for lr in [0.05, 0.1]:
            lgbm = LightGBMAQI(num_leaves=nl, learning_rate=lr, n_estimators=ne)
            ok = lgbm.train(X_train, y_train_raw, X_val, y_val_raw)
            if not ok: continue
            val_metrics = lgbm.evaluate(X_val, y_val_raw) or {'r2': -1e9}
            lgb_candidates.append((lgbm, val_metrics['r2'], {'num_leaves': nl, 'n_estimators': ne, 'learning_rate': lr, 'target': 'raw'}))

best_lgb, _, best_lgb_params = max(lgb_candidates, key=lambda t: t[1]) if lgb_candidates else (None, None, None)
lgb_test_metrics = None
if best_lgb:
    y_te = y_test_raw if best_lgb_params['target']=='raw' else y_test_smooth
    lgb_test_metrics = best_lgb.evaluate(X_test, y_te)
    best_lgb.save_model(str(SAVE_DIR / 'lightgbm_advanced.txt'))
    with open(SAVE_DIR / 'lightgbm_advanced_metrics.json', 'w') as f:
        json.dump(lgb_test_metrics, f, indent=2)
record_result('lightgbm_advanced', best_lgb_params, best_lgb, lgb_test_metrics)

# CatBoost grid
cb_candidates = []
for depth in [6, 8]:
    for iters in [500, 800]:
        for lr in [0.05, 0.1]:
            cb = CatBoostAQI(depth=depth, iterations=iters, learning_rate=lr)
            ok = cb.train(X_train, y_train_raw, X_val, y_val_raw)
            if not ok: continue
            val_metrics = cb.evaluate(X_val, y_val_raw) or {'r2': -1e9}
            cb_candidates.append((cb, val_metrics['r2'], {'depth': depth, 'iterations': iters, 'learning_rate': lr, 'target': 'raw'}))

best_cb, _, best_cb_params = max(cb_candidates, key=lambda t: t[1]) if cb_candidates else (None, None, None)
cb_test_metrics = None
if best_cb:
    y_te = y_test_raw if best_cb_params['target']=='raw' else y_test_smooth
    cb_test_metrics = best_cb.evaluate(X_test, y_te)
    best_cb.save_model(str(SAVE_DIR / 'catboost_advanced.cbm'))
    with open(SAVE_DIR / 'catboost_advanced_metrics.json', 'w') as f:
        json.dump(cb_test_metrics, f, indent=2)
record_result('catboost_advanced', best_cb_params, best_cb, cb_test_metrics)

# Persist preprocessing artifacts
with open(SAVE_DIR / 'median_imputation.json', 'w') as f:
    json.dump(global_medians, f, indent=2)
with open(SAVE_DIR / 'per_city_scaler_stats.json', 'w') as f:
    json.dump({city: {'mean': {k: float(v) for k, v in stats['mean'].items()}, 'std': {k: float(v) for k, v in stats['std'].items()}} for city, stats in scaler_stats.items()}, f, indent=2)
with open(SAVE_DIR / 'advanced_features.json', 'w') as f:
    json.dump({'features': all_features}, f, indent=2)

# Summary
summary = {k: {'params': v['params'], 'metrics': v['metrics']} for k, v in results.items()}
summary_path = SAVE_DIR / f"render_last7d_advanced_training_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
with open(summary_path, 'w') as f:
    json.dump(summary, f, indent=2)

# Print best by R2 on test
best_available = [(k, v['metrics']['r2']) for k, v in results.items() if v['metrics']]
if best_available:
    best = max(best_available, key=lambda kv: kv[1])
    print('Best model R2 on test:', best)
else:
    print('No successful models evaluated')
