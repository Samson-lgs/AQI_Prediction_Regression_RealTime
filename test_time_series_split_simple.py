"""
Simple Time-Series Split Test (No Model Dependencies)

This script tests the time-series splitting logic without requiring TensorFlow or model dependencies.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SimpleTimeSeriesSplitter:
    """Simplified version for testing without model dependencies"""
    
    def __init__(self, train_ratio=0.7, val_ratio=0.15, test_ratio=0.15):
        if not np.isclose(train_ratio + val_ratio + test_ratio, 1.0):
            raise ValueError("Train, validation, and test ratios must sum to 1.0")
        
        self.train_ratio = train_ratio
        self.val_ratio = val_ratio
        self.test_ratio = test_ratio
    
    def time_series_split(self, X, y, timestamps=None):
        """Split data using time-series-aware approach"""
        n = len(X)
        
        # Calculate split indices
        train_end = int(n * self.train_ratio)
        val_end = int(n * (self.train_ratio + self.val_ratio))
        
        # Split chronologically
        X_train = X[:train_end]
        y_train = y[:train_end]
        
        X_val = X[train_end:val_end]
        y_val = y[train_end:val_end]
        
        X_test = X[val_end:]
        y_test = y[val_end:]
        
        # Log split information
        logger.info(f"Time-Series Split Summary:")
        logger.info(f"  Total samples: {n}")
        logger.info(f"  Training set: {len(X_train)} samples ({len(X_train)/n*100:.1f}%)")
        logger.info(f"  Validation set: {len(X_val)} samples ({len(X_val)/n*100:.1f}%)")
        logger.info(f"  Test set: {len(X_test)} samples ({len(X_test)/n*100:.1f}%)")
        
        if timestamps is not None and len(timestamps) == n:
            logger.info(f"  Training period: {timestamps[0]} to {timestamps[train_end-1]}")
            logger.info(f"  Validation period: {timestamps[train_end]} to {timestamps[val_end-1]}")
            logger.info(f"  Test period: {timestamps[val_end]} to {timestamps[-1]}")
        
        return X_train, X_val, X_test, y_train, y_val, y_test


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
    
    # Initialize splitter with default ratios (70% train, 15% val, 15% test)
    print("\n2. Initializing time-series splitter...")
    splitter = SimpleTimeSeriesSplitter(train_ratio=0.7, val_ratio=0.15, test_ratio=0.15)
    print("   ✓ Splitter initialized")
    
    # Perform time-series split
    print("\n3. Performing time-series-aware split...")
    X_train, X_val, X_test, y_train, y_val, y_test = splitter.time_series_split(
        X, y, timestamps
    )
    
    # Verify split properties
    print("\n4. Verifying split properties...")
    
    # Check sizes
    total = len(X)
    assert len(X_train) == 700, f"Training set size incorrect: {len(X_train)} != 700"
    assert len(X_val) == 150, f"Validation set size incorrect: {len(X_val)} != 150"
    assert len(X_test) == 150, f"Test set size incorrect: {len(X_test)} != 150"
    print("   ✓ Split sizes are correct (700/150/150)")
    
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
    print(f"\n7. Testing custom split ratios (60/20/20)...")
    custom_splitter = SimpleTimeSeriesSplitter(train_ratio=0.6, val_ratio=0.2, test_ratio=0.2)
    X_train2, X_val2, X_test2, y_train2, y_val2, y_test2 = custom_splitter.time_series_split(
        X, y, timestamps
    )
    
    assert len(X_train2) == 600, f"Custom training size incorrect: {len(X_train2)} != 600"
    assert len(X_val2) == 200, f"Custom validation size incorrect: {len(X_val2)} != 200"
    assert len(X_test2) == 200, f"Custom test size incorrect: {len(X_test2)} != 200"
    print("   ✓ Custom split ratios work correctly (600/200/200)")
    
    # Test ratio validation
    print(f"\n8. Testing ratio validation...")
    try:
        invalid_splitter = SimpleTimeSeriesSplitter(train_ratio=0.5, val_ratio=0.3, test_ratio=0.3)
        print("   ✗ Should have raised ValueError for invalid ratios!")
        assert False, "Failed to catch invalid ratios"
    except ValueError as e:
        print(f"   ✓ Correctly rejected invalid ratios: {e}")
    
    # Test with different sample sizes
    print(f"\n9. Testing with different data sizes...")
    for n in [100, 500, 2000]:
        X_test, y_test, ts_test = create_synthetic_time_series_data(n_samples=n)
        X_tr, X_v, X_te, y_tr, y_v, y_te = splitter.time_series_split(X_test, y_test, ts_test)
        expected_train = int(n * 0.7)
        expected_val = int(n * 0.15)
        assert len(X_tr) == expected_train, f"Size {n}: train size mismatch"
        assert len(X_v) == expected_val, f"Size {n}: val size mismatch"
        print(f"   ✓ Correctly split {n} samples into {len(X_tr)}/{len(X_v)}/{len(X_te)}")
    
    print("\n" + "="*80)
    print("✅ ALL TIME-SERIES SPLIT TESTS PASSED!")
    print("="*80)
    
    print("\n📊 Key Advantages of Time-Series-Aware Splitting:")
    print("   1. ✅ Prevents data leakage from future to past")
    print("   2. ✅ Mimics real-world prediction scenarios")
    print("   3. ✅ Provides realistic performance estimates")
    print("   4. ✅ Preserves temporal dependencies and autocorrelation")
    print("   5. ✅ Validation and test sets represent future unseen data")
    
    print("\n⚠️  Why NOT Random Splitting:")
    print("   ❌ Random split breaks temporal order")
    print("   ❌ Model sees future data during training (data leakage)")
    print("   ❌ Overestimates model performance")
    print("   ❌ Ignores autocorrelation and trends")
    print("   ❌ Not representative of real deployment")
    
    print("\n📝 Implementation Summary:")
    print(f"   • Default split ratios: 70% train / 15% validation / 15% test")
    print(f"   • Chronological splitting (NO shuffling)")
    print(f"   • Customizable split ratios")
    print(f"   • Comprehensive logging with timestamps")
    print(f"   • Automatic ratio validation")


if __name__ == "__main__":
    test_time_series_split()
