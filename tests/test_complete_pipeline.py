import pytest
from database.db_operations import DatabaseOperations
from feature_engineering.feature_processor import FeatureProcessor
from api_handlers import CPCBHandler, OpenWeatherHandler, IQAirHandler
from ml_models.linear_regression_model import LinearRegressionAQI
import numpy as np

class TestCompletePipeline:
    @pytest.fixture
    def setup(self):
        self.db = DatabaseOperations()
        self.processor = FeatureProcessor()
    
    def test_database_connection(self, setup):
        assert self.db is not None
    
    def test_feature_processor(self, setup):
        # Test with sample data
        data = self.processor.prepare_training_data('Delhi', days=7)
        assert data is not None
    
    def test_model_training(self, setup):
        model = LinearRegressionAQI()
        X_train = np.random.rand(100, 10)
        y_train = np.random.rand(100)
        assert model.train(X_train, y_train) == True

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
