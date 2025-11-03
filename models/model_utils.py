"""Utility functions for model operations"""

import joblib
import os
from typing import Any

def save_model(model: Any, model_name: str, version: str = "1.0.0") -> str:
    """
    Save a trained model to disk
    
    Args:
        model: The trained model object
        model_name: Name of the model
        version: Version of the model
        
    Returns:
        str: Path where the model was saved
    """
    filepath = f"models/trained_models/{model_name}_v{version}.joblib"
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    joblib.dump(model, filepath)
    return filepath

def load_model(model_name: str, version: str = "1.0.0") -> Any:
    """
    Load a trained model from disk
    
    Args:
        model_name: Name of the model to load
        version: Version of the model to load
        
    Returns:
        The loaded model object
    """
    filepath = f"models/trained_models/{model_name}_v{version}.joblib"
    return joblib.load(filepath)