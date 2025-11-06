"""
User Feedback System

Collects, stores, and analyzes user feedback for UI/UX improvements
and alert rule refinement.
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
from collections import Counter

logger = logging.getLogger(__name__)


class FeedbackCollector:
    """
    Collects and manages user feedback
    """
    
    FEEDBACK_CATEGORIES = [
        'ui_design',
        'prediction_accuracy',
        'alert_relevance',
        'alert_timing',
        'alert_frequency',
        'data_visualization',
        'feature_request',
        'bug_report',
        'performance',
        'other'
    ]
    
    def __init__(self, db_url: str):
        """
        Initialize feedback collector
        
        Args:
            db_url: PostgreSQL database URL
        """
        self.db_url = db_url
    
    def _get_connection(self):
        """Get database connection"""
        return psycopg2.connect(self.db_url)
    
    def submit_feedback(
        self,
        user_id: str,
        category: str,
        feedback_text: str,
        rating: int = None,
        page: str = None,
        metadata: Dict = None
    ) -> int:
        """
        Submit user feedback
        
        Args:
            user_id: User identifier
            category: Feedback category
            feedback_text: Feedback content
            rating: Optional rating (1-5)
            page: Page/feature where feedback originated
            metadata: Additional context
        
        Returns:
            Feedback ID
        """
        if category not in self.FEEDBACK_CATEGORIES:
            raise ValueError(f"Invalid category. Must be one of {self.FEEDBACK_CATEGORIES}")
        
        if rating and (rating < 1 or rating > 5):
            raise ValueError("Rating must be between 1 and 5")
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO user_feedback (
                    user_id, category, feedback_text, rating,
                    page, metadata, created_at, status
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                user_id, category, feedback_text, rating,
                page, json.dumps(metadata) if metadata else None,
                datetime.now(), 'new'
            ))
            
            feedback_id = cursor.fetchone()[0]
            conn.commit()
            
            logger.info(f"Submitted feedback {feedback_id} from user {user_id}")
            
            return feedback_id
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error submitting feedback: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    def submit_alert_feedback(
        self,
        user_id: str,
        alert_id: int,
        was_useful: bool,
        was_timely: bool,
        feedback_text: str = None
    ) -> int:
        """
        Submit feedback specific to an alert
        
        Args:
            user_id: User identifier
            alert_id: ID of alert being rated
            was_useful: Whether alert was useful
            was_timely: Whether alert was timely
            feedback_text: Optional additional feedback
        
        Returns:
            Feedback ID
        """
        metadata = {
            'alert_id': alert_id,
            'was_useful': was_useful,
            'was_timely': was_timely
        }
        
        return self.submit_feedback(
            user_id=user_id,
            category='alert_relevance',
            feedback_text=feedback_text or f"Alert feedback: useful={was_useful}, timely={was_timely}",
            metadata=metadata
        )
    
    def get_feedback(
        self,
        category: str = None,
        status: str = None,
        days: int = 30
    ) -> pd.DataFrame:
        """
        Get feedback records
        
        Args:
            category: Filter by category
            status: Filter by status ('new', 'reviewed', 'implemented', 'closed')
            days: Days to look back
        
        Returns:
            DataFrame with feedback
        """
        conn = self._get_connection()
        
        try:
            query = """
                SELECT *
                FROM user_feedback
                WHERE created_at >= %s
            """
            params = [datetime.now() - timedelta(days=days)]
            
            if category:
                query += " AND category = %s"
                params.append(category)
            
            if status:
                query += " AND status = %s"
                params.append(status)
            
            query += " ORDER BY created_at DESC"
            
            df = pd.read_sql_query(query, conn, params=params)
            return df
            
        except Exception as e:
            logger.error(f"Error getting feedback: {e}")
            raise
        finally:
            conn.close()
    
    def analyze_feedback(self, days: int = 30) -> Dict:
        """
        Analyze feedback patterns
        
        Args:
            days: Days to analyze
        
        Returns:
            Analysis summary
        """
        df = self.get_feedback(days=days)
        
        if df.empty:
            return {
                'total_feedback': 0,
                'message': 'No feedback data available'
            }
        
        analysis = {
            'total_feedback': len(df),
            'by_category': df['category'].value_counts().to_dict(),
            'by_status': df['status'].value_counts().to_dict(),
            'avg_rating': float(df['rating'].mean()) if 'rating' in df.columns else None,
            'by_page': df['page'].value_counts().to_dict() if 'page' in df.columns else {},
            'date_range': {
                'start': df['created_at'].min().isoformat(),
                'end': df['created_at'].max().isoformat()
            }
        }
        
        # Analyze alert feedback specifically
        alert_feedback = df[df['category'].isin(['alert_relevance', 'alert_timing', 'alert_frequency'])]
        if not alert_feedback.empty:
            analysis['alert_feedback'] = {
                'count': len(alert_feedback),
                'avg_rating': float(alert_feedback['rating'].mean()) if not alert_feedback['rating'].isna().all() else None
            }
        
        return analysis
    
    def get_common_issues(
        self,
        category: str = None,
        days: int = 30,
        min_occurrences: int = 2
    ) -> List[Dict]:
        """
        Identify common issues from feedback
        
        Args:
            category: Filter by category
            days: Days to analyze
            min_occurrences: Minimum times an issue must appear
        
        Returns:
            List of common issues
        """
        df = self.get_feedback(category=category, days=days)
        
        if df.empty:
            return []
        
        # Simple keyword extraction (in production, use NLP)
        keywords = []
        for text in df['feedback_text']:
            if pd.notna(text):
                # Extract words (simplified)
                words = text.lower().split()
                keywords.extend([w for w in words if len(w) > 4])
        
        # Count occurrences
        word_counts = Counter(keywords)
        
        common_issues = [
            {
                'keyword': word,
                'count': count,
                'category': category
            }
            for word, count in word_counts.most_common(10)
            if count >= min_occurrences
        ]
        
        return common_issues
    
    def update_feedback_status(
        self,
        feedback_id: int,
        status: str,
        admin_notes: str = None
    ):
        """
        Update feedback status
        
        Args:
            feedback_id: Feedback ID
            status: New status ('new', 'reviewed', 'implemented', 'closed')
            admin_notes: Admin notes
        """
        valid_statuses = ['new', 'reviewed', 'implemented', 'closed']
        if status not in valid_statuses:
            raise ValueError(f"Status must be one of {valid_statuses}")
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE user_feedback
                SET status = %s,
                    admin_notes = %s,
                    updated_at = %s
                WHERE id = %s
            """, (status, admin_notes, datetime.now(), feedback_id))
            
            conn.commit()
            logger.info(f"Updated feedback {feedback_id} status to {status}")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error updating feedback: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    def get_alert_effectiveness(self, days: int = 30) -> Dict:
        """
        Analyze alert effectiveness from feedback
        
        Args:
            days: Days to analyze
        
        Returns:
            Alert effectiveness metrics
        """
        conn = self._get_connection()
        
        try:
            # Get alert feedback with metadata
            query = """
                SELECT metadata, rating, created_at
                FROM user_feedback
                WHERE category IN ('alert_relevance', 'alert_timing')
                AND metadata IS NOT NULL
                AND created_at >= %s
            """
            
            df = pd.read_sql_query(
                query, conn,
                params=[datetime.now() - timedelta(days=days)]
            )
            
            if df.empty:
                return {
                    'total_alert_feedback': 0,
                    'message': 'No alert feedback data available'
                }
            
            # Parse metadata
            useful_count = 0
            timely_count = 0
            total = len(df)
            
            for _, row in df.iterrows():
                metadata = json.loads(row['metadata']) if isinstance(row['metadata'], str) else row['metadata']
                if metadata.get('was_useful'):
                    useful_count += 1
                if metadata.get('was_timely'):
                    timely_count += 1
            
            return {
                'total_alert_feedback': total,
                'useful_pct': (useful_count / total * 100) if total > 0 else 0,
                'timely_pct': (timely_count / total * 100) if total > 0 else 0,
                'avg_rating': float(df['rating'].mean()) if not df['rating'].isna().all() else None
            }
            
        except Exception as e:
            logger.error(f"Error analyzing alert effectiveness: {e}")
            raise
        finally:
            conn.close()
    
    def generate_feedback_report(self, days: int = 30) -> Dict:
        """
        Generate comprehensive feedback report
        
        Args:
            days: Days to analyze
        
        Returns:
            Comprehensive report
        """
        logger.info(f"Generating feedback report for last {days} days...")
        
        analysis = self.analyze_feedback(days=days)
        alert_effectiveness = self.get_alert_effectiveness(days=days)
        
        # Get top issues by category
        top_issues = {}
        for category in self.FEEDBACK_CATEGORIES:
            issues = self.get_common_issues(category=category, days=days)
            if issues:
                top_issues[category] = issues[:5]
        
        report = {
            'report_date': datetime.now().isoformat(),
            'period_days': days,
            'summary': analysis,
            'alert_effectiveness': alert_effectiveness,
            'top_issues': top_issues,
            'recommendations': self._generate_recommendations(analysis, alert_effectiveness)
        }
        
        return report
    
    def _generate_recommendations(
        self,
        analysis: Dict,
        alert_effectiveness: Dict
    ) -> List[str]:
        """Generate recommendations based on feedback"""
        recommendations = []
        
        # Check alert effectiveness
        if alert_effectiveness.get('total_alert_feedback', 0) > 10:
            useful_pct = alert_effectiveness.get('useful_pct', 0)
            timely_pct = alert_effectiveness.get('timely_pct', 0)
            
            if useful_pct < 50:
                recommendations.append(
                    f"Alert usefulness is low ({useful_pct:.1f}%). "
                    "Review alert thresholds and relevance criteria."
                )
            
            if timely_pct < 60:
                recommendations.append(
                    f"Alert timing needs improvement ({timely_pct:.1f}%). "
                    "Consider adjusting alert trigger timing."
                )
        
        # Check feedback volume by category
        by_category = analysis.get('by_category', {})
        
        if by_category.get('bug_report', 0) > 5:
            recommendations.append(
                f"Multiple bug reports ({by_category['bug_report']}). "
                "Prioritize bug fixes."
            )
        
        if by_category.get('feature_request', 0) > 10:
            recommendations.append(
                f"High volume of feature requests ({by_category['feature_request']}). "
                "Review and prioritize top requested features."
            )
        
        # Check ratings
        avg_rating = analysis.get('avg_rating')
        if avg_rating and avg_rating < 3.0:
            recommendations.append(
                f"Low average rating ({avg_rating:.1f}/5). "
                "User satisfaction needs attention."
            )
        
        if not recommendations:
            recommendations.append("System performing well based on user feedback.")
        
        return recommendations


if __name__ == "__main__":
    # Test feedback collector
    import logging
    logging.basicConfig(level=logging.INFO)
    
    DATABASE_URL = "postgresql://aqi_user:u2I3Xl9kBvUj1xCXGJaeSFHczxNgzdFJ@dpg-d452eqn5r7bs73ba6o7g-a.oregon-postgres.render.com/aqi_db_gr7o"
    
    collector = FeedbackCollector(DATABASE_URL)
    
    print("Testing Feedback Collector...")
    print("="*80)
    
    # Test feedback analysis
    print("\nAnalyzing feedback:")
    analysis = collector.analyze_feedback(days=30)
    print(json.dumps(analysis, indent=2))
    
    print("\n✅ Feedback Collector test complete")
