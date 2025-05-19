import unittest
import sys
import os
from pathlib import Path
import pandas as pd

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

# Import the function to test
from data.download_data import parse_remaining_lease

class TestParseRemainingLease(unittest.TestCase):
    """Test cases for the parse_remaining_lease function."""

    def test_years_and_months_format(self):
        """Test format 'X years Y months'."""
        self.assertAlmostEqual(parse_remaining_lease("60 years 7 months"), 60.583, places=3)
        self.assertAlmostEqual(parse_remaining_lease("61 years 02 months"), 61.167, places=3)
        self.assertAlmostEqual(parse_remaining_lease("65 years 11 months"), 65.917, places=3)
        self.assertAlmostEqual(parse_remaining_lease("70 years 0 months"), 70.0, places=3)

    def test_years_only_format(self):
        """Test format 'X years'."""
        self.assertEqual(parse_remaining_lease("60 years"), 60.0)
        self.assertEqual(parse_remaining_lease("75 years"), 75.0)
        self.assertEqual(parse_remaining_lease("99 years"), 99.0)
        self.assertEqual(parse_remaining_lease("65 yrs"), 65.0)
        self.assertEqual(parse_remaining_lease("70 Yrs"), 70.0)

    def test_months_only_format(self):
        """Test format 'X months'."""
        self.assertAlmostEqual(parse_remaining_lease("6 months"), 0.5, places=3)
        self.assertAlmostEqual(parse_remaining_lease("12 mths"), 1.0, places=3)
        self.assertAlmostEqual(parse_remaining_lease("24 Mths"), 2.0, places=3)

    def test_numeric_only_format(self):
        """Test format with just the number."""
        self.assertEqual(parse_remaining_lease("60"), 60.0)
        self.assertEqual(parse_remaining_lease("75.5"), 75.5)
        self.assertEqual(parse_remaining_lease("99"), 99.0)
        
        # Test with numeric values (not strings)
        self.assertEqual(parse_remaining_lease(60), 60.0)
        self.assertEqual(parse_remaining_lease(75.5), 75.5)

    def test_alternative_formats(self):
        """Test alternative formats that should be handled."""
        self.assertEqual(parse_remaining_lease("60 years 0 mths"), 60.0)
        self.assertEqual(parse_remaining_lease("61 yrs 6 mths"), 61.5)
        self.assertAlmostEqual(parse_remaining_lease("65 years 3"), 65.25, places=3)  # Assuming 3 is months
        self.assertEqual(parse_remaining_lease("70 years 6 month"), 70.5)

    def test_invalid_inputs(self):
        """Test invalid inputs that should return None."""
        self.assertIsNone(parse_remaining_lease(None))
        self.assertIsNone(parse_remaining_lease(""))
        self.assertIsNone(parse_remaining_lease("invalid"))
        self.assertIsNone(parse_remaining_lease("years"))
        self.assertIsNone(parse_remaining_lease("months"))
        
        # Test with NaN
        self.assertIsNone(parse_remaining_lease(pd.NA))
        self.assertIsNone(parse_remaining_lease(float('nan')))

    def test_edge_cases(self):
        """Test edge cases."""
        # Test with leading/trailing spaces
        self.assertEqual(parse_remaining_lease("  60 years  "), 60.0)
        
        # Test with mixed case
        self.assertEqual(parse_remaining_lease("60 Years 6 Months"), 60.5)
        
        # The current implementation doesn't handle cases without spaces
        # These should return None with the current implementation
        self.assertIsNone(parse_remaining_lease("60years 6months"))
        self.assertIsNone(parse_remaining_lease("60-years 6-months"))

if __name__ == "__main__":
    unittest.main() 