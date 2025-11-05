"""
Robust Data Cleaning Module for AQI Prediction System

This module provides comprehensive data cleaning capabilities:
1. Missing value imputation (forward fill, backward fill, interpolation, mean/median)
2. Outlier detection (Z-score, IQR, domain-specific thresholds)
3. Cross-source consistency checks (CPCB, OpenWeather, IQAir)
4. Data quality metrics and validation
5. Anomaly detection using statistical methods
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from scipy import stats
from scipy.interpolate import interp1d
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataCleaner:
    """
    Advanced data cleaning pipeline with multi-source validation
    """
    
    # Domain-specific thresholds for pollutants (WHO guidelines + CPCB standards)
    POLLUTANT_THRESHOLDS = {
        'pm25': {'min': 0, 'max': 999, 'typical_max': 500},      # μg/m³
        'pm10': {'min': 0, 'max': 999, 'typical_max': 600},      # μg/m³
        'no2': {'min': 0, 'max': 2000, 'typical_max': 400},      # μg/m³
        'so2': {'min': 0, 'max': 1000, 'typical_max': 500},      # μg/m³
        'co': {'min': 0, 'max': 50000, 'typical_max': 30000},    # μg/m³
        'o3': {'min': 0, 'max': 500, 'typical_max': 400},        # μg/m³
        'aqi_value': {'min': 0, 'max': 999, 'typical_max': 500},
        'temperature': {'min': -50, 'max': 60, 'typical_max': 55},  # Celsius
        'humidity': {'min': 0, 'max': 100, 'typical_max': 100},     # %
        'wind_speed': {'min': 0, 'max': 150, 'typical_max': 100},   # m/s
        'atmospheric_pressure': {'min': 850, 'max': 1100, 'typical_max': 1050}  # hPa
    }
    
    # Expected correlations between pollutants (for consistency checks)
    EXPECTED_CORRELATIONS = {
        ('pm25', 'pm10'): (0.7, 0.95),    # PM2.5 is subset of PM10
        ('no2', 'co'): (0.5, 0.9),        # Both from combustion
        ('pm25', 'aqi_value'): (0.8, 0.98) # PM2.5 dominates AQI
    }
    
    def __init__(self):
        self.cleaning_stats = {}
        self.quality_metrics = {}
        
    def validate_data_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Assess overall data quality and return metrics
        
        Args:
            df: Input DataFrame
            
        Returns:
            Dictionary with quality metrics
        """
        try:
            metrics = {
                'total_records': len(df),
                'date_range': {
                    'start': df['timestamp'].min() if 'timestamp' in df else None,
                    'end': df['timestamp'].max() if 'timestamp' in df else None
                },
                'missing_percentage': {},
                'outlier_percentage': {},
                'data_sources': df['data_source'].value_counts().to_dict() if 'data_source' in df else {},
                'completeness_score': 0.0,
                'consistency_score': 0.0
            }
            
            # Calculate missing percentages
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            for col in numeric_cols:
                missing_pct = (df[col].isna().sum() / len(df)) * 100
                metrics['missing_percentage'][col] = round(missing_pct, 2)
            
            # Calculate outlier percentages
            for col in ['pm25', 'pm10', 'no2', 'so2', 'co', 'o3', 'aqi_value']:
                if col in df.columns:
                    outliers = self._detect_outliers_zscore(df[col].dropna(), threshold=3)
                    outlier_pct = (outliers.sum() / len(df)) * 100
                    metrics['outlier_percentage'][col] = round(outlier_pct, 2)
            
            # Completeness score (100 - avg missing percentage)
            avg_missing = np.mean(list(metrics['missing_percentage'].values())) if metrics['missing_percentage'] else 0
            metrics['completeness_score'] = round(100 - avg_missing, 2)
            
            # Consistency score (based on expected correlations)
            if 'pm25' in df.columns and 'pm10' in df.columns:
                valid_data = df[['pm25', 'pm10']].dropna()
                if len(valid_data) > 10:
                    # Check if PM2.5 <= PM10 (physical constraint)
                    consistency = (valid_data['pm25'] <= valid_data['pm10']).sum() / len(valid_data)
                    metrics['consistency_score'] = round(consistency * 100, 2)
            
            self.quality_metrics = metrics
            logger.info(f"Data quality assessed: {metrics['completeness_score']}% complete, {metrics['consistency_score']}% consistent")
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error validating data quality: {str(e)}")
            return {}
    
    def impute_missing_values(self, df: pd.DataFrame, method: str = 'hybrid') -> pd.DataFrame:
        """
        Advanced missing value imputation with multiple strategies
        
        Args:
            df: Input DataFrame
            method: 'forward', 'backward', 'interpolate', 'mean', 'median', 'hybrid'
            
        Returns:
            DataFrame with imputed values
        """
        try:
            df = df.copy()
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            
            initial_missing = df[numeric_cols].isna().sum().sum()
            
            if method == 'hybrid':
                # Best practice: Combine multiple strategies
                for col in numeric_cols:
                    # Skip if no missing values
                    if df[col].isna().sum() == 0:
                        continue
                    
                    # Step 1: Linear interpolation for time-series continuity
                    df[col] = df[col].interpolate(method='linear', limit_direction='both')
                    
                    # Step 2: Forward fill for remaining gaps (short-term persistence)
                    df[col] = df[col].fillna(method='ffill', limit=3)
                    
                    # Step 3: Backward fill
                    df[col] = df[col].fillna(method='bfill', limit=3)
                    
                    # Step 4: Fill remaining with rolling mean (6-hour window)
                    rolling_mean = df[col].rolling(window=6, min_periods=1, center=True).mean()
                    df[col] = df[col].fillna(rolling_mean)
                    
                    # Step 5: Last resort - use median (robust to outliers)
                    df[col] = df[col].fillna(df[col].median())
                    
            elif method == 'forward':
                df[numeric_cols] = df[numeric_cols].fillna(method='ffill')
                
            elif method == 'backward':
                df[numeric_cols] = df[numeric_cols].fillna(method='bfill')
                
            elif method == 'interpolate':
                df[numeric_cols] = df[numeric_cols].interpolate(method='linear', limit_direction='both')
                
            elif method == 'mean':
                df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].mean())
                
            elif method == 'median':
                df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].median())
            
            final_missing = df[numeric_cols].isna().sum().sum()
            imputed_count = initial_missing - final_missing
            
            self.cleaning_stats['imputed_values'] = imputed_count
            logger.info(f"Imputed {imputed_count} missing values using '{method}' method")
            
            return df
            
        except Exception as e:
            logger.error(f"Error imputing missing values: {str(e)}")
            return df
    
    def _detect_outliers_zscore(self, series: pd.Series, threshold: float = 3) -> pd.Series:
        """Detect outliers using Z-score method"""
        z_scores = np.abs(stats.zscore(series, nan_policy='omit'))
        return z_scores > threshold
    
    def _detect_outliers_iqr(self, series: pd.Series, multiplier: float = 1.5) -> pd.Series:
        """Detect outliers using Interquartile Range (IQR) method"""
        Q1 = series.quantile(0.25)
        Q3 = series.quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - multiplier * IQR
        upper_bound = Q3 + multiplier * IQR
        return (series < lower_bound) | (series > upper_bound)
    
    def _detect_outliers_domain(self, df: pd.DataFrame, col: str) -> pd.Series:
        """Detect outliers using domain-specific thresholds"""
        if col not in self.POLLUTANT_THRESHOLDS:
            return pd.Series([False] * len(df), index=df.index)
        
        thresholds = self.POLLUTANT_THRESHOLDS[col]
        return (df[col] < thresholds['min']) | (df[col] > thresholds['max'])
    
    def detect_and_handle_outliers(self, df: pd.DataFrame, 
                                   method: str = 'combined',
                                   action: str = 'cap') -> Tuple[pd.DataFrame, Dict[str, int]]:
        """
        Comprehensive outlier detection using multiple methods
        
        Args:
            df: Input DataFrame
            method: 'zscore', 'iqr', 'domain', 'combined'
            action: 'cap' (clip to threshold), 'remove', 'flag', 'interpolate'
            
        Returns:
            Tuple of (cleaned DataFrame, outlier counts)
        """
        try:
            df = df.copy()
            outlier_counts = {}
            pollutant_cols = ['pm25', 'pm10', 'no2', 'so2', 'co', 'o3', 'aqi_value']
            weather_cols = ['temperature', 'humidity', 'wind_speed', 'atmospheric_pressure']
            all_cols = pollutant_cols + weather_cols
            
            for col in all_cols:
                if col not in df.columns:
                    continue
                
                # Detect outliers using selected method(s)
                outliers_mask = pd.Series([False] * len(df), index=df.index)
                
                if method in ['zscore', 'combined']:
                    outliers_mask |= self._detect_outliers_zscore(df[col].dropna(), threshold=3)
                
                if method in ['iqr', 'combined']:
                    outliers_mask |= self._detect_outliers_iqr(df[col].dropna(), multiplier=1.5)
                
                if method in ['domain', 'combined']:
                    outliers_mask |= self._detect_outliers_domain(df, col)
                
                outlier_counts[col] = outliers_mask.sum()
                
                if outlier_counts[col] == 0:
                    continue
                
                # Handle outliers based on action
                if action == 'cap':
                    # Cap to 5th and 95th percentiles
                    lower = df[col].quantile(0.05)
                    upper = df[col].quantile(0.95)
                    df.loc[outliers_mask, col] = df.loc[outliers_mask, col].clip(lower, upper)
                    
                elif action == 'remove':
                    df.loc[outliers_mask, col] = np.nan
                    
                elif action == 'flag':
                    df[f'{col}_outlier_flag'] = outliers_mask
                    
                elif action == 'interpolate':
                    df.loc[outliers_mask, col] = np.nan
                    df[col] = df[col].interpolate(method='linear', limit_direction='both')
            
            total_outliers = sum(outlier_counts.values())
            self.cleaning_stats['outliers_detected'] = total_outliers
            logger.info(f"Detected and handled {total_outliers} outliers using '{method}' method with '{action}' action")
            
            return df, outlier_counts
            
        except Exception as e:
            logger.error(f"Error detecting outliers: {str(e)}")
            return df, {}
    
    def cross_source_consistency_check(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Validate consistency across multiple data sources (CPCB, OpenWeather, IQAir)
        
        Args:
            df: DataFrame with data from multiple sources
            
        Returns:
            Dictionary with consistency metrics and flags
        """
        try:
            if 'data_source' not in df.columns:
                logger.warning("No 'data_source' column found for cross-validation")
                return {}
            
            consistency_report = {
                'sources_available': df['data_source'].unique().tolist(),
                'discrepancies': [],
                'agreement_score': 0.0,
                'recommendations': []
            }
            
            # Group by timestamp and city to compare sources
            if 'timestamp' in df.columns and 'city' in df.columns:
                grouped = df.groupby(['timestamp', 'city'])
                
                discrepancy_count = 0
                total_comparisons = 0
                
                for (timestamp, city), group in grouped:
                    if len(group) < 2:
                        continue  # Need at least 2 sources to compare
                    
                    total_comparisons += 1
                    
                    # Compare PM2.5 values across sources
                    if 'pm25' in group.columns:
                        pm25_values = group['pm25'].dropna()
                        if len(pm25_values) >= 2:
                            # Calculate coefficient of variation (std/mean)
                            cv = pm25_values.std() / pm25_values.mean() if pm25_values.mean() > 0 else 0
                            
                            # Flag if variation > 30%
                            if cv > 0.30:
                                discrepancy_count += 1
                                consistency_report['discrepancies'].append({
                                    'timestamp': timestamp,
                                    'city': city,
                                    'parameter': 'pm25',
                                    'values': pm25_values.to_dict(),
                                    'coefficient_variation': round(cv, 3),
                                    'sources': group['data_source'].tolist()
                                })
                    
                    # Compare AQI values
                    if 'aqi_value' in group.columns:
                        aqi_values = group['aqi_value'].dropna()
                        if len(aqi_values) >= 2:
                            max_diff = aqi_values.max() - aqi_values.min()
                            
                            # Flag if difference > 50 AQI points
                            if max_diff > 50:
                                discrepancy_count += 1
                                consistency_report['discrepancies'].append({
                                    'timestamp': timestamp,
                                    'city': city,
                                    'parameter': 'aqi_value',
                                    'values': aqi_values.to_dict(),
                                    'max_difference': int(max_diff),
                                    'sources': group['data_source'].tolist()
                                })
                
                # Calculate agreement score
                if total_comparisons > 0:
                    consistency_report['agreement_score'] = round(
                        ((total_comparisons - discrepancy_count) / total_comparisons) * 100, 2
                    )
            
            # Generate recommendations
            if len(consistency_report['discrepancies']) > 0:
                consistency_report['recommendations'].append(
                    "Significant discrepancies found between data sources. Consider:"
                )
                consistency_report['recommendations'].append(
                    "1. Prioritize government sources (CPCB) for official reporting"
                )
                consistency_report['recommendations'].append(
                    "2. Use ensemble averaging when multiple sources agree"
                )
                consistency_report['recommendations'].append(
                    "3. Flag outlier sources for manual review"
                )
            else:
                consistency_report['recommendations'].append(
                    "Data sources show good agreement. Safe to use any source."
                )
            
            logger.info(f"Cross-source consistency check: {consistency_report['agreement_score']}% agreement across {len(consistency_report['sources_available'])} sources")
            
            return consistency_report
            
        except Exception as e:
            logger.error(f"Error in cross-source consistency check: {str(e)}")
            return {}
    
    def validate_physical_constraints(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Validate and enforce physical/chemical constraints between pollutants
        
        Examples:
        - PM2.5 should be <= PM10 (PM2.5 is subset of PM10)
        - AQI should correlate with dominant pollutant
        - Temperature should be within reasonable range for location
        """
        try:
            df = df.copy()
            violations = 0
            
            # Constraint 1: PM2.5 <= PM10
            if 'pm25' in df.columns and 'pm10' in df.columns:
                violation_mask = df['pm25'] > df['pm10']
                violations += violation_mask.sum()
                
                if violation_mask.sum() > 0:
                    # Fix: Set PM10 = PM2.5 when violated
                    df.loc[violation_mask, 'pm10'] = df.loc[violation_mask, 'pm25']
                    logger.warning(f"Fixed {violation_mask.sum()} PM2.5 > PM10 violations")
            
            # Constraint 2: All pollutants should be non-negative
            pollutant_cols = ['pm25', 'pm10', 'no2', 'so2', 'co', 'o3']
            for col in pollutant_cols:
                if col in df.columns:
                    negative_mask = df[col] < 0
                    if negative_mask.sum() > 0:
                        df.loc[negative_mask, col] = 0
                        violations += negative_mask.sum()
                        logger.warning(f"Fixed {negative_mask.sum()} negative values in {col}")
            
            # Constraint 3: AQI should be non-negative
            if 'aqi_value' in df.columns:
                negative_aqi = df['aqi_value'] < 0
                if negative_aqi.sum() > 0:
                    df.loc[negative_aqi, 'aqi_value'] = 0
                    violations += negative_aqi.sum()
                    logger.warning(f"Fixed {negative_aqi.sum()} negative AQI values")
            
            # Constraint 4: Humidity should be 0-100%
            if 'humidity' in df.columns:
                df['humidity'] = df['humidity'].clip(0, 100)
            
            # Constraint 5: Wind speed should be non-negative
            if 'wind_speed' in df.columns:
                df['wind_speed'] = df['wind_speed'].clip(0, None)
            
            self.cleaning_stats['constraint_violations'] = violations
            logger.info(f"Validated physical constraints, fixed {violations} violations")
            
            return df
            
        except Exception as e:
            logger.error(f"Error validating physical constraints: {str(e)}")
            return df
    
    def detect_anomalies(self, df: pd.DataFrame, window: int = 24) -> Dict[str, List[Dict]]:
        """
        Detect temporal anomalies using statistical methods
        
        Args:
            df: Input DataFrame
            window: Rolling window size in hours for baseline calculation
            
        Returns:
            Dictionary of detected anomalies by parameter
        """
        try:
            anomalies = {}
            
            for col in ['pm25', 'pm10', 'no2', 'aqi_value']:
                if col not in df.columns:
                    continue
                
                # Calculate rolling statistics
                rolling_mean = df[col].rolling(window=window, min_periods=1).mean()
                rolling_std = df[col].rolling(window=window, min_periods=1).std()
                
                # Detect anomalies (values > 3 std deviations from rolling mean)
                anomaly_mask = np.abs(df[col] - rolling_mean) > (3 * rolling_std)
                
                if anomaly_mask.sum() > 0:
                    anomalies[col] = []
                    anomaly_indices = df[anomaly_mask].index
                    
                    for idx in anomaly_indices:
                        anomalies[col].append({
                            'index': int(idx),
                            'timestamp': df.loc[idx, 'timestamp'] if 'timestamp' in df.columns else None,
                            'value': float(df.loc[idx, col]),
                            'expected_range': (
                                float(rolling_mean[idx] - 3 * rolling_std[idx]),
                                float(rolling_mean[idx] + 3 * rolling_std[idx])
                            ),
                            'severity': 'high' if np.abs(df.loc[idx, col] - rolling_mean[idx]) > (5 * rolling_std[idx]) else 'medium'
                        })
            
            total_anomalies = sum(len(v) for v in anomalies.values())
            logger.info(f"Detected {total_anomalies} temporal anomalies across parameters")
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Error detecting anomalies: {str(e)}")
            return {}
    
    def comprehensive_cleaning_pipeline(self, df: pd.DataFrame, 
                                       validate_quality: bool = True,
                                       check_consistency: bool = True) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Execute complete data cleaning pipeline
        
        Args:
            df: Input DataFrame
            validate_quality: Whether to run quality validation
            check_consistency: Whether to check cross-source consistency
            
        Returns:
            Tuple of (cleaned DataFrame, cleaning report)
        """
        try:
            logger.info("=" * 60)
            logger.info("Starting comprehensive data cleaning pipeline")
            logger.info("=" * 60)
            
            cleaning_report = {
                'initial_records': len(df),
                'steps_completed': [],
                'quality_metrics': {},
                'consistency_metrics': {},
                'cleaning_stats': {}
            }
            
            # Step 1: Validate data quality
            if validate_quality:
                quality_metrics = self.validate_data_quality(df)
                cleaning_report['quality_metrics'] = quality_metrics
                cleaning_report['steps_completed'].append('quality_validation')
            
            # Step 2: Handle missing values
            df = self.impute_missing_values(df, method='hybrid')
            cleaning_report['steps_completed'].append('missing_value_imputation')
            
            # Step 3: Detect and handle outliers
            df, outlier_counts = self.detect_and_handle_outliers(df, method='combined', action='cap')
            cleaning_report['outlier_counts'] = outlier_counts
            cleaning_report['steps_completed'].append('outlier_handling')
            
            # Step 4: Validate physical constraints
            df = self.validate_physical_constraints(df)
            cleaning_report['steps_completed'].append('constraint_validation')
            
            # Step 5: Cross-source consistency check
            if check_consistency and 'data_source' in df.columns:
                consistency_metrics = self.cross_source_consistency_check(df)
                cleaning_report['consistency_metrics'] = consistency_metrics
                cleaning_report['steps_completed'].append('consistency_check')
            
            # Step 6: Anomaly detection
            anomalies = self.detect_anomalies(df, window=24)
            cleaning_report['anomalies_detected'] = {k: len(v) for k, v in anomalies.items()}
            cleaning_report['steps_completed'].append('anomaly_detection')
            
            # Final statistics
            cleaning_report['final_records'] = len(df)
            cleaning_report['records_removed'] = cleaning_report['initial_records'] - cleaning_report['final_records']
            cleaning_report['cleaning_stats'] = self.cleaning_stats
            
            logger.info("=" * 60)
            logger.info("Data cleaning pipeline completed successfully")
            logger.info(f"Records processed: {cleaning_report['initial_records']} → {cleaning_report['final_records']}")
            logger.info("=" * 60)
            
            return df, cleaning_report
            
        except Exception as e:
            logger.error(f"Error in comprehensive cleaning pipeline: {str(e)}")
            return df, {'error': str(e)}
