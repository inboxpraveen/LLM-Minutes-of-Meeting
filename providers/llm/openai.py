"""
OpenAI LLM provider.
https://platform.openai.com/
"""
import asyncio
import warnings
from typing import Optional, Dict, Any, List

from .base import BaseLLMProvider
from .config import get_config


class OpenAIProvider(BaseLLMProvider):
    """
    OpenAI API-based LLM provider.
    Supports GPT-3.5, GPT-4, and other OpenAI models.
    """
    
    provider_name = "openai"
    is_local = False
    max_concurrent = 5
    supports_streaming = True
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize OpenAI provider.
        
        Args:
            config: Optional configuration dictionary. Supported keys:
                - api_key: OpenAI API key (overrides env.config)
                - model: Model to use (default: 'gpt-3.5-turbo')
                - temperature: Temperature for sampling (default: 0.7)
                - max_tokens: Maximum tokens to generate (default: 1000)
                - top_p: Top-p sampling parameter (default: 1.0)
                - frequency_penalty: Frequency penalty (default: 0.0)
                - presence_penalty: Presence penalty (default: 0.0)
                - max_concurrent: Max concurrent requests (default: 5)
        """
        super().__init__(config)
        
        # Set defaults
        self.config.setdefault('model', 'gpt-3.5-turbo')
        self.config.setdefault('temperature', 0.7)
        self.config.setdefault('max_tokens', 1000)
        self.config.setdefault('top_p', 1.0)
        self.config.setdefault('frequency_penalty', 0.0)
        self.config.setdefault('presence_penalty', 0.0)
        
        if 'max_concurrent' in self.config:
            self.max_concurrent = self.config['max_concurrent']
            self._semaphore = asyncio.Semaphore(self.max_concurrent)
    
    def _validate_config(self) -> None:
        """Validate OpenAI configuration and API key."""
        llm_config = get_config()
        
        # Check for API key in config or global config
        api_key = self.config.get('api_key') or llm_config.get_api_key('openai')
        
        if not api_key:
            warnings.warn(
                "OpenAI API key not found. Please set OPENAI_API_KEY in env.config "
                "or provide 'api_key' in provider config.",
                UserWarning
            )
        else:
            self.config['api_key'] = api_key
    
    async def generate_async(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Generate text using OpenAI API.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            **kwargs: Additional OpenAI parameters
            
        Returns:
            Generated text
            
        Raises:
            ValueError: If API key is missing or generation fails
        """
        api_key = self.config.get('api_key')
        if not api_key:
            raise ValueError(
                "OpenAI API key is required. Set OPENAI_API_KEY in env.config "
                "or provide 'api_key' in config."
            )
        
        try:
            # Import OpenAI SDK
            from openai import AsyncOpenAI
            
            # Initialize client
            client = AsyncOpenAI(api_key=api_key)
            
            # Build messages
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            # Merge config with kwargs (kwargs take precedence)
            params = {
                'model': self.config.get('model', 'gpt-3.5-turbo'),
                'temperature': self.config.get('temperature', 0.7),
                'max_tokens': self.config.get('max_tokens', 1000),
                'top_p': self.config.get('top_p', 1.0),
                'frequency_penalty': self.config.get('frequency_penalty', 0.0),
                'presence_penalty': self.config.get('presence_penalty', 0.0),
            }
            params.update(kwargs)
            
            # Make API call
            response = await client.chat.completions.create(
                messages=messages,
                **params
            )
            
            return response.choices[0].message.content
            
        except ImportError:
            raise ImportError(
                "OpenAI SDK not installed. Install with: pip install openai"
            )
        except Exception as e:
            raise ValueError(f"OpenAI generation failed: {str(e)}")
    
    async def chat_async(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> str:
        """
        Generate chat completion using OpenAI API.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            **kwargs: Additional OpenAI parameters
            
        Returns:
            Generated response
        """
        api_key = self.config.get('api_key')
        if not api_key:
            raise ValueError(
                "OpenAI API key is required. Set OPENAI_API_KEY in env.config "
                "or provide 'api_key' in config."
            )
        
        try:
            from openai import AsyncOpenAI
            
            client = AsyncOpenAI(api_key=api_key)
            
            # Merge config with kwargs
            params = {
                'model': self.config.get('model', 'gpt-3.5-turbo'),
                'temperature': self.config.get('temperature', 0.7),
                'max_tokens': self.config.get('max_tokens', 1000),
                'top_p': self.config.get('top_p', 1.0),
                'frequency_penalty': self.config.get('frequency_penalty', 0.0),
                'presence_penalty': self.config.get('presence_penalty', 0.0),
            }
            params.update(kwargs)
            
            response = await client.chat.completions.create(
                messages=messages,
                **params
            )
            
            return response.choices[0].message.content
            
        except ImportError:
            raise ImportError(
                "OpenAI SDK not installed. Install with: pip install openai"
            )
        except Exception as e:
            raise ValueError(f"OpenAI chat generation failed: {str(e)}")

