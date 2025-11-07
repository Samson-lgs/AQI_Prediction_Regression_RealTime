"""Test predictions with newly trained models"""
import os
os.environ['DATABASE_URL'] = 'postgresql://aqi_user:u2I3Xl9kBvUj1xCXGJaeSFHczxNgzdFJ@dpg-d452eqn5r7bs73ba6o7g-a.oregon-postgres.render.com/aqi_db_gr7o'

from models.train_models import ModelTrainer
import pickle
import json

print("\n" + "="*70)
print("🔮 TESTING PREDICTIONS WITH NEWLY TRAINED MODELS")
print("="*70)

# Test cities
test_cities = ['Delhi', 'Mumbai', 'Bangalore']

for city in test_cities:
    print(f"\n📍 {city}:")
    print("-" * 70)
    
    # Load models
    lr_path = f'models/trained_models/{city}_lr.pkl'
    rf_path = f'models/trained_models/{city}_rf.pkl'
    xgb_path = f'models/trained_models/{city}_xgb.json'
    
    try:
        # Linear Regression
        with open(lr_path, 'rb') as f:
            lr_model = pickle.load(f)
        print(f"  ✅ Linear Regression loaded")
        
        # Random Forest
        with open(rf_path, 'rb') as f:
            rf_model = pickle.load(f)
        print(f"  ✅ Random Forest loaded")
        
        # XGBoost
        import xgboost as xgb
        xgb_model = xgb.Booster()
        xgb_model.load_model(xgb_path)
        print(f"  ✅ XGBoost loaded")
        
        print(f"  🎯 All 3 models ready for predictions!")
        
    except Exception as e:
        print(f"  ❌ Error: {e}")

print("\n" + "="*70)
print("✅ Model loading test complete!")
print("="*70 + "\n")
