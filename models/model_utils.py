"""
Model Utilities - Simple model selector for API
"""
import logging

logger = logging.getLogger(__name__)


class ModelSelector:
    """
    Simple model selector that returns the default model to use for predictions.
    Can be extended to select best model based on performance metrics.
    """
    
    def __init__(self):
        self.default_model = "xgboost"
    
    def get_best_model(self, city: str) -> str:
        """
        Get the best performing model for a given city.
        
        Args:
            city: City name
            
        Returns:
            str: Name of the best model (currently returns default)
        """
        try:
            # TODO: Query database for actual best model based on metrics
            # For now, return default model
            from database.db_operations import DatabaseOperations
            db = DatabaseOperations()
            
            # Try to get model performance metrics
            metrics = db.get_model_performance(city, None, 30)
            
            if metrics and len(metrics) > 0:
                # Find model with highest R² score
                best_model = None
                best_r2 = -float('inf')
                
                for metric in metrics:
                    model_name = metric.get('model_name')
                    r2_score = metric.get('r2_score')
                    
                    if model_name and r2_score is not None:
                        if r2_score > best_r2:
                            best_r2 = r2_score
                            best_model = model_name
                
                if best_model:
                    logger.info(f"Best model for {city}: {best_model} (R²={best_r2:.3f})")
                    return best_model
            
            # Fallback to default
            logger.info(f"No metrics found for {city}, using default: {self.default_model}")
            return self.default_model
            
        except Exception as e:
            logger.warning(f"Error selecting best model for {city}: {e}")
            return self.default_model
    
    def get_available_models(self) -> list:
        """
        Get list of available model types.
        
        Returns:
            list: List of model names
        """
        return [
            "linear_regression",
            "random_forest", 
            "xgboost",
            "lstm",
            "stacked_ensemble"
        ]
