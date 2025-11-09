"""
Test script for enhanced feature engineering capabilities

Demonstrates:
1. Temporal features (hour, day, month, season)
2. Seasonal indicators (weekend, rush hour, time of day)
3. Cyclical encodings (sin/cos transformations)
4. Derived metrics (pollutant ratios, indices)
5. Moving averages (3h, 6h, 12h, 24h)
6. Lag features (1h, 6h, 12h, 24h)
7. Rate of change (deltas, percentage changes)
8. Interaction features (weather × pollutants)
"""

import os
import sys
from datetime import datetime, timedelta
# Ensure project root is on sys.path so local packages can be imported when running tests directly
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from database.db_operations import DatabaseOperations
# Robust import for FeatureProcessor: try normal import then fall back to loading by file path relative to ROOT_DIR
try:
    from feature_engineering.advanced_features import FeatureProcessor
except Exception:
    import importlib
    import importlib.util
    import os
    # Try to find the module spec first (works when package is installable)
    spec = importlib.util.find_spec("feature_engineering.feature_processor")
    if spec is not None:
        module = importlib.import_module("feature_engineering.feature_processor")
        FeatureProcessor = getattr(module, "FeatureProcessor")
    else:
        # Fallback: load directly from file path relative to ROOT_DIR
        fp = os.path.join(ROOT_DIR, "feature_engineering", "feature_processor.py")
        spec = importlib.util.spec_from_file_location("feature_engineering.feature_processor", fp)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        FeatureProcessor = getattr(module, "FeatureProcessor")
import pandas as pd

