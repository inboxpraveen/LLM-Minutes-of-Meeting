"""
LLM providers module.

This module provides a unified interface for various Large Language Model providers,
including both API-based services and local models.

Available Providers:
    - openai: OpenAI API (GPT-3.5, GPT-4, etc.) - requires OPENAI_API_KEY
    - gemini: Google Gemini API - requires GEMINI_API_KEY
    - grok: Grok (xAI) API - requires GROK_API_KEY
    - ollama: Ollama local models (no API key needed)

Quick Start:
    >>> from providers.llm import generate_text
    >>> text = generate_text('Explain quantum computing', provider='ollama')
    
    >>> # Chat completion
    >>> from providers.llm import chat_completion
    >>> messages = [
    ...     {"role": "user", "content": "Hello, how are you?"}
    ... ]
    >>> response = chat_completion(messages, provider='openai')
    
    >>> # Advanced usage with custom config
    >>> from providers.llm import LLMRouter
    >>> router = LLMRouter('openai', config={'model': 'gpt-4', 'temperature': 0.7})
    >>> text = router.generate('Write a poem about AI')
    
    >>> # Async usage
    >>> import asyncio
    >>> from providers.llm import generate_text_async
    >>> text = asyncio.run(generate_text_async('Explain AI', provider='gemini'))

Configuration:
    API keys should be set in env.config file or as environment variables:
    - OPENAI_API_KEY=your_key_here
    - GEMINI_API_KEY=your_key_here
    - GROK_API_KEY=your_key_here

For more information, see individual provider documentation.
"""

from .base import BaseLLMProvider
from .config import LLMConfig, get_config, reset_config
from .router import (
    LLMRouter,
    generate_text,
    generate_text_async,
    chat_completion,
    chat_completion_async,
    PROVIDER_REGISTRY,
)

# Import all providers for direct access if needed
from .openai import OpenAIProvider
from .gemini import GeminiProvider
from .grok import GrokProvider
from .ollama import OllamaProvider


__all__ = [
    # Main classes
    'LLMRouter',
    'BaseLLMProvider',
    'LLMConfig',
    
    # Convenience functions
    'generate_text',
    'generate_text_async',
    'chat_completion',
    'chat_completion_async',
    'get_config',
    'reset_config',
    
    # Provider classes
    'OpenAIProvider',
    'GeminiProvider',
    'GrokProvider',
    'OllamaProvider',
    
    # Registry
    'PROVIDER_REGISTRY',
]


__version__ = '1.0.0'


def list_available_providers():
    """
    List all available LLM providers.
    
    Returns:
        List of provider names with their type (API/Local)
    """
    providers = []
    for name, provider_class in PROVIDER_REGISTRY.items():
        provider_type = "Local" if provider_class.is_local else "API"
        providers.append(f"{name} ({provider_type})")
    return providers


def get_provider_info(provider_name: str = None):
    """
    Get detailed information about a provider or all providers.
    
    Args:
        provider_name: Optional provider name. If None, returns info for all providers.
        
    Returns:
        Dictionary with provider information
    """
    if provider_name:
        provider_class = PROVIDER_REGISTRY.get(provider_name.lower())
        if not provider_class:
            raise ValueError(f"Unknown provider: {provider_name}")
        
        return {
            'name': provider_class.provider_name,
            'is_local': provider_class.is_local,
            'max_concurrent': provider_class.max_concurrent,
            'supports_streaming': provider_class.supports_streaming,
            'requires_api_key': not provider_class.is_local,
        }
    else:
        # Return info for all providers
        return {
            name: {
                'is_local': provider_class.is_local,
                'max_concurrent': provider_class.max_concurrent,
                'supports_streaming': provider_class.supports_streaming,
                'requires_api_key': not provider_class.is_local,
            }
            for name, provider_class in PROVIDER_REGISTRY.items()
        }
