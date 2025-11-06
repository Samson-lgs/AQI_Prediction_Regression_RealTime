"""
Quick test script to verify Step 6 validation framework

Tests each component with synthetic data to ensure integration works
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_synthetic_data(n_samples=500, n_cities=3):
    """Create synthetic AQI data for testing"""
    logger.info(f"Creating synthetic dataset with {n_samples} samples...")
    
    cities = ['Delhi', 'Mumbai', 'Bangalore'][:n_cities]
    timestamps = pd.date_range(
        start=datetime.now() - timedelta(days=30),
        periods=n_samples,
        freq='1H'
    )
    
    data = []
    for i in range(n_samples):
        city = cities[i % n_cities]
        ts = timestamps[i]
        
        # Generate correlated features
        base_aqi = 100 + 50 * np.sin(i / 24) + np.random.normal(0, 20)
        
        row = {
            'city': city,
            'timestamp': ts,
            'aqi_value': max(0, base_aqi),
            'pm25': base_aqi * 0.6 + np.random.normal(0, 10),
            'pm10': base_aqi * 0.8 + np.random.normal(0, 15),
            'no2': base_aqi * 0.3 + np.random.normal(0, 5),
            'so2': base_aqi * 0.2 + np.random.normal(0, 3),
            'co': base_aqi * 0.4 + np.random.normal(0, 8),
            'o3': base_aqi * 0.5 + np.random.normal(0, 7),
            'temperature': 25 + 10 * np.sin(i / 24) + np.random.normal(0, 3),
            'humidity': 60 + 20 * np.cos(i / 24) + np.random.normal(0, 5),
            'wind_speed': 5 + 3 * np.random.random(),
            'pressure': 1013 + np.random.normal(0, 5),
            'precipitation': max(0, np.random.normal(0, 2)),
        }
        
        data.append(row)
    
    df = pd.DataFrame(data)
    logger.info(f"Created dataset: {len(df)} rows, {len(df.columns)} columns")
    return df


def test_multi_city_validator():
    """Test MultiCityValidator"""
    logger.info("\n" + "="*80)
    logger.info("TEST 1: Multi-City Validator")
    logger.info("="*80)
    
    try:
        from models.validation.multi_city_validator import MultiCityValidator
        from sklearn.linear_model import LinearRegression
        
        # Create test data
        data = create_synthetic_data(n_samples=300, n_cities=3)
        
        # Create simple model
        model = LinearRegression()
        models = {'TestModel': model}
        
        # Run validation
        validator = MultiCityValidator(validation_cities=['Delhi', 'Mumbai', 'Bangalore'])
        results = validator.validate_all_cities(models, data, test_size=0.2)
        
        # Generate summary
        summary = validator.generate_summary()
        
        logger.info("✅ MultiCityValidator test PASSED")
        logger.info(f"\nResults summary:\n{summary.head()}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ MultiCityValidator test FAILED: {e}", exc_info=True)
        return False


def test_forecasting_validator():
    """Test ForecastingValidator"""
    logger.info("\n" + "="*80)
    logger.info("TEST 2: Forecasting Validator")
    logger.info("="*80)
    
    try:
        from models.validation.forecasting_validator import ForecastingValidator
        from sklearn.linear_model import LinearRegression
        
        # Create test data
        data = create_synthetic_data(n_samples=300, n_cities=1)
        
        # Create simple model
        model = LinearRegression()
        models = {'TestModel': model}
        
        # Feature columns
        feature_cols = ['pm25', 'pm10', 'no2', 'so2', 'co', 'o3', 
                       'temperature', 'humidity', 'wind_speed', 'pressure']
        
        # Run validation
        validator = ForecastingValidator(horizons=[1, 6, 12])
        results = validator.multi_horizon_validation(
            models, data, feature_cols, city='Delhi'
        )
        
        # Generate summary
        summary = validator.generate_summary()
        
        logger.info("✅ ForecastingValidator test PASSED")
        logger.info(f"\nResults summary:\n{summary.head()}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ ForecastingValidator test FAILED: {e}", exc_info=True)
        return False


def test_api_benchmark():
    """Test APIBenchmark"""
    logger.info("\n" + "="*80)
    logger.info("TEST 3: API Benchmark")
    logger.info("="*80)
    
    try:
        from models.validation.api_benchmark import APIBenchmark
        
        # Create benchmark instance (no API keys needed for research comparison)
        benchmark = APIBenchmark()
        
        # Test research comparison
        mock_results = {
            'metrics': {
                'rmse': 40.5,
                'mae': 32.1,
                'r2': 0.85
            }
        }
        
        comparison = benchmark.compare_with_research_benchmarks(
            mock_results, 'Delhi', 'TestModel'
        )
        
        logger.info("✅ APIBenchmark test PASSED")
        logger.info(f"\nComparison result: {comparison}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ APIBenchmark test FAILED: {e}", exc_info=True)
        return False


def test_validation_report():
    """Test ValidationReport"""
    logger.info("\n" + "="*80)
    logger.info("TEST 4: Validation Report")
    logger.info("="*80)
    
    try:
        from models.validation.validation_report import ValidationReport
        
        # Create dummy results
        multi_city_results = {
            'TestModel': {
                'Delhi': {
                    'metrics': {'r2': 0.85, 'rmse': 35.2, 'mae': 28.1}
                },
                'Mumbai': {
                    'metrics': {'r2': 0.82, 'rmse': 38.5, 'mae': 30.3}
                }
            }
        }
        
        forecasting_results = {
            'TestModel': {
                1: {'metrics': {'rmse': 30.1, 'mae': 24.5, 'r2': 0.87}},
                6: {'metrics': {'rmse': 35.8, 'mae': 28.9, 'r2': 0.83}}
            }
        }
        
        benchmark_results = {'research_comparisons': {}}
        
        # Generate report
        reporter = ValidationReport()
        report = reporter.generate_summary_report(
            multi_city_results,
            forecasting_results,
            benchmark_results
        )
        
        logger.info("✅ ValidationReport test PASSED")
        logger.info(f"\nReport metadata: {report['metadata']}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ ValidationReport test FAILED: {e}", exc_info=True)
        return False


def main():
    """Run all tests"""
    logger.info("="*80)
    logger.info("STEP 6 VALIDATION FRAMEWORK - INTEGRATION TEST")
    logger.info("="*80)
    
    results = {
        'MultiCityValidator': test_multi_city_validator(),
        'ForecastingValidator': test_forecasting_validator(),
        'APIBenchmark': test_api_benchmark(),
        'ValidationReport': test_validation_report()
    }
    
    logger.info("\n" + "="*80)
    logger.info("TEST RESULTS SUMMARY")
    logger.info("="*80)
    
    for component, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"{component}: {status}")
    
    all_passed = all(results.values())
    
    logger.info("\n" + "="*80)
    if all_passed:
        logger.info("🎉 ALL TESTS PASSED - Framework is ready!")
        logger.info("\nNext steps:")
        logger.info("1. python scripts/prepare_validation_data.py")
        logger.info("2. python models/run_step6_validation.py --data-path <output>")
    else:
        logger.info("⚠️  SOME TESTS FAILED - Review errors above")
    logger.info("="*80)
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
