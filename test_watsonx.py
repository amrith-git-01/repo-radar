"""
watsonx.ai Connection Test Script

This script tests the connection to IBM watsonx.ai API and validates
that the configuration is correct.
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import configuration
from config.watsonx_config import config

# Import watsonx.ai SDK
try:
    from ibm_watsonx_ai.foundation_models import Model
    from ibm_watsonx_ai import APIClient
except ImportError:
    print("Error: ibm-watsonx-ai package not installed.")
    print("Please install it using: pip install ibm-watsonx-ai")
    sys.exit(1)


def test_connection():
    """Test connection to watsonx.ai API."""
    print("=" * 60)
    print("watsonx.ai Connection Test")
    print("=" * 60)
    print()
    
    # Validate configuration
    print("1. Validating configuration...")
    is_valid, error_msg = config.validate()
    
    if not is_valid:
        print(f"   ❌ Configuration Error: {error_msg}")
        print()
        print("Please ensure the following environment variables are set:")
        print("  - WATSONX_API_KEY")
        print("  - WATSONX_PROJECT_ID")
        print()
        print("You can set them in a .env file or export them in your shell.")
        return False
    
    print(f"   ✓ Configuration valid")
    print(f"   ✓ URL: {config.url}")
    print(f"   ✓ Model: {config.model_id}")
    print()
    
    # Test API connection
    print("2. Testing API connection...")
    try:
        # Initialize the model
        model = Model(
            model_id=config.model_id,
            credentials=config.get_credentials(),
            project_id=config.project_id,
            params=config.get_model_params()
        )
        
        print("   ✓ Model initialized successfully")
        print()
        
        # Test with a simple prompt
        print("3. Testing text generation...")
        test_prompt = "What is IBM watsonx.ai? Provide a brief answer."
        
        print(f"   Prompt: {test_prompt}")
        print()
        
        response = model.generate_text(prompt=test_prompt)
        
        print("   ✓ Response received:")
        print("   " + "-" * 56)
        # Print response with indentation
        for line in response.split('\n'):
            print(f"   {line}")
        print("   " + "-" * 56)
        print()
        
        print("=" * 60)
        print("✓ All tests passed! watsonx.ai is configured correctly.")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        print()
        print("Possible issues:")
        print("  - Invalid API key")
        print("  - Invalid project ID")
        print("  - Network connectivity issues")
        print("  - Insufficient permissions")
        print()
        return False


def main():
    """Main entry point."""
    try:
        success = test_connection()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

# Made with Bob
