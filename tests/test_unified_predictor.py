"""Test unified predictor with actual city data"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from models.unified_predictor import get_predictor
except ImportError:
    try:
        # try alternative package layout
        from src.models.unified_predictor import get_predictor
    except ImportError:
        # fallback: load module directly from file path (works even if package __init__.py is missing)
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "unified_predictor",
            str(PROJECT_ROOT / "models" / "unified_predictor.py"),
        )
        unified = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(unified)
        get_predictor = unified.get_predictor

from database.db_operations import DatabaseOperations
from datetime import datetime, timedelta

def test_predictor():
    """Test the unified predictor with real data."""
    print("=" * 80)
    print("TESTING UNIFIED PREDICTOR")
    print("=" * 80)
    
    # Initialize
    predictor = get_predictor()
    db = DatabaseOperations()
    
    print(f"\n✅ Loaded models: {predictor.available_models()}")
    
    # Test cities
    test_cities = ["Delhi", "Mumbai", "Bangalore", "Chennai", "Kolkata"]
    
    for city in test_cities:
        print(f"\n{'='*60}")
        print(f"Testing: {city}")
        print(f"{'='*60}")
        
        try:
            # Get latest data
            end = datetime.now()
            start = end - timedelta(hours=24)
            data = db.get_pollution_data(city, start, end)
            
            if not data:
                print(f"❌ No data available for {city}")
                continue
            
            latest = data[0]
            print(f"Latest reading: {latest.get('timestamp')}")
            print(f"Actual AQI: {latest.get('aqi_value')}")
            
            # Prepare pollutants
            pollutants = {
                'pm25': float(latest.get('pm25', 0)) if latest.get('pm25') is not None else 0,
                'pm10': float(latest.get('pm10', 0)) if latest.get('pm10') is not None else 0,
                'no2': float(latest.get('no2', 0)) if latest.get('no2') is not None else 0,
                'so2': float(latest.get('so2', 0)) if latest.get('so2') is not None else 0,
                'co': float(latest.get('co', 0)) if latest.get('co') is not None else 0,
                'o3': float(latest.get('o3', 0)) if latest.get('o3') is not None else 0,
            }
            
            print(f"\nPollutants:")
            for pol, val in pollutants.items():
                print(f"  {pol.upper()}: {val:.2f}")
            
            # Get predictions
            result = predictor.get_best_prediction(city, pollutants)
            
            print(f"\nPredictions:")
            print(f"  Best model: {result['model']}")
            print(f"  Predicted AQI: {result['aqi']:.1f}")
            print(f"\n  All models:")
            for model, aqi in result['all_predictions'].items():
                if aqi is not None:
                    print(f"    {model:20s}: {aqi:6.1f}")
                else:
                    print(f"    {model:20s}: ERROR")
            
            # Compare with actual
            if latest.get('aqi_value'):
                error = abs(result['aqi'] - float(latest.get('aqi_value')))
                print(f"\n  Error vs actual: ±{error:.1f} AQI units")
            
            print(f"✅ Prediction successful for {city}")
            
        except Exception as e:
            print(f"❌ Error for {city}: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*80}")
    print("TEST COMPLETE")
    print(f"{'='*80}")

if __name__ == "__main__":
    test_predictor()
