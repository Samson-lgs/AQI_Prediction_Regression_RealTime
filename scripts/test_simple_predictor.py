from models.simple_predictor import get_predictor

print("=" * 60)
print("TESTING SIMPLE PREDICTOR")
print("=" * 60)

# Load predictor
predictor = get_predictor()

print(f"\nAvailable models: {predictor.available_models()}")

# Test with sample pollutant values
test_cases = [
    {"name": "Good Air", "pm25": 20, "pm10": 30, "no2": 1, "so2": 5, "co": 0.2, "o3": 80},
    {"name": "Moderate Air", "pm25": 50, "pm10": 100, "no2": 2, "so2": 10, "co": 0.5, "o3": 150},
    {"name": "Poor Air", "pm25": 100, "pm10": 200, "no2": 5, "so2": 20, "co": 1.0, "o3": 200},
]

for test in test_cases:
    name = test.pop("name")
    print(f"\n{'-' * 60}")
    print(f"Test: {name}")
    print(f"{'-' * 60}")
    print(f"Pollutants: PM2.5={test['pm25']}, PM10={test['pm10']}, NO2={test['no2']}, SO2={test['so2']}, CO={test['co']}, O3={test['o3']}")
    
    result = predictor.get_best_prediction(test)
    
    print(f"\nBest Model: {result['model']}")
    print(f"Predicted AQI: {result['aqi']:.1f}")
    print(f"\nAll Model Predictions:")
    for model, aqi in result['all_predictions'].items():
        if aqi:
            print(f"  {model:20s}: {aqi:6.1f}")

print("\n" + "=" * 60)
print("✅ TEST COMPLETE - Models working!")
print("=" * 60)
