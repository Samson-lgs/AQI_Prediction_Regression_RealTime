"""
Dynamic Alert Rules Manager

Manages alert configuration and dynamically adjusts rules based on user feedback
and system performance.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
import json

from monitoring.feedback_collector import FeedbackCollector

logger = logging.getLogger(__name__)


class AlertRulesManager:
    """
    Manages dynamic alert rules and configuration
    """
    
    # Default alert thresholds (AQI levels)
    DEFAULT_THRESHOLDS = {
        'good': {'min': 0, 'max': 50, 'alert': False},
        'moderate': {'min': 51, 'max': 100, 'alert': False},
        'unhealthy_sensitive': {'min': 101, 'max': 150, 'alert': True},
        'unhealthy': {'min': 151, 'max': 200, 'alert': True},
        'very_unhealthy': {'min': 201, 'max': 300, 'alert': True},
        'hazardous': {'min': 301, 'max': 500, 'alert': True}
    }
    
    def __init__(self, db_url: str, feedback_collector: FeedbackCollector = None):
        """
        Initialize alert rules manager
        
        Args:
            db_url: PostgreSQL database URL
            feedback_collector: Optional FeedbackCollector instance
        """
        self.db_url = db_url
        self.feedback_collector = feedback_collector or FeedbackCollector(db_url)
        self.rules_cache = {}
    
    def _get_connection(self):
        """Get database connection"""
        return psycopg2.connect(self.db_url)
    
    def create_alert_rule(
        self,
        rule_name: str,
        city: str,
        condition_type: str,
        threshold_value: float,
        severity: str,
        message_template: str,
        enabled: bool = True,
        metadata: Dict = None
    ) -> int:
        """
        Create a new alert rule
        
        Args:
            rule_name: Descriptive name for the rule
            city: City to apply rule (or 'all')
            condition_type: Type of condition ('aqi_threshold', 'rapid_increase', 'forecast_high', etc.)
            threshold_value: Numeric threshold for trigger
            severity: Alert severity ('info', 'warning', 'critical')
            message_template: Template for alert message
            enabled: Whether rule is active
            metadata: Additional configuration
        
        Returns:
            Rule ID
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO alert_rules (
                    rule_name, city, condition_type, threshold_value,
                    severity, message_template, enabled, metadata,
                    created_at, updated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                rule_name, city, condition_type, threshold_value,
                severity, message_template, enabled,
                json.dumps(metadata) if metadata else None,
                datetime.now(), datetime.now()
            ))
            
            rule_id = cursor.fetchone()[0]
            conn.commit()
            
            logger.info(f"Created alert rule {rule_id}: {rule_name}")
            
            return rule_id
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error creating alert rule: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    def get_active_rules(self, city: str = None) -> List[Dict]:
        """
        Get active alert rules
        
        Args:
            city: Filter by city (optional)
        
        Returns:
            List of active rules
        """
        conn = self._get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            query = """
                SELECT *
                FROM alert_rules
                WHERE enabled = true
            """
            params = []
            
            if city:
                query += " AND (city = %s OR city = 'all')"
                params.append(city)
            
            query += " ORDER BY severity DESC, threshold_value ASC"
            
            cursor.execute(query, params)
            rules = cursor.fetchall()
            
            return [dict(rule) for rule in rules]
            
        except Exception as e:
            logger.error(f"Error getting active rules: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    def update_rule(
        self,
        rule_id: int,
        threshold_value: float = None,
        enabled: bool = None,
        message_template: str = None,
        metadata: Dict = None
    ):
        """
        Update an existing rule
        
        Args:
            rule_id: Rule ID to update
            threshold_value: New threshold (optional)
            enabled: Enable/disable rule (optional)
            message_template: New message template (optional)
            metadata: New metadata (optional)
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if threshold_value is not None:
            updates.append("threshold_value = %s")
            params.append(threshold_value)
        
        if enabled is not None:
            updates.append("enabled = %s")
            params.append(enabled)
        
        if message_template is not None:
            updates.append("message_template = %s")
            params.append(message_template)
        
        if metadata is not None:
            updates.append("metadata = %s")
            params.append(json.dumps(metadata))
        
        if not updates:
            logger.warning("No updates provided")
            return
        
        updates.append("updated_at = %s")
        params.append(datetime.now())
        
        params.append(rule_id)
        
        try:
            query = f"""
                UPDATE alert_rules
                SET {', '.join(updates)}
                WHERE id = %s
            """
            
            cursor.execute(query, params)
            conn.commit()
            
            logger.info(f"Updated alert rule {rule_id}")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error updating rule: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    def evaluate_rules(
        self,
        city: str,
        current_aqi: float,
        forecast_data: Dict = None
    ) -> List[Dict]:
        """
        Evaluate rules against current conditions
        
        Args:
            city: City name
            current_aqi: Current AQI value
            forecast_data: Optional forecast data
        
        Returns:
            List of triggered alerts
        """
        rules = self.get_active_rules(city=city)
        triggered_alerts = []
        
        for rule in rules:
            triggered = False
            
            condition_type = rule['condition_type']
            threshold = rule['threshold_value']
            
            if condition_type == 'aqi_threshold':
                if current_aqi >= threshold:
                    triggered = True
            
            elif condition_type == 'rapid_increase' and forecast_data:
                # Check if forecast shows rapid increase
                forecast_aqi = forecast_data.get('forecast_aqi', 0)
                increase = forecast_aqi - current_aqi
                if increase >= threshold:
                    triggered = True
            
            elif condition_type == 'forecast_high' and forecast_data:
                # Check if forecast predicts high AQI
                forecast_aqi = forecast_data.get('forecast_aqi', 0)
                if forecast_aqi >= threshold:
                    triggered = True
            
            if triggered:
                alert = {
                    'rule_id': rule['id'],
                    'rule_name': rule['rule_name'],
                    'city': city,
                    'severity': rule['severity'],
                    'message': rule['message_template'].format(
                        city=city,
                        aqi=current_aqi,
                        threshold=threshold
                    ),
                    'current_aqi': current_aqi,
                    'threshold': threshold
                }
                
                triggered_alerts.append(alert)
        
        return triggered_alerts
    
    def adjust_rules_from_feedback(self, days: int = 30):
        """
        Adjust alert rules based on user feedback
        
        Args:
            days: Days of feedback to analyze
        """
        logger.info("Adjusting alert rules based on user feedback...")
        
        # Get alert effectiveness
        effectiveness = self.feedback_collector.get_alert_effectiveness(days=days)
        
        if effectiveness.get('total_alert_feedback', 0) < 10:
            logger.info("Insufficient feedback for rule adjustment")
            return
        
        useful_pct = effectiveness.get('useful_pct', 0)
        timely_pct = effectiveness.get('timely_pct', 0)
        
        adjustments_made = []
        
        # If alerts are not useful, increase thresholds (reduce alert frequency)
        if useful_pct < 50:
            logger.info(f"Low usefulness ({useful_pct:.1f}%). Increasing thresholds...")
            
            conn = self._get_connection()
            cursor = conn.cursor()
            
            try:
                # Increase thresholds by 10%
                cursor.execute("""
                    UPDATE alert_rules
                    SET threshold_value = threshold_value * 1.1,
                        updated_at = %s,
                        metadata = jsonb_set(
                            COALESCE(metadata, '{}'::jsonb),
                            '{adjustment_history}',
                            COALESCE(metadata->'adjustment_history', '[]'::jsonb) || 
                            jsonb_build_object(
                                'date', %s,
                                'reason', 'low_usefulness',
                                'change', '+10%%'
                            )::jsonb
                        )
                    WHERE condition_type = 'aqi_threshold'
                    AND enabled = true
                """, (datetime.now(), datetime.now().isoformat()))
                
                conn.commit()
                adjustments_made.append("Increased AQI thresholds by 10% (low usefulness)")
                
            except Exception as e:
                conn.rollback()
                logger.error(f"Error adjusting thresholds: {e}")
            finally:
                cursor.close()
                conn.close()
        
        # If alerts are too late, adjust timing
        if timely_pct < 60:
            logger.info(f"Low timeliness ({timely_pct:.1f}%). Adjusting forecast horizons...")
            adjustments_made.append("Recommendation: Increase forecast alert lead time")
        
        # Log adjustments
        for adjustment in adjustments_made:
            logger.info(f"  - {adjustment}")
        
        return adjustments_made
    
    def get_rule_performance(self, rule_id: int, days: int = 30) -> Dict:
        """
        Get performance metrics for a specific rule
        
        Args:
            rule_id: Rule ID
            days: Days to analyze
        
        Returns:
            Performance metrics
        """
        conn = self._get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            # Get triggered count
            cursor.execute("""
                SELECT COUNT(*) as triggered_count
                FROM alerts
                WHERE rule_id = %s
                AND created_at >= %s
            """, (rule_id, datetime.now() - timedelta(days=days)))
            
            result = cursor.fetchone()
            triggered_count = result['triggered_count'] if result else 0
            
            # Get feedback on alerts from this rule
            cursor.execute("""
                SELECT 
                    COUNT(*) as feedback_count,
                    AVG(CASE WHEN (metadata->>'was_useful')::boolean THEN 1 ELSE 0 END) as useful_rate
                FROM user_feedback
                WHERE category = 'alert_relevance'
                AND (metadata->>'alert_id')::int IN (
                    SELECT id FROM alerts WHERE rule_id = %s
                )
                AND created_at >= %s
            """, (rule_id, datetime.now() - timedelta(days=days)))
            
            feedback_result = cursor.fetchone()
            
            return {
                'rule_id': rule_id,
                'triggered_count': triggered_count,
                'feedback_count': feedback_result['feedback_count'] if feedback_result else 0,
                'useful_rate': float(feedback_result['useful_rate']) if feedback_result and feedback_result['useful_rate'] else None,
                'period_days': days
            }
            
        except Exception as e:
            logger.error(f"Error getting rule performance: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    def initialize_default_rules(self):
        """Initialize default alert rules for the system"""
        logger.info("Initializing default alert rules...")
        
        default_rules = [
            {
                'rule_name': 'Unhealthy AQI Alert',
                'city': 'all',
                'condition_type': 'aqi_threshold',
                'threshold_value': 151,
                'severity': 'warning',
                'message_template': 'Air quality in {city} is unhealthy (AQI: {aqi}). Sensitive groups should limit outdoor activities.'
            },
            {
                'rule_name': 'Very Unhealthy AQI Alert',
                'city': 'all',
                'condition_type': 'aqi_threshold',
                'threshold_value': 201,
                'severity': 'critical',
                'message_template': 'Air quality in {city} is very unhealthy (AQI: {aqi}). Everyone should avoid outdoor activities.'
            },
            {
                'rule_name': 'Hazardous AQI Alert',
                'city': 'all',
                'condition_type': 'aqi_threshold',
                'threshold_value': 301,
                'severity': 'critical',
                'message_template': 'HAZARDOUS air quality in {city} (AQI: {aqi}). Health warning of emergency conditions!'
            },
            {
                'rule_name': 'Rapid AQI Increase Alert',
                'city': 'all',
                'condition_type': 'rapid_increase',
                'threshold_value': 50,
                'severity': 'warning',
                'message_template': 'Rapid AQI increase predicted for {city}. Current: {aqi}, expected increase: >{threshold}.'
            }
        ]
        
        for rule in default_rules:
            try:
                rule_id = self.create_alert_rule(**rule)
                logger.info(f"  ✓ Created: {rule['rule_name']} (ID: {rule_id})")
            except Exception as e:
                logger.error(f"  ✗ Failed to create {rule['rule_name']}: {e}")


if __name__ == "__main__":
    # Test alert rules manager
    import logging
    logging.basicConfig(level=logging.INFO)
    
    DATABASE_URL = "postgresql://aqi_user:u2I3Xl9kBvUj1xCXGJaeSFHczxNgzdFJ@dpg-d452eqn5r7bs73ba6o7g-a.oregon-postgres.render.com/aqi_db_gr7o"
    
    manager = AlertRulesManager(DATABASE_URL)
    
    print("Testing Alert Rules Manager...")
    print("="*80)
    
    # Test rule evaluation
    print("\nEvaluating rules for Delhi with AQI 180:")
    alerts = manager.evaluate_rules('Delhi', 180)
    for alert in alerts:
        print(f"  - {alert['severity'].upper()}: {alert['message']}")
    
    print("\n✅ Alert Rules Manager test complete")
