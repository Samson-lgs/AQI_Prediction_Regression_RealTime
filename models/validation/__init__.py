"""
Step 6: Validation Framework for AQI Prediction Models

This module provides comprehensive validation including:
- Multi-city validation (Delhi, Mumbai, Bangalore)
- Time-series hold-out strategies (1-48 hour forecasting)
- Benchmarking against commercial APIs (IQAir, AQICN)
- Performance metrics and reporting
"""

from .multi_city_validator import MultiCityValidator
from .forecasting_validator import ForecastingValidator
from .api_benchmark import APIBenchmark
from .validation_report import ValidationReport

__all__ = [
    'MultiCityValidator',
    'ForecastingValidator',
    'APIBenchmark',
    'ValidationReport'
]
