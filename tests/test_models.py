"""Test cases for ML models"""

import unittest
import numpy as np
from ml_models.linear_regression_model import AQILinearRegression
from ml_models.random_forest_model import AQIRandomForest
from ml_models.xgboost_model import AQIXGBoost
from ml_models.lstm_model import AQILSTM

class TestModels(unittest.TestCase):
    def setUp(self):
        # Create sample data
        np.random.seed(42)
        self.X = np.random.rand(100, 5)
        self.y = np.random.rand(100)
        self.X_test = np.random.rand(20, 5)
        self.y_test = np.random.rand(20)
        
    def test_linear_regression(self):
        model = AQILinearRegression()
        model.train(self.X, self.y)
        predictions = model.predict(self.X_test)
        rmse, r2 = model.evaluate(self.X_test, self.y_test)
        
        self.assertEqual(predictions.shape, (20,))
        self.assertIsInstance(rmse, float)
        self.assertIsInstance(r2, float)
        
    def test_random_forest(self):
        model = AQIRandomForest()
        model.train(self.X, self.y)
        predictions = model.predict(self.X_test)
        rmse, r2 = model.evaluate(self.X_test, self.y_test)
        
        self.assertEqual(predictions.shape, (20,))
        self.assertIsInstance(rmse, float)
        self.assertIsInstance(r2, float)
        
    def test_xgboost(self):
        model = AQIXGBoost()
        model.train(self.X, self.y)
        predictions = model.predict(self.X_test)
        rmse, r2 = model.evaluate(self.X_test, self.y_test)
        
        self.assertEqual(predictions.shape, (20,))
        self.assertIsInstance(rmse, float)
        self.assertIsInstance(r2, float)
        
    def test_lstm(self):
        sequence_length = 10
        n_features = 5
        model = AQILSTM(sequence_length, n_features)
        
        # Reshape data for LSTM
        X_lstm = np.random.rand(100, sequence_length, n_features)
        y_lstm = np.random.rand(100)
        X_test_lstm = np.random.rand(20, sequence_length, n_features)
        y_test_lstm = np.random.rand(20)
        
        model.train(X_lstm, y_lstm, epochs=2)
        predictions = model.predict(X_test_lstm)
        rmse, r2 = model.evaluate(X_test_lstm, y_test_lstm)
        
        self.assertEqual(predictions.shape, (20, 1))
        self.assertIsInstance(rmse, float)
        self.assertIsInstance(r2, float)

if __name__ == '__main__':
    unittest.main()