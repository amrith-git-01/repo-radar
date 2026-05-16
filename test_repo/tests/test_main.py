"""
Tests for main module.
"""

import unittest
from src.main import main
from src.utils import calculate_total, validate_input
from src.config import get_config


class TestMain(unittest.TestCase):
    """Test cases for main module."""
    
    def test_calculate_total(self):
        """Test calculate_total function."""
        data = [1, 2, 3, 4, 5]
        result = calculate_total(data)
        self.assertEqual(result, 15)
    
    def test_validate_input_valid(self):
        """Test validate_input with valid data."""
        data = [1, 2, 3]
        self.assertTrue(validate_input(data))
    
    def test_validate_input_empty(self):
        """Test validate_input with empty data."""
        data = []
        self.assertFalse(validate_input(data))
    
    def test_get_config(self):
        """Test get_config function."""
        config = get_config()
        self.assertIsInstance(config, dict)
        self.assertIn('format', config)


if __name__ == '__main__':
    unittest.main()

# Made with Bob
