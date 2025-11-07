# Step 6: Validation Framework - Quick Start Guide

## Overview

This validation framework provides comprehensive evaluation of AQI prediction models across three dimensions:

1. **Multi-City Validation**: Test model generalization across Delhi, Mumbai, and Bangalore
2. **Time-Series Forecasting**: Evaluate 1-48 hour ahead predictions with walk-forward validation
3. **API Benchmarking**: Compare against commercial APIs (IQAir, AQICN) and published research

## Quick Start

### 1. Prepare Validation Data

Fetch data from Render PostgreSQL database and prepare features:

```bash
python scripts/prepare_validation_data.py
```

This will:
- Fetch pollution and weather data for Delhi, Mumbai, Bangalore
- Merge datasets on timestamp
- Apply feature engineering
- Save processed data to `data/processed/validation_data_TIMESTAMP.csv`

### 2. Run Complete Validation

```bash
python models/run_step6_validation.py --data-path data/processed/validation_data_TIMESTAMP.csv
```

**Options:**
- `--cities Delhi Mumbai Bangalore` - Cities to validate (default: all three)
- `--horizons 1 6 12 24 48` - Forecast horizons in hours (default: [1,6,12,24,48])
- `--force-train` - Force model retraining
- `--iqair-key YOUR_KEY` - IQAir API key for live benchmarking
- `--aqicn-key YOUR_KEY` - AQICN API key for live benchmarking

### 3. View Results

Results are saved to `models/validation/reports/`:
- `validation_report_TIMESTAMP.json` - Complete results in JSON
- `validation_report_TIMESTAMP.md` - Human-readable markdown report
- `multi_city_summary_TIMESTAMP.csv` - Multi-city metrics table
- `forecasting_summary_TIMESTAMP.csv` - Forecasting metrics table
- `model_rankings_TIMESTAMP.csv` - Overall model rankings
- `validation_plots_TIMESTAMP.png` - Visualization with 6 subplots

## Architecture

### Module Structure

```
models/validation/
├── __init__.py                    # Package exports
├── multi_city_validator.py       # Multi-city validation (676 lines)
├── forecasting_validator.py      # Time-series forecasting (553 lines)
├── api_benchmark.py               # API benchmarking (490 lines)
├── validation_report.py           # Report generation (571 lines)
└── reports/                       # Output directory
```

### Models Validated

1. **Linear Regression** - Baseline model
2. **Random Forest** - Ensemble tree model
3. **XGBoost** - Gradient boosting
4. **LSTM** - Recurrent neural network
5. **Stacked Ensemble** - Meta-learner combining all models

## Validation Details

### Multi-City Validation

**Purpose**: Test geographic generalization

**Methodology**:
- Hold-out validation per city (80/20 split)
- Cross-city generalization tests (train on one city, test on another)
- Stratified metrics by AQI category

**Metrics**:
- R² (coefficient of determination)
- RMSE (Root Mean Square Error)
- MAE (Mean Absolute Error)
- MAPE (Mean Absolute Percentage Error)
- Max Error, Median Absolute Error

**Output**: Best model per city, cross-city performance matrix

### Time-Series Forecasting

**Purpose**: Evaluate temporal prediction accuracy

**Methodology**:
- Rolling window validation with walk-forward approach
- Multi-horizon evaluation (1, 6, 12, 24, 48 hours)
- Temporal train/test split (no data leakage)

**Metrics**:
- Standard regression metrics (R², RMSE, MAE)
- Directional accuracy (% of correctly predicted trend)
- Bias (systematic over/under prediction)
- Skill score vs persistence model

**Output**: Performance degradation analysis, best model per horizon

### API Benchmarking

**Purpose**: Compare against industry standards

**Methodology**:
- Compare predictions with commercial API ground truth
- Benchmark against published research metrics
- Assess improvement over baseline

**Research Benchmarks**:
- **Delhi**: Kumar et al. (2023), Singh et al. (2023), Sharma et al. (2023)
- **Mumbai**: Patel et al. (2023), Gupta et al. (2023)
- **Bangalore**: Reddy et al. (2023), Rao et al. (2023)

**Output**: Performance vs API comparison, improvement over research baselines

## Example Workflow

### Complete Validation Run

