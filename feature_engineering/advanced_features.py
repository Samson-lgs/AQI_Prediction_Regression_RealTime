"""
Advanced Feature Engineering for AQI Prediction
Adds temporal, lag, rolling, and interaction features to improve model performance.
"""

import pandas as pd
import numpy as np
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class AdvancedFeatureEngineer:
    """
    Creates advanced features from pollution and weather data.
    
    Features generated:
    1. Temporal: hour, day_of_week, month, is_weekend, is_rush_hour
    2. Lag: previous 1h, 3h, 6h, 12h, 24h values
    3. Rolling: 3h, 6h, 12h, 24h rolling means and std
    4. Interactions: PM2.5 × NO2, PM10 × O3, etc.
    5. Ratios: PM2.5/PM10, NO2/O3, etc.
    """
    
    def __init__(self):
        self.feature_columns = []
        self.required_base_features = ['pm25', 'pm10', 'no2', 'so2', 'co', 'o3']
    
    def add_temporal_features(self, df):
        """Add time-based features."""
        if 'timestamp' not in df.columns:
            logger.warning("No timestamp column found, skipping temporal features")
            return df
        
        df = df.copy()
        
        # Ensure timestamp is datetime
        if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Extract temporal components
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek  # 0=Monday, 6=Sunday
        df['month'] = df['timestamp'].dt.month
        df['day_of_month'] = df['timestamp'].dt.day
        df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
        
        # Rush hour features (7-9 AM and 5-7 PM)
        df['is_morning_rush'] = ((df['hour'] >= 7) & (df['hour'] <= 9)).astype(int)
        df['is_evening_rush'] = ((df['hour'] >= 17) & (df['hour'] <= 19)).astype(int)
        df['is_rush_hour'] = (df['is_morning_rush'] | df['is_evening_rush']).astype(int)
        
        # Cyclical encoding for hour (preserves circular nature: 23 is close to 0)
        df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
        df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
        
        # Cyclical encoding for day of week
        df['dow_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
        df['dow_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
        
        # Cyclical encoding for month
        df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
        df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
        
        logger.info("Added temporal features")
        return df
    
    def add_lag_features(self, df, city_column='city'):
        """Add lagged pollutant values (1h, 3h, 6h, 12h, 24h)."""
        df = df.copy()
        
        if 'timestamp' not in df.columns:
            logger.warning("No timestamp column, skipping lag features")
            return df
        
        # Ensure sorted by city and timestamp
        df = df.sort_values(['city', 'timestamp']) if city_column in df.columns else df.sort_values('timestamp')
        
        lag_hours = [1, 3, 6, 12, 24]
        pollutants = [col for col in self.required_base_features if col in df.columns]
        
        for pollutant in pollutants:
            for lag_h in lag_hours:
                col_name = f'{pollutant}_lag{lag_h}h'
                if city_column in df.columns:
                    df[col_name] = df.groupby('city')[pollutant].shift(lag_h)
                else:
                    df[col_name] = df[pollutant].shift(lag_h)
        
        logger.info(f"Added lag features for {len(pollutants)} pollutants at {len(lag_hours)} time lags")
        return df
    
    def add_rolling_features(self, df, city_column='city'):
        """Add rolling window statistics (mean, std) for 3h, 6h, 12h, 24h."""
        df = df.copy()
        
        if 'timestamp' not in df.columns:
            logger.warning("No timestamp column, skipping rolling features")
            return df
        
        # Ensure sorted
        df = df.sort_values(['city', 'timestamp']) if city_column in df.columns else df.sort_values('timestamp')
        
        window_hours = [3, 6, 12, 24]
        pollutants = [col for col in self.required_base_features if col in df.columns]
        
        for pollutant in pollutants:
            for window_h in window_hours:
                # Rolling mean
                mean_col = f'{pollutant}_rolling{window_h}h_mean'
                if city_column in df.columns:
                    df[mean_col] = df.groupby('city')[pollutant].transform(
                        lambda x: x.rolling(window=window_h, min_periods=1).mean()
                    )
                else:
                    df[mean_col] = df[pollutant].rolling(window=window_h, min_periods=1).mean()
                
                # Rolling std (volatility)
                std_col = f'{pollutant}_rolling{window_h}h_std'
                if city_column in df.columns:
                    df[std_col] = df.groupby('city')[pollutant].transform(
                        lambda x: x.rolling(window=window_h, min_periods=1).std()
                    )
                else:
                    df[std_col] = df[pollutant].rolling(window=window_h, min_periods=1).std()
                
                # Fill NaN std with 0 (happens when window has only 1 value)
                df[std_col] = df[std_col].fillna(0)
        
        logger.info(f"Added rolling features for {len(pollutants)} pollutants at {len(window_hours)} windows")
        return df
    
    def add_interaction_features(self, df):
        """Add interaction features (products of pollutants)."""
        df = df.copy()
        
        # Key interactions based on atmospheric chemistry
        interactions = [
            ('pm25', 'no2'),   # Fine particles + nitrogen dioxide
            ('pm10', 'o3'),    # Coarse particles + ozone
            ('no2', 'o3'),     # Photochemical reactions
            ('co', 'no2'),     # Combustion-related
            ('so2', 'pm25'),   # Sulfate aerosol formation
        ]
        
        for pol1, pol2 in interactions:
            if pol1 in df.columns and pol2 in df.columns:
                df[f'{pol1}_x_{pol2}'] = df[pol1] * df[pol2]
        
        logger.info(f"Added {len(interactions)} interaction features")
        return df
    
    def add_ratio_features(self, df):
        """Add ratio features between pollutants."""
        df = df.copy()
        
        # Important ratios
        ratios = [
            ('pm25', 'pm10'),  # Fine to coarse particle ratio
            ('no2', 'o3'),     # NOx to ozone ratio
            ('co', 'no2'),     # Carbon monoxide to NO2 ratio
        ]
        
        for numerator, denominator in ratios:
            if numerator in df.columns and denominator in df.columns:
                ratio_col = f'{numerator}_to_{denominator}_ratio'
                # Avoid division by zero
                df[ratio_col] = np.where(
                    df[denominator] > 0.01,
                    df[numerator] / df[denominator],
                    0
                )
        
        logger.info(f"Added {len(ratios)} ratio features")
        return df
    
    def add_statistical_features(self, df, city_column='city'):
        """Add statistical aggregations per city."""
        df = df.copy()
        
        if city_column not in df.columns:
            return df
        
        pollutants = [col for col in self.required_base_features if col in df.columns]
        
        for pollutant in pollutants:
            # City-level mean (helps model learn city baseline pollution)
            city_mean_col = f'{pollutant}_city_mean'
            df[city_mean_col] = df.groupby('city')[pollutant].transform('mean')
            
            # Deviation from city mean
            deviation_col = f'{pollutant}_dev_from_city_mean'
            df[deviation_col] = df[pollutant] - df[city_mean_col]
        
        logger.info(f"Added statistical features for {len(pollutants)} pollutants")
        return df
    
    def add_weather_features(self, df):
        """Add weather-related features if available."""
        df = df.copy()
        
        weather_cols = ['temperature', 'humidity', 'wind_speed', 'pressure']
        available_weather = [col for col in weather_cols if col in df.columns]
        
        if not available_weather:
            logger.info("No weather columns found, skipping weather features")
            return df
        
        # Temperature interactions with pollutants
        if 'temperature' in df.columns:
            if 'o3' in df.columns:
                df['temp_x_o3'] = df['temperature'] * df['o3']  # Ozone formation increases with temp
            if 'pm25' in df.columns:
                df['temp_x_pm25'] = df['temperature'] * df['pm25']
        
        # Wind speed interactions (dispersion)
        if 'wind_speed' in df.columns:
            for pol in ['pm25', 'pm10', 'no2']:
                if pol in df.columns:
                    # Higher wind = better dispersion = lower pollution
                    df[f'wind_dispersion_{pol}'] = df[pol] / (df['wind_speed'] + 0.1)
        
        # Humidity effects
        if 'humidity' in df.columns and 'pm25' in df.columns:
            df['humidity_x_pm25'] = df['humidity'] * df['pm25']
        
        logger.info(f"Added weather interaction features for {len(available_weather)} weather variables")
        return df
    
    def create_all_features(self, df, include_lag=True, include_rolling=True, 
                           include_interactions=True, include_weather=True):
        """
        Apply all feature engineering steps.
        
        Args:
            df: DataFrame with base features (pm25, pm10, no2, so2, co, o3, timestamp, city)
            include_lag: Whether to include lag features
            include_rolling: Whether to include rolling window features
            include_interactions: Whether to include interaction features
            include_weather: Whether to include weather features
        
        Returns:
            DataFrame with engineered features
        """
        logger.info(f"Starting feature engineering on {len(df)} rows")
        original_cols = df.columns.tolist()
        
        # Temporal features (always include)
        df = self.add_temporal_features(df)
        
        # Lag features
        if include_lag:
            df = self.add_lag_features(df)
        
        # Rolling features
        if include_rolling:
            df = self.add_rolling_features(df)
        
        # Interaction features
        if include_interactions:
            df = self.add_interaction_features(df)
            df = self.add_ratio_features(df)
        
        # Statistical features
        df = self.add_statistical_features(df)
        
        # Weather features
        if include_weather:
            df = self.add_weather_features(df)
        
        # Track new features
        new_cols = [col for col in df.columns if col not in original_cols]
        self.feature_columns = new_cols
        
        logger.info(f"Feature engineering complete. Added {len(new_cols)} new features")
        logger.info(f"Total features: {len(df.columns)}")
        
        return df
    
    def get_feature_names(self):
        """Return list of engineered feature names."""
        return self.feature_columns
    
    def prepare_single_prediction_features(self, pollutants_dict, city=None, timestamp=None):
        """
        Prepare features for a single prediction (without historical data for lag/rolling).
        
        Args:
            pollutants_dict: Dict with keys pm25, pm10, no2, so2, co, o3
            city: City name (optional, used for city-level stats)
            timestamp: Datetime object (if None, uses current time)
        
        Returns:
            Dict with base + temporal + interaction + ratio features
            (Note: lag and rolling features will be NaN/0 without historical data)
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        # Create base DataFrame
        data = pollutants_dict.copy()
        data['timestamp'] = timestamp
        if city:
            data['city'] = city
        
        df = pd.DataFrame([data])
        
        # Add only features that don't require historical data
        df = self.add_temporal_features(df)
        df = self.add_interaction_features(df)
        df = self.add_ratio_features(df)
        
        # Convert to dict
        return df.iloc[0].to_dict()


def engineer_features_for_training(df, **kwargs):
    """
    Convenience function to engineer features for training data.
    
    Args:
        df: Training DataFrame
        **kwargs: Additional arguments for create_all_features
    
    Returns:
        DataFrame with engineered features
    """
    engineer = AdvancedFeatureEngineer()
    return engineer.create_all_features(df, **kwargs)


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    # Create sample data
    sample_data = {
        'city': ['Delhi'] * 48 + ['Mumbai'] * 48,
        'timestamp': pd.date_range('2025-11-07', periods=96, freq='H'),
        'pm25': np.random.uniform(30, 150, 96),
        'pm10': np.random.uniform(50, 200, 96),
        'no2': np.random.uniform(20, 80, 96),
        'so2': np.random.uniform(5, 30, 96),
        'co': np.random.uniform(0.5, 2.5, 96),
        'o3': np.random.uniform(20, 100, 96),
        'temperature': np.random.uniform(15, 35, 96),
        'humidity': np.random.uniform(30, 90, 96),
    }
    
    df = pd.DataFrame(sample_data)
    
    # Engineer features
    engineer = AdvancedFeatureEngineer()
    df_enhanced = engineer.create_all_features(df)
    
    print(f"\nOriginal shape: {df.shape}")
    print(f"Enhanced shape: {df_enhanced.shape}")
    print(f"\nNew features ({len(engineer.get_feature_names())}):")
    for feat in engineer.get_feature_names()[:20]:  # Show first 20
        print(f"  - {feat}")
    
    if len(engineer.get_feature_names()) > 20:
        print(f"  ... and {len(engineer.get_feature_names()) - 20} more")
