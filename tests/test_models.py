"""Quick test of newly trained models"""
import os

print("\n" + "="*60)
print("🎯 TRAINED MODELS VERIFICATION")
print("="*60)

cities = ['Delhi', 'Mumbai', 'Bangalore', 'Chennai', 'Kolkata', 'Hyderabad']
models_dir = 'models/trained_models'

for city in cities:
    print(f"\n{city}:")
    lr_file = f"{models_dir}/{city}_lr.pkl"
    rf_file = f"{models_dir}/{city}_rf.pkl"
    xgb_file = f"{models_dir}/{city}_xgb.json"
    
    if os.path.exists(lr_file):
        size = os.path.getsize(lr_file) / 1024
        print(f"  ✅ Linear Regression ({size:.1f} KB)")
    else:
        print(f"  ❌ Linear Regression - NOT FOUND")
        
    if os.path.exists(rf_file):
        size = os.path.getsize(rf_file) / 1024
        print(f"  ✅ Random Forest ({size:.1f} KB)")
    else:
        print(f"  ❌ Random Forest - NOT FOUND")
        
    if os.path.exists(xgb_file):
        size = os.path.getsize(xgb_file) / 1024
        print(f"  ✅ XGBoost ({size:.1f} KB)")
    else:
        print(f"  ❌ XGBoost - NOT FOUND")

print("\n" + "="*60)
print("\n📊 Summary:")
total_files = len([f for f in os.listdir(models_dir) if f.endswith(('.pkl', '.json'))])
cities_trained = len(set([f.split('_')[0] for f in os.listdir(models_dir) if f.endswith('_lr.pkl')]))
print(f"  Total model files: {total_files}")
print(f"  Cities with models: {cities_trained}")
print("="*60 + "\n")
