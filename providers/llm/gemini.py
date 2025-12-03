"""
Google Gemini LLM provider.
https://ai.google.dev/
"""
import asyncio
import warnings
from typing import Optional, Dict, Any, List

from .base import BaseLLMProvider
from .config import get_config


class GeminiProvider(BaseLLMProvider):
    """
    Google Gemini API-based LLM provider.
    Supports Gemini Pro and other Google AI models.
    """
    
    provider_name = "gemini"
    is_local = False
    max_concurrent = 5
    supports_streaming = True
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Gemini provider.
        
        Args:
            config: Optional configuration dictionary. Supported keys:
                - api_key: Gemini API key (overrides env.config)
                - model: Model to use (default: 'gemini-pro')
                - temperature: Temperature for sampling (default: 0.7)
                - max_tokens: Maximum tokens to generate (default: 1000)
                - top_p: Top-p sampling parameter (default: 0.95)
                - top_k: Top-k sampling parameter (default: 40)
                - max_concurrent: Max concurrent requests (default: 5)
        """
        super().__init__(config)
        
        # Set defaults
        self.config.setdefault('model', 'gemini-pro')
        self.config.setdefault('temperature', 0.7)
        self.config.setdefault('max_tokens', 1000)
        self.config.setdefault('top_p', 0.95)
        self.config.setdefault('top_k', 40)
        
        if 'max_concurrent' in self.config:
            self.max_concurrent = self.config['max_concurrent']
            self._semaphore = asyncio.Semaphore(self.max_concurrent)
    
    def _validate_config(self) -> None:
        """Validate Gemini configuration and API key."""
        llm_config = get_config()
        
        # Check for API key in config or global config
        api_key = self.config.get('api_key') or llm_config.get_api_key('gemini')
        
        if not api_key:
            warnings.warn(
                "Gemini API key not found. Please set GEMINI_API_KEY in env.config "
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
        Generate text using Gemini API.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt (prepended to user prompt)
            **kwargs: Additional Gemini parameters
            
        Returns:
            Generated text
            
        Raises:
            ValueError: If API key is missing or generation fails
        """
        api_key = self.config.get('api_key')
        if not api_key:
            raise ValueError(
                "Gemini API key is required. Set GEMINI_API_KEY in env.config "
                "or provide 'api_key' in config."
            )
        
        try:
            # Import Google GenerativeAI SDK
            import google.generativeai as genai
            
            # Configure API key
            genai.configure(api_key=api_key)
            
            # Build generation config
            generation_config = {
                'temperature': kwargs.get('temperature', self.config.get('temperature', 0.7)),
                'top_p': kwargs.get('top_p', self.config.get('top_p', 0.95)),
                'top_k': kwargs.get('top_k', self.config.get('top_k', 40)),
                'max_output_tokens': kwargs.get('max_tokens', self.config.get('max_tokens', 1000)),
            }
            
            # Initialize model
            model = genai.GenerativeModel(
                model_name=self.config.get('model', 'gemini-pro'),
                generation_config=generation_config
            )
            
            # Combine system prompt with user prompt if provided
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            
            # Run generation in executor to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: model.generate_content(full_prompt)
            )
            
            return response.text
            
        except ImportError:
            raise ImportError(
                "Google GenerativeAI SDK not installed. Install with: pip install google-generativeai"
            )
        except Exception as e:
            raise ValueError(f"Gemini generation failed: {str(e)}")
    
    async def chat_async(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> str:
        """
        Generate chat completion using Gemini API.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            **kwargs: Additional Gemini parameters
            
        Returns:
            Generated response
        """
        api_key = self.config.get('api_key')
        if not api_key:
            raise ValueError(
                "Gemini API key is required. Set GEMINI_API_KEY in env.config "
                "or provide 'api_key' in config."
            )
        
        try:
            import google.generativeai as genai
            
            genai.configure(api_key=api_key)
            
            # Build generation config
            generation_config = {
                'temperature': kwargs.get('temperature', self.config.get('temperature', 0.7)),
                'top_p': kwargs.get('top_p', self.config.get('top_p', 0.95)),
                'top_k': kwargs.get('top_k', self.config.get('top_k', 40)),
                'max_output_tokens': kwargs.get('max_tokens', self.config.get('max_tokens', 1000)),
            }
            
            model = genai.GenerativeModel(
                model_name=self.config.get('model', 'gemini-pro'),
                generation_config=generation_config
            )
            
            # Convert messages to Gemini chat format
            chat = model.start_chat(history=[])
            
            # Process messages
            system_prompt = None
            for msg in messages[:-1]:  # All but last message
                if msg.get('role') == 'system':
                    system_prompt = msg.get('content', '')
                elif msg.get('role') == 'user':
                    chat.send_message(msg.get('content', ''))
            
            # Get last user message
            last_message = messages[-1].get('content', '') if messages else ''
            
            # Prepend system prompt if exists
            if system_prompt:
                last_message = f"{system_prompt}\n\n{last_message}"
            
            # Run chat in executor
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: chat.send_message(last_message)
            )
            
            return response.text
            
        except ImportError:
            raise ImportError(
                "Google GenerativeAI SDK not installed. Install with: pip install google-generativeai"
            )
        except Exception as e:
            raise ValueError(f"Gemini chat generation failed: {str(e)}")

