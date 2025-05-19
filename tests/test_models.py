import unittest
import sys
import os
from pathlib import Path
from datetime import datetime

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

# Import the models to test
from utils.models import ResalePrice, CompletionStatus

class TestResalePriceModel(unittest.TestCase):
    """Test cases for the ResalePrice model."""
    
    def test_resale_price_creation(self):
        """Test creating a ResalePrice instance."""
        # Create a model instance
        resale = ResalePrice(
            month=datetime(2022, 1, 1),
            town="ANG MO KIO",
            flat_type="3 ROOM",
            block="123",
            street_name="Test Street",
            storey_range="01 TO 03",
            floor_area_sqm=75.0,
            flat_model="Improved",
            lease_commence_date=1980,
            resale_price=450000.0,
            remaining_lease_years=58.0
        )
        
        # Check attributes
        self.assertEqual(resale.month, datetime(2022, 1, 1))
        self.assertEqual(resale.town, "ANG MO KIO")
        self.assertEqual(resale.flat_type, "3 ROOM")
        self.assertEqual(resale.block, "123")
        self.assertEqual(resale.street_name, "Test Street")
        self.assertEqual(resale.storey_range, "01 TO 03")
        self.assertEqual(resale.floor_area_sqm, 75.0)
        self.assertEqual(resale.flat_model, "Improved")
        self.assertEqual(resale.lease_commence_date, 1980)
        self.assertEqual(resale.resale_price, 450000.0)
        self.assertEqual(resale.remaining_lease_years, 58.0)
    
    def test_resale_price_from_dict(self):
        """Test creating a ResalePrice instance from a dictionary."""
        # Create a dictionary
        data = {
            'month': datetime(2022, 1, 1),
            'town': "ANG MO KIO",
            'flat_type': "3 ROOM",
            'block': "123",
            'street_name': "Test Street",
            'storey_range': "01 TO 03",
            'floor_area_sqm': 75.0,
            'flat_model': "Improved",
            'lease_commence_date': 1980,
            'resale_price': 450000.0,
            'remaining_lease_years': 58.0
        }
        
        # Create a model instance from the dictionary
        resale = ResalePrice.from_dict(data)
        
        # Check attributes
        self.assertEqual(resale.month, datetime(2022, 1, 1))
        self.assertEqual(resale.town, "ANG MO KIO")
        self.assertEqual(resale.flat_type, "3 ROOM")
        self.assertEqual(resale.block, "123")
        self.assertEqual(resale.street_name, "Test Street")
        self.assertEqual(resale.storey_range, "01 TO 03")
        self.assertEqual(resale.floor_area_sqm, 75.0)
        self.assertEqual(resale.flat_model, "Improved")
        self.assertEqual(resale.lease_commence_date, 1980)
        self.assertEqual(resale.resale_price, 450000.0)
        self.assertEqual(resale.remaining_lease_years, 58.0)
    
    def test_resale_price_repr(self):
        """Test the ResalePrice __repr__ method."""
        # Create a model instance
        resale = ResalePrice(
            id=1,
            month=datetime(2022, 1, 1),
            town="ANG MO KIO",
            flat_type="3 ROOM",
            resale_price=450000.0
        )
        
        # Check __repr__
        expected_repr = "<ResalePrice(id=1, town='ANG MO KIO', month='2022-01-01 00:00:00', price=450000.0)>"
        self.assertEqual(repr(resale), expected_repr)


class TestCompletionStatusModel(unittest.TestCase):
    """Test cases for the CompletionStatus model."""
    
    def test_completion_status_creation(self):
        """Test creating a CompletionStatus instance."""
        # Create a model instance
        completion = CompletionStatus(
            financial_year=2020,
            town_or_estate="ANG MO KIO",
            status="Completed",
            no_of_units=123
        )
        
        # Check attributes
        self.assertEqual(completion.financial_year, 2020)
        self.assertEqual(completion.town_or_estate, "ANG MO KIO")
        self.assertEqual(completion.status, "Completed")
        self.assertEqual(completion.no_of_units, 123)
    
    def test_completion_status_from_dict(self):
        """Test creating a CompletionStatus instance from a dictionary."""
        # Create a dictionary
        data = {
            'financial_year': 2020,
            'town_or_estate': "ANG MO KIO",
            'status': "Completed",
            'no_of_units': 123
        }
        
        # Create a model instance from the dictionary
        completion = CompletionStatus.from_dict(data)
        
        # Check attributes
        self.assertEqual(completion.financial_year, 2020)
        self.assertEqual(completion.town_or_estate, "ANG MO KIO")
        self.assertEqual(completion.status, "Completed")
        self.assertEqual(completion.no_of_units, 123)
    
    def test_completion_status_repr(self):
        """Test the CompletionStatus __repr__ method."""
        # Create a model instance
        completion = CompletionStatus(
            id=1,
            financial_year=2020,
            town_or_estate="ANG MO KIO",
            status="Completed"
        )
        
        # Check __repr__
        expected_repr = "<CompletionStatus(id=1, town='ANG MO KIO', year=2020)>"
        self.assertEqual(repr(completion), expected_repr)


if __name__ == "__main__":
    unittest.main() 