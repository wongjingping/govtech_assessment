import unittest
import sys
from pathlib import Path
import pandas as pd
from unittest.mock import patch, MagicMock

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

# Import modules to test
from data.import_to_postgres import import_resale_prices, import_completion_status
from utils.models import ResalePrice, CompletionStatus

class TestImportToPostgres(unittest.TestCase):
    """Test cases for the import_to_postgres functions."""

    def setUp(self):
        """Set up test fixtures."""
        # Create patch for the read_csv method to prevent real file system access
        self.read_csv_patcher = patch('data.import_to_postgres.pd.read_csv')
        self.mock_read_csv = self.read_csv_patcher.start()

    def tearDown(self):
        """Tear down test fixtures."""
        self.read_csv_patcher.stop()

    def test_import_resale_prices(self):
        """Test the import_resale_prices function with appropriate mocks."""
        # Setup mock DataFrame with test data
        test_data = pd.DataFrame({
            'month': ['2022-01-01', '2022-02-01'],
            'town': ['ANG MO KIO', 'BEDOK'],
            'flat_type': ['3 ROOM', '4 ROOM'],
            'block': ['123', '456'],
            'street_name': ['Test Street 1', 'Test Street 2'],
            'storey_range': ['01 TO 03', '04 TO 06'],
            'floor_area_sqm': [75.0, 90.0],
            'flat_model': ['Improved', 'New Generation'],
            'lease_commence_date': [1980, 1985],
            'resale_price': [450000.0, 550000.0],
            'remaining_lease_years': [58.0, 63.0]
        })
        
        # Convert month to datetime
        test_data['month'] = pd.to_datetime(test_data['month'])
        
        # Configure mocks for read_csv
        self.mock_read_csv.return_value = [test_data]  # Return a list to simulate chunks
        
        # Create mock objects
        mock_engine = MagicMock()
        mock_session = MagicMock()
        mock_sessionmaker = MagicMock(return_value=mock_session)
        
        # Apply patch for sessionmaker within the test method
        with patch('data.import_to_postgres.sessionmaker', return_value=mock_sessionmaker):
            # Call the function
            import_resale_prices(mock_engine)
            
            # Assert correct method calls
            self.mock_read_csv.assert_called()
            self.assertTrue(mock_session.query.called)
            self.assertTrue(mock_session.query.return_value.delete.called)
            self.assertTrue(mock_session.bulk_save_objects.called)
            self.assertTrue(mock_session.commit.called)
            self.assertTrue(mock_session.close.called)

    def test_import_completion_status(self):
        """Test the import_completion_status function with appropriate mocks."""
        # Setup mock DataFrame with test data
        test_data = pd.DataFrame({
            'financial_year': [2020, 2021],
            'town_or_estate': ['ANG MO KIO', 'BEDOK'],
            'status': ['Completed', 'Under Construction'],
            'no_of_units': [123, 456]
        })
        
        # Configure mocks for read_csv
        self.mock_read_csv.return_value = test_data
        
        # Create mock objects
        mock_engine = MagicMock()
        mock_session = MagicMock()
        mock_sessionmaker = MagicMock(return_value=mock_session)
        
        # Apply patch for sessionmaker within the test method
        with patch('data.import_to_postgres.sessionmaker', return_value=mock_sessionmaker):
            # Call the function
            import_completion_status(mock_engine)
            
            # Assert correct method calls
            self.mock_read_csv.assert_called()
            self.assertTrue(mock_session.query.called)
            self.assertTrue(mock_session.query.return_value.delete.called)
            self.assertTrue(mock_session.bulk_save_objects.called)
            self.assertTrue(mock_session.commit.called)
            self.assertTrue(mock_session.close.called)

if __name__ == "__main__":
    unittest.main() 