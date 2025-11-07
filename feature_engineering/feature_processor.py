import pandas as pd
import numpy as np
from datetime import datetime, timedelta
try:
    from sklearn.preprocessing import StandardScaler, MinMaxScaler
except Exception:
    # Minimal fallback implementations when scikit-learn is not available.
    # These implementations cover the methods used in this module: fit, transform, fit_transform.
    class StandardScaler:
        def __init__(self):
            self.mean_ = None
            self.scale_ = None

        def fit(self, X):
            arr = np.asarray(X, dtype=float)
            self.mean_ = np.nanmean(arr, axis=0)
            self.scale_ = np.nanstd(arr, axis=0)
            # avoid division by zero
            self.scale_ = np.where(self.scale_ == 0, 1.0, self.scale_)
            return self

        def transform(self, X):
            arr = np.asarray(X, dtype=float)
            return (arr - self.mean_) / self.scale_

        def fit_transform(self, X):
            return self.fit(X).transform(X)

    class MinMaxScaler:
        def __init__(self, feature_range=(0, 1)):
            self.feature_range = feature_range
            self.data_min_ = None
            self.data_range_ = None

        def fit(self, X):
            arr = np.asarray(X, dtype=float)
            self.data_min_ = np.nanmin(arr, axis=0)
            data_max = np.nanmax(arr, axis=0)
            self.data_range_ = data_max - self.data_min_
            # avoid division by zero
            self.data_range_ = np.where(self.data_range_ == 0, 1.0, self.data_range_)
            return self

        def transform(self, X):
            arr = np.asarray(X, dtype=float)
            fr_min, fr_max = self.feature_range
            X_std = (arr - self.data_min_) / self.data_range_
            return X_std * (fr_max - fr_min) + fr_min

        def fit_transform(self, X):
            return self.fit(X).transform(X)
