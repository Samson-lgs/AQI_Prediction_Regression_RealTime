"""Test cases for database operations"""

import unittest
from unittest.mock import patch, MagicMock
from database.db_operations import save_aqi_data, get_historical_data
from datetime import datetime

class TestDatabase(unittest.TestCase):
    def setUp(self):
        # Mock database session
        self.mock_session = MagicMock()
        
    def test_save_aqi_data(self):
        test_data = {
            "city": "Delhi",
            "aqi": 100,
            "timestamp": datetime.now()
        }
        
        save_aqi_data(self.mock_session, test_data)
        self.mock_session.add.assert_called_once()
        self.mock_session.commit.assert_called_once()
        
    def test_get_historical_data(self):
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 1, 2)
        
        # Mock query result
        mock_result = [
            {"timestamp": datetime(2023, 1, 1, 12), "aqi": 100},
            {"timestamp": datetime(2023, 1, 1, 13), "aqi": 110}
        ]
        self.mock_session.query.return_value.filter.return_value.all.return_value = mock_result
        
        result = get_historical_data(self.mock_session, "Delhi", start_date, end_date)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["aqi"], 100)

if __name__ == '__main__':
    unittest.main()