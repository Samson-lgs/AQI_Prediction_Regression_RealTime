"""
Auto Model Selector

Automatically selects the best performing model for each city and horizon
based on live performance metrics.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging
import json

from monitoring.performance_monitor import PerformanceMonitor

logger = logging.getLogger(__name__)


class AutoModelSelector:
    """
    Automatically selects best model per city and horizon based on performance
    """
    
    def __init__(self, db_url: str, performance_monitor: PerformanceMonitor = None):
        """
        Initialize auto selector
        
        Args:
            db_url: PostgreSQL database URL
            performance_monitor: Optional PerformanceMonitor instance
        """
        self.db_url = db_url
        self.monitor = performance_monitor or PerformanceMonitor(db_url)
        self.selection_cache = {}
        
    def _get_connection(self):
        """Get database connection"""
        return psycopg2.connect(self.db_url)
    
    def select_best_model(
        self,
        city: str,
        horizon_hours: int,
        lookback_days: int = 7,
        primary_metric: str = 'rmse',
        min_predictions: int = 10
    ) -> Dict[str, any]:
        """
        Select best performing model for city and horizon
        
        Args:
            city: City name
            horizon_hours: Forecast horizon in hours
            lookback_days: Days to analyze for selection
            primary_metric: Primary metric for selection ('rmse', 'mae', 'r2')
            min_predictions: Minimum predictions required for consideration
        
        Returns:
            Dictionary with best model info
        """
        comparison = self.monitor.get_model_comparison(
            city=city,
            horizon_hours=horizon_hours,
            days=lookback_days
        )
        
        if comparison.empty:
            logger.warning(f"No performance data for {city}/{horizon_hours}h")
            return {
                'city': city,
                'horizon_hours': horizon_hours,
                'best_model': None,
                'reason': 'No performance data available'
            }
        
        # Filter by minimum predictions
        comparison = comparison[comparison['total_predictions'] >= min_predictions]
        
        if comparison.empty:
            logger.warning(
                f"No models meet minimum prediction requirement "
                f"({min_predictions}) for {city}/{horizon_hours}h"
            )
            return {
                'city': city,
                'horizon_hours': horizon_hours,
                'best_model': None,
                'reason': f'No models with >={min_predictions} predictions'
            }
        
        # Select based on primary metric
        if primary_metric == 'rmse':
            best_idx = comparison['avg_rmse'].idxmin()
        elif primary_metric == 'mae':
            best_idx = comparison['avg_mae'].idxmin()
        elif primary_metric == 'r2':
            best_idx = comparison['avg_r2'].idxmax()
        else:
            raise ValueError(f"Unknown metric: {primary_metric}")
        
        best_row = comparison.loc[best_idx]
        
        result = {
            'city': city,
            'horizon_hours': horizon_hours,
            'best_model': best_row['model_name'],
            'metrics': {
                'r2': float(best_row['avg_r2']),
                'rmse': float(best_row['avg_rmse']),
                'mae': float(best_row['avg_mae']),
                'mape': float(best_row['avg_mape'])
            },
            'total_predictions': int(best_row['total_predictions']),
            'selection_date': datetime.now().isoformat(),
            'lookback_days': lookback_days,
            'primary_metric': primary_metric
        }
        
        # Compare with second best
        if len(comparison) > 1:
            comparison_sorted = comparison.sort_values(f'avg_{primary_metric}')
            if primary_metric == 'r2':
                comparison_sorted = comparison_sorted.iloc[::-1]
            
            second_best = comparison_sorted.iloc[1]
            result['second_best_model'] = second_best['model_name']
            result['performance_gap'] = abs(
                best_row[f'avg_{primary_metric}'] - 
                second_best[f'avg_{primary_metric}']
            )
        
        logger.info(
            f"Selected {result['best_model']} for {city}/{horizon_hours}h "
            f"(RMSE={result['metrics']['rmse']:.2f})"
        )
        
        return result
    
    def select_all_best_models(
        self,
        cities: List[str],
        horizons: List[int],
        lookback_days: int = 7
    ) -> Dict[Tuple[str, int], Dict]:
        """
        Select best model for all city/horizon combinations
        
        Args:
            cities: List of cities
            horizons: List of forecast horizons
            lookback_days: Days to analyze
        
        Returns:
            Dictionary mapping (city, horizon) to best model info
        """
        selections = {}
        
        for city in cities:
            for horizon in horizons:
                try:
                    selection = self.select_best_model(
                        city=city,
                        horizon_hours=horizon,
                        lookback_days=lookback_days
                    )
                    
                    key = (city, horizon)
                    selections[key] = selection
                    
                except Exception as e:
                    logger.error(
                        f"Error selecting model for {city}/{horizon}h: {e}"
                    )
        
        return selections
    
    def store_selection(self, selection: Dict):
        """
        Store model selection in database
        
        Args:
            selection: Selection dictionary from select_best_model
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO model_selections (
                    city, horizon_hours, selected_model,
                    selection_reason, metrics, created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                selection['city'],
                selection['horizon_hours'],
                selection['best_model'],
                f"Auto-selected based on {selection.get('primary_metric', 'rmse')}",
                json.dumps(selection.get('metrics', {})),
                datetime.now()
            ))
            
            conn.commit()
            logger.info(
                f"Stored selection: {selection['best_model']} for "
                f"{selection['city']}/{selection['horizon_hours']}h"
            )
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error storing selection: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    def get_active_model(
        self,
        city: str,
        horizon_hours: int
    ) -> Optional[str]:
        """
        Get currently active model for city and horizon
        
        Args:
            city: City name
            horizon_hours: Forecast horizon
        
        Returns:
            Model name or None
        """
        # Check cache first
        cache_key = (city, horizon_hours)
        if cache_key in self.selection_cache:
            cached = self.selection_cache[cache_key]
            # Cache valid for 1 hour
            if (datetime.now() - cached['timestamp']).seconds < 3600:
                return cached['model']
        
        conn = self._get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            cursor.execute("""
                SELECT selected_model, created_at
                FROM model_selections
                WHERE city = %s AND horizon_hours = %s
                ORDER BY created_at DESC
                LIMIT 1
            """, (city, horizon_hours))
            
            result = cursor.fetchone()
            
            if result:
                model = result['selected_model']
                # Update cache
                self.selection_cache[cache_key] = {
                    'model': model,
                    'timestamp': datetime.now()
                }
                return model
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting active model: {e}")
            return None
        finally:
            cursor.close()
            conn.close()
    
    def run_auto_selection(
        self,
        cities: List[str],
        horizons: List[int],
        lookback_days: int = 7,
        store_results: bool = True
    ) -> Dict:
        """
        Run automatic model selection for all combinations
        
        Args:
            cities: List of cities
            horizons: List of horizons
            lookback_days: Days to analyze
            store_results: Whether to store selections in database
        
        Returns:
            Summary of selections
        """
        logger.info("="*80)
        logger.info("AUTO MODEL SELECTION")
        logger.info("="*80)
        
        selections = self.select_all_best_models(
            cities=cities,
            horizons=horizons,
            lookback_days=lookback_days
        )
        
        # Store results
        if store_results:
            for selection in selections.values():
                if selection.get('best_model'):
                    self.store_selection(selection)
        
        # Generate summary
        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_combinations': len(selections),
            'successful_selections': sum(
                1 for s in selections.values() if s.get('best_model')
            ),
            'selections': selections
        }
        
        # Print summary
        logger.info("\nSelection Summary:")
        logger.info(f"Total combinations: {summary['total_combinations']}")
        logger.info(f"Successful selections: {summary['successful_selections']}")
        
        # Group by model
        model_counts = {}
        for selection in selections.values():
            model = selection.get('best_model')
            if model:
                model_counts[model] = model_counts.get(model, 0) + 1
        
        logger.info("\nModel distribution:")
        for model, count in sorted(model_counts.items(), key=lambda x: -x[1]):
            logger.info(f"  {model}: {count} combinations")
        
        return summary
    
    def compare_model_switches(
        self,
        days: int = 30
    ) -> pd.DataFrame:
        """
        Analyze how often models are switched
        
        Args:
            days: Days to analyze
        
        Returns:
            DataFrame with switch analysis
        """
        conn = self._get_connection()
        
        try:
            query = """
                SELECT 
                    city,
                    horizon_hours,
                    selected_model,
                    created_at
                FROM model_selections
                WHERE created_at >= %s
                ORDER BY city, horizon_hours, created_at
            """
            
            df = pd.read_sql_query(
                query, conn,
                params=[datetime.now() - timedelta(days=days)]
            )
            
            if df.empty:
                return pd.DataFrame()
            
            # Count switches per combination
            switches = []
            
            for (city, horizon), group in df.groupby(['city', 'horizon_hours']):
                models = group['selected_model'].tolist()
                
                # Count transitions
                switch_count = sum(
                    1 for i in range(1, len(models))
                    if models[i] != models[i-1]
                )
                
                switches.append({
                    'city': city,
                    'horizon_hours': horizon,
                    'selections': len(models),
                    'switches': switch_count,
                    'current_model': models[-1],
                    'stability': 1 - (switch_count / max(len(models) - 1, 1))
                })
            
            return pd.DataFrame(switches)
            
        except Exception as e:
            logger.error(f"Error analyzing switches: {e}")
            raise
        finally:
            conn.close()
    
    def get_selection_history(
        self,
        city: str,
        horizon_hours: int,
        days: int = 30
    ) -> pd.DataFrame:
        """
        Get selection history for specific city/horizon
        
        Args:
            city: City name
            horizon_hours: Forecast horizon
            days: Days to look back
        
        Returns:
            DataFrame with selection history
        """
        conn = self._get_connection()
        
        try:
            query = """
                SELECT 
                    selected_model,
                    selection_reason,
                    metrics,
                    created_at
                FROM model_selections
                WHERE city = %s
                AND horizon_hours = %s
                AND created_at >= %s
                ORDER BY created_at DESC
            """
            
            df = pd.read_sql_query(
                query, conn,
                params=[city, horizon_hours, datetime.now() - timedelta(days=days)]
            )
            
            return df
            
        except Exception as e:
            logger.error(f"Error getting selection history: {e}")
            raise
        finally:
            conn.close()


if __name__ == "__main__":
    # Test auto selector
    import logging
    logging.basicConfig(level=logging.INFO)
    
    DATABASE_URL = "postgresql://aqi_user:u2I3Xl9kBvUj1xCXGJaeSFHczxNgzdFJ@dpg-d452eqn5r7bs73ba6o7g-a.oregon-postgres.render.com/aqi_db_gr7o"
    
    selector = AutoModelSelector(DATABASE_URL)
    
    print("Testing Auto Model Selector...")
    print("="*80)
    
    # Test selection for one combination
    print("\nSelecting best model for Delhi, 24h:")
    selection = selector.select_best_model('Delhi', 24)
    print(json.dumps(selection, indent=2))
    
    print("\n✅ Auto Model Selector test complete")