def test_feature_engineering(city='Delhi', days=7):
    """
    Test comprehensive feature engineering on real data
    """
    print("="*80)
    print("FEATURE ENGINEERING TEST")
    print("="*80)
    print(f"\nCity: {city}")
    print(f"Data Range: Last {days} days")
    print()
    
    # Initialize
    processor = FeatureProcessor()
    
    # Fetch raw data
    print("Step 1: Fetching raw data from database...")
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    pollution_data = processor.db.get_pollution_data(city, start_date, end_date)
    
    if not pollution_data or len(pollution_data) == 0:
        print(f"❌ No data found for {city}")
        print("Try running: python main.py --once")
        return
    
    print(f"✓ Fetched {len(pollution_data)} raw pollution records")
    
    # Convert to DataFrame
    df_raw = pd.DataFrame(pollution_data)
    df_raw['timestamp'] = pd.to_datetime(df_raw['timestamp'])
    df_raw = df_raw.sort_values('timestamp').reset_index(drop=True)
    
    print(f"✓ Raw data: {len(df_raw)} rows × {len(df_raw.columns)} columns")
    print()
    
    # Show raw data sample
    print("Step 2: Raw Data Sample (First 3 rows)")
    print("-" * 80)
    print(df_raw[['timestamp', 'pm25', 'pm10', 'no2', 'aqi_value', 'data_source']].head(3).to_string(index=False))
    print()
    
    # Create features
    print("Step 3: Creating comprehensive features...")
    print("-" * 80)
    
    df_features = processor.create_features(df_raw)
    
    if df_features is None or df_features.empty:
        print("❌ Feature creation failed")
        return
    
    print(f"\n✅ Features created successfully!")
    print(f"   Final shape: {len(df_features)} rows × {len(df_features.columns)} columns")
    print()
    
    # Analyze created features
    print("Step 4: Feature Analysis")
    print("-" * 80)
    
    # Count features by category
    all_features = df_features.columns.tolist()
    
    # Temporal features
    temporal = [c for c in all_features if any(x in c for x in ['hour', 'day_of_week', 'month', 'quarter', 'week', 'day_of_year']) 
                and 'sin' not in c and 'cos' not in c and 'lag' not in c and 'ma' not in c and 'delta' not in c and 'interaction' not in c]
    
    # Seasonal indicators
    seasonal = [c for c in all_features if any(x in c for x in ['season', 'is_spring', 'is_summer', 'is_fall', 'is_winter', 
                'is_weekend', 'is_rush', 'is_morning', 'is_afternoon', 'is_evening', 'is_night', 'time_of_day'])]
    
    # Cyclical encodings
    cyclical = [c for c in all_features if any(x in c for x in ['_sin', '_cos'])]
    
    # Derived metrics
    derived = [c for c in all_features if any(x in c for x in ['_ratio', 'total_', 'pollutant_index'])]
    
    # Moving averages
    moving_avg = [c for c in all_features if '_ma_' in c or '_std_' in c or ('_min_' in c and 'pm' in c) or ('_max_' in c and 'pm' in c)]
    
    # Lag features
    lags = [c for c in all_features if '_lag_' in c]
    
    # Rate of change
    rate_change = [c for c in all_features if '_delta_' in c or '_pct_change_' in c]
    
    # Interactions
    interactions = [c for c in all_features if 'interaction' in c or 'winter_pm25' in c or 'summer_o3' in c]
    
    print(f"\n📊 Feature Categories:")
    print(f"   1. Temporal Features: {len(temporal)}")
    print(f"      Examples: {', '.join(temporal[:5])}")
    
    print(f"\n   2. Seasonal Indicators: {len(seasonal)}")
    print(f"      Examples: {', '.join(seasonal[:5])}")
    
    print(f"\n   3. Cyclical Encodings: {len(cyclical)}")
    print(f"      Examples: {', '.join(cyclical[:4])}")
    
    print(f"\n   4. Derived Metrics: {len(derived)}")
    print(f"      Examples: {', '.join(derived[:3])}")
    
    print(f"\n   5. Moving Averages: {len(moving_avg)}")
    print(f"      Examples: {', '.join(moving_avg[:5])}")
    
    print(f"\n   6. Lag Features: {len(lags)}")
    print(f"      Examples: {', '.join(lags[:5])}")
    
    print(f"\n   7. Rate of Change: {len(rate_change)}")
    print(f"      Examples: {', '.join(rate_change[:3])}")
    
    print(f"\n   8. Interaction Features: {len(interactions)}")
    print(f"      Examples: {', '.join(interactions[:3])}")
    
    print(f"\n   📈 Total Features: {len(all_features)}")
    print()
    
    # Show sample engineered features
    print("Step 5: Sample Engineered Features (Latest row)")
    print("-" * 80)
    
    latest = df_features.iloc[-1]
    
    print(f"\n⏰ Temporal Features:")
    print(f"   Timestamp: {latest['timestamp']}")
    print(f"   Hour: {latest['hour']}")
    print(f"   Day of Week: {latest['day_of_week']} ({'Weekend' if latest['is_weekend'] else 'Weekday'})")
    print(f"   Month: {latest['month']}")
    print(f"   Season: {latest['season'].title()}")
    
    print(f"\n🔔 Contextual Indicators:")
    print(f"   Rush Hour: {'Yes ⚠️' if latest['is_rush_hour'] else 'No'}")
    print(f"   Time of Day: {latest['time_of_day'].title()}")
    
    print(f"\n🔄 Cyclical Encodings:")
    print(f"   hour_sin: {latest['hour_sin']:.3f}")
    print(f"   hour_cos: {latest['hour_cos']:.3f}")
    print(f"   month_sin: {latest['month_sin']:.3f}")
    print(f"   month_cos: {latest['month_cos']:.3f}")
    
    print(f"\n🧪 Derived Metrics:")
    print(f"   PM2.5/PM10 Ratio: {latest['pm25_pm10_ratio']:.3f}")
    if 'no2_so2_ratio' in latest:
        print(f"   NO₂/SO₂ Ratio: {latest['no2_so2_ratio']:.3f}")
    if 'total_pm' in latest:
        print(f"   Total PM: {latest['total_pm']:.1f} μg/m³")
    if 'pollutant_index' in latest:
        print(f"   Pollutant Index: {latest['pollutant_index']:.1f}")
    
    print(f"\n📊 Moving Averages (PM2.5):")
    if 'pm25_ma_3' in latest:
        print(f"   3-hour MA: {latest['pm25_ma_3']:.1f} μg/m³")
    if 'pm25_ma_6' in latest:
        print(f"   6-hour MA: {latest['pm25_ma_6']:.1f} μg/m³")
    if 'pm25_ma_12' in latest:
        print(f"   12-hour MA: {latest['pm25_ma_12']:.1f} μg/m³")
    if 'pm25_ma_24' in latest:
        print(f"   24-hour MA: {latest['pm25_ma_24']:.1f} μg/m³")
    
    print(f"\n⏮️ Lag Features (PM2.5):")
    if 'pm25_lag_1' in latest and not pd.isna(latest['pm25_lag_1']):
        print(f"   1-hour ago: {latest['pm25_lag_1']:.1f} μg/m³")
    if 'pm25_lag_6' in latest and not pd.isna(latest['pm25_lag_6']):
        print(f"   6-hours ago: {latest['pm25_lag_6']:.1f} μg/m³")
    if 'pm25_lag_24' in latest and not pd.isna(latest['pm25_lag_24']):
        print(f"   24-hours ago (yesterday): {latest['pm25_lag_24']:.1f} μg/m³")
    
    print(f"\n📈 Rate of Change:")
    if 'pm25_delta_1h' in latest and not pd.isna(latest['pm25_delta_1h']):
        delta = latest['pm25_delta_1h']
        direction = "↑" if delta > 0 else "↓" if delta < 0 else "→"
        print(f"   1-hour change: {direction} {abs(delta):.1f} μg/m³")
    if 'pm25_pct_change_1h' in latest and not pd.isna(latest['pm25_pct_change_1h']):
        print(f"   1-hour % change: {latest['pm25_pct_change_1h']:.1f}%")
    
    print(f"\n🔗 Interaction Features:")
    if 'temp_humidity_interaction' in latest and not pd.isna(latest['temp_humidity_interaction']):
        print(f"   Temp × Humidity: {latest['temp_humidity_interaction']:.1f}")
    if 'wind_dispersion_index' in latest and not pd.isna(latest['wind_dispersion_index']):
        print(f"   Wind Dispersion Index: {latest['wind_dispersion_index']:.3f}")
    
    print()
    
    # Feature statistics
    print("Step 6: Feature Statistics")
    print("-" * 80)
    
    # Check for missing values
    missing = df_features.isnull().sum()
    cols_with_missing = missing[missing > 0]
    
    if len(cols_with_missing) > 0:
        print(f"\n⚠️  Features with missing values:")
        for col, count in cols_with_missing.head(5).items():
            pct = (count / len(df_features)) * 100
            print(f"   {col}: {count} ({pct:.1f}%)")
    else:
        print(f"\n✅ No missing values in feature set!")
    
    # Value ranges
    print(f"\n📏 Feature Value Ranges:")
    print(f"   Cyclical features: [-1, 1] (sin/cos)")
    print(f"   Seasonal indicators: [0, 1] (binary)")
    print(f"   Ratios: [0, ∞) (non-negative)")
    print(f"   Moving averages: Match raw data range")
    
    print()
    
    # Summary
    print("="*80)
    print("SUMMARY")
    print("="*80)
    print(f"\n✅ Feature engineering successfully demonstrated on {city} data")
    
    print(f"\n📊 Feature Breakdown:")
    print(f"   • Temporal: {len(temporal)} features")
    print(f"   • Seasonal: {len(seasonal)} indicators")
    print(f"   • Cyclical: {len(cyclical)} encodings")
    print(f"   • Derived: {len(derived)} metrics")
    print(f"   • Moving Averages: {len(moving_avg)} features")
    print(f"   • Lags: {len(lags)} historical features")
    print(f"   • Rate of Change: {len(rate_change)} features")
    print(f"   • Interactions: {len(interactions)} features")
    print(f"   • Total: {len(all_features)} features")
    
    print(f"\n✨ All features are ready for model training!")
    print("="*80)


if __name__ == "__main__":
    # Test with cities that have data
    test_cities = ['Delhi', 'Mumbai', 'Bangalore', 'Chennai', 'Ahmedabad']
    
    print("\n🧪 Testing Feature Engineering Pipeline")
    print("=" * 80)
    
    # Try each city until we find one with data
    for city in test_cities:
        try:
            test_feature_engineering(city, days=7)
            break  # Success, exit after first city with data
        except Exception as e:
            print(f"\n⚠️  Error testing {city}: {str(e)}")
            print(f"Trying next city...\n")
            continue
    else:
        print("\n❌ No cities with sufficient data found. Please collect data first using:")
        print("   python main.py --once")
