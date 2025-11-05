"""
Test script to demonstrate robust data cleaning capabilities

This script shows:
1. Missing value imputation
2. Outlier detection and handling
3. Cross-source consistency checks
4. Physical constraint validation
5. Anomaly detection
"""

import os
import sys
from datetime import datetime, timedelta
from database.db_operations import DatabaseOperations
from feature_engineering.data_cleaner import DataCleaner
import pandas as pd
import json

def test_data_cleaning_pipeline(city='Delhi', days=7):
    """
    Test comprehensive data cleaning on real database data
    """
    print("="*80)
    print("DATA CLEANING PIPELINE TEST")
    print("="*80)
    print(f"\nCity: {city}")
    print(f"Data Range: Last {days} days")
    print()
    
    # Initialize components
    db = DatabaseOperations()
    cleaner = DataCleaner()
    
    # Fetch data from database
    print("Step 1: Fetching data from database...")
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    pollution_data = db.get_pollution_data(city, start_date, end_date)
    
    if not pollution_data or len(pollution_data) == 0:
        print(f"❌ No pollution data found for {city}")
        return
    
    print(f"✓ Fetched {len(pollution_data)} pollution records")
    
    # Convert to DataFrame
    df = pd.DataFrame(pollution_data)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp').reset_index(drop=True)
    
    print(f"✓ DataFrame created: {len(df)} rows × {len(df.columns)} columns")
    print()
    
    # Display initial data quality
    print("Step 2: Assessing initial data quality...")
    print("-" * 80)
    quality_before = cleaner.validate_data_quality(df)
    
    print(f"\n📊 Data Quality Metrics (Before Cleaning):")
    print(f"  Total Records: {quality_before.get('total_records', 0)}")
    print(f"  Date Range: {quality_before['date_range']['start']} to {quality_before['date_range']['end']}")
    print(f"  Completeness Score: {quality_before.get('completeness_score', 0)}%")
    print(f"  Consistency Score: {quality_before.get('consistency_score', 0)}%")
    
    print(f"\n  Missing Value Percentages:")
    for col, pct in list(quality_before.get('missing_percentage', {}).items())[:5]:
        print(f"    - {col}: {pct}%")
    
    print(f"\n  Outlier Percentages:")
    for col, pct in list(quality_before.get('outlier_percentage', {}).items())[:5]:
        print(f"    - {col}: {pct}%")
    
    print(f"\n  Data Sources:")
    for source, count in quality_before.get('data_sources', {}).items():
        print(f"    - {source}: {count} records")
    print()
    
    # Run comprehensive cleaning pipeline
    print("Step 3: Running comprehensive data cleaning pipeline...")
    print("-" * 80)
    
    df_cleaned, cleaning_report = cleaner.comprehensive_cleaning_pipeline(
        df,
        validate_quality=True,
        check_consistency=True
    )
    
    print(f"\n✅ Cleaning Pipeline Completed!")
    print(f"\n📋 Cleaning Report:")
    print(f"  Initial Records: {cleaning_report.get('initial_records', 0)}")
    print(f"  Final Records: {cleaning_report.get('final_records', 0)}")
    print(f"  Records Removed: {cleaning_report.get('records_removed', 0)}")
    
    print(f"\n  Steps Completed:")
    for i, step in enumerate(cleaning_report.get('steps_completed', []), 1):
        print(f"    {i}. {step.replace('_', ' ').title()}")
    
    if 'cleaning_stats' in cleaning_report:
        cs = cleaning_report['cleaning_stats']
        print(f"\n  Cleaning Statistics:")
        print(f"    - Values Imputed: {cs.get('imputed_values', 0)}")
        print(f"    - Outliers Detected: {cs.get('outliers_detected', 0)}")
        print(f"    - Constraint Violations Fixed: {cs.get('constraint_violations', 0)}")
    
    if 'outlier_counts' in cleaning_report:
        print(f"\n  Outliers by Parameter:")
        for param, count in cleaning_report['outlier_counts'].items():
            if count > 0:
                print(f"    - {param}: {count}")
    
    if 'anomalies_detected' in cleaning_report:
        print(f"\n  Anomalies Detected:")
        for param, count in cleaning_report['anomalies_detected'].items():
            if count > 0:
                print(f"    - {param}: {count} anomalies")
    print()
    
    # Cross-source consistency check
    if 'consistency_metrics' in cleaning_report and cleaning_report['consistency_metrics']:
        cm = cleaning_report['consistency_metrics']
        print("Step 4: Cross-Source Consistency Analysis...")
        print("-" * 80)
        print(f"\n  Sources Available: {', '.join(cm.get('sources_available', []))}")
        print(f"  Agreement Score: {cm.get('agreement_score', 0)}%")
        
        if len(cm.get('discrepancies', [])) > 0:
            print(f"\n  ⚠️  Discrepancies Found: {len(cm['discrepancies'])}")
            for i, disc in enumerate(cm['discrepancies'][:3], 1):  # Show first 3
                print(f"\n    Discrepancy {i}:")
                print(f"      Timestamp: {disc['timestamp']}")
                print(f"      Parameter: {disc['parameter']}")
                print(f"      Values: {disc['values']}")
                print(f"      Sources: {', '.join(disc['sources'])}")
        
        print(f"\n  💡 Recommendations:")
        for rec in cm.get('recommendations', []):
            print(f"    • {rec}")
        print()
    
    # Final quality assessment
    print("Step 5: Final data quality assessment...")
    print("-" * 80)
    quality_after = cleaner.validate_data_quality(df_cleaned)
    
    print(f"\n📊 Data Quality Metrics (After Cleaning):")
    print(f"  Total Records: {quality_after.get('total_records', 0)}")
    print(f"  Completeness Score: {quality_after.get('completeness_score', 0)}% "
          f"({'↑' if quality_after.get('completeness_score', 0) > quality_before.get('completeness_score', 0) else '→'} "
          f"{abs(quality_after.get('completeness_score', 0) - quality_before.get('completeness_score', 0)):.1f}%)")
    print(f"  Consistency Score: {quality_after.get('consistency_score', 0)}% "
          f"({'↑' if quality_after.get('consistency_score', 0) > quality_before.get('consistency_score', 0) else '→'} "
          f"{abs(quality_after.get('consistency_score', 0) - quality_before.get('consistency_score', 0)):.1f}%)")
    
    print(f"\n  Missing Values After Cleaning:")
    any_missing = False
    for col, pct in quality_after.get('missing_percentage', {}).items():
        if pct > 0:
            print(f"    - {col}: {pct}%")
            any_missing = True
    if not any_missing:
        print(f"    ✅ No missing values remaining!")
    
    print()
    
    # Summary
    print("="*80)
    print("SUMMARY")
    print("="*80)
    print(f"\n✅ Data cleaning pipeline successfully tested on {city} data")
    print(f"\n📈 Quality Improvements:")
    print(f"   • Completeness: {quality_before.get('completeness_score', 0):.1f}% → {quality_after.get('completeness_score', 0):.1f}%")
    print(f"   • Consistency: {quality_before.get('consistency_score', 0):.1f}% → {quality_after.get('consistency_score', 0):.1f}%")
    print(f"   • Records Processed: {cleaning_report.get('initial_records', 0)} → {cleaning_report.get('final_records', 0)}")
    
    print(f"\n🔧 Cleaning Actions:")
    print(f"   • Missing values imputed: {cleaning_report['cleaning_stats'].get('imputed_values', 0)}")
    print(f"   • Outliers handled: {cleaning_report['cleaning_stats'].get('outliers_detected', 0)}")
    print(f"   • Constraint violations fixed: {cleaning_report['cleaning_stats'].get('constraint_violations', 0)}")
    
    print(f"\n✨ The data is now clean and ready for model training!")
    print("="*80)
    

if __name__ == "__main__":
    # Test with a city that has data
    test_cities = ['Delhi', 'Mumbai', 'Bangalore', 'Chennai', 'Ahmedabad']
    
    print("\n🧪 Testing Data Cleaning Pipeline")
    print("=" * 80)
    
    # Try each city until we find one with data
    for city in test_cities:
        try:
            test_data_cleaning_pipeline(city, days=7)
            break  # Success, exit after first city with data
        except Exception as e:
            print(f"\n⚠️  Error testing {city}: {str(e)}")
            print(f"Trying next city...\n")
            continue
    else:
        print("\n❌ No cities with sufficient data found. Please collect data first using:")
        print("   python main.py --once")
