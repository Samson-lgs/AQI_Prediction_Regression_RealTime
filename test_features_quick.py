"""Quick test of enhanced feature engineering"""
from feature_engineering.feature_processor import FeatureProcessor
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Create synthetic data
df = pd.DataFrame({
    'timestamp': pd.date_range(start=datetime.now()-timedelta(days=2), periods=50, freq='h'),
    'pm25': np.random.uniform(30, 150, 50),
    'pm10': np.random.uniform(50, 200, 50),
    'no2': np.random.uniform(20, 100, 50),
    'so2': np.random.uniform(5, 50, 50),
    'o3': np.random.uniform(10, 80, 50),
    'aqi_value': np.random.randint(50, 200, 50),
    'temperature': np.random.uniform(15, 35, 50),
    'humidity': np.random.uniform(40, 90, 50),
    'wind_speed': np.random.uniform(1, 10, 50)
})

# Create features
processor = FeatureProcessor()
df_features = processor.create_features(df)

print(f'✅ Feature engineering successful!')
print(f'Input: {len(df)} rows × {len(df.columns)} columns')
print(f'Output: {len(df_features)} rows × {len(df_features.columns)} columns')
print(f'New features created: {len(df_features.columns) - len(df.columns)}')
print(f'\nSample features from latest row:')
print(f'  hour: {df_features.iloc[-1]["hour"]}')
print(f'  season: {df_features.iloc[-1]["season"]}')
print(f'  is_weekend: {df_features.iloc[-1]["is_weekend"]}')
print(f'  pm25_ma_24: {df_features.iloc[-1]["pm25_ma_24"]:.1f}')
print(f'  pm25_pm10_ratio: {df_features.iloc[-1]["pm25_pm10_ratio"]:.3f}')