from database.db_operations import DatabaseOperations
from feature_engineering.data_cleaner import DataCleaner
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FeatureProcessor:
    def __init__(self):
        self.db = DatabaseOperations()
        self.scaler_features = StandardScaler()
        self.scaler_target = MinMaxScaler(feature_range=(0, 500))
        self.data_cleaner = DataCleaner()  # Integrated advanced cleaning
    
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
        """
        Create comprehensive temporal and derived features
        
        Features Created:
        1. Temporal Features: hour, day_of_week, month, quarter, day_of_year
        2. Seasonal Indicators: season (spring/summer/fall/winter), is_weekend, is_rush_hour
        3. Cyclical Encodings: hour_sin/cos, dow_sin/cos, month_sin/cos
        4. Derived Metrics: pollutant ratios, pollutant indices
        5. Moving Averages: 3h, 6h, 12h, 24h windows
        6. Lag Features: 1h, 6h, 12h, 24h lags
        7. Rate of Change: hourly delta for key pollutants
        8. Interaction Features: temperature × humidity, etc.
        """
        try:
            df = df.copy()
            
            # ========================================
            # 1. TEMPORAL FEATURES
            # ========================================
            df['hour'] = df['timestamp'].dt.hour
            df['day_of_week'] = df['timestamp'].dt.dayofweek  # 0=Monday, 6=Sunday
            df['month'] = df['timestamp'].dt.month
            df['quarter'] = df['timestamp'].dt.quarter
            df['day_of_year'] = df['timestamp'].dt.dayofyear
            df['week_of_year'] = df['timestamp'].dt.isocalendar().week
            
            # ========================================
            # 2. SEASONAL INDICATORS
            # ========================================
            # Season (meteorological): Spring(3-5), Summer(6-8), Fall(9-11), Winter(12-2)
            def get_season(month):
                if month in [3, 4, 5]:
                    return 'spring'
                elif month in [6, 7, 8]:
                    return 'summer'
                elif month in [9, 10, 11]:
                    return 'fall'
                else:  # 12, 1, 2
                    return 'winter'
            
            df['season'] = df['month'].apply(get_season)
            
            # One-hot encode seasons
            df['is_spring'] = (df['season'] == 'spring').astype(int)
            df['is_summer'] = (df['season'] == 'summer').astype(int)
            df['is_fall'] = (df['season'] == 'fall').astype(int)
            df['is_winter'] = (df['season'] == 'winter').astype(int)
            
            # Weekend indicator
            df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)  # Saturday=5, Sunday=6
            
            # Rush hour indicators (7-10 AM and 5-8 PM)
            df['is_morning_rush'] = df['hour'].isin([7, 8, 9, 10]).astype(int)
            df['is_evening_rush'] = df['hour'].isin([17, 18, 19, 20]).astype(int)
            df['is_rush_hour'] = (df['is_morning_rush'] | df['is_evening_rush']).astype(int)
            
            # Time of day categories
            def get_time_category(hour):
                if 6 <= hour < 12:
                    return 'morning'
                elif 12 <= hour < 17:
                    return 'afternoon'
                elif 17 <= hour < 21:
                    return 'evening'
                else:
                    return 'night'
            
            df['time_of_day'] = df['hour'].apply(get_time_category)
            df['is_morning'] = (df['time_of_day'] == 'morning').astype(int)
            df['is_afternoon'] = (df['time_of_day'] == 'afternoon').astype(int)
            df['is_evening'] = (df['time_of_day'] == 'evening').astype(int)
            df['is_night'] = (df['time_of_day'] == 'night').astype(int)
            
            # ========================================
            # 3. CYCLICAL ENCODINGS
            # ========================================
            # Hour (24-hour cycle)
            df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
            df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
            
            # Day of week (7-day cycle)
            df['dow_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
            df['dow_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
            
            # Month (12-month cycle)
            df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
            df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
            
            # Day of year (365-day cycle)
            df['doy_sin'] = np.sin(2 * np.pi * df['day_of_year'] / 365)
            df['doy_cos'] = np.cos(2 * np.pi * df['day_of_year'] / 365)
            
            # ========================================
            # 4. DERIVED POLLUTANT METRICS
            # ========================================
            # Pollutant ratios (avoid division by zero with small epsilon)
            if 'pm25' in df.columns and 'pm10' in df.columns:
                df['pm25_pm10_ratio'] = df['pm25'] / (df['pm10'] + 0.1)
            
            if 'no2' in df.columns and 'so2' in df.columns:
                df['no2_so2_ratio'] = df['no2'] / (df['so2'] + 0.1)
            
            if 'co' in df.columns and 'no2' in df.columns:
                df['co_no2_ratio'] = df['co'] / (df['no2'] + 0.1)
            
            # Total particulate matter
            if 'pm25' in df.columns and 'pm10' in df.columns:
                df['total_pm'] = df['pm25'] + df['pm10']
            
            # Total gaseous pollutants
            if 'no2' in df.columns or 'so2' in df.columns or 'o3' in df.columns:
                df['total_gases'] = (
                    df['no2'].fillna(0) if 'no2' in df.columns else 0 +
                    df['so2'].fillna(0) if 'so2' in df.columns else 0 +
                    df['o3'].fillna(0) if 'o3' in df.columns else 0
                )
            
            # Pollutant index (weighted sum)
            df['pollutant_index'] = (
                (df['pm25'].fillna(0) * 2.0 if 'pm25' in df.columns else 0) +
                (df['pm10'].fillna(0) * 1.0 if 'pm10' in df.columns else 0) +
                (df['no2'].fillna(0) * 1.5 if 'no2' in df.columns else 0) +
                (df['so2'].fillna(0) * 1.2 if 'so2' in df.columns else 0) +
                (df['o3'].fillna(0) * 1.3 if 'o3' in df.columns else 0)
            )
            
            # ========================================
            # 5. MOVING AVERAGES (Rolling Windows)
            # ========================================
            # Short-term (3h), medium-term (6h, 12h), long-term (24h)
            for window in [3, 6, 12, 24]:
                # PM2.5 moving averages
                if 'pm25' in df.columns:
                    df[f'pm25_ma_{window}'] = df['pm25'].rolling(
                        window=window, min_periods=1
                    ).mean()
                    df[f'pm25_std_{window}'] = df['pm25'].rolling(
                        window=window, min_periods=1
                    ).std()
                    df[f'pm25_min_{window}'] = df['pm25'].rolling(
                        window=window, min_periods=1
                    ).min()
                    df[f'pm25_max_{window}'] = df['pm25'].rolling(
                        window=window, min_periods=1
                    ).max()
                
                # PM10 moving averages
                if 'pm10' in df.columns:
                    df[f'pm10_ma_{window}'] = df['pm10'].rolling(
                        window=window, min_periods=1
                    ).mean()
                
                # NO2 moving averages
                if 'no2' in df.columns:
                    df[f'no2_ma_{window}'] = df['no2'].rolling(
                        window=window, min_periods=1
                    ).mean()
                
                # AQI moving averages
                if 'aqi_value' in df.columns:
                    df[f'aqi_ma_{window}'] = df['aqi_value'].rolling(
                        window=window, min_periods=1
                    ).mean()
            
            # ========================================
            # 6. LAG FEATURES (Historical Values)
            # ========================================
            for lag in [1, 6, 12, 24]:
                if 'pm25' in df.columns:
                    df[f'pm25_lag_{lag}'] = df['pm25'].shift(lag)
                if 'pm10' in df.columns:
                    df[f'pm10_lag_{lag}'] = df['pm10'].shift(lag)
                if 'aqi_value' in df.columns:
                    df[f'aqi_lag_{lag}'] = df['aqi_value'].shift(lag)
                if 'no2' in df.columns:
                    df[f'no2_lag_{lag}'] = df['no2'].shift(lag)
            
            # ========================================
            # 7. RATE OF CHANGE (Delta Features)
            # ========================================
            # Hourly change
            if 'pm25' in df.columns:
                df['pm25_delta_1h'] = df['pm25'].diff(1)
                df['pm25_delta_6h'] = df['pm25'].diff(6)
                df['pm25_pct_change_1h'] = df['pm25'].pct_change(1) * 100
            
            if 'pm10' in df.columns:
                df['pm10_delta_1h'] = df['pm10'].diff(1)
            
            if 'aqi_value' in df.columns:
                df['aqi_delta_1h'] = df['aqi_value'].diff(1)
                df['aqi_delta_6h'] = df['aqi_value'].diff(6)
                df['aqi_pct_change_1h'] = df['aqi_value'].pct_change(1) * 100
            
            # ========================================
            # 8. INTERACTION FEATURES
            # ========================================
            # Weather interactions (if weather data available)
            if 'temperature' in df.columns and 'humidity' in df.columns:
                # Apparent temperature effect
                df['temp_humidity_interaction'] = df['temperature'] * df['humidity'] / 100
                
                # Temperature × PM2.5 (thermal inversion effect)
                df['temp_pm25_interaction'] = df['temperature'] * df['pm25']
                
                # Wind speed × pollutants (dispersion effect)
                if 'wind_speed' in df.columns:
                    df['wind_pm25_interaction'] = df['wind_speed'] * df['pm25']
                    df['wind_dispersion_index'] = df['wind_speed'] / (df['pm25'] + 1)
            
            # Hour × Weekend (different patterns on weekends)
            df['hour_weekend_interaction'] = df['hour'] * df['is_weekend']
            
            # Season × pollutants (seasonal variations)
            df['winter_pm25'] = df['is_winter'] * df['pm25']
            df['summer_o3'] = df['is_summer'] * df['o3'].fillna(0)
            
            logger.info(f"Features created successfully: {len(df.columns)} total features")
            logger.info(f"  - Temporal: hour, day_of_week, month, quarter, week, day_of_year")
            logger.info(f"  - Seasonal: season categories, weekend, rush hour, time of day")
            logger.info(f"  - Cyclical: 4 pairs (hour, dow, month, doy)")
            logger.info(f"  - Derived: pollutant ratios, indices, totals")
            logger.info(f"  - Moving averages: 3h, 6h, 12h, 24h windows")
            logger.info(f"  - Lags: 1h, 6h, 12h, 24h historical values")
            logger.info(f"  - Rate of change: deltas and percentage changes")
            logger.info(f"  - Interactions: weather × pollutants, time × categories")
            
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
    
    def prepare_training_data(self, city, days=90, use_advanced_cleaning=True):
        """
        Complete preprocessing pipeline with advanced data cleaning
        
        Args:
            city: City name
            days: Number of days of historical data
            use_advanced_cleaning: Whether to use comprehensive cleaning pipeline
        """
        logger.info(f"Preparing training data for {city}")
        
        # Fetch raw data
        df = self.get_training_data(city, days)
        if df is None or df.empty:
            logger.warning(f"No raw data found for {city}")
            return None
        
        logger.info(f"Fetched {len(df)} raw data rows for {city}")
        
        if use_advanced_cleaning:
            # Use comprehensive cleaning pipeline
            df, cleaning_report = self.data_cleaner.comprehensive_cleaning_pipeline(
                df, 
                validate_quality=True,
                check_consistency=True
            )
            
            # Log cleaning summary
            logger.info(f"Advanced cleaning completed:")
            logger.info(f"  - Steps: {', '.join(cleaning_report.get('steps_completed', []))}")
            if 'quality_metrics' in cleaning_report:
                qm = cleaning_report['quality_metrics']
                logger.info(f"  - Completeness: {qm.get('completeness_score', 0)}%")
                logger.info(f"  - Consistency: {qm.get('consistency_score', 0)}%")
            if 'cleaning_stats' in cleaning_report:
                cs = cleaning_report['cleaning_stats']
                logger.info(f"  - Imputed values: {cs.get('imputed_values', 0)}")
                logger.info(f"  - Outliers handled: {cs.get('outliers_detected', 0)}")
                logger.info(f"  - Constraint violations fixed: {cs.get('constraint_violations', 0)}")
        else:
            # Use basic cleaning (backward compatibility)
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