"""
Convert XGBoost JSON model to Pickle format
"""
import xgboost as xgb
import pickle
from pathlib import Path

# Define paths
MODELS_DIR = Path(__file__).parent.parent / "models" / "saved_models"
JSON_MODEL_PATH = MODELS_DIR / "xgboost_latest.json"
PKL_MODEL_PATH = MODELS_DIR / "xgboost_latest.pkl"

def convert_json_to_pkl():
    """Convert XGBoost JSON model to pickle format"""
    try:
        print(f"Loading XGBoost model from: {JSON_MODEL_PATH}")
        
        # Load the model from JSON
        model = xgb.XGBRegressor()
        model.load_model(str(JSON_MODEL_PATH))
        
        print(f"Model loaded successfully")
        
        # Save as pickle
        with open(PKL_MODEL_PATH, 'wb') as f:
            pickle.dump(model, f)
        
        print(f"Model saved as pickle to: {PKL_MODEL_PATH}")
        print(f"Pickle file size: {PKL_MODEL_PATH.stat().st_size / 1024:.2f} KB")
        
        # Verify by loading the pickle
        with open(PKL_MODEL_PATH, 'rb') as f:
            loaded_model = pickle.load(f)
        
        print("Pickle file verified successfully!")
        
        return True
        
    except Exception as e:
        print(f"Error during conversion: {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("XGBoost JSON to Pickle Converter")
    print("=" * 60)
    
    if not JSON_MODEL_PATH.exists():
        print(f"Error: JSON model not found at {JSON_MODEL_PATH}")
        print("\nAvailable XGBoost models:")
        for model_file in sorted(MODELS_DIR.glob("xgboost*.json")):
            print(f"  - {model_file.name}")
    else:
        convert_json_to_pkl()
