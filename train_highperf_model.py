"""
High-Performance AQI Prediction Model
Target: R² > 0.85

Strategy:
1. Focus on PM2.5 and PM10 (highest correlation: 0.90 and 0.85)
2. Add polynomial features for non-linear relationships
3. Use ensemble methods with optimized hyperparameters
4. More training data (all available, not just 90 days)
"""
import os
import sys
import numpy as np
import pandas as pd
from sklearn.preprocessing import PolynomialFeatures, StandardScaler
from sklearn.linear_model import Ridge, Lasso
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
import joblib

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database.db_operations import DatabaseOperations


class HighPerformanceAQIModel:
    """Optimized model targeting R² > 0.85"""
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.poly = PolynomialFeatures(degree=2, include_bias=False)
        self.model = None
        
    def prepare_data(self, city, days=None):
        """Get all available data for a city"""
        db = DatabaseOperations()
        
        if days:
            query = f"""
                SELECT pm25, pm10, no2, so2, co, o3, aqi_value, timestamp
                FROM pollution_data
                WHERE city = '{city}'
                AND timestamp >= NOW() - INTERVAL '{days} days'
                AND pm25 IS NOT NULL
                AND pm10 IS NOT NULL
                AND aqi_value IS NOT NULL
                ORDER BY timestamp ASC
            """
        else:
            # Get ALL data
            query = f"""
                SELECT pm25, pm10, no2, so2, co, o3, aqi_value, timestamp
                FROM pollution_data
                WHERE city = '{city}'
                AND pm25 IS NOT NULL
                AND pm10 IS NOT NULL
                AND aqi_value IS NOT NULL
                ORDER BY timestamp ASC
            """
        
        data = db.db.execute_query_dicts(query)
        df = pd.DataFrame(data)
        
        print(f"✅ Loaded {len(df)} samples for {city}")
        print(f"   Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
        print(f"   AQI range: {df['aqi_value'].min():.0f} - {df['aqi_value'].max():.0f}")
        
        return df
    
    def engineer_features(self, df):
        """Create optimized features focusing on PM2.5 and PM10"""
        df = df.copy()
        
        # Core pollutants (strongest predictors)
        features = []
        feature_names = []
        
        # 1. Raw pollutant values (highest importance)
        for col in ['pm25', 'pm10', 'no2', 'so2', 'co', 'o3']:
            features.append(df[col].fillna(0).values)
            feature_names.append(col)
        
        # 2. PM ratios (important for AQI calculation)
        pm_ratio = (df['pm25'] / (df['pm10'] + 1)).fillna(0)
        features.append(pm_ratio.values)
        feature_names.append('pm_ratio')
        
        # 3. Total pollution index
        total_pm = (df['pm25'] + df['pm10']).fillna(0)
        features.append(total_pm.values)
        feature_names.append('total_pm')
        
        # 4. Weighted pollution index (PM2.5 is most correlated)
        weighted_index = (df['pm25'] * 2 + df['pm10']).fillna(0) / 3
        features.append(weighted_index.values)
        feature_names.append('weighted_pm')
        
        # 5. Add temporal features (hour of day patterns)
        df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
        df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
        df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
        features.append(df['hour_sin'].values)
        features.append(df['hour_cos'].values)
        feature_names.extend(['hour_sin', 'hour_cos'])
        
        # Convert to numpy array
        X = np.column_stack(features)
        
        print(f"✅ Created {X.shape[1]} features:")
        for i, name in enumerate(feature_names):
            print(f"   {i+1}. {name}")
        
        return X, feature_names
    
    def train(self, city, test_size=0.15):
        """Train high-performance model"""
        print(f"\n{'='*80}")
        print(f"TRAINING HIGH-PERFORMANCE MODEL: {city}")
        print(f"{'='*80}\n")
        
        # Load data (ALL available data for better training)
        df = self.prepare_data(city, days=None)
        
        if len(df) < 100:
            print(f"❌ Insufficient data: {len(df)} samples")
            return None
        
        # Engineer features
        X, feature_names = self.engineer_features(df)
        y = df['aqi_value'].values
        
        # Time-series split (no shuffling!)
        n = len(X)
        train_end = int(n * (1 - test_size))
        
        X_train, X_test = X[:train_end], X[train_end:]
        y_train, y_test = y[:train_end], y[train_end:]
        
        print(f"\n📊 Data Split:")
        print(f"   Train: {len(X_train)} samples ({len(X_train)/n*100:.1f}%)")
        print(f"   Test:  {len(X_test)} samples ({len(X_test)/n*100:.1f}%)")
        
        # Add polynomial features (degree 2 for non-linear relationships)
        print(f"\n🔧 Adding polynomial features (degree 2)...")
        X_train_poly = self.poly.fit_transform(X_train)
        X_test_poly = self.poly.transform(X_test)
        
        print(f"   Features: {X.shape[1]} → {X_train_poly.shape[1]}")
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train_poly)
        X_test_scaled = self.scaler.transform(X_test_poly)
        
        # Try multiple models and pick the best
        models = {
            'Ridge Regression': Ridge(alpha=1.0),
            'Lasso Regression': Lasso(alpha=0.1),
            'Random Forest': RandomForestRegressor(
                n_estimators=200,
                max_depth=20,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1
            ),
            'Gradient Boosting': GradientBoostingRegressor(
                n_estimators=200,
                max_depth=10,
                learning_rate=0.1,
                random_state=42
            )
        }
        
        print(f"\n🚀 Training {len(models)} models...")
        print(f"{'-'*80}")
        
        results = {}
        best_r2 = 0
        best_model_name = None
        
        for name, model in models.items():
            print(f"\nTraining {name}...")
            
            model.fit(X_train_scaled, y_train)
            y_pred = model.predict(X_test_scaled)
            
            # Metrics
            r2 = r2_score(y_test, y_pred)
            rmse = np.sqrt(mean_squared_error(y_test, y_pred))
            mae = mean_absolute_error(y_test, y_pred)
            mape = np.mean(np.abs((y_test - y_pred) / (y_test + 1e-6))) * 100
            
            results[name] = {
                'r2': r2,
                'rmse': rmse,
                'mae': mae,
                'mape': mape,
                'model': model
            }
            
            status = "✅" if r2 > 0.85 else "⚠️" if r2 > 0.70 else "❌"
            print(f"  {status} R² = {r2:.4f}, RMSE = {rmse:.2f}, MAE = {mae:.2f}")
            
            if r2 > best_r2:
                best_r2 = r2
                best_model_name = name
                self.model = model
        
        print(f"\n{'-'*80}")
        print(f"🏆 Best Model: {best_model_name}")
        print(f"{'='*80}")
        print(f"   R² Score:  {results[best_model_name]['r2']:.4f} {'✅' if results[best_model_name]['r2'] > 0.85 else '❌'}")
        print(f"   RMSE:      {results[best_model_name]['rmse']:.2f}")
        print(f"   MAE:       {results[best_model_name]['mae']:.2f}")
        print(f"   MAPE:      {results[best_model_name]['mape']:.2f}%")
        print(f"{'='*80}\n")
        
        # Save model
        model_path = f"models/trained_models/{city}_highperf.pkl"
        os.makedirs("models/trained_models", exist_ok=True)
        
        joblib.dump({
            'model': self.model,
            'scaler': self.scaler,
            'poly': self.poly,
            'feature_names': feature_names,
            'metrics': results[best_model_name]
        }, model_path)
        
        print(f"💾 Model saved to: {model_path}\n")
        
        return results
    
    def predict(self, df):
        """Make predictions"""
        X, _ = self.engineer_features(df)
        X_poly = self.poly.transform(X)
        X_scaled = self.scaler.transform(X_poly)
        return self.model.predict(X_scaled)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Train high-performance AQI model')
    parser.add_argument('--city', type=str, default='Delhi', help='City name')
    args = parser.parse_args()
    
    # Train model
    model = HighPerformanceAQIModel()
    results = model.train(args.city)
    
    if results:
        print("\n🎉 Training Complete!")
    else:
        print("\n❌ Training Failed!")
