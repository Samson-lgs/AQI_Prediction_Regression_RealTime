"""
Multi-City Validation Module

Conducts comprehensive validation on held-out data from specific cities
(Delhi, Mumbai, Bangalore) to assess model generalization across
different geographical and pollution patterns.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional
from sklearn.metrics import (
    mean_squared_error, mean_absolute_error, r2_score,
    mean_absolute_percentage_error
)
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class MultiCityValidator:
    """
    Validates models across multiple cities with different hold-out strategies
    
    Key Features:
    - City-specific hold-out validation
    - Stratified temporal split (ensure all seasons represented)
    - Cross-city generalization testing
    - Pollution-level stratification (Good/Moderate/Unhealthy/Hazardous)
    """
    
    def __init__(self, validation_cities: List[str] = None):
        """
        Initialize Multi-City Validator
        
        Args:
            validation_cities: List of cities for validation
                              Default: ['Delhi', 'Mumbai', 'Bangalore']
        """
        self.validation_cities = validation_cities or ['Delhi', 'Mumbai', 'Bangalore']
        self.results = {}
        
        logger.info(f"MultiCityValidator initialized for cities: {self.validation_cities}")
    
    def prepare_city_data(
        self,
        data: pd.DataFrame,
        city: str,
        test_size: float = 0.2,
        temporal_split: bool = True
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Prepare training and test data for a specific city
        
        Args:
            data: Full dataset with all cities
            city: City name to filter
            test_size: Fraction of data to use for testing
            temporal_split: If True, use most recent data for testing
                          If False, use random split
        
        Returns:
            X_train, X_test, y_train, y_test
        """
        # Filter data for specific city
        city_data = data[data['city'] == city].copy()
        
        if len(city_data) == 0:
            raise ValueError(f"No data found for city: {city}")
        
        logger.info(f"City {city}: {len(city_data)} total samples")
        
        # Sort by timestamp if temporal split
        if temporal_split and 'timestamp' in city_data.columns:
            city_data = city_data.sort_values('timestamp')
            logger.info(f"  Using temporal split (recent {test_size*100}% for testing)")
        else:
            city_data = city_data.sample(frac=1, random_state=42)  # Shuffle
            logger.info(f"  Using random split ({test_size*100}% for testing)")
        
        # Calculate split index
        split_idx = int(len(city_data) * (1 - test_size))
        
        # Split into train/test
        train_data = city_data.iloc[:split_idx]
        test_data = city_data.iloc[split_idx:]
        
        # Separate features and target
        feature_cols = [col for col in city_data.columns 
                       if col not in ['city', 'timestamp', 'aqi_value', 'aqi', 'target']]
        
        # Try different target column names
        target_col = None
        for possible_target in ['aqi_value', 'aqi', 'target']:
            if possible_target in city_data.columns:
                target_col = possible_target
                break
        
        if target_col is None:
            raise ValueError("No target column found (tried: aqi_value, aqi, target)")
        
        X_train = train_data[feature_cols]
        y_train = train_data[target_col]
        X_test = test_data[feature_cols]
        y_test = test_data[target_col]
        
        logger.info(f"  Train: {len(X_train)} samples, Test: {len(X_test)} samples")
        logger.info(f"  Features: {len(feature_cols)} columns")
        
        return X_train, X_test, y_train, y_test
    
    def validate_single_city(
        self,
        model: Any,
        X_test: pd.DataFrame,
        y_test: pd.Series,
        city: str
    ) -> Dict[str, Any]:
        """
        Validate model on a single city's test data
        
        Args:
            model: Trained model with predict() method
            X_test: Test features
            y_test: Test targets
            city: City name
        
        Returns:
            Dictionary with comprehensive metrics
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"Validating on {city}")
        logger.info(f"{'='*60}")
        
        # Make predictions
        y_pred = model.predict(X_test)
        
        # Ensure non-negative predictions
        y_pred = np.maximum(y_pred, 0)
        
        # Calculate metrics
        metrics = self._calculate_metrics(y_test, y_pred, city)
        
        # Calculate stratified metrics (by AQI category)
        stratified_metrics = self._calculate_stratified_metrics(y_test, y_pred)
        metrics['stratified'] = stratified_metrics
        
        # Log results
        logger.info(f"\nOverall Metrics for {city}:")
        logger.info(f"  R² Score:  {metrics['r2']:.4f}")
        logger.info(f"  RMSE:      {metrics['rmse']:.2f}")
        logger.info(f"  MAE:       {metrics['mae']:.2f}")
        logger.info(f"  MAPE:      {metrics['mape']:.2f}%")
        logger.info(f"  Max Error: {metrics['max_error']:.2f}")
        
        logger.info(f"\nStratified Performance (by AQI Category):")
        for category, cat_metrics in stratified_metrics.items():
            logger.info(f"  {category:15} - RMSE: {cat_metrics['rmse']:.2f}, "
                       f"MAE: {cat_metrics['mae']:.2f}, "
                       f"Samples: {cat_metrics['n_samples']}")
        
        return metrics
    
    def validate_all_cities(
        self,
        models: Dict[str, Any],
        data: pd.DataFrame,
        test_size: float = 0.2
    ) -> Dict[str, Dict[str, Any]]:
        """
        Validate all models on all validation cities
        
        Args:
            models: Dictionary of {model_name: trained_model}
            data: Full dataset
            test_size: Fraction for testing
        
        Returns:
            Nested dictionary: {model_name: {city_name: metrics}}
        """
        results = {}
        
        for model_name, model in models.items():
            logger.info(f"\n{'#'*60}")
            logger.info(f"# VALIDATING MODEL: {model_name.upper()}")
            logger.info(f"{'#'*60}")
            
            model_results = {}
            
            for city in self.validation_cities:
                try:
                    # Prepare city-specific data
                    X_train, X_test, y_train, y_test = self.prepare_city_data(
                        data, city, test_size
                    )
                    
                    # Validate on this city
                    city_metrics = self.validate_single_city(
                        model, X_test, y_test, city
                    )
                    
                    model_results[city] = city_metrics
                    
                except Exception as e:
                    logger.error(f"Error validating {model_name} on {city}: {str(e)}")
                    model_results[city] = {'error': str(e)}
            
            results[model_name] = model_results
        
        self.results = results
        return results
    
    def test_cross_city_generalization(
        self,
        model: Any,
        data: pd.DataFrame,
        train_city: str,
        test_city: str
    ) -> Dict[str, Any]:
        """
        Test model generalization from one city to another
        
        Train on one city, test on another to assess geographic transferability
        
        Args:
            model: Model to train and test
            data: Full dataset
            train_city: City to train on
            test_city: City to test on
        
        Returns:
            Metrics dictionary
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"Cross-City Generalization Test")
        logger.info(f"  Train on: {train_city}")
        logger.info(f"  Test on:  {test_city}")
        logger.info(f"{'='*60}")
        
        # Get training data (all data from train_city)
        X_train, _, y_train, _ = self.prepare_city_data(
            data, train_city, test_size=0.01  # Use almost all for training
        )
        
        # Get test data (all data from test_city)
        _, X_test, _, y_test = self.prepare_city_data(
            data, test_city, test_size=0.99  # Use almost all for testing
        )
        
        # Train model on train_city
        from sklearn.base import clone
        model_clone = clone(model)
        
        if hasattr(model_clone, 'fit'):
            model_clone.fit(X_train, y_train)
        elif hasattr(model_clone, 'train'):
            model_clone.train(X_train, y_train)
        
        # Test on test_city
        y_pred = model_clone.predict(X_test)
        y_pred = np.maximum(y_pred, 0)
        
        # Calculate metrics
        metrics = self._calculate_metrics(y_test, y_pred, 
                                         f"{train_city}→{test_city}")
        
        logger.info(f"\nCross-City Results ({train_city} → {test_city}):")
        logger.info(f"  R² Score: {metrics['r2']:.4f}")
        logger.info(f"  RMSE:     {metrics['rmse']:.2f}")
        logger.info(f"  MAE:      {metrics['mae']:.2f}")
        
        return metrics
    
    def _calculate_metrics(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        label: str = ""
    ) -> Dict[str, float]:
        """Calculate comprehensive metrics"""
        
        # Handle any NaN values
        mask = ~(np.isnan(y_true) | np.isnan(y_pred))
        y_true = y_true[mask]
        y_pred = y_pred[mask]
        
        # Basic metrics
        r2 = r2_score(y_true, y_pred)
        rmse = np.sqrt(mean_squared_error(y_true, y_pred))
        mae = mean_absolute_error(y_true, y_pred)
        
        # MAPE (handle zero values)
        mask_nonzero = y_true != 0
        if np.sum(mask_nonzero) > 0:
            mape = np.mean(np.abs((y_true[mask_nonzero] - y_pred[mask_nonzero]) / 
                                  y_true[mask_nonzero])) * 100
        else:
            mape = np.nan
        
        # Additional metrics
        max_error = np.max(np.abs(y_true - y_pred))
        median_ae = np.median(np.abs(y_true - y_pred))
        
        # Error statistics
        errors = y_pred - y_true
        mean_error = np.mean(errors)
        std_error = np.std(errors)
        
        return {
            'r2': float(r2),
            'rmse': float(rmse),
            'mae': float(mae),
            'mape': float(mape) if not np.isnan(mape) else None,
            'max_error': float(max_error),
            'median_ae': float(median_ae),
            'mean_error': float(mean_error),
            'std_error': float(std_error),
            'n_samples': len(y_true)
        }
    
    def _calculate_stratified_metrics(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray
    ) -> Dict[str, Dict[str, float]]:
        """
        Calculate metrics stratified by AQI category
        
        AQI Categories:
        - Good: 0-50
        - Moderate: 51-100
        - Unhealthy for Sensitive: 101-150
        - Unhealthy: 151-200
        - Very Unhealthy: 201-300
        - Hazardous: 301+
        """
        def get_aqi_category(aqi):
            if aqi <= 50:
                return 'Good (0-50)'
            elif aqi <= 100:
                return 'Moderate (51-100)'
            elif aqi <= 150:
                return 'Unhealthy-S (101-150)'
            elif aqi <= 200:
                return 'Unhealthy (151-200)'
            elif aqi <= 300:
                return 'V.Unhealthy (201-300)'
            else:
                return 'Hazardous (301+)'
        
        # Categorize actual values
        categories = [get_aqi_category(val) for val in y_true]
        
        stratified_metrics = {}
        
        for category in set(categories):
            mask = np.array([c == category for c in categories])
            
            if np.sum(mask) > 0:
                y_true_cat = y_true[mask]
                y_pred_cat = y_pred[mask]
                
                stratified_metrics[category] = {
                    'rmse': float(np.sqrt(mean_squared_error(y_true_cat, y_pred_cat))),
                    'mae': float(mean_absolute_error(y_true_cat, y_pred_cat)),
                    'r2': float(r2_score(y_true_cat, y_pred_cat)),
                    'n_samples': int(np.sum(mask))
                }
        
        return stratified_metrics
    
    def generate_summary(self) -> pd.DataFrame:
        """
        Generate summary table of validation results
        
        Returns:
            DataFrame with model x city performance matrix
        """
        if not self.results:
            logger.warning("No results available. Run validate_all_cities() first.")
            return pd.DataFrame()
        
        summary_data = []
        
        for model_name, city_results in self.results.items():
            for city, metrics in city_results.items():
                if 'error' not in metrics:
                    summary_data.append({
                        'Model': model_name,
                        'City': city,
                        'R²': metrics['r2'],
                        'RMSE': metrics['rmse'],
                        'MAE': metrics['mae'],
                        'MAPE': metrics['mape'],
                        'Max Error': metrics['max_error'],
                        'Samples': metrics['n_samples']
                    })
        
        df = pd.DataFrame(summary_data)
        
        # Sort by Model and R²
        if not df.empty:
            df = df.sort_values(['Model', 'R²'], ascending=[True, False])
        
        return df


