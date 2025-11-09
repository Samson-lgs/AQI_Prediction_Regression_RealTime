# Archive Directory

This directory contains deprecated or superseded code kept for reference.

## Archived Files

### feature_processor.py.DEPRECATED
- **Original Location**: `feature_engineering/feature_processor.py`
- **Archived Date**: November 9, 2025
- **Reason**: Replaced by `feature_engineering/advanced_features.py`
- **Status**: Do not use in new code
- **Description**: Original feature engineering implementation with ~400 lines. Replaced by cleaner, more modular implementation in `advanced_features.py` which is currently used by the training pipeline.

**Migration**: Use `feature_engineering/advanced_features.py` and `AdvancedFeatureEngineer` class instead.

---

## Why Archive Instead of Delete?

Files are archived rather than deleted to:
1. Maintain historical reference for development decisions
2. Allow rollback if needed
3. Preserve documentation of previous approaches
4. Aid in understanding project evolution

## Cleanup Policy

Archived files older than 1 year and confirmed unused may be permanently removed during maintenance cycles.
