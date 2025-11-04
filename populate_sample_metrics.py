"""
Populate sample model performance metrics for testing the dashboard
"""
from database.db_operations import DatabaseOperations
from config.settings import CITIES
import random
from datetime import datetime, timedelta

def generate_sample_metrics():
    """Generate realistic sample metrics for models"""
    return {
        'r2_score': round(random.uniform(0.75, 0.95), 4),
        'rmse': round(random.uniform(8.0, 25.0), 2),
        'mae': round(random.uniform(5.0, 18.0), 2),
        'mape': round(random.uniform(8.0, 20.0), 2)
    }

def populate_sample_data():
    """Populate sample model performance data for all cities"""
    db = DatabaseOperations()
    
    models = ['xgboost', 'random_forest', 'lstm', 'linear_regression']
    
    print("Populating sample model performance metrics...")
    
    # Insert metrics for the last 7 days for each city
    for city in CITIES[:10]:  # First 10 cities for demo
        print(f"Adding metrics for {city}...")
        
        for model in models:
            for days_ago in range(7):
                metric_date = datetime.now().date() - timedelta(days=days_ago)
                metrics = generate_sample_metrics()
                
                try:
                    db.insert_model_performance(city, model, metrics, metric_date)
                    print(f"  ✓ {model} - {metric_date}: R²={metrics['r2_score']}, RMSE={metrics['rmse']}")
                except Exception as e:
                    print(f"  ✗ Error for {city}/{model}: {e}")
    
    print("\n✅ Sample metrics populated successfully!")
    print("\nMetrics added for cities:", CITIES[:10])
    print("Models:", models)
    print("Time range: Last 7 days")

if __name__ == "__main__":
    populate_sample_data()