```powershell
# Step 1: Activate environment
.\aqi_env\Scripts\Activate.ps1

# Step 2: Prepare data
python scripts/prepare_validation_data.py

# Step 3: Run validation (using latest prepared data)
$latest_data = Get-ChildItem data\processed\validation_data_*.csv | Sort-Object LastWriteTime -Descending | Select-Object -First 1
python models/run_step6_validation.py --data-path $latest_data.FullName

# Step 4: View markdown report
$latest_report = Get-ChildItem models\validation\reports\validation_report_*.md | Sort-Object LastWriteTime -Descending | Select-Object -First 1
code $latest_report.FullName
```

### With API Keys (Optional)

```bash
# Set environment variables
$env:IQAIR_API_KEY="your_iqair_key"
$env:AQICN_API_KEY="your_aqicn_key"

# Run with live API benchmarking
python models/run_step6_validation.py `
  --data-path data/processed/validation_data_latest.csv `
  --iqair-key $env:IQAIR_API_KEY `
  --aqicn-key $env:AQICN_API_KEY
```

### Force Model Retraining

```bash
python models/run_step6_validation.py `
  --data-path data/processed/validation_data_latest.csv `
  --force-train
```

## Interpreting Results

### Model Rankings

Models are ranked using a combined score:
- **60% weight**: Multi-city R² (generalization)
- **40% weight**: Forecasting RMSE (temporal accuracy)

Higher combined score = better overall performance

### Key Metrics to Watch

1. **R² > 0.80**: Good model fit
2. **RMSE < 50**: Acceptable error for most use cases
3. **Directional Accuracy > 70%**: Reliable trend prediction
4. **Skill Score > 0**: Better than persistence baseline

### Red Flags

- Large performance drop across cities → overfitting to one region
- Rapid RMSE increase with horizon → poor long-term forecasting
- Negative skill score → worse than naive baseline
- High bias → systematic under/over prediction

## Troubleshooting

### No Data Available

```bash
# Check database connection
python scripts/test_db_connection.py

# Verify data collection status
python scripts/check_collection_status.py

# View available data
python scripts/view_render_db_data.py
```

### Model Training Fails

- Ensure sufficient data (>500 records per city)
- Check for missing values in features
- Verify column names match expected schema
- Use `--force-train` to retrain from scratch

### Out of Memory

- Reduce number of cities: `--cities Delhi`
- Reduce horizons: `--horizons 1 6 24`
- Use smaller dataset window

### Missing Dependencies

```bash
pip install -r requirements.txt
pip install psycopg2-binary scikit-learn xgboost tensorflow joblib
```

## Performance Expectations

Based on 1,940+ records from 66 cities (as of Nov 2025):

**Expected Metrics**:
- Multi-city R²: 0.75-0.90
- 1-hour RMSE: 20-35
- 24-hour RMSE: 35-50
- 48-hour RMSE: 45-65

**Typical Runtime**:
- Data preparation: 30-60 seconds
- Model training (5 models): 2-5 minutes
- Multi-city validation: 1-2 minutes
- Forecasting validation: 3-5 minutes
- Report generation: 10-20 seconds
- **Total**: ~10-15 minutes

## Output Files Reference

### JSON Report Structure

```json
{
  "metadata": {
    "timestamp": "2025-11-06T...",
    "validation_cities": ["Delhi", "Mumbai", "Bangalore"],
    "models_validated": [...],
    "horizons": [1, 6, 12, 24, 48]
  },
  "multi_city_results": {...},
  "forecasting_results": {...},
  "benchmark_results": {...},
  "overall_rankings": {
    "best_model": "XGBoost",
    "combined_score": 0.8542,
    "rankings": [...]
  }
}
```

### CSV Summaries

**multi_city_summary.csv**:
```
model,city,R²,RMSE,MAE,MAPE
XGBoost,Delhi,0.87,32.5,24.1,18.3
...
```

**forecasting_summary.csv**:
```
model,horizon,R²,RMSE,MAE,directional_accuracy,skill_score
XGBoost,1,0.89,28.3,21.2,0.78,0.32
...
```

## Next Steps

After validation is complete:

1. **Review Results**: Analyze markdown report and plots
2. **Select Best Model**: Based on rankings and use-case requirements
3. **Deploy Model**: Use best performer for production predictions
4. **Monitor Performance**: Set up continuous validation
5. **Iterate**: Retrain with more data, tune hyperparameters

## Support

For issues or questions:
1. Check logs in `models/validation/validation_TIMESTAMP.log`
2. Review error messages in console output
3. Verify database connectivity and data availability
4. Ensure all dependencies are installed

---

**Last Updated**: November 2025  
**Validation Framework Version**: 1.0  
**Models**: Linear Regression, Random Forest, XGBoost, LSTM, Stacked Ensemble
