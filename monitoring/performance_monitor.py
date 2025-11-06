"""
Performance Monitoring System

Tracks live model performance metrics (R², RMSE, MAE) in production,
stores historical data, and provides analytics for continuous improvement.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any
import logging
import json

from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """
    Monitors live model performance and tracks metrics over time
    """
    
    def __init__(self, db_url: str):
        """
        Initialize performance monitor
        
        Args:
            db_url: PostgreSQL database URL
        """
        self.db_url = db_url
        self.metrics_cache = {}
        
    def _get_connection(self):
        """Get database connection"""
        return psycopg2.connect(self.db_url)
    
    def record_prediction(
        self,
        model_name: str,
        city: str,
        horizon_hours: int,
        predicted_value: float,
        actual_value: float = None,
        features: Dict[str, Any] = None,
        timestamp: datetime = None
    ):
        """
        Record a prediction and optionally its actual value for later evaluation
        
        Args:
            model_name: Name of model making prediction
            city: City name
            horizon_hours: Forecast horizon in hours
            predicted_value: Predicted AQI value
            actual_value: Actual AQI value (if available)
            features: Input features used for prediction
            timestamp: Prediction timestamp (defaults to now)
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Store in predictions table with performance tracking
            cursor.execute("""
                INSERT INTO predictions (
                    city, timestamp, predicted_aqi, model_used,
                    horizon_hours, actual_aqi, features, created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                city, timestamp, predicted_value, model_name,
                horizon_hours, actual_value, json.dumps(features) if features else None,
                datetime.now()
            ))
            
            prediction_id = cursor.fetchone()[0]
            conn.commit()
            
            logger.info(f"Recorded prediction {prediction_id} for {city} by {model_name}")
            
            return prediction_id
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error recording prediction: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    def update_prediction_actual(self, prediction_id: int, actual_value: float):
        """
        Update a prediction with its actual value once known
        
        Args:
            prediction_id: ID of prediction record
            actual_value: Actual AQI value observed
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE predictions
                SET actual_aqi = %s,
                    updated_at = %s
                WHERE id = %s
            """, (actual_value, datetime.now(), prediction_id))
            
            conn.commit()
            logger.info(f"Updated prediction {prediction_id} with actual value {actual_value}")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error updating prediction: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    def calculate_metrics(
        self,
        model_name: str,
        city: str = None,
        horizon_hours: int = None,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> Dict[str, float]:
        """
        Calculate performance metrics for a model
        
        Args:
            model_name: Name of model
            city: Filter by city (optional)
            horizon_hours: Filter by horizon (optional)
            start_date: Start date for metrics calculation
            end_date: End date for metrics calculation
        
        Returns:
            Dictionary of metrics (r2, rmse, mae, mape, count)
        """
        conn = self._get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            # Build query with filters
            query = """
                SELECT predicted_aqi, actual_aqi
                FROM predictions
                WHERE model_used = %s
                AND actual_aqi IS NOT NULL
            """
            params = [model_name]
            
            if city:
                query += " AND city = %s"
                params.append(city)
            
            if horizon_hours is not None:
                query += " AND horizon_hours = %s"
                params.append(horizon_hours)
            
            if start_date:
                query += " AND timestamp >= %s"
                params.append(start_date)
            
            if end_date:
                query += " AND timestamp <= %s"
                params.append(end_date)
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            if not results or len(results) < 2:
                return {
                    'r2': None,
                    'rmse': None,
                    'mae': None,
                    'mape': None,
                    'count': len(results) if results else 0
                }
            
            # Extract predictions and actuals
            y_true = np.array([r['actual_aqi'] for r in results])
            y_pred = np.array([r['predicted_aqi'] for r in results])
            
            # Calculate metrics
            r2 = r2_score(y_true, y_pred)
            rmse = np.sqrt(mean_squared_error(y_true, y_pred))
            mae = mean_absolute_error(y_true, y_pred)
            
            # MAPE (handle division by zero)
            mape = np.mean(np.abs((y_true - y_pred) / np.maximum(y_true, 1))) * 100
            
            metrics = {
                'r2': float(r2),
                'rmse': float(rmse),
                'mae': float(mae),
                'mape': float(mape),
                'count': len(results),
                'mean_error': float(np.mean(y_pred - y_true)),
                'std_error': float(np.std(y_pred - y_true))
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating metrics: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    def store_metrics(
        self,
        model_name: str,
        city: str,
        horizon_hours: int,
        metrics: Dict[str, float],
        timestamp: datetime = None
    ):
        """
        Store calculated metrics in model_performance table
        
        Args:
            model_name: Name of model
            city: City name
            horizon_hours: Forecast horizon
            metrics: Dictionary of metric values
            timestamp: Timestamp for metrics (defaults to now)
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO model_performance (
                    model_name, city, horizon_hours, timestamp,
                    r2_score, rmse, mae, mape,
                    prediction_count, mean_error, std_error,
                    created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                model_name, city, horizon_hours, timestamp,
                metrics.get('r2'), metrics.get('rmse'), metrics.get('mae'),
                metrics.get('mape'), metrics.get('count'),
                metrics.get('mean_error'), metrics.get('std_error'),
                datetime.now()
            ))
            
            conn.commit()
            logger.info(f"Stored metrics for {model_name}/{city}/{horizon_hours}h")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error storing metrics: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    def get_recent_metrics(
        self,
        model_name: str = None,
        city: str = None,
        horizon_hours: int = None,
        days: int = 7
    ) -> pd.DataFrame:
        """
        Get recent performance metrics
        
        Args:
            model_name: Filter by model (optional)
            city: Filter by city (optional)
            horizon_hours: Filter by horizon (optional)
            days: Number of days to look back
        
        Returns:
            DataFrame with recent metrics
        """
        conn = self._get_connection()
        
        try:
            query = """
                SELECT *
                FROM model_performance
                WHERE timestamp >= %s
            """
            params = [datetime.now() - timedelta(days=days)]
            
            if model_name:
                query += " AND model_name = %s"
                params.append(model_name)
            
            if city:
                query += " AND city = %s"
                params.append(city)
            
            if horizon_hours is not None:
                query += " AND horizon_hours = %s"
                params.append(horizon_hours)
            
            query += " ORDER BY timestamp DESC"
            
            df = pd.read_sql_query(query, conn, params=params)
            return df
            
        except Exception as e:
            logger.error(f"Error getting recent metrics: {e}")
            raise
        finally:
            conn.close()
    
    def get_model_comparison(
        self,
        city: str,
        horizon_hours: int,
        days: int = 7
    ) -> pd.DataFrame:
        """
        Compare all models for a specific city and horizon
        
        Args:
            city: City name
            horizon_hours: Forecast horizon
            days: Number of days to average over
        
        Returns:
            DataFrame with model comparison
        """
        conn = self._get_connection()
        
        try:
            query = """
                SELECT 
                    model_name,
                    AVG(r2_score) as avg_r2,
                    AVG(rmse) as avg_rmse,
                    AVG(mae) as avg_mae,
                    AVG(mape) as avg_mape,
                    SUM(prediction_count) as total_predictions,
                    COUNT(*) as data_points
                FROM model_performance
                WHERE city = %s
                AND horizon_hours = %s
                AND timestamp >= %s
                GROUP BY model_name
                ORDER BY avg_rmse ASC
            """
            
            df = pd.read_sql_query(
                query, conn,
                params=[city, horizon_hours, datetime.now() - timedelta(days=days)]
            )
            
            return df
            
        except Exception as e:
            logger.error(f"Error getting model comparison: {e}")
            raise
        finally:
            conn.close()
    
    def calculate_and_store_all_metrics(
        self,
        models: List[str],
        cities: List[str],
        horizons: List[int],
        lookback_hours: int = 24
    ):
        """
        Calculate and store metrics for all model/city/horizon combinations
        
        Args:
            models: List of model names
            cities: List of cities
            horizons: List of forecast horizons
            lookback_hours: Hours to look back for metric calculation
        """
        start_time = datetime.now() - timedelta(hours=lookback_hours)
        results = []
        
        for model in models:
            for city in cities:
                for horizon in horizons:
                    try:
                        metrics = self.calculate_metrics(
                            model_name=model,
                            city=city,
                            horizon_hours=horizon,
                            start_date=start_time
                        )
                        
                        if metrics['count'] > 0:
                            self.store_metrics(
                                model_name=model,
                                city=city,
                                horizon_hours=horizon,
                                metrics=metrics
                            )
                            
                            results.append({
                                'model': model,
                                'city': city,
                                'horizon': horizon,
                                'metrics': metrics
                            })
                            
                            logger.info(
                                f"{model}/{city}/{horizon}h: "
                                f"R²={metrics['r2']:.3f}, RMSE={metrics['rmse']:.2f}, "
                                f"MAE={metrics['mae']:.2f} (n={metrics['count']})"
                            )
                        else:
                            logger.warning(
                                f"No data for {model}/{city}/{horizon}h"
                            )
                    
                    except Exception as e:
                        logger.error(
                            f"Error processing {model}/{city}/{horizon}h: {e}"
                        )
        
        return results
    
    def get_performance_trends(
        self,
        model_name: str,
        city: str,
        horizon_hours: int,
        days: int = 30
    ) -> pd.DataFrame:
        """
        Get performance trends over time
        
        Args:
            model_name: Model name
            city: City name
            horizon_hours: Forecast horizon
            days: Days to analyze
        
        Returns:
            DataFrame with daily metrics
        """
        conn = self._get_connection()
        
        try:
            query = """
                SELECT 
                    DATE(timestamp) as date,
                    AVG(r2_score) as r2,
                    AVG(rmse) as rmse,
                    AVG(mae) as mae,
                    SUM(prediction_count) as predictions
                FROM model_performance
                WHERE model_name = %s
                AND city = %s
                AND horizon_hours = %s
                AND timestamp >= %s
                GROUP BY DATE(timestamp)
                ORDER BY date
            """
            
            df = pd.read_sql_query(
                query, conn,
                params=[
                    model_name, city, horizon_hours,
                    datetime.now() - timedelta(days=days)
                ]
            )
            
            return df
            
        except Exception as e:
            logger.error(f"Error getting performance trends: {e}")
            raise
        finally:
            conn.close()
    
    def detect_performance_degradation(
        self,
        model_name: str,
        city: str,
        horizon_hours: int,
        threshold_pct: float = 10.0
    ) -> Dict[str, Any]:
        """
        Detect if model performance has degraded
        
        Args:
            model_name: Model name
            city: City name
            horizon_hours: Forecast horizon
            threshold_pct: Percentage threshold for degradation alert
        
        Returns:
            Dictionary with degradation status and details
        """
        trends = self.get_performance_trends(
            model_name, city, horizon_hours, days=14
        )
        
        if len(trends) < 7:
            return {
                'degraded': False,
                'reason': 'Insufficient data',
                'data_points': len(trends)
            }
        
        # Compare recent week vs previous week
        recent_week = trends.tail(7)
        previous_week = trends.head(7)
        
        recent_rmse = recent_week['rmse'].mean()
        previous_rmse = previous_week['rmse'].mean()
        
        pct_change = ((recent_rmse - previous_rmse) / previous_rmse) * 100
        
        degraded = pct_change > threshold_pct
        
        return {
            'degraded': degraded,
            'recent_rmse': float(recent_rmse),
            'previous_rmse': float(previous_rmse),
            'pct_change': float(pct_change),
            'threshold': threshold_pct,
            'model': model_name,
            'city': city,
            'horizon': horizon_hours
        }


if __name__ == "__main__":
    # Test the performance monitor
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Use Render database URL
    DATABASE_URL = "postgresql://aqi_user:u2I3Xl9kBvUj1xCXGJaeSFHczxNgzdFJ@dpg-d452eqn5r7bs73ba6o7g-a.oregon-postgres.render.com/aqi_db_gr7o"
    
    monitor = PerformanceMonitor(DATABASE_URL)
    
    print("Testing Performance Monitor...")
    print("="*80)
    
    # Test model comparison
    print("\nModel Comparison for Delhi, 24h forecast:")
    comparison = monitor.get_model_comparison('Delhi', 24, days=7)
    print(comparison)
    
    print("\n✅ Performance Monitor test complete")
