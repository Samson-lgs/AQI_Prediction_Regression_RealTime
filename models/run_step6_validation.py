"""
Step 6: Validation Orchestrator

Main script to run comprehensive validation including:
- Multi-city validation (Delhi, Mumbai, Bangalore)
- Time-series forecasting evaluation (1-48 hours)
- API benchmarking against commercial services
- Research benchmark comparisons
- Comprehensive reporting

Usage:
    python models/run_step6_validation.py --data-path data/processed/aqi_data.csv
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
import logging
import pandas as pd
import numpy as np
from pathlib import Path
import joblib
from datetime import datetime
from typing import Dict, Any, List

# Import validation modules
from models.validation.multi_city_validator import MultiCityValidator
from models.validation.forecasting_validator import ForecastingValidator
from models.validation.api_benchmark import APIBenchmark
from models.validation.validation_report import ValidationReport

# Import models
from ml_models.linear_regression_model import LinearRegressionAQI
from ml_models.random_forest_model import RandomForestAQI
from ml_models.xgboost_model import XGBoostAQI
from ml_models.lstm_model import LSTMAQI
from ml_models.stacked_ensemble import StackedEnsembleAQI

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'models/validation/validation_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def load_and_prepare_data(data_path: str) -> pd.DataFrame:
    """
    Load and prepare data for validation
    
    Args:
        data_path: Path to processed data CSV
    
    Returns:
        Prepared DataFrame
    """
    logger.info(f"Loading data from {data_path}")
    
    if not Path(data_path).exists():
        raise FileNotFoundError(f"Data file not found: {data_path}")
    
    data = pd.read_csv(data_path)
    
    logger.info(f"Loaded {len(data)} rows")
    logger.info(f"Columns: {list(data.columns)}")
    
    # Ensure timestamp column
    if 'timestamp' in data.columns:
        data['timestamp'] = pd.to_datetime(data['timestamp'])
        data = data.sort_values('timestamp')
    
    # Check for required columns
    required_cols = ['city']
    missing = [col for col in required_cols if col not in data.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    
    logger.info(f"Unique cities: {data['city'].nunique()}")
    logger.info(f"Date range: {data['timestamp'].min()} to {data['timestamp'].max()}")
    
    return data


def load_or_train_models(data: pd.DataFrame, force_train: bool = False) -> Dict[str, Any]:
    """
    Load pre-trained models or train new ones
    
    Args:
        data: Training data
        force_train: If True, train new models even if saved ones exist
    
    Returns:
        Dictionary of {model_name: trained_model}
    """
    models = {}
    model_dir = Path("models/trained_models")
    model_dir.mkdir(parents=True, exist_ok=True)
    
    # Define models
    model_specs = {
        'LinearRegression': (LinearRegressionAQI, 'linear_regression'),
        'RandomForest': (RandomForestAQI, 'random_forest'),
        'XGBoost': (XGBoostAQI, 'xgboost'),
        'LSTM': (LSTMAQI, 'lstm'),
        'StackedEnsemble': (StackedEnsembleAQI, 'stacked_ensemble')
    }
    
    # Prepare features and target
    feature_cols = [col for col in data.columns 
                   if col not in ['city', 'timestamp', 'aqi_value', 'aqi', 'target', 'created_at', 'data_source', 'id']]
    
    target_col = 'aqi_value' if 'aqi_value' in data.columns else 'aqi'
    
    logger.info(f"Using {len(feature_cols)} features for training")
    
    X = data[feature_cols]
    y = data[target_col]
    
    # Split for initial training (80/20)
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
    
    for model_name, (ModelClass, save_name) in model_specs.items():
        model_path = model_dir / f"{save_name}_step6.joblib"
        
        try:
            if model_path.exists() and not force_train:
                logger.info(f"Loading {model_name} from {model_path}")
                model = joblib.load(model_path)
                models[model_name] = model
            else:
                logger.info(f"Training {model_name}...")
                
                # Initialize model
                if model_name == 'LSTM':
                    model = ModelClass(input_shape=(X_train.shape[1],))
                else:
                    model = ModelClass()
                
                # Train
                if hasattr(model, 'fit'):
                    model.fit(X_train, y_train)
                elif hasattr(model, 'train'):
                    model.train(X_train, y_train)
                
                # Save
                joblib.dump(model, model_path)
                logger.info(f"✓ {model_name} trained and saved")
                
                models[model_name] = model
                
        except Exception as e:
            logger.error(f"Error with {model_name}: {str(e)}")
            continue
    
    logger.info(f"Loaded/trained {len(models)} models")
    return models


def run_multi_city_validation(
    models: Dict[str, Any],
    data: pd.DataFrame,
    cities: List[str] = ['Delhi', 'Mumbai', 'Bangalore']
) -> Dict[str, Any]:
    """
    Run multi-city validation
    
    Args:
        models: Dictionary of trained models
        data: Full dataset
        cities: Cities to validate on
    
    Returns:
        Validation results
    """
    logger.info("\n" + "="*80)
    logger.info("STEP 1: MULTI-CITY VALIDATION")
    logger.info("="*80)
    
    validator = MultiCityValidator(validation_cities=cities)
    results = validator.validate_all_cities(models, data, test_size=0.2)
    
    # Generate summary
    summary_df = validator.generate_summary()
    logger.info("\nMulti-City Validation Summary:")
    logger.info(f"\n{summary_df.to_string()}")
    
    # Test cross-city generalization
    logger.info("\n" + "-"*80)
    logger.info("Cross-City Generalization Tests")
    logger.info("-"*80)
    
    cross_city_results = {}
    for model_name, model in models.items():
        # Train on Delhi, test on Mumbai
        cross_results = validator.test_cross_city_generalization(
            model, data, 'Delhi', 'Mumbai'
        )
        cross_city_results[f"{model_name}_Delhi→Mumbai"] = cross_results
    
    return results


def run_forecasting_validation(
    models: Dict[str, Any],
    data: pd.DataFrame,
    horizons: List[int] = [1, 6, 12, 24, 48],
    city: str = 'Delhi'
) -> Dict[str, Any]:
    """
    Run time-series forecasting validation
    
    Args:
        models: Dictionary of trained models
        data: Full dataset
        horizons: Forecast horizons in hours
        city: City to focus on
    
    Returns:
        Forecasting validation results
    """
    logger.info("\n" + "="*80)
    logger.info("STEP 2: TIME-SERIES FORECASTING VALIDATION")
    logger.info("="*80)
    
    # Prepare feature columns
    feature_cols = [col for col in data.columns 
                   if col not in ['city', 'timestamp', 'aqi_value', 'aqi', 'target', 'created_at', 'data_source', 'id']]
    
    validator = ForecastingValidator(horizons=horizons)
    results = validator.multi_horizon_validation(
        models, data, feature_cols, city=city
    )
    
    # Generate summary
    summary_df = validator.generate_summary()
    logger.info("\nForecasting Validation Summary:")
    logger.info(f"\n{summary_df.to_string()}")
    
    # Generate plots
    try:
        validator.plot_forecast_performance()
    except Exception as e:
        logger.warning(f"Could not generate forecast plots: {e}")
    
    return results


def run_api_benchmarking(
    models: Dict[str, Any],
    multi_city_results: Dict[str, Any],
    iqair_key: str = None,
    aqicn_key: str = None
) -> Dict[str, Any]:
    """
    Run API benchmarking against commercial services
    
    Args:
        models: Dictionary of trained models
        multi_city_results: Results from multi-city validation
        iqair_key: IQAir API key
        aqicn_key: AQICN API key
    
    Returns:
        Benchmarking results
    """
    logger.info("\n" + "="*80)
    logger.info("STEP 3: API BENCHMARKING")
    logger.info("="*80)
    
    benchmark = APIBenchmark(iqair_key=iqair_key, aqicn_key=aqicn_key)
    
    # Compare with research benchmarks
    logger.info("\nComparing with Published Research Benchmarks...")
    
    research_comparisons = {}
    cities = ['Delhi', 'Mumbai', 'Bangalore']
    
    for model_name, city_results in multi_city_results.items():
        for city in cities:
            if city in city_results and 'error' not in city_results[city]:
                comparison = benchmark.compare_with_research_benchmarks(
                    city_results[city],
                    city,
                    model_name
                )
                
                key = f"{model_name}_{city}"
                research_comparisons[key] = comparison
    
    # Generate benchmark report
    benchmark_df = benchmark.generate_benchmark_report(
        multi_city_results,
        cities
    )
    
    logger.info("\nResearch Benchmark Comparison:")
    logger.info(f"\n{benchmark_df.to_string()}")
    
    return {
        'research_comparisons': research_comparisons,
        'benchmark_summary': benchmark_df.to_dict('records')
    }


def generate_comprehensive_report(
    multi_city_results: Dict[str, Any],
    forecasting_results: Dict[str, Any],
    benchmark_results: Dict[str, Any]
):
    """
    Generate comprehensive validation report
    
    Args:
        multi_city_results: Multi-city validation results
        forecasting_results: Forecasting validation results
        benchmark_results: API benchmarking results
    """
    logger.info("\n" + "="*80)
    logger.info("GENERATING COMPREHENSIVE REPORT")
    logger.info("="*80)
    
    reporter = ValidationReport()
    
    # Generate main report
    report = reporter.generate_summary_report(
        multi_city_results,
        forecasting_results,
        benchmark_results
    )
    
    # Generate plots
    try:
        reporter.plot_validation_results(
            multi_city_results,
            forecasting_results
        )
    except Exception as e:
        logger.warning(f"Could not generate validation plots: {e}")
    
    logger.info("\n" + "="*80)
    logger.info("VALIDATION COMPLETE!")
    logger.info("="*80)
    logger.info(f"\nBest Overall Model: {report['overall_rankings']['overall_ranking'][0]['model']}")
    logger.info(f"Combined Score: {report['overall_rankings']['overall_ranking'][0]['combined_score']:.4f}")
    
    return report


def main():
    """Main validation orchestrator"""
    parser = argparse.ArgumentParser(
        description='Step 6: Comprehensive Model Validation'
    )
    parser.add_argument(
        '--data-path',
        type=str,
        default='data/processed/aqi_data.csv',
        help='Path to processed AQI data'
    )
    parser.add_argument(
        '--cities',
        nargs='+',
        default=['Delhi', 'Mumbai', 'Bangalore'],
        help='Cities for validation'
    )
    parser.add_argument(
        '--horizons',
        nargs='+',
        type=int,
        default=[1, 6, 12, 24, 48],
        help='Forecast horizons in hours'
    )
    parser.add_argument(
        '--force-train',
        action='store_true',
        help='Force model retraining'
    )
    parser.add_argument(
        '--iqair-key',
        type=str,
        help='IQAir API key for benchmarking'
    )
    parser.add_argument(
        '--aqicn-key',
        type=str,
        help='AQICN API key for benchmarking'
    )
    
    args = parser.parse_args()
    
    logger.info("="*80)
    logger.info("STEP 6: COMPREHENSIVE MODEL VALIDATION")
    logger.info("="*80)
    logger.info(f"Data path: {args.data_path}")
    logger.info(f"Validation cities: {args.cities}")
    logger.info(f"Forecast horizons: {args.horizons} hours")
    
    try:
        # Load data
        data = load_and_prepare_data(args.data_path)
        
        # Load or train models
        models = load_or_train_models(data, force_train=args.force_train)
        
        if not models:
            logger.error("No models available for validation")
            return
        
        # Run multi-city validation
        multi_city_results = run_multi_city_validation(
            models, data, cities=args.cities
        )
        
        # Run forecasting validation
        forecasting_results = run_forecasting_validation(
            models, data, horizons=args.horizons, city=args.cities[0]
        )
        
        # Run API benchmarking
        benchmark_results = run_api_benchmarking(
            models,
            multi_city_results,
            iqair_key=args.iqair_key,
            aqicn_key=args.aqicn_key
        )
        
        # Generate comprehensive report
        report = generate_comprehensive_report(
            multi_city_results,
            forecasting_results,
            benchmark_results
        )
        
        logger.info("\n✅ Step 6 Validation Complete!")
        logger.info("Check models/validation/reports/ for detailed reports")
        
    except Exception as e:
        logger.error(f"Validation failed: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
