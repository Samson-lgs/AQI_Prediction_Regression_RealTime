"""
Analyze correlation between pollutants and AQI
Check if the data quality supports R² > 0.85
"""
import os
import pandas as pd
import numpy as np
from database.db_operations import DatabaseOperations
from scipy.stats import pearsonr

def analyze_correlations(city='Delhi'):
    """Analyze pollutant-AQI correlations"""
    print(f"\n{'='*80}")
    print(f"AQI CORRELATION ANALYSIS - {city}")
    print(f"{'='*80}\n")
    
    # Get database connection
    db = DatabaseOperations()
    
    # Fetch data
    query = f"""
        SELECT pm25, pm10, no2, so2, co, o3, aqi_value
        FROM pollution_data
        WHERE city = '{city}'
        AND pm25 IS NOT NULL 
        AND pm10 IS NOT NULL
        AND aqi_value IS NOT NULL
        ORDER BY timestamp DESC
        LIMIT 2000
    """
    
    data = db.db.execute_query_dicts(query)
    df = pd.DataFrame(data)
    
    print(f"📊 Data Summary:")
    print(f"  Total samples: {len(df)}")
    print(f"  AQI range: {df['aqi_value'].min():.1f} - {df['aqi_value'].max():.1f}")
    print(f"  AQI mean: {df['aqi_value'].mean():.1f}")
    print(f"  AQI std: {df['aqi_value'].std():.1f}\n")
    
    # Calculate correlations
    pollutants = ['pm25', 'pm10', 'no2', 'so2', 'co', 'o3']
    
    print(f"📈 Pollutant-AQI Correlations:")
    print(f"{'-'*80}")
    print(f"{'Pollutant':<15} {'Correlation':<15} {'Strength':<20} {'P-value'}")
    print(f"{'-'*80}")
    
    correlations = {}
    for pollutant in pollutants:
        if pollutant in df.columns and df[pollutant].notna().sum() > 0:
            corr, p_value = pearsonr(df[pollutant].fillna(0), df['aqi_value'])
            correlations[pollutant] = corr
            
            # Determine strength
            abs_corr = abs(corr)
            if abs_corr > 0.7:
                strength = "Strong ✅"
            elif abs_corr > 0.4:
                strength = "Moderate ⚠️"
            else:
                strength = "Weak ❌"
            
            print(f"{pollutant:<15} {corr:>+.4f}         {strength:<20} {p_value:.2e}")
    
    print(f"{'-'*80}\n")
    
    # Check AQI variance
    print(f"📊 AQI Variance Analysis:")
    print(f"{'-'*80}")
    print(f"  Unique AQI values: {df['aqi_value'].nunique()}")
    print(f"  Variance: {df['aqi_value'].var():.2f}")
    print(f"  Coefficient of Variation: {(df['aqi_value'].std() / df['aqi_value'].mean() * 100):.2f}%")
    
    # Check if most values are the same (indicating poor variability)
    value_counts = df['aqi_value'].value_counts()
    most_common = value_counts.iloc[0]
    most_common_pct = (most_common / len(df)) * 100
    
    print(f"  Most common AQI: {value_counts.index[0]:.0f} ({most_common_pct:.1f}% of data)")
    
    if most_common_pct > 70:
        print(f"\n⚠️  WARNING: {most_common_pct:.1f}% of data has same AQI value!")
        print(f"   This explains low R² - not enough variance to predict!")
    
    print(f"{'-'*80}\n")
    
    # Expected R² based on correlations
    max_corr = max(abs(c) for c in correlations.values())
    expected_r2 = max_corr ** 2
    
    print(f"💡 Expected Performance:")
    print(f"{'-'*80}")
    print(f"  Best single-pollutant R²: {expected_r2:.4f} ({max_corr:.4f}²)")
    print(f"  Multi-pollutant R² (estimated): {min(expected_r2 * 1.2, 0.95):.4f}")
    
    if expected_r2 < 0.85:
        print(f"\n❌ Target R² > 0.85 may NOT be achievable with current data!")
        print(f"   Reasons:")
        print(f"   - Weak pollutant-AQI correlations")
        print(f"   - Data has low variance")
        print(f"   - Possibly synthetic/duplicate data")
    else:
        print(f"\n✅ Target R² > 0.85 should be achievable!")
    
    print(f"{'-'*80}\n")
    
    # Sample data distribution
    print(f"📋 Sample AQI Distribution:")
    print(f"{'-'*80}")
    bins = [0, 50, 100, 200, 300, 400, 500]
    labels = ['0-50', '51-100', '101-200', '201-300', '301-400', '401-500']
    df['aqi_category'] = pd.cut(df['aqi_value'], bins=bins, labels=labels, right=False)
    
    for cat in labels:
        count = (df['aqi_category'] == cat).sum()
        pct = (count / len(df)) * 100
        bar = "█" * int(pct / 5)
        print(f"  {cat:<12} {count:>5} ({pct:>5.1f}%) {bar}")
    
    print(f"{'-'*80}\n")
    
    return correlations, expected_r2


if __name__ == "__main__":
    # Analyze multiple cities
    cities = ['Delhi', 'Mumbai', 'Bangalore']
    
    all_results = {}
    for city in cities:
        correlations, expected_r2 = analyze_correlations(city)
        all_results[city] = {'correlations': correlations, 'expected_r2': expected_r2}
    
    # Summary
    print(f"\n{'='*80}")
    print(f"SUMMARY - All Cities")
    print(f"{'='*80}\n")
    
    print(f"{'City':<15} {'Best Correlation':<20} {'Expected R²':<15} {'Achievable > 0.85?'}")
    print(f"{'-'*80}")
    
    for city, results in all_results.items():
        corrs = results['correlations']
        best_corr = max(abs(c) for c in corrs.values())
        expected_r2 = results['expected_r2']
        achievable = "✅ Yes" if expected_r2 > 0.70 else "❌ No"
        
        print(f"{city:<15} {best_corr:>+.4f}             {expected_r2:<.4f}          {achievable}")
    
    print(f"{'-'*80}\n")
