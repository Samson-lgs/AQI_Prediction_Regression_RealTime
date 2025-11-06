"""
Continuous Improvement Orchestrator

Main script to run all continuous improvement tasks:
- Monitor performance metrics
- Auto-select best models
- Process user feedback
- Adjust alert rules
- Maintain documentation
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
import logging
import json
from datetime import datetime, timedelta
from pathlib import Path

from monitoring.performance_monitor import PerformanceMonitor
from monitoring.auto_model_selector import AutoModelSelector
from monitoring.feedback_collector import FeedbackCollector
from monitoring.alert_rules_manager import AlertRulesManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/continuous_improvement_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ContinuousImprovementOrchestrator:
    """
    Orchestrates all continuous improvement activities
    """
    
    def __init__(self, db_url: str):
        """
        Initialize orchestrator
        
        Args:
            db_url: PostgreSQL database URL
        """
        self.db_url = db_url
        self.performance_monitor = PerformanceMonitor(db_url)
        self.model_selector = AutoModelSelector(db_url, self.performance_monitor)
        self.feedback_collector = FeedbackCollector(db_url)
        self.alert_manager = AlertRulesManager(db_url, self.feedback_collector)
    
    def monitor_performance(
        self,
        models: list,
        cities: list,
        horizons: list,
        lookback_hours: int = 24
    ):
        """
        Monitor and store performance metrics
        
        Args:
            models: List of model names to monitor
            cities: List of cities
            horizons: List of forecast horizons
            lookback_hours: Hours to look back for calculation
        """
        logger.info("="*80)
        logger.info("STEP 1: PERFORMANCE MONITORING")
        logger.info("="*80)
        
        results = self.performance_monitor.calculate_and_store_all_metrics(
            models=models,
            cities=cities,
            horizons=horizons,
            lookback_hours=lookback_hours
        )
        
        logger.info(f"\n✓ Monitored {len(results)} model/city/horizon combinations")
        
        # Check for performance degradation
        degradations = []
        for model in models:
            for city in cities:
                for horizon in horizons:
                    degradation = self.performance_monitor.detect_performance_degradation(
                        model_name=model,
                        city=city,
                        horizon_hours=horizon,
                        threshold_pct=10.0
                    )
                    
                    if degradation.get('degraded'):
                        degradations.append(degradation)
                        logger.warning(
                            f"⚠️  Performance degradation detected: {model}/{city}/{horizon}h "
                            f"(+{degradation['pct_change']:.1f}% RMSE)"
                        )
        
        return {
            'metrics_calculated': len(results),
            'degradations_detected': len(degradations),
            'degradations': degradations
        }
    
    def auto_select_models(
        self,
        cities: list,
        horizons: list,
        lookback_days: int = 7
    ):
        """
        Automatically select best models
        
        Args:
            cities: List of cities
            horizons: List of horizons
            lookback_days: Days to analyze for selection
        """
        logger.info("\n" + "="*80)
        logger.info("STEP 2: AUTO MODEL SELECTION")
        logger.info("="*80)
        
        summary = self.model_selector.run_auto_selection(
            cities=cities,
            horizons=horizons,
            lookback_days=lookback_days,
            store_results=True
        )
        
        logger.info(f"\n✓ Selected best models for {summary['successful_selections']} combinations")
        
        return summary
    
    def process_feedback(self, days: int = 30):
        """
        Process and analyze user feedback
        
        Args:
            days: Days of feedback to analyze
        """
        logger.info("\n" + "="*80)
        logger.info("STEP 3: FEEDBACK PROCESSING")
        logger.info("="*80)
        
        report = self.feedback_collector.generate_feedback_report(days=days)
        
        logger.info(f"\nFeedback Summary (last {days} days):")
        logger.info(f"  Total feedback: {report['summary']['total_feedback']}")
        
        if report['summary']['total_feedback'] > 0:
            logger.info(f"  Average rating: {report['summary'].get('avg_rating', 'N/A')}")
            logger.info(f"  By category: {report['summary']['by_category']}")
        
        logger.info(f"\nAlert Effectiveness:")
        alert_eff = report['alert_effectiveness']
        if alert_eff.get('total_alert_feedback', 0) > 0:
            logger.info(f"  Useful: {alert_eff['useful_pct']:.1f}%")
            logger.info(f"  Timely: {alert_eff['timely_pct']:.1f}%")
        else:
            logger.info("  No alert feedback data")
        
        logger.info(f"\nRecommendations:")
        for rec in report['recommendations']:
            logger.info(f"  • {rec}")
        
        # Save report
        report_dir = Path("reports/feedback")
        report_dir.mkdir(parents=True, exist_ok=True)
        
        report_path = report_dir / f"feedback_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"\n✓ Feedback report saved: {report_path}")
        
        return report
    
    def adjust_alert_rules(self, days: int = 30):
        """
        Adjust alert rules based on feedback
        
        Args:
            days: Days of feedback to consider
        """
        logger.info("\n" + "="*80)
        logger.info("STEP 4: ALERT RULES ADJUSTMENT")
        logger.info("="*80)
        
        adjustments = self.alert_manager.adjust_rules_from_feedback(days=days)
        
        if adjustments:
            logger.info(f"\n✓ Made {len(adjustments)} adjustments:")
            for adj in adjustments:
                logger.info(f"  • {adj}")
        else:
            logger.info("\n✓ No adjustments needed")
        
        return adjustments
    
    def generate_system_report(self):
        """
        Generate comprehensive system health report
        """
        logger.info("\n" + "="*80)
        logger.info("SYSTEM HEALTH REPORT")
        logger.info("="*80)
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'sections': {}
        }
        
        # Recent model performance
        logger.info("\nRecent Model Performance (7 days):")
        performance_df = self.performance_monitor.get_recent_metrics(days=7)
        
        if not performance_df.empty:
            avg_metrics = performance_df.groupby('model_name').agg({
                'r2_score': 'mean',
                'rmse': 'mean',
                'mae': 'mean'
            }).round(3)
            
            logger.info(f"\n{avg_metrics.to_string()}")
            report['sections']['performance'] = avg_metrics.to_dict()
        else:
            logger.info("  No performance data available")
        
        # Model selection stability
        logger.info("\nModel Selection Stability:")
        switches_df = self.model_selector.compare_model_switches(days=30)
        
        if not switches_df.empty:
            logger.info(f"  Average stability: {switches_df['stability'].mean():.2%}")
            unstable = switches_df[switches_df['stability'] < 0.7]
            if not unstable.empty:
                logger.info(f"  ⚠️  {len(unstable)} combinations with low stability")
            
            report['sections']['selection_stability'] = {
                'avg_stability': float(switches_df['stability'].mean()),
                'unstable_count': len(unstable)
            }
        else:
            logger.info("  No selection history available")
        
        # Feedback summary
        logger.info("\nUser Feedback (30 days):")
        feedback_analysis = self.feedback_collector.analyze_feedback(days=30)
        
        if feedback_analysis['total_feedback'] > 0:
            logger.info(f"  Total feedback: {feedback_analysis['total_feedback']}")
            logger.info(f"  Average rating: {feedback_analysis.get('avg_rating', 'N/A')}")
            
            report['sections']['feedback'] = {
                'total': feedback_analysis['total_feedback'],
                'avg_rating': feedback_analysis.get('avg_rating')
            }
        else:
            logger.info("  No feedback data")
        
        # Save report
        report_dir = Path("reports/system")
        report_dir.mkdir(parents=True, exist_ok=True)
        
        report_path = report_dir / f"system_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"\n✓ System report saved: {report_path}")
        
        return report
    
    def run_all(
        self,
        models: list,
        cities: list,
        horizons: list,
        lookback_hours: int = 24,
        lookback_days: int = 7,
        feedback_days: int = 30
    ):
        """
        Run all continuous improvement tasks
        
        Args:
            models: List of models to monitor
            cities: List of cities
            horizons: List of forecast horizons
            lookback_hours: Hours for performance calculation
            lookback_days: Days for model selection
            feedback_days: Days of feedback to analyze
        """
        logger.info("="*80)
        logger.info("CONTINUOUS IMPROVEMENT - FULL RUN")
        logger.info("="*80)
        logger.info(f"Started at: {datetime.now()}")
        
        results = {}
        
        # 1. Monitor performance
        try:
            results['performance'] = self.monitor_performance(
                models=models,
                cities=cities,
                horizons=horizons,
                lookback_hours=lookback_hours
            )
        except Exception as e:
            logger.error(f"Performance monitoring failed: {e}", exc_info=True)
            results['performance'] = {'error': str(e)}
        
        # 2. Auto-select models
        try:
            results['model_selection'] = self.auto_select_models(
                cities=cities,
                horizons=horizons,
                lookback_days=lookback_days
            )
        except Exception as e:
            logger.error(f"Model selection failed: {e}", exc_info=True)
            results['model_selection'] = {'error': str(e)}
        
        # 3. Process feedback
        try:
            results['feedback'] = self.process_feedback(days=feedback_days)
        except Exception as e:
            logger.error(f"Feedback processing failed: {e}", exc_info=True)
            results['feedback'] = {'error': str(e)}
        
        # 4. Adjust alert rules
        try:
            results['alert_adjustments'] = self.adjust_alert_rules(days=feedback_days)
        except Exception as e:
            logger.error(f"Alert adjustment failed: {e}", exc_info=True)
            results['alert_adjustments'] = {'error': str(e)}
        
        # 5. Generate system report
        try:
            results['system_report'] = self.generate_system_report()
        except Exception as e:
            logger.error(f"System report generation failed: {e}", exc_info=True)
            results['system_report'] = {'error': str(e)}
        
        logger.info("\n" + "="*80)
        logger.info("CONTINUOUS IMPROVEMENT - COMPLETE")
        logger.info("="*80)
        logger.info(f"Completed at: {datetime.now()}")
        
        return results


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Step 7: Continuous Improvement Orchestrator'
    )
    parser.add_argument(
        '--db-url',
        type=str,
        default=os.getenv('DATABASE_URL'),
        help='PostgreSQL database URL'
    )
    parser.add_argument(
        '--models',
        nargs='+',
        default=['LinearRegression', 'RandomForest', 'XGBoost', 'LSTM', 'StackedEnsemble'],
        help='Models to monitor'
    )
    parser.add_argument(
        '--cities',
        nargs='+',
        default=['Delhi', 'Mumbai', 'Bangalore'],
        help='Cities to monitor'
    )
    parser.add_argument(
        '--horizons',
        nargs='+',
        type=int,
        default=[1, 6, 12, 24, 48],
        help='Forecast horizons (hours)'
    )
    parser.add_argument(
        '--lookback-hours',
        type=int,
        default=24,
        help='Hours to look back for performance metrics'
    )
    parser.add_argument(
        '--lookback-days',
        type=int,
        default=7,
        help='Days to analyze for model selection'
    )
    parser.add_argument(
        '--feedback-days',
        type=int,
        default=30,
        help='Days of feedback to analyze'
    )
    parser.add_argument(
        '--task',
        choices=['all', 'performance', 'selection', 'feedback', 'alerts', 'report'],
        default='all',
        help='Specific task to run'
    )
    
    args = parser.parse_args()
    
    if not args.db_url:
        logger.error("Database URL not provided. Set DATABASE_URL or use --db-url")
        return 1
    
    orchestrator = ContinuousImprovementOrchestrator(args.db_url)
    
    try:
        if args.task == 'all':
            orchestrator.run_all(
                models=args.models,
                cities=args.cities,
                horizons=args.horizons,
                lookback_hours=args.lookback_hours,
                lookback_days=args.lookback_days,
                feedback_days=args.feedback_days
            )
        
        elif args.task == 'performance':
            orchestrator.monitor_performance(
                models=args.models,
                cities=args.cities,
                horizons=args.horizons,
                lookback_hours=args.lookback_hours
            )
        
        elif args.task == 'selection':
            orchestrator.auto_select_models(
                cities=args.cities,
                horizons=args.horizons,
                lookback_days=args.lookback_days
            )
        
        elif args.task == 'feedback':
            orchestrator.process_feedback(days=args.feedback_days)
        
        elif args.task == 'alerts':
            orchestrator.adjust_alert_rules(days=args.feedback_days)
        
        elif args.task == 'report':
            orchestrator.generate_system_report()
        
        return 0
        
    except Exception as e:
        logger.error(f"Continuous improvement failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