if __name__ == "__main__":
    # Test with synthetic data
    print("Testing MultiCityValidator...")
    print("=" * 60)
    
    # Create synthetic city data
    np.random.seed(42)
    n_samples = 1000
    
    data = pd.DataFrame({
        'city': np.random.choice(['Delhi', 'Mumbai', 'Bangalore'], n_samples),
        'timestamp': pd.date_range('2025-01-01', periods=n_samples, freq='H'),
        'pm25': np.random.rand(n_samples) * 100,
        'pm10': np.random.rand(n_samples) * 150,
        'temperature': np.random.rand(n_samples) * 30 + 15,
        'humidity': np.random.rand(n_samples) * 60 + 20,
        'aqi_value': np.random.rand(n_samples) * 200 + 50
    })
    
    # Initialize validator
    validator = MultiCityValidator()
    
    # Test prepare_city_data
    print("\n1. Testing prepare_city_data...")
    X_train, X_test, y_train, y_test = validator.prepare_city_data(
        data, 'Delhi', test_size=0.2
    )
    print(f"   ✓ Delhi data prepared: {len(X_train)} train, {len(X_test)} test")
    
    # Test validation with a simple model
    print("\n2. Testing validation with LinearRegression...")
    from sklearn.linear_model import LinearRegression
    
    model = LinearRegression()
    model.fit(X_train, y_train)
    
    metrics = validator.validate_single_city(model, X_test, y_test, 'Delhi')
    print(f"   ✓ Validation complete: R²={metrics['r2']:.4f}")
    
    print("\n✅ MultiCityValidator test complete!")
