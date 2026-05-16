"""
Main application entry point.

This is a sample application for testing the DevRamp analysis system.
"""

import sys
from src.utils import calculate_total, format_output
from src.config import get_config


def main():
    """Main application function."""
    print("Starting application...")
    
    # Load configuration
    config = get_config()
    print(f"Loaded configuration: {config}")
    
    # Sample data processing
    data = [10, 20, 30, 40, 50]
    total = calculate_total(data)
    
    # Format and display output
    output = format_output(total, config.get('format', 'default'))
    print(output)
    
    print("Application completed successfully!")
    return 0


if __name__ == "__main__":
    sys.exit(main())

# Made with Bob
