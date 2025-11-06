# Monitoring Package - Continuous Improvement System

## Overview

Comprehensive continuous improvement system for AQI prediction platform implementing live performance monitoring, automatic model selection, user feedback integration, and dynamic alert management.

## ✅ Status: Complete

All Step 7 requirements implemented and ready for production.

## 🚀 Quick Start

### 1. Update Database

```powershell
# Apply schema updates
psql $DATABASE_URL -f database/step7_schema_updates.sql
```

### 2. Run Continuous Improvement

```powershell
# Full run
python monitoring/continuous_improvement.py --db-url $DATABASE_URL

# Or specific task
python monitoring/continuous_improvement.py --task performance
python monitoring/continuous_improvement.py --task selection
python monitoring/continuous_improvement.py --task feedback
```

## 📦 Components

### 1. PerformanceMonitor
**Purpose**: Track live model performance

**Key Methods**:
- `record_prediction()` - Store predictions
- `calculate_metrics()` - Compute R², RMSE, MAE
- `detect_performance_degradation()` - Alert on issues
- `get_model_comparison()` - Compare all models

**Example**:
```python
from monitoring import PerformanceMonitor

monitor = PerformanceMonitor(DATABASE_URL)
metrics = monitor.calculate_metrics('XGBoost', 'Delhi', 24)
```

### 2. AutoModelSelector
**Purpose**: Select best model per city/horizon

**Key Methods**:
- `select_best_model()` - Choose best performer
- `run_auto_selection()` - Select for all combos
- `get_active_model()` - Get current selection
- `compare_model_switches()` - Analyze stability

**Example**:
```python
from monitoring import AutoModelSelector

selector = AutoModelSelector(DATABASE_URL)
best = selector.select_best_model('Delhi', 24)
print(f"Best model: {best['best_model']}")
```

### 3. FeedbackCollector
**Purpose**: Collect and analyze user feedback

**Key Methods**:
- `submit_feedback()` - Store feedback
- `submit_alert_feedback()` - Alert-specific feedback
- `analyze_feedback()` - Get statistics
- `get_alert_effectiveness()` - Alert metrics
- `generate_feedback_report()` - Full report

**Example**:
```python
from monitoring import FeedbackCollector

collector = FeedbackCollector(DATABASE_URL)
feedback_id = collector.submit_feedback(
    user_id='user123',
    category='alert_relevance',
    feedback_text='Very helpful alert!',
    rating=5
)
```

### 4. AlertRulesManager
**Purpose**: Dynamic alert configuration

**Key Methods**:
- `create_alert_rule()` - Add new rule
- `get_active_rules()` - Get enabled rules
- `evaluate_rules()` - Check conditions
- `adjust_rules_from_feedback()` - Auto-adjust
- `initialize_default_rules()` - Setup defaults

**Example**:
```python
from monitoring import AlertRulesManager

manager = AlertRulesManager(DATABASE_URL)
alerts = manager.evaluate_rules('Delhi', current_aqi=180)
```

### 5. ContinuousImprovementOrchestrator
**Purpose**: Coordinate all activities

**Key Methods**:
- `monitor_performance()` - Track metrics
- `auto_select_models()` - Select best models
- `process_feedback()` - Analyze feedback
- `adjust_alert_rules()` - Update rules
- `generate_system_report()` - Health report
- `run_all()` - Execute everything

**Example**:
```python
from monitoring import ContinuousImprovementOrchestrator

orchestrator = ContinuousImprovementOrchestrator(DATABASE_URL)
results = orchestrator.run_all(
    models=['XGBoost', 'LSTM'],
    cities=['Delhi', 'Mumbai'],
    horizons=[1, 24]
)
```

## 📊 Database Schema

### New Tables

1. **model_selections** - Auto-selected models history
2. **user_feedback** - User feedback with categories
3. **alert_rules** - Dynamic alert configuration
4. **system_config** - Versioned configuration
5. **change_log** - Audit trail
6. **documentation_versions** - Version-controlled docs

### Updated Tables

1. **alerts** - Added rule_id, acknowledged fields
2. **predictions** - Added actual_aqi, features, error
3. **model_performance** - Added mean_error, std_error, prediction_count

## 🎯 Key Features

### Performance Monitoring
- ✅ Real-time prediction tracking
- ✅ Automatic metrics calculation (R², RMSE, MAE, MAPE)
- ✅ Performance degradation detection (>10% threshold)
- ✅ Historical trend analysis
- ✅ Model comparison reports

### Auto Model Selection
- ✅ Best model per city/horizon
- ✅ Multiple selection criteria (RMSE, MAE, R²)
- ✅ Selection history tracking
- ✅ Stability analysis
- ✅ Cached active selections

### User Feedback
- ✅ 10 feedback categories
- ✅ 1-5 star ratings
- ✅ Alert-specific feedback
- ✅ Pattern detection
- ✅ Effectiveness tracking

### Dynamic Alerts
- ✅ Multiple condition types
- ✅ Severity levels (info, warning, critical)
- ✅ Feedback-driven adjustments
- ✅ Performance tracking per rule
- ✅ Auto-threshold adjustment

## 📅 Automation

### Daily Schedule (GitHub Actions)

Create `.github/workflows/continuous_improvement.yml`:

```yaml
name: Continuous Improvement
on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM
  workflow_dispatch:

jobs:
  run-ci:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run Continuous Improvement
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
        run: python monitoring/continuous_improvement.py --task all
```

## 📈 Usage Examples

### Record Prediction and Track Performance

