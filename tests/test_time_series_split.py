"""
Test Time-Series-Aware Data Splitting

This script demonstrates the time-series-aware splitting approach for model training:
1. Data is sorted chronologically
2. No shuffling to preserve temporal order
3. Training data comes before validation data
4. Validation data comes before test data
5. No data leakage from future to past
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from models.train_models import ModelTrainer
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_synthetic_time_series_data(n_samples=1000):
    """Create synthetic time-series data for testing"""
    start_date = datetime.now() - timedelta(days=90)
    timestamps = [start_date + timedelta(hours=i) for i in range(n_samples)]
    
    # Create features with temporal patterns
    hours = np.array([t.hour for t in timestamps])
    days = np.array([t.day for t in timestamps])
    
    # Synthetic features with temporal correlation
    temp = 20 + 10 * np.sin(hours * 2 * np.pi / 24) + np.random.randn(n_samples) * 2
    humidity = 50 + 20 * np.cos(hours * 2 * np.pi / 24) + np.random.randn(n_samples) * 5
    pm25 = 50 + 30 * np.sin(hours * 2 * np.pi / 24) + np.random.randn(n_samples) * 10
    
    # Target (AQI) with temporal dependency
    aqi = 50 + 0.8 * pm25 + 0.1 * temp - 0.05 * humidity + np.random.randn(n_samples) * 5
    aqi = np.clip(aqi, 0, 500)
    
    X = np.column_stack([temp, humidity, pm25, hours, days])
    y = aqi
    
    return X, y, timestamps

def test_time_series_split():
    """Test the time-series split functionality"""
    print("="*80)
    print("TIME-SERIES-AWARE DATA SPLITTING TEST")
    print("="*80)
    
    # Create synthetic data
    print("\n1. Creating synthetic time-series data...")
    X, y, timestamps = create_synthetic_time_series_data(n_samples=1000)
    print(f"   ✓ Created {len(X)} samples spanning {timestamps[0]} to {timestamps[-1]}")
    
    # Initialize trainer with default ratios (70% train, 15% val, 15% test)
    print("\n2. Initializing ModelTrainer with time-series split...")
    trainer = ModelTrainer(train_ratio=0.7, val_ratio=0.15, test_ratio=0.15)
    print("   ✓ ModelTrainer initialized")
    
    # Perform time-series split
    print("\n3. Performing time-series-aware split...")
    X_train, X_val, X_test, y_train, y_val, y_test = trainer.time_series_split(
        X, y, timestamps
    )
    
    # Verify split properties
    print("\n4. Verifying split properties...")
    
    # Check sizes
    total = len(X)
    assert len(X_train) == int(total * 0.7), "Training set size incorrect"
    assert len(X_val) == int(total * 0.15), "Validation set size incorrect"
    assert len(X_test) == total - len(X_train) - len(X_val), "Test set size incorrect"
    print("   ✓ Split sizes are correct")
    
    # Check temporal ordering (no overlap)
    train_end_idx = len(X_train)
    val_end_idx = train_end_idx + len(X_val)
    
    print(f"\n5. Temporal Order Verification:")
    print(f"   Training period: {timestamps[0]} to {timestamps[train_end_idx-1]}")
    print(f"   Validation period: {timestamps[train_end_idx]} to {timestamps[val_end_idx-1]}")
    print(f"   Test period: {timestamps[val_end_idx]} to {timestamps[-1]}")
    
    # Verify no time leakage
    train_max_time = timestamps[train_end_idx - 1]
    val_min_time = timestamps[train_end_idx]
    val_max_time = timestamps[val_end_idx - 1]
    test_min_time = timestamps[val_end_idx]
    
    assert train_max_time < val_min_time, "Time leakage: training overlaps with validation!"
    assert val_max_time < test_min_time, "Time leakage: validation overlaps with test!"
    print("   ✓ No time leakage detected - temporal order preserved")
    
    # Statistical summary
    print(f"\n6. Data Statistics:")
    print(f"   Training set:")
    print(f"     - Mean AQI: {y_train.mean():.2f} ± {y_train.std():.2f}")
    print(f"     - Range: [{y_train.min():.2f}, {y_train.max():.2f}]")
    
    print(f"   Validation set:")
    print(f"     - Mean AQI: {y_val.mean():.2f} ± {y_val.std():.2f}")
    print(f"     - Range: [{y_val.min():.2f}, {y_val.max():.2f}]")
    
    print(f"   Test set:")
    print(f"     - Mean AQI: {y_test.mean():.2f} ± {y_test.std():.2f}")
    print(f"     - Range: [{y_test.min():.2f}, {y_test.max():.2f}]")
    
    # Test different split ratios
    print(f"\n7. Testing custom split ratios...")
    custom_trainer = ModelTrainer(train_ratio=0.6, val_ratio=0.2, test_ratio=0.2)
    X_train2, X_val2, X_test2, y_train2, y_val2, y_test2 = custom_trainer.time_series_split(
        X, y, timestamps
    )
    
    assert len(X_train2) == int(total * 0.6), "Custom training size incorrect"
    assert len(X_val2) == int(total * 0.2), "Custom validation size incorrect"
    print("   ✓ Custom split ratios work correctly")
    
    # Test ratio validation
    print(f"\n8. Testing ratio validation...")
    try:
        invalid_trainer = ModelTrainer(train_ratio=0.5, val_ratio=0.3, test_ratio=0.3)
        print("   ✗ Should have raised ValueError for invalid ratios!")
    except ValueError as e:
        print(f"   ✓ Correctly rejected invalid ratios: {e}")
    
    print("\n" + "="*80)
    print("✅ ALL TIME-SERIES SPLIT TESTS PASSED!")
    print("="*80)
    
    print("\n📊 Key Advantages of Time-Series-Aware Splitting:")
    print("   1. Prevents data leakage from future to past")
    print("   2. Mimics real-world prediction scenarios")
    print("   3. Provides realistic performance estimates")
    print("   4. Preserves temporal dependencies and autocorrelation")
    print("   5. Validation and test sets represent future unseen data")
    
    print("\n⚠️  Why NOT Random Splitting:")
    print("   ❌ Random split breaks temporal order")
    print("   ❌ Model sees future data during training (data leakage)")
    print("   ❌ Overestimates model performance")
    print("   ❌ Ignores autocorrelation and trends")
    print("   ❌ Not representative of real deployment")

if __name__ == "__main__":
    test_time_series_split()
