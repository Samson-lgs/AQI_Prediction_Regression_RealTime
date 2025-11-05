# Time-Series-Aware Data Splitting Documentation

## Overview

This document explains the implementation of time-series-aware data splitting for the AQI prediction model development pipeline. This approach ensures proper temporal ordering and prevents data leakage, which are critical for accurate time-series forecasting.

---

## Table of Contents

1. [Why Time-Series Splitting Matters](#why-time-series-splitting-matters)
2. [Implementation Details](#implementation-details)
3. [Usage Guide](#usage-guide)
4. [Validation and Testing](#validation-and-testing)
5. [Best Practices](#best-practices)
6. [Common Pitfalls](#common-pitfalls)

---

## Why Time-Series Splitting Matters

### The Problem with Random Splitting

Traditional random train-test splitting (using `train_test_split` with shuffle=True) is **inappropriate** for time-series data because:

1. **Data Leakage**: Model sees future data during training, leading to unrealistic performance estimates
2. **Broken Temporal Dependencies**: Autocorrelation and trends are disrupted
3. **Overoptimistic Metrics**: Performance metrics don't reflect real-world deployment scenarios
4. **Invalid Predictions**: Model learns patterns that won't exist when predicting future values

### Time-Series Splitting Approach

Time-series-aware splitting ensures:

1. **Chronological Order**: Training data comes before validation, validation before test
2. **No Data Leakage**: Model never sees future data during training
3. **Realistic Evaluation**: Test performance reflects real deployment scenarios
4. **Preserved Dependencies**: Temporal patterns and autocorrelation remain intact

### Visual Representation

```
Timeline: ──────────────────────────────────────────────────────────→
         Past                                                    Future

Random Split (WRONG):
  [Train] ──── [Test] ──── [Train] ──── [Test] ──── [Train]
  ❌ Data leakage, broken temporal order

Time-Series Split (CORRECT):
  [──── Training ────][─ Validation ─][── Test ──]
  ✅ Proper temporal order, no leakage
```

---

## Implementation Details

### Core Function: `time_series_split()`

Located in `train_models.py`, the `ModelTrainer` class includes:

```python
def time_series_split(self, X, y, timestamps=None):
    """
    Split data using time-series-aware approach
    
    This ensures:
    1. Training data comes before validation data
    2. Validation data comes before test data
    3. No data leakage from future to past
    4. Temporal ordering is preserved
    
    Args:
        X: Feature matrix (numpy array)
        y: Target values (numpy array)
        timestamps: Optional timestamps for logging split points
        
    Returns:
        X_train, X_val, X_test, y_train, y_val, y_test
    """
    n = len(X)
    
    # Calculate split indices based on time order (no shuffling!)
    train_end = int(n * self.train_ratio)
    val_end = int(n * (self.train_ratio + self.val_ratio))
    
    # Split data chronologically
    X_train = X[:train_end]
    y_train = y[:train_end]
    
    X_val = X[train_end:val_end]
    y_val = y[train_end:val_end]
    
    X_test = X[val_end:]
    y_test = y[val_end:]
    
    return X_train, X_val, X_test, y_train, y_val, y_test
```

### Default Split Ratios

- **Training**: 70% (earliest data)
- **Validation**: 15% (middle period)
- **Test**: 15% (most recent data)

These ratios can be customized during initialization:

```python
trainer = ModelTrainer(train_ratio=0.6, val_ratio=0.2, test_ratio=0.2)
```

### Key Implementation Details

1. **Data Sorting**: Data is explicitly sorted by timestamp before splitting
   ```python
   df = df.sort_values('timestamp').reset_index(drop=True)
   ```

2. **No Shuffling**: Unlike random splitting, NO shuffling is performed
   ```python
   # ❌ WRONG: Random split with shuffle
   train_test_split(X, y, test_size=0.2, random_state=42)
   
   # ✅ CORRECT: Time-series split without shuffle
   X_train = X[:train_end]
   ```

3. **Timestamp Logging**: Split points are logged with actual timestamps for transparency

4. **Ratio Validation**: Input ratios are validated to ensure they sum to 1.0

---

## Usage Guide

### Basic Usage

```python
from train_models import ModelTrainer

# Initialize with default ratios (70/15/15)
trainer = ModelTrainer()

# Train models for a specific city
results = trainer.train_all_models('Delhi')
```

### Custom Split Ratios

```python
# Initialize with custom ratios (60/20/20)
trainer = ModelTrainer(
    train_ratio=0.6,
    val_ratio=0.2,
    test_ratio=0.2
)

results = trainer.train_all_models('Mumbai')
```

### Manual Splitting

```python
import numpy as np
from train_models import ModelTrainer

# Create trainer
trainer = ModelTrainer()

# Your data (ensure it's sorted by time!)
X = np.array([...])  # Features
y = np.array([...])  # Target
timestamps = np.array([...])  # Timestamps

# Perform split
X_train, X_val, X_test, y_train, y_val, y_test = trainer.time_series_split(
    X, y, timestamps
)

# Train your model
model.fit(X_train, y_train)
val_score = model.score(X_val, y_val)
test_score = model.score(X_test, y_test)
```

---

## Validation and Testing

### Test Script: `test_time_series_split.py`

Run the comprehensive test suite:

```bash
python test_time_series_split.py
```

This script validates:

1. ✅ Split sizes are correct
2. ✅ Temporal order is preserved
3. ✅ No time leakage between sets
4. ✅ Custom ratios work correctly
5. ✅ Invalid ratios are rejected

### Expected Output

```
================================================================================
TIME-SERIES-AWARE DATA SPLITTING TEST
================================================================================

1. Creating synthetic time-series data...
   ✓ Created 1000 samples spanning 2024-08-07 to 2024-11-05

2. Initializing ModelTrainer with time-series split...
   ✓ ModelTrainer initialized

3. Performing time-series-aware split...
   Time-Series Split Summary:
     Total samples: 1000
     Training set: 700 samples (70.0%)
     Validation set: 150 samples (15.0%)
     Test set: 150 samples (15.0%)
     Training period: 2024-08-07 to 2024-09-15
     Validation period: 2024-09-15 to 2024-10-08
     Test period: 2024-10-08 to 2024-11-05

✅ ALL TIME-SERIES SPLIT TESTS PASSED!
```

---

## Best Practices

### 1. Always Sort Data First

```python
# ✅ CORRECT: Sort before splitting
df = df.sort_values('timestamp').reset_index(drop=True)
X_train, X_val, X_test, y_train, y_val, y_test = trainer.time_series_split(X, y)

# ❌ WRONG: Split unsorted data
X_train, X_val, X_test, y_train, y_val, y_test = trainer.time_series_split(X, y)
```

### 2. Use Sufficient Training Data

- Minimum: 60% training data
- Recommended: 70% training data
- Ensure training set has enough samples to learn patterns

### 3. Consider Data Characteristics

For **seasonal data** (daily/weekly/monthly patterns):
- Ensure training set covers full seasonal cycles
- Example: For weekly patterns, use at least 4-8 weeks of training data

For **trending data** (continuously increasing/decreasing):
- Use recent data for training
- Test set should be the most recent period

### 4. Validation Set Usage

- Use validation set for:
  - Hyperparameter tuning
  - Early stopping
  - Model selection
- **Never** use validation set for final performance reporting

### 5. Test Set Usage

- Reserve test set for:
  - Final performance evaluation
  - Model comparison
  - Reporting to stakeholders
- **Only evaluate once** on test set to avoid overfitting

### 6. Cross-Validation Considerations

For time-series cross-validation, use `TimeSeriesSplit`:

```python
from sklearn.model_selection import TimeSeriesSplit

tscv = TimeSeriesSplit(n_splits=5)
for train_idx, val_idx in tscv.split(X):
    X_train, X_val = X[train_idx], X[val_idx]
    y_train, y_val = y[train_idx], y[val_idx]
    # Train and evaluate
```

---

## Common Pitfalls

### ❌ Pitfall 1: Using Random Splitting

```python
# WRONG: Random split destroys temporal order
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)
```

**Impact**: Data leakage, overoptimistic metrics, poor real-world performance

### ❌ Pitfall 2: Not Sorting Data

```python
# WRONG: Splitting without sorting
X_train = X[:train_end]  # If X is not sorted by time
```

**Impact**: Training on future data, validation on past data, meaningless results

### ❌ Pitfall 3: Overlapping Periods

```python
# WRONG: Using same data for training and validation
X_val = X[int(n*0.6):int(n*0.8)]
X_train = X[:int(n*0.7)]  # Overlaps with validation!
```

**Impact**: Data leakage, inflated validation performance

### ❌ Pitfall 4: Test Set Contamination

```python
# WRONG: Using test set for model selection
best_model = None
best_score = 0
for model in models:
    score = model.score(X_test, y_test)  # Don't do this!
    if score > best_score:
        best_model = model
```

**Impact**: Overfitting to test set, unreliable final metrics

### ❌ Pitfall 5: Insufficient Training Data

```python
# WRONG: Too small training set
trainer = ModelTrainer(train_ratio=0.4, val_ratio=0.3, test_ratio=0.3)
```

**Impact**: Model can't learn patterns, poor generalization

---

## Performance Considerations

### Computational Efficiency

Time-series splitting is **faster** than random splitting:
- No shuffling required
- Simple array slicing
- O(n) complexity

### Memory Usage

```python
# Memory-efficient splitting (views, not copies)
X_train = X[:train_end]  # View of original array
X_val = X[train_end:val_end]  # Another view

# If you need copies (for modifications):
X_train = X[:train_end].copy()
```

---

## Integration with Model Training

### Modified Training Pipeline

The `train_all_models()` method now:

1. Fetches data and sorts by timestamp
2. Extracts features and target
3. Performs time-series split
4. Trains all models
5. Evaluates on validation and test sets

```python
def train_all_models(self, city):
    # 1. Fetch and sort data
    df = self.processor.prepare_training_data(city, days=90)
    df = df.sort_values('timestamp').reset_index(drop=True)
    
    # 2. Extract features and target
    X = df[feature_cols].values
    y = df['aqi_value'].values
    
    # 3. Time-series split
    X_train, X_val, X_test, y_train, y_val, y_test = self.time_series_split(
        X, y, df['timestamp'].values
    )
    
    # 4. Train models
    for model_name, model in self.models.items():
        model.train(X_train, y_train)
        model.evaluate(X_test, y_test)
```

---

## Methodology Compliance

This implementation satisfies **Step 2 of Model Development**:

✅ **"Split data into training, validation, and test sets using time-series-aware sampling"**

Key compliance points:
1. Three distinct sets: training, validation, test
2. Time-series-aware approach (chronological splitting)
3. No data leakage
4. Proper temporal ordering
5. Configurable split ratios
6. Comprehensive logging and validation

---

## References

### Academic Literature

1. **Bergmeir, C., & Benítez, J. M. (2012)**. "On the use of cross-validation for time series predictor evaluation." Information Sciences, 191, 192-213.

2. **Tashman, L. J. (2000)**. "Out-of-sample tests of forecasting accuracy: an analysis and review." International Journal of Forecasting, 16(4), 437-450.

3. **Hyndman, R. J., & Athanasopoulos, G. (2018)**. "Forecasting: principles and practice." OTexts.

### Scikit-learn Documentation

- [TimeSeriesSplit](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html)
- [Cross-validation for time series](https://scikit-learn.org/stable/modules/cross_validation.html#time-series-split)

---

## Summary

### Key Takeaways

1. ✅ Time-series splitting preserves temporal order
2. ✅ Prevents data leakage from future to past
3. ✅ Provides realistic performance estimates
4. ✅ Essential for time-series forecasting tasks
5. ✅ Default ratios: 70% train, 15% validation, 15% test

### Quick Start

```python
from train_models import ModelTrainer

# Initialize and train
trainer = ModelTrainer()
results = trainer.train_all_models('Delhi')

# Check results
print(results)
```

---

**Last Updated**: November 5, 2025  
**Version**: 1.0.0  
**Author**: AQI Prediction System Team