```python
from monitoring import PerformanceMonitor

monitor = PerformanceMonitor(DATABASE_URL)

# 1. Record prediction
prediction_id = monitor.record_prediction(
    model_name='XGBoost',
    city='Delhi',
    horizon_hours=24,
    predicted_value=156.3,
    features={'pm25': 95.2, 'temp': 28.5}
)

# 2. Later, update with actual value
monitor.update_prediction_actual(prediction_id, actual_value=148.7)

# 3. Calculate metrics
metrics = monitor.calculate_metrics('XGBoost', 'Delhi', 24)
print(f"R²: {metrics['r2']:.3f}, RMSE: {metrics['rmse']:.2f}")

# 4. Check for degradation
degradation = monitor.detect_performance_degradation('XGBoost', 'Delhi', 24)
if degradation['degraded']:
    print(f"⚠️  Performance degraded by {degradation['pct_change']:.1f}%")
```

### Auto-Select Best Model

```python
from monitoring import AutoModelSelector

selector = AutoModelSelector(DATABASE_URL)

# Select best model
selection = selector.select_best_model(
    city='Delhi',
    horizon_hours=24,
    lookback_days=7,
    primary_metric='rmse'
)

print(f"Best model: {selection['best_model']}")
print(f"RMSE: {selection['metrics']['rmse']:.2f}")
print(f"R²: {selection['metrics']['r2']:.3f}")

# Use in production
active_model = selector.get_active_model('Delhi', 24)
```

### Process Feedback

```python
from monitoring import FeedbackCollector

collector = FeedbackCollector(DATABASE_URL)

# Submit feedback
feedback_id = collector.submit_feedback(
    user_id='user123',
    category='alert_relevance',
    feedback_text='Alert was very helpful, came just in time!',
    rating=5,
    page='dashboard'
)

# Alert-specific feedback
collector.submit_alert_feedback(
    user_id='user123',
    alert_id=456,
    was_useful=True,
    was_timely=True
)

# Generate report
report = collector.generate_feedback_report(days=30)
print(f"Total feedback: {report['summary']['total_feedback']}")
print(f"Alert effectiveness: {report['alert_effectiveness']}")
```

### Manage Alert Rules

```python
from monitoring import AlertRulesManager

manager = AlertRulesManager(DATABASE_URL)

# Create custom rule
rule_id = manager.create_alert_rule(
    rule_name='High AQI Alert - Delhi',
    city='Delhi',
    condition_type='aqi_threshold',
    threshold_value=150,
    severity='warning',
    message_template='AQI in {city} is {aqi}. Limit outdoor activities.'
)

# Evaluate rules
alerts = manager.evaluate_rules(
    city='Delhi',
    current_aqi=185,
    forecast_data={'forecast_aqi': 210}
)

for alert in alerts:
    print(f"{alert['severity']}: {alert['message']}")

# Auto-adjust based on feedback
manager.adjust_rules_from_feedback(days=30)
```

### Full Orchestration

```python
from monitoring import ContinuousImprovementOrchestrator

orchestrator = ContinuousImprovementOrchestrator(DATABASE_URL)

# Run everything
results = orchestrator.run_all(
    models=['LinearRegression', 'RandomForest', 'XGBoost', 'LSTM', 'StackedEnsemble'],
    cities=['Delhi', 'Mumbai', 'Bangalore'],
    horizons=[1, 6, 12, 24, 48],
    lookback_hours=24,
    lookback_days=7,
    feedback_days=30
)

print(f"Metrics calculated: {results['performance']['metrics_calculated']}")
print(f"Models selected: {results['model_selection']['successful_selections']}")
print(f"Feedback processed: {results['feedback']['summary']['total_feedback']}")
```

## 📊 Reports

### System Health Report
- Location: `reports/system/system_report_*.json`
- Contents: Performance, stability, feedback summary
- Generated: Daily or on-demand

### Feedback Report
- Location: `reports/feedback/feedback_report_*.json`
- Contents: Feedback stats, alert effectiveness, recommendations
- Generated: Weekly or on-demand

## 🎯 Success Metrics

**Performance**:
- R² > 0.80 (good fit)
- RMSE < 50 (acceptable error)
- Degradation detection: <10% change

**Feedback**:
- Alert usefulness >70%
- Alert timeliness >75%
- Average rating >3.5/5

**Selection**:
- Stability >85%
- Switches <3/month per combination

## 🛠️ Troubleshooting

### No Metrics Calculated

```python
# Check if predictions have actual values
from monitoring import PerformanceMonitor
monitor = PerformanceMonitor(DATABASE_URL)
df = monitor.get_recent_metrics(days=7)
print(f"Records: {len(df)}")
```

### Selection Fails

```powershell
# 1. Calculate metrics first
python monitoring/continuous_improvement.py --task performance

# 2. Then select
python monitoring/continuous_improvement.py --task selection
```

### Feedback Not Collected

```sql
-- Check feedback table
SELECT COUNT(*), category FROM user_feedback GROUP BY category;
```

## 📚 Documentation

- **STEP7_CONTINUOUS_IMPROVEMENT_GUIDE.md** - Comprehensive usage guide
- **STEP7_IMPLEMENTATION_SUMMARY.md** - Technical implementation details
- **monitoring/README.md** - This file

## 📞 Support

For issues:
1. Check logs: `logs/continuous_improvement_*.log`
2. Review database schema: `database/step7_schema_updates.sql`
3. Test components individually
4. Verify DATABASE_URL connectivity

## ✅ Validation

All components tested and ready:
- [x] Performance monitoring operational
- [x] Auto model selection working
- [x] Feedback collection active
- [x] Alert rules adjusting dynamically
- [x] Reports generating successfully
- [x] Database schema updated
- [x] Documentation complete

---

**Package Version**: 1.0  
**Implementation Date**: November 2025  
**Status**: ✅ Production Ready  
**Total Lines**: ~3,200 across 8 files
