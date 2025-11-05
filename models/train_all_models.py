"""
Train All Regression Models Script

This script trains all four regression models (Linear Regression, Random Forest, 
XGBoost, and LSTM) on available data for each city.
"""

import os
import sys
import logging
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.train_models import ModelTrainer
from config.settings import CITIES

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def train_all_cities(min_samples=100):
    """
    Train models for all cities with sufficient data
    
    Args:
        min_samples: Minimum number of samples required for training
    """
    print("="*80)
    print("AQI PREDICTION MODEL TRAINING")
    print("="*80)
    print(f"Start Time: {datetime.now()}")
    print(f"Minimum Samples Required: {min_samples}")
    print("="*80)
    
    # Initialize trainer
    trainer = ModelTrainer(train_ratio=0.7, val_ratio=0.15, test_ratio=0.15)
    
    trained_cities = []
    skipped_cities = []
    results_summary = {}
    
    for i, city in enumerate(CITIES, 1):
        print(f"\n{'='*80}")
        print(f"[{i}/{len(CITIES)}] Processing: {city}")
        print(f"{'='*80}")
        
        try:
            # Check data availability
            df = trainer.processor.get_training_data(city, days=90)
            
            if df is None or df.empty:
                logger.warning(f"No data available for {city}")
                skipped_cities.append({'city': city, 'reason': 'No data'})
                continue
            
            sample_count = len(df)
            logger.info(f"Found {sample_count} samples for {city}")
            
            if sample_count < min_samples:
                logger.warning(f"Insufficient data for {city}: {sample_count} < {min_samples}")
                skipped_cities.append({'city': city, 'reason': f'Insufficient data ({sample_count} samples)'})
                continue
            
            # Train models
            results = trainer.train_all_models(city)
            
            if results:
                trained_cities.append(city)
                results_summary[city] = results
                logger.info(f"✅ Successfully trained models for {city}")
            else:
                skipped_cities.append({'city': city, 'reason': 'Training failed'})
                logger.error(f"❌ Training failed for {city}")
        
        except Exception as e:
            logger.error(f"❌ Error processing {city}: {str(e)}")
            skipped_cities.append({'city': city, 'reason': f'Error: {str(e)}'})
    
    # Print summary
    print("\n" + "="*80)
    print("TRAINING SUMMARY")
    print("="*80)
    print(f"End Time: {datetime.now()}")
    print(f"Total Cities: {len(CITIES)}")
    print(f"Successfully Trained: {len(trained_cities)}")
    print(f"Skipped: {len(skipped_cities)}")
    print("="*80)
    
    if trained_cities:
        print("\n✅ SUCCESSFULLY TRAINED CITIES:")
        print("-"*80)
        for city in trained_cities:
            print(f"  • {city}")
            if city in results_summary:
                for model_name, metrics in results_summary[city].items():
                    if metrics:
                        print(f"    - {model_name}: R²={metrics.get('r2', 0):.4f}, RMSE={metrics.get('rmse', 0):.2f}")
    
    if skipped_cities:
        print("\n⚠️  SKIPPED CITIES:")
        print("-"*80)
        for item in skipped_cities:
            print(f"  • {item['city']}: {item['reason']}")
    
    # Model performance comparison
    if results_summary:
        print("\n📊 MODEL PERFORMANCE COMPARISON")
        print("="*80)
        
        # Aggregate metrics across all cities
        model_metrics = {
            'linear_regression': [],
            'random_forest': [],
            'xgboost': [],
            'lstm': []
        }
        
        for city, results in results_summary.items():
            for model_name, metrics in results.items():
                if metrics and 'r2' in metrics:
                    model_metrics[model_name].append(metrics['r2'])
        
        print("\nAverage R² Score by Model:")
        print("-"*80)
        for model_name, r2_scores in model_metrics.items():
            if r2_scores:
                avg_r2 = sum(r2_scores) / len(r2_scores)
                print(f"  {model_name:20s}: {avg_r2:.4f} (trained on {len(r2_scores)} cities)")
        
    print("\n" + "="*80)
    print("🎉 Training Complete!")
    print("="*80)
    
    return trained_cities, skipped_cities, results_summary


def train_single_city(city_name, min_samples=50):
    """
    Train models for a single city
    
    Args:
        city_name: Name of the city
        min_samples: Minimum number of samples required
    """
    print("="*80)
    print(f"TRAINING MODELS FOR: {city_name}")
    print("="*80)
    
    trainer = ModelTrainer(train_ratio=0.7, val_ratio=0.15, test_ratio=0.15)
    
    try:
        # Check data availability
        df = trainer.processor.get_training_data(city_name, days=90)
        
        if df is None or df.empty:
            print(f"❌ No data available for {city_name}")
            return None
        
        sample_count = len(df)
        print(f"📊 Found {sample_count} samples for {city_name}")
        
        if sample_count < min_samples:
            print(f"⚠️  Insufficient data: {sample_count} < {min_samples}")
            print(f"💡 Tip: Run scheduler.py to collect more data")
            return None
        
        # Train models
        print(f"\n🚀 Starting training for {city_name}...")
        results = trainer.train_all_models(city_name)
        
        if results:
            print(f"\n✅ Successfully trained models for {city_name}")
            print("\n📊 Model Performance:")
            print("-"*80)
            for model_name, metrics in results.items():
                if metrics:
                    print(f"\n{model_name.upper()}:")
                    print(f"  R² Score: {metrics.get('r2', 0):.4f}")
                    print(f"  RMSE: {metrics.get('rmse', 0):.2f}")
                    print(f"  MAE: {metrics.get('mae', 0):.2f}")
                    print(f"  MAPE: {metrics.get('mape', 0):.2f}%")
            
            return results
        else:
            print(f"❌ Training failed for {city_name}")
            return None
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        logger.exception(e)
        return None


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Train AQI prediction models')
    parser.add_argument('--city', type=str, help='Train models for specific city')
    parser.add_argument('--min-samples', type=int, default=100, 
                        help='Minimum samples required for training (default: 100)')
    parser.add_argument('--all', action='store_true', 
                        help='Train models for all cities')
    
    args = parser.parse_args()
    
    if args.city:
        # Train single city
        train_single_city(args.city, min_samples=args.min_samples)
    elif args.all:
        # Train all cities
        train_all_cities(min_samples=args.min_samples)
    else:
        # Default: train all cities
        print("💡 No arguments provided. Training all cities with sufficient data...")
        print("💡 Use --city <name> to train a specific city")
        print("💡 Use --min-samples <n> to set minimum sample requirement")
        print()
        train_all_cities(min_samples=args.min_samples)
