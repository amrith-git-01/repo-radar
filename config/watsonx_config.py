"""
watsonx.ai Configuration Module

This module provides configuration settings for IBM watsonx.ai API integration.
All sensitive credentials should be loaded from environment variables.
"""

import os
from typing import Dict, Any


class WatsonxConfig:
    """Configuration class for watsonx.ai API settings."""
    
    def __init__(self):
        """Initialize configuration from environment variables."""
        self.api_key = os.getenv('WATSONX_API_KEY')
        self.project_id = os.getenv('WATSONX_PROJECT_ID')
        self.url = 'https://us-south.ml.cloud.ibm.com'
        self.model_id = 'ibm/granite-13b-chat-v2'
        
        # Model parameters
        self.parameters = {
            'max_new_tokens': 1000,
            'temperature': 0.7,
            'top_p': 0.9,
            'decoding_method': 'greedy',
            'repetition_penalty': 1.0
        }
    
    def validate(self) -> tuple[bool, str]:
        """
        Validate that all required configuration is present.
        
        Returns:
            tuple: (is_valid, error_message)
        """
        if not self.api_key:
            return False, "WATSONX_API_KEY environment variable is not set"
        
        if not self.project_id:
            return False, "WATSONX_PROJECT_ID environment variable is not set"
        
        return True, ""
    
    def get_credentials(self) -> Dict[str, str]:
        """
        Get credentials dictionary for watsonx.ai API.
        
        Returns:
            dict: Credentials containing API key and URL
        """
        return {
            'url': self.url,
            'apikey': self.api_key
        }
    
    def get_model_params(self) -> Dict[str, Any]:
        """
        Get model parameters for text generation.
        
        Returns:
            dict: Model parameters
        """
        return self.parameters.copy()
    
    def __repr__(self) -> str:
        """String representation of config (without exposing credentials)."""
        return (
            f"WatsonxConfig(url={self.url}, "
            f"model_id={self.model_id}, "
            f"api_key={'***' if self.api_key else 'NOT SET'}, "
            f"project_id={'***' if self.project_id else 'NOT SET'})"
        )


# Global configuration instance
config = WatsonxConfig()

# Made with Bob
