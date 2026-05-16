"""
Base Agent Class for DevRamp AI Agents

Provides common functionality for all AI agents including watsonx.ai integration,
prompt formatting, error handling, and logging.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
import json

from ibm_watsonx_ai.foundation_models import Model
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams

from config.watsonx_config import config


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class BaseAgent(ABC):
    """
    Abstract base class for all DevRamp AI agents.
    
    Provides common functionality for interacting with watsonx.ai,
    formatting prompts, handling errors, and logging operations.
    """
    
    def __init__(
        self,
        name: str,
        model_id: Optional[str] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """
        Initialize the base agent.
        
        Args:
            name: Name of the agent for logging
            model_id: Optional watsonx.ai model ID (defaults to config)
            max_retries: Maximum number of retry attempts for API calls
            retry_delay: Delay in seconds between retries
        """
        self.name = name
        self.logger = logging.getLogger(f"agent.{name}")
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # Validate configuration
        is_valid, error_msg = config.validate()
        if not is_valid:
            raise ValueError(f"Invalid watsonx configuration: {error_msg}")
        
        # Initialize watsonx.ai model
        self.model_id = model_id or config.model_id
        self.model = self._initialize_model()
        
        self.logger.info(f"Initialized {name} agent with model {self.model_id}")
    
    def _initialize_model(self) -> Model:
        """
        Initialize the watsonx.ai model.
        
        Returns:
            Model: Initialized watsonx.ai model instance
        """
        try:
            model = Model(
                model_id=self.model_id,
                credentials=config.get_credentials(),
                project_id=config.project_id,
                params=config.get_model_params()
            )
            return model
        except Exception as e:
            self.logger.error(f"Failed to initialize watsonx.ai model: {e}")
            raise
    
    async def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> str:
        """
        Generate text using watsonx.ai with retry logic.
        
        Args:
            prompt: Input prompt for generation
            max_tokens: Maximum tokens to generate (overrides config)
            temperature: Temperature for generation (overrides config)
            **kwargs: Additional parameters for generation
            
        Returns:
            str: Generated text
            
        Raises:
            Exception: If generation fails after all retries
        """
        # Update parameters if provided
        params = config.get_model_params()
        if max_tokens is not None:
            params['max_new_tokens'] = max_tokens
        if temperature is not None:
            params['temperature'] = temperature
        params.update(kwargs)
        
        # Retry logic
        last_error = None
        for attempt in range(self.max_retries):
            try:
                self.logger.debug(f"Generation attempt {attempt + 1}/{self.max_retries}")
                
                # Run synchronous model.generate in executor to avoid blocking
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: self.model.generate(prompt=prompt, params=params)
                )
                
                # Extract generated text
                if isinstance(response, dict):
                    generated_text = response.get('results', [{}])[0].get('generated_text', '')
                else:
                    generated_text = str(response)
                
                self.logger.debug(f"Generated {len(generated_text)} characters")
                return generated_text.strip()
                
            except Exception as e:
                last_error = e
                self.logger.warning(
                    f"Generation attempt {attempt + 1} failed: {e}"
                )
                
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
        
        # All retries failed
        error_msg = f"Generation failed after {self.max_retries} attempts: {last_error}"
        self.logger.error(error_msg)
        raise Exception(error_msg)
    
    def format_prompt(self, template: str, **kwargs) -> str:
        """
        Format a prompt template with provided variables.
        
        Args:
            template: Prompt template string with {variable} placeholders
            **kwargs: Variables to substitute in template
            
        Returns:
            str: Formatted prompt
        """
        try:
            return template.format(**kwargs)
        except KeyError as e:
            self.logger.error(f"Missing template variable: {e}")
            raise ValueError(f"Missing required template variable: {e}")
    
    def parse_json_response(self, response: str) -> Dict[str, Any]:
        """
        Parse JSON from model response, handling markdown code blocks.
        
        Args:
            response: Model response that may contain JSON
            
        Returns:
            dict: Parsed JSON data
            
        Raises:
            ValueError: If JSON cannot be parsed
        """
        # Try to extract JSON from markdown code blocks
        if '```json' in response:
            start = response.find('```json') + 7
            end = response.find('```', start)
            json_str = response[start:end].strip()
        elif '```' in response:
            start = response.find('```') + 3
            end = response.find('```', start)
            json_str = response[start:end].strip()
        else:
            json_str = response.strip()
        
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON: {e}")
            self.logger.debug(f"Response was: {response[:500]}")
            raise ValueError(f"Invalid JSON in response: {e}")
    
    def format_list(self, items: List[str], bullet: str = "-") -> str:
        """
        Format a list of items as a bulleted list.
        
        Args:
            items: List of items to format
            bullet: Bullet character to use
            
        Returns:
            str: Formatted bulleted list
        """
        return "\n".join(f"{bullet} {item}" for item in items)
    
    def truncate_text(self, text: str, max_length: int = 1000, suffix: str = "...") -> str:
        """
        Truncate text to maximum length.
        
        Args:
            text: Text to truncate
            max_length: Maximum length
            suffix: Suffix to add if truncated
            
        Returns:
            str: Truncated text
        """
        if len(text) <= max_length:
            return text
        return text[:max_length - len(suffix)] + suffix
    
    @abstractmethod
    async def analyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform agent-specific analysis.
        
        This method must be implemented by all concrete agent classes.
        
        Args:
            context: Context data for analysis
            
        Returns:
            dict: Analysis results
        """
        pass
    
    async def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the agent with error handling and logging.
        
        Args:
            context: Context data for analysis
            
        Returns:
            dict: Analysis results with metadata
        """
        self.logger.info(f"Starting {self.name} agent")
        start_time = asyncio.get_event_loop().time()
        
        try:
            result = await self.analyze(context)
            
            elapsed_time = asyncio.get_event_loop().time() - start_time
            self.logger.info(
                f"{self.name} agent completed in {elapsed_time:.2f}s"
            )
            
            return {
                'agent': self.name,
                'status': 'success',
                'elapsed_time': elapsed_time,
                'result': result
            }
            
        except Exception as e:
            elapsed_time = asyncio.get_event_loop().time() - start_time
            self.logger.error(
                f"{self.name} agent failed after {elapsed_time:.2f}s: {e}",
                exc_info=True
            )
            
            return {
                'agent': self.name,
                'status': 'error',
                'elapsed_time': elapsed_time,
                'error': str(e)
            }
    
    def log_info(self, message: str):
        """Log an info message."""
        self.logger.info(message)
    
    def log_warning(self, message: str):
        """Log a warning message."""
        self.logger.warning(message)
    
    def log_error(self, message: str, exc_info: bool = False):
        """Log an error message."""
        self.logger.error(message, exc_info=exc_info)
    
    def log_debug(self, message: str):
        """Log a debug message."""
        self.logger.debug(message)

# Made with Bob
