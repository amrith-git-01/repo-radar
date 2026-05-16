"""
Configuration management for the application.

Handles loading and managing application configuration.
"""

import os
from typing import Dict, Any


DEFAULT_CONFIG = {
    'format': 'default',
    'batch_size': 10,
    'debug': False,
    'max_retries': 3,
    'timeout': 30
}


def get_config() -> Dict[str, Any]:
    """
    Get application configuration.
    
    Returns:
        dict: Configuration dictionary
    """
    config = DEFAULT_CONFIG.copy()
    
    # Override with environment variables
    if os.getenv('APP_FORMAT'):
        config['format'] = os.getenv('APP_FORMAT')
    
    if os.getenv('APP_DEBUG'):
        config['debug'] = os.getenv('APP_DEBUG').lower() == 'true'
    
    if os.getenv('APP_BATCH_SIZE'):
        try:
            config['batch_size'] = int(os.getenv('APP_BATCH_SIZE'))
        except ValueError:
            pass
    
    return config


def validate_config(config: Dict[str, Any]) -> bool:
    """
    Validate configuration.
    
    Args:
        config: Configuration to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    required_keys = ['format', 'batch_size', 'debug']
    
    for key in required_keys:
        if key not in config:
            return False
    
    if config['batch_size'] <= 0:
        return False
    
    return True


class ConfigManager:
    """Manages application configuration."""
    
    def __init__(self):
        """Initialize configuration manager."""
        self.config = get_config()
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        """
        Set configuration value.
        
        Args:
            key: Configuration key
            value: Value to set
        """
        self.config[key] = value
    
    def reload(self):
        """Reload configuration from environment."""
        self.config = get_config()

# Made with Bob
