"""
Utility functions for the application.

This module contains helper functions used throughout the application.
"""

from typing import List, Any


def calculate_total(items: List[int]) -> int:
    """
    Calculate the total sum of items.
    
    Args:
        items: List of integers to sum
        
    Returns:
        int: Total sum
    """
    total = 0
    for item in items:
        total += item
    return total


def format_output(value: Any, format_type: str = 'default') -> str:
    """
    Format output value based on format type.
    
    Args:
        value: Value to format
        format_type: Type of formatting to apply
        
    Returns:
        str: Formatted output string
    """
    if format_type == 'json':
        import json
        return json.dumps({'result': value})
    elif format_type == 'xml':
        return f'<result>{value}</result>'
    else:
        return f'Result: {value}'


def validate_input(data: List[int]) -> bool:
    """
    Validate input data.
    
    Args:
        data: Data to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not data:
        return False
    
    for item in data:
        if not isinstance(item, int):
            return False
        if item < 0:
            return False
    
    return True


def process_batch(items: List[int], batch_size: int = 10) -> List[List[int]]:
    """
    Process items in batches.
    
    Args:
        items: Items to process
        batch_size: Size of each batch
        
    Returns:
        list: List of batches
    """
    batches = []
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        batches.append(batch)
    return batches

# Made with Bob
