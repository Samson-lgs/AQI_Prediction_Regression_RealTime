"""
Test script to verify XGBoost model predictions are working
"""

import sys
import logging
from models.unified_predictor import get_predictor

logging.basicConfig(level=logging.INFO)

# Test with different cities
test_cities = ['Delhi', 'Mumbai', 'Bangalore', 'Chennai', 'Kolkata']

print("\n" + "="*70)
print("TESTING XGBOOST MODEL PREDICTIONS")
print("="*70 + "\n")

predictor = get_predictor()

# Test pollutant values (typical ranges)
test_cases = [
    {
        'city': 'Delhi',
        'pollutants': {
            'pm25': 150.0,
            'pm10': 250.0,
            'no2': 60.0,
            'so2': 20.0,
            'co': 2.5,
            'o3': 45.0
        }
    },
    {
        'city': 'Mumbai',
        'pollutants': {
            'pm25': 80.0,
            'pm10': 120.0,
            'no2': 45.0,
            'so2': 15.0,
            'co': 1.8,
            'o3': 35.0
        }
    },
    {
        'city': 'Bangalore',
        'pollutants': {
            'pm25': 55.0,
            'pm10': 95.0,
            'no2': 40.0,
            'so2': 12.0,
            'co': 1.2,
            'o3': 38.0
        }
    }
]

for test_case in test_cases:
    city = test_case['city']
    pollutants = test_case['pollutants']
    
    print(f"\n{'='*70}")
    print(f"Testing: {city}")
    print(f"{'='*70}")
    print(f"Input pollutants:")
    for key, val in pollutants.items():
        print(f"  {key}: {val}")
    
    result = predictor.get_best_prediction(city, pollutants)
    
    print(f"\nPrediction Results:")
    print(f"  Best Model: {result['model']}")
    print(f"  Predicted AQI: {result['aqi']:.1f}")
    print(f"\n  All Model Predictions:")
    for model_name, aqi_val in result['all_predictions'].items():
        print(f"    {model_name}: {aqi_val:.1f}" if aqi_val else f"    {model_name}: N/A")

print("\n" + "="*70)
print("TEST COMPLETE")
print("="*70 + "\n")

# Check if models are loaded
print(f"Available models: {predictor.available_models()}")
print(f"Number of models loaded: {len(predictor.models)}")
