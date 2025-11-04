import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from database.db_operations import DatabaseOperations
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FeatureProcessor:
    def __init__(self):
        self.db = DatabaseOperations()
        self.scaler_features = StandardScaler()
        self.scaler_target = MinMaxScaler(feature_range=(0, 500))
    
    def get_training_data(self, city, days=90):
        """Get historical data for training"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            pollution_data = self.db.get_pollution_data(
                city, start_date, end_date
            )
            
            if not pollution_data:
                logger.warning(f"No data found for {city}")
                return None
            
            df = pd.DataFrame(pollution_data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp').reset_index(drop=True)
            
            return df
        
        except Exception as e:
            logger.error(f"Error fetching training data: {str(e)}")
            return None
    
    def create_features(self, df):
        """Create temporal and derived features"""
        try:
            df = df.copy()
            
            # Temporal features
            df['hour'] = df['timestamp'].dt.hour
            df['day_of_week'] = df['timestamp'].dt.dayofweek
            df['month'] = df['timestamp'].dt.month
            df['quarter'] = df['timestamp'].dt.quarter
            df['day_of_year'] = df['timestamp'].dt.dayofyear
            
            # Cyclical encoding for hour
            df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
            df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
            
            # Cyclical encoding for day of week
            df['dow_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
            df['dow_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
            
            # Derived features
            df['pollutant_ratio'] = df['pm25'] / (df['pm10'] + 0.1)
            df['no2_so2_ratio'] = df['no2'] / (df['so2'] + 0.1)
            
            # Moving averages (lag features)
            for window in [3, 6, 12, 24]:
                df[f'pm25_ma_{window}'] = df['pm25'].rolling(
                    window=window, min_periods=1
                ).mean()
                df[f'pm10_ma_{window}'] = df['pm10'].rolling(
                    window=window, min_periods=1
                ).mean()
                df[f'no2_ma_{window}'] = df['no2'].rolling(
                    window=window, min_periods=1
                ).mean()
            
            # Lag features
            for lag in [1, 6, 12, 24]:
                df[f'pm25_lag_{lag}'] = df['pm25'].shift(lag)
                df[f'pm10_lag_{lag}'] = df['pm10'].shift(lag)
                df[f'aqi_lag_{lag}'] = df['aqi_value'].shift(lag)
            
            logger.info("Features created successfully")
            return df
        
        except Exception as e:
            logger.error(f"Error creating features: {str(e)}")
            return None
    
    def handle_missing_values(self, df):
        """Handle missing values with imputation"""
        try:
            df = df.copy()
            
            # Forward fill then backward fill for time-series
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            
            for col in numeric_cols:
                df[col] = df[col].fillna(method='ffill').fillna(method='bfill')
                
                # If still NaN, fill with mean
                df[col] = df[col].fillna(df[col].mean())
            
            logger.info("Missing values handled")
            return df
        
        except Exception as e:
            logger.error(f"Error handling missing values: {str(e)}")
            return None
    
    def detect_outliers(self, df, threshold=3):
        """Detect and handle outliers using Z-score"""
        try:
            df = df.copy()
            numeric_cols = ['pm25', 'pm10', 'no2', 'so2', 'co', 'o3', 'aqi_value']
            
            for col in numeric_cols:
                if col in df.columns:
                    z_scores = np.abs((df[col] - df[col].mean()) / df[col].std())
                    # Cap outliers instead of removing
                    df.loc[z_scores > threshold, col] = df[col].quantile(0.95)
            
            logger.info("Outliers handled")
            return df
        
        except Exception as e:
            logger.error(f"Error detecting outliers: {str(e)}")
            return None
    
    def normalize_features(self, df, fit=True):
        """Normalize features to standard scale"""
        try:
            df = df.copy()
            feature_cols = [col for col in df.columns 
                           if col not in ['timestamp', 'city', 'data_source', 'id', 'created_at']]
            
            if fit:
                df[feature_cols] = self.scaler_features.fit_transform(
                    df[feature_cols].fillna(0)
                )
            else:
                df[feature_cols] = self.scaler_features.transform(
                    df[feature_cols].fillna(0)
                )
            
            logger.info("Features normalized")
            return df
        
        except Exception as e:
            logger.error(f"Error normalizing features: {str(e)}")
            return None
    
    def prepare_training_data(self, city, days=90):
        """Complete preprocessing pipeline"""
        logger.info(f"Preparing training data for {city}")
        
        # Fetch raw data
        df = self.get_training_data(city, days)
        if df is None or df.empty:
            logger.warning(f"No raw data found for {city}")
            return None
        
        logger.info(f"Fetched {len(df)} raw data rows for {city}")
        
        # Handle missing values
        df = self.handle_missing_values(df)
        if df is None or df.empty:
            logger.warning(f"Data became empty after handling missing values")
            return None
        
        # Detect outliers
        df = self.detect_outliers(df)
        if df is None or df.empty:
            logger.warning(f"Data became empty after outlier detection")
            return None
        
        # Create features
        df = self.create_features(df)
        if df is None or df.empty:
            logger.warning(f"Data became empty after feature creation")
            return None
        
        # Remove rows with NaN values created by lag features
        df = df.dropna()
        
        if df.empty:
            logger.warning(f"Not enough data for {city}. Need at least 24 hours of continuous data for lag features. Found only {len(df)} rows after dropna.")
            return None
        
        # Normalize features
        df = self.normalize_features(df, fit=True)
        if df is None or df.empty:
            logger.warning(f"Data became empty after normalization")
            return None
        
        logger.info(f"Training data ready: {len(df)} rows, {len(df.columns)} columns")
        return df