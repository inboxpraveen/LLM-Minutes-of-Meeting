"""
Grok (xAI) LLM provider.
https://x.ai/
"""
import asyncio
import warnings
from typing import Optional, Dict, Any, List

from .base import BaseLLMProvider
from .config import get_config


class GrokProvider(BaseLLMProvider):
    """
    Grok (xAI) API-based LLM provider.
    Supports Grok models from xAI.
    """
    
    provider_name = "grok"
    is_local = False
    max_concurrent = 5
    supports_streaming = True
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Grok provider.
        
        Args:
            config: Optional configuration dictionary. Supported keys:
                - api_key: Grok API key (overrides env.config)
                - model: Model to use (default: 'grok-beta')
                - temperature: Temperature for sampling (default: 0.7)
                - max_tokens: Maximum tokens to generate (default: 1000)
                - top_p: Top-p sampling parameter (default: 1.0)
                - base_url: API base URL (default: 'https://api.x.ai/v1')
                - max_concurrent: Max concurrent requests (default: 5)
        """
        super().__init__(config)
        
        # Set defaults
        self.config.setdefault('model', 'grok-beta')
        self.config.setdefault('temperature', 0.7)
        self.config.setdefault('max_tokens', 1000)
        self.config.setdefault('top_p', 1.0)
        self.config.setdefault('base_url', 'https://api.x.ai/v1')
        
        if 'max_concurrent' in self.config:
            self.max_concurrent = self.config['max_concurrent']
            self._semaphore = asyncio.Semaphore(self.max_concurrent)
    
    def _validate_config(self) -> None:
        """Validate Grok configuration and API key."""
        llm_config = get_config()
        
        # Check for API key in config or global config
        api_key = self.config.get('api_key') or llm_config.get_api_key('grok')
        
        if not api_key:
            warnings.warn(
                "Grok API key not found. Please set GROK_API_KEY in env.config "
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
        Generate text using Grok API.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            **kwargs: Additional Grok parameters
            
        Returns:
            Generated text
            
        Raises:
            ValueError: If API key is missing or generation fails
        """
        api_key = self.config.get('api_key')
        if not api_key:
            raise ValueError(
                "Grok API key is required. Set GROK_API_KEY in env.config "
                "or provide 'api_key' in config."
            )
        
        try:
            # Grok uses OpenAI-compatible API
            from openai import AsyncOpenAI
            
            # Initialize client with Grok endpoint
            client = AsyncOpenAI(
                api_key=api_key,
                base_url=self.config.get('base_url', 'https://api.x.ai/v1')
            )
            
            # Build messages
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            # Merge config with kwargs (kwargs take precedence)
            params = {
                'model': self.config.get('model', 'grok-beta'),
                'temperature': self.config.get('temperature', 0.7),
                'max_tokens': self.config.get('max_tokens', 1000),
                'top_p': self.config.get('top_p', 1.0),
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
                "OpenAI SDK not installed (required for Grok). Install with: pip install openai"
            )
        except Exception as e:
            raise ValueError(f"Grok generation failed: {str(e)}")
    
    async def chat_async(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> str:
        """
        Generate chat completion using Grok API.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            **kwargs: Additional Grok parameters
            
        Returns:
            Generated response
        """
        api_key = self.config.get('api_key')
        if not api_key:
            raise ValueError(
                "Grok API key is required. Set GROK_API_KEY in env.config "
                "or provide 'api_key' in config."
            )
        
        try:
            from openai import AsyncOpenAI
            
            client = AsyncOpenAI(
                api_key=api_key,
                base_url=self.config.get('base_url', 'https://api.x.ai/v1')
            )
            
            # Merge config with kwargs
            params = {
                'model': self.config.get('model', 'grok-beta'),
                'temperature': self.config.get('temperature', 0.7),
                'max_tokens': self.config.get('max_tokens', 1000),
                'top_p': self.config.get('top_p', 1.0),
            }
            params.update(kwargs)
            
            response = await client.chat.completions.create(
                messages=messages,
                **params
            )
            
            return response.choices[0].message.content
            
        except ImportError:
            raise ImportError(
                "OpenAI SDK not installed (required for Grok). Install with: pip install openai"
            )
        except Exception as e:
            raise ValueError(f"Grok chat generation failed: {str(e)}")

