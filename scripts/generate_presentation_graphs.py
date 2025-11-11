"""
Generate Presentation-Ready Graphs for XGBoost AQI Prediction Model
Author: Generated for AQI Prediction Project
Date: November 11, 2025
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import xgboost as xgb
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Set professional style
plt.style.use('default')
plt.rcParams['figure.facecolor'] = 'white'
plt.rcParams['axes.grid'] = True

# Define paths
BASE_DIR = Path(__file__).parent.parent
DATA_PATH = BASE_DIR / "current_aqi_all_cities.csv"
MODEL_PATH = BASE_DIR / "models" / "saved_models" / "xgboost_20251108_153120.json"
OUTPUT_DIR = BASE_DIR / "presentation_graphs"
OUTPUT_DIR.mkdir(exist_ok=True)

# Color scheme for professional presentation
COLORS = {
    'primary': '#2E86AB',
    'secondary': '#A23B72',
    'accent': '#F18F01',
    'success': '#06A77D',
    'warning': '#C73E1D',
    'neutral': '#6C757D'
}

def load_and_prepare_data():
    """Load and prepare the current AQI data"""
    print("📊 Loading data from current_aqi_all_cities.csv...")
    
    df = pd.read_csv(DATA_PATH)
    print(f"   ✓ Loaded {len(df)} records from {len(df['city'].unique())} cities")
    
    # Feature columns (pollutants)
    feature_cols = ['pm25', 'pm10', 'no2', 'so2', 'co', 'o3']
    
    # Prepare features and target
    X = df[feature_cols].copy()
    y = df['aqi_value'].copy()
    
    # Handle any missing values
    X = X.fillna(X.median())
    
    print(f"   ✓ Features shape: {X.shape}")
    print(f"   ✓ Target range: {y.min():.1f} - {y.max():.1f}")
    
    return df, X, y, feature_cols

def load_xgboost_model():
    """Load the trained XGBoost model"""
    print(f"\n🤖 Loading XGBoost model from {MODEL_PATH.name}...")
    
    model = xgb.XGBRegressor()
    model.load_model(str(MODEL_PATH))
    
    print("   ✓ Model loaded successfully")
    return model

def make_predictions(model, X):
    """Make predictions using the loaded model"""
    print("\n🔮 Generating predictions...")
    
    predictions = model.predict(X)
    predictions = np.maximum(predictions, 0)  # Ensure non-negative
    
    print(f"   ✓ Predictions range: {predictions.min():.1f} - {predictions.max():.1f}")
    return predictions

def calculate_metrics(y_actual, y_pred):
    """Calculate model performance metrics"""
    from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
    
    mse = mean_squared_error(y_actual, y_pred)
    rmse = np.sqrt(mse)
    mae = mean_absolute_error(y_actual, y_pred)
    r2 = r2_score(y_actual, y_pred)
    
    # MAPE
    safe_y = np.where(y_actual == 0, 1e-6, y_actual)
    mape = np.mean(np.abs((y_actual - y_pred) / safe_y)) * 100
    
    metrics = {
        'RMSE': rmse,
        'MAE': mae,
        'R²': r2,
        'MAPE': mape
    }
    
    print("\n📈 Model Performance Metrics:")
    for metric, value in metrics.items():
        print(f"   {metric}: {value:.3f}")
    
    return metrics

def plot_correlation_heatmap(df, feature_cols):
    """🔹 Plot 1: Correlation Heatmap"""
    print("\n🎨 Creating Correlation Heatmap...")
    
    plt.figure(figsize=(12, 8))
    
    # Select features and target
    corr_data = df[feature_cols + ['aqi_value']].copy()
    corr_matrix = corr_data.corr()
    
    # Create heatmap without mask (full matrix) using matplotlib
    im = plt.imshow(corr_matrix, cmap='RdYlGn_r', aspect='auto', vmin=-1, vmax=1)
    
    # Add colorbar
    cbar = plt.colorbar(im, shrink=0.8)
    cbar.set_label('Correlation', rotation=270, labelpad=20)
    
    # Add correlation values as text
    for i in range(len(corr_matrix)):
        for j in range(len(corr_matrix)):
            text = plt.text(j, i, f'{corr_matrix.iloc[i, j]:.3f}',
                          ha="center", va="center", color="black", fontsize=9)
    
    # Set ticks and labels
    plt.xticks(range(len(corr_matrix)), corr_matrix.columns, rotation=45, ha='right')
    plt.yticks(range(len(corr_matrix)), corr_matrix.columns)
    
    plt.title('Correlation Heatmap: Pollutants vs AQI Value', 
              fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Features', fontsize=12, fontweight='bold')
    plt.ylabel('Features', fontsize=12, fontweight='bold')
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    plt.tight_layout()
    
    output_path = OUTPUT_DIR / '01_correlation_heatmap.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"   ✓ Saved: {output_path.name}")
    plt.close()

def plot_actual_vs_predicted(y_actual, y_pred, metrics):
    """🔹 Plot 2: Actual vs Predicted Scatter Plot"""
    print("\n🎨 Creating Actual vs Predicted Scatter Plot...")
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Scatter plot
    scatter = ax.scatter(y_actual, y_pred, 
                        alpha=0.6, 
                        s=100,
                        c=y_actual,
                        cmap='viridis',
                        edgecolors='black',
                        linewidth=0.5)
    
    # Perfect prediction line
    min_val = min(y_actual.min(), y_pred.min())
    max_val = max(y_actual.max(), y_pred.max())
    ax.plot([min_val, max_val], [min_val, max_val], 
            'r--', linewidth=2, label='Perfect Prediction', alpha=0.7)
    
    # Add colorbar
    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label('Actual AQI Value', fontsize=11, fontweight='bold')
    
    # Add metrics text box
    textstr = f'R² = {metrics["R²"]:.3f}\nRMSE = {metrics["RMSE"]:.2f}\nMAE = {metrics["MAE"]:.2f}\nMAPE = {metrics["MAPE"]:.2f}%'
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.8)
    ax.text(0.05, 0.95, textstr, transform=ax.transAxes, 
            fontsize=11, verticalalignment='top', bbox=props)
    
    ax.set_xlabel('Actual AQI Value', fontsize=13, fontweight='bold')
    ax.set_ylabel('Predicted AQI Value', fontsize=13, fontweight='bold')
    ax.set_title('Actual vs Predicted AQI Values (XGBoost Model)', 
                fontsize=16, fontweight='bold', pad=20)
    ax.legend(loc='lower right', fontsize=11)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    output_path = OUTPUT_DIR / '02_actual_vs_predicted.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"   ✓ Saved: {output_path.name}")
    plt.close()

def plot_residual_distribution(y_actual, y_pred):
    """🔹 Plot 3: Residual Error Distribution"""
    print("\n🎨 Creating Residual Error Distribution...")
    
    residuals = y_actual - y_pred
    
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    
    # 1. Histogram with KDE
    ax1 = axes[0, 0]
    ax1.hist(residuals, bins=30, alpha=0.7, color=COLORS['primary'], edgecolor='black')
    ax1.axvline(x=0, color='red', linestyle='--', linewidth=2, label='Zero Error')
    ax1.set_xlabel('Residual Error (Actual - Predicted)', fontsize=11, fontweight='bold')
    ax1.set_ylabel('Frequency', fontsize=11, fontweight='bold')
    ax1.set_title('Residual Distribution', fontsize=13, fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2. KDE Plot
    ax2 = axes[0, 1]
    residuals.plot(kind='kde', ax=ax2, color=COLORS['secondary'], linewidth=2)
    ax2.axvline(x=0, color='red', linestyle='--', linewidth=2, label='Zero Error')
    ax2.set_xlabel('Residual Error', fontsize=11, fontweight='bold')
    ax2.set_ylabel('Density', fontsize=11, fontweight='bold')
    ax2.set_title('Residual Density Plot', fontsize=13, fontweight='bold')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 3. Residual vs Predicted
    ax3 = axes[1, 0]
    ax3.scatter(y_pred, residuals, alpha=0.6, s=80, color=COLORS['accent'], edgecolors='black', linewidth=0.5)
    ax3.axhline(y=0, color='red', linestyle='--', linewidth=2)
    ax3.set_xlabel('Predicted AQI Value', fontsize=11, fontweight='bold')
    ax3.set_ylabel('Residual Error', fontsize=11, fontweight='bold')
    ax3.set_title('Residuals vs Predicted Values', fontsize=13, fontweight='bold')
    ax3.grid(True, alpha=0.3)
    
    # 4. Q-Q Plot
    ax4 = axes[1, 1]
    from scipy import stats
    stats.probplot(residuals, dist="norm", plot=ax4)
    ax4.set_title('Q-Q Plot (Normality Check)', fontsize=13, fontweight='bold')
    ax4.grid(True, alpha=0.3)
    
    # Add statistics
    stats_text = f'Mean Error: {residuals.mean():.2f}\nStd Dev: {residuals.std():.2f}\nSkewness: {residuals.skew():.3f}'
    fig.text(0.5, 0.02, stats_text, ha='center', fontsize=11, 
             bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.7))
    
    plt.suptitle('Residual Error Analysis', fontsize=16, fontweight='bold', y=0.995)
    plt.tight_layout(rect=[0, 0.03, 1, 0.99])
    
    output_path = OUTPUT_DIR / '03_residual_distribution.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"   ✓ Saved: {output_path.name}")
    plt.close()

def plot_feature_importance(model, feature_cols):
    """🔹 Plot 4: Feature Importance Plot"""
    print("\n🎨 Creating Feature Importance Plot...")
    
    # Get feature importance
    importance_dict = model.get_booster().get_score(importance_type='gain')
    
    # Map feature names
    feature_names = {f'f{i}': name for i, name in enumerate(feature_cols)}
    importance_data = {feature_names.get(k, k): v for k, v in importance_dict.items()}
    
    # Sort by importance
    sorted_importance = dict(sorted(importance_data.items(), key=lambda x: x[1], reverse=True))
    
    # Create plot
    fig, ax = plt.subplots(figsize=(12, 8))
    
    features = list(sorted_importance.keys())
    importances = list(sorted_importance.values())
    colors_list = [COLORS['primary'], COLORS['secondary'], COLORS['accent'], 
                   COLORS['success'], COLORS['warning'], COLORS['neutral']]
    
    bars = ax.barh(features, importances, color=colors_list[:len(features)], 
                   edgecolor='black', linewidth=1.5)
    
    # Add value labels
    for i, (bar, val) in enumerate(zip(bars, importances)):
        ax.text(val, i, f' {val:.1f}', va='center', fontsize=10, fontweight='bold')
    
    ax.set_xlabel('Importance Score (Gain)', fontsize=13, fontweight='bold')
    ax.set_ylabel('Features (Pollutants)', fontsize=13, fontweight='bold')
    ax.set_title('Feature Importance in XGBoost AQI Prediction Model', 
                fontsize=16, fontweight='bold', pad=20)
    ax.grid(axis='x', alpha=0.3)
    
    plt.tight_layout()
    output_path = OUTPUT_DIR / '04_feature_importance.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"   ✓ Saved: {output_path.name}")
    plt.close()

def plot_predicted_vs_actual_trend(df, y_actual, y_pred):
    """🔹 Plot 5: Predicted vs Actual Trend Plot"""
    print("\n🎨 Creating Predicted vs Actual Trend Plot...")
    
    # Create a dataframe for plotting
    plot_df = pd.DataFrame({
        'City': df['city'].values,
        'Actual': y_actual.values,
        'Predicted': y_pred
    })
    
    # Sort by actual AQI for better visualization
    plot_df = plot_df.sort_values('Actual', ascending=False).reset_index(drop=True)
    
    # Take top 30 cities for clarity
    plot_df = plot_df.head(30)
    
    fig, ax = plt.subplots(figsize=(16, 10))
    
    x_pos = np.arange(len(plot_df))
    width = 0.35
    
    # Create bars
    bars1 = ax.bar(x_pos - width/2, plot_df['Actual'], width, 
                   label='Actual AQI', color=COLORS['primary'], 
                   alpha=0.8, edgecolor='black', linewidth=1)
    bars2 = ax.bar(x_pos + width/2, plot_df['Predicted'], width, 
                   label='Predicted AQI', color=COLORS['accent'], 
                   alpha=0.8, edgecolor='black', linewidth=1)
    
    # Add value labels on bars
    def add_value_labels(bars):
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.0f}',
                   ha='center', va='bottom', fontsize=8, rotation=0)
    
    add_value_labels(bars1)
    add_value_labels(bars2)
    
    # Customize
    ax.set_xlabel('Cities (Sorted by Actual AQI)', fontsize=13, fontweight='bold')
    ax.set_ylabel('AQI Value', fontsize=13, fontweight='bold')
    ax.set_title('Predicted vs Actual AQI Values Across Top 30 Cities', 
                fontsize=16, fontweight='bold', pad=20)
    ax.set_xticks(x_pos)
    ax.set_xticklabels(plot_df['City'], rotation=45, ha='right', fontsize=9)
    ax.legend(loc='upper right', fontsize=12)
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    output_path = OUTPUT_DIR / '05_predicted_vs_actual_trend.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"   ✓ Saved: {output_path.name}")
    plt.close()

def create_summary_report(df, metrics, feature_cols, predictions):
    """Create a summary report"""
    print("\n📄 Creating Summary Report...")
    
    report_path = OUTPUT_DIR / 'model_summary_report.txt'
    
    with open(report_path, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("XGBoost AQI Prediction Model - Summary Report\n")
        f.write("=" * 80 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("DATA SUMMARY\n")
        f.write("-" * 80 + "\n")
        f.write(f"Total Cities: {len(df['city'].unique())}\n")
        f.write(f"Total Records: {len(df)}\n")
        f.write(f"Features Used: {', '.join(feature_cols)}\n\n")
        
        f.write("AQI STATISTICS\n")
        f.write("-" * 80 + "\n")
        f.write(f"Actual AQI Range: {df['aqi_value'].min():.1f} - {df['aqi_value'].max():.1f}\n")
        f.write(f"Actual AQI Mean: {df['aqi_value'].mean():.2f}\n")
        f.write(f"Actual AQI Median: {df['aqi_value'].median():.2f}\n")
        f.write(f"Predicted AQI Range: {predictions.min():.1f} - {predictions.max():.1f}\n")
        f.write(f"Predicted AQI Mean: {predictions.mean():.2f}\n\n")
        
        f.write("MODEL PERFORMANCE METRICS\n")
        f.write("-" * 80 + "\n")
        for metric, value in metrics.items():
            f.write(f"{metric}: {value:.4f}\n")
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("All graphs have been saved in: " + str(OUTPUT_DIR) + "\n")
        f.write("=" * 80 + "\n")
    
    print(f"   ✓ Saved: {report_path.name}")

def main():
    """Main execution function"""
    print("=" * 80)
    print("🎯 XGBoost AQI Prediction - Presentation Graph Generator")
    print("=" * 80)
    
    # Load data
    df, X, y, feature_cols = load_and_prepare_data()
    
    # Load model
    model = load_xgboost_model()
    
    # Make predictions
    predictions = make_predictions(model, X)
    
    # Calculate metrics
    metrics = calculate_metrics(y, predictions)
    
    print(f"\n📁 Generating graphs in: {OUTPUT_DIR}")
    print("=" * 80)
    
    # Generate all plots
    plot_correlation_heatmap(df, feature_cols)
    plot_actual_vs_predicted(y, predictions, metrics)
    plot_residual_distribution(y, predictions)
    plot_feature_importance(model, feature_cols)
    plot_predicted_vs_actual_trend(df, y, predictions)
    
    # Create summary report
    create_summary_report(df, metrics, feature_cols, predictions)
    
    print("\n" + "=" * 80)
    print("✅ ALL PRESENTATION GRAPHS GENERATED SUCCESSFULLY!")
    print("=" * 80)
    print(f"\n📂 Output Location: {OUTPUT_DIR}")
    print("\nGenerated Files:")
    for file in sorted(OUTPUT_DIR.glob("*.png")):
        print(f"   ✓ {file.name}")
    print(f"   ✓ model_summary_report.txt")
    print("\n🎉 Ready for presentation!")

if __name__ == "__main__":
    main()
