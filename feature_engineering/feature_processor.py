"""Feature processing for AQI prediction"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from typing import Tuple, List
from config.settings import FEATURE_SCALING, ROLLING_WINDOW

class FeatureProcessor:
    def __init__(self):
        self.scaler = StandardScaler() if FEATURE_SCALING == "standard" else MinMaxScaler()
        self.rolling_window = ROLLING_WINDOW
    
    def process_features(self, data: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
        """
        Process and engineer features for AQI prediction
        
        Args:
            data: Raw data DataFrame
            
        Returns:
            Tuple containing processed features and feature names
        """
        # Add rolling statistics
        data['aqi_rolling_mean'] = data['aqi'].rolling(window=self.rolling_window).mean()
        data['aqi_rolling_std'] = data['aqi'].rolling(window=self.rolling_window).std()
        
        # Add time-based features
        data['hour'] = data.index.hour
        data['day_of_week'] = data.index.dayofweek
        data['month'] = data.index.month
        
        # Scale numerical features
        numerical_features = ['temperature', 'humidity', 'wind_speed', 'aqi_rolling_mean', 'aqi_rolling_std']
        data[numerical_features] = self.scaler.fit_transform(data[numerical_features])
        
        return data, numerical_features