"""
Main router and orchestrator for LLM providers.
Provides factory pattern and batch processing capabilities.
"""
import asyncio
from typing import Optional, Dict, Any, List, Type
import warnings

from .base import BaseLLMProvider
from .config import get_config

# Import all providers
from .openai import OpenAIProvider
from .gemini import GeminiProvider
from .grok import GrokProvider
from .ollama import OllamaProvider


# Provider registry
PROVIDER_REGISTRY: Dict[str, Type[BaseLLMProvider]] = {
    'openai': OpenAIProvider,
    'gemini': GeminiProvider,
    'grok': GrokProvider,
    'ollama': OllamaProvider,
}


class LLMRouter:
    """
    Main router for LLM providers.
    Handles provider selection, initialization, and orchestration.
    """
    
    def __init__(self, provider_name: str = 'ollama', config: Optional[Dict[str, Any]] = None):
        """
        Initialize the router with a specific provider.
        
        Args:
            provider_name: Name of the provider to use
            config: Optional provider-specific configuration
            
        Raises:
            ValueError: If provider_name is not recognized
        """
        self.provider_name = provider_name.lower()
        
        if self.provider_name not in PROVIDER_REGISTRY:
            available = ', '.join(PROVIDER_REGISTRY.keys())
            raise ValueError(
                f"Unknown provider '{provider_name}'. "
                f"Available providers: {available}"
            )
        
        # Initialize provider
        provider_class = PROVIDER_REGISTRY[self.provider_name]
        self.provider: BaseLLMProvider = provider_class(config)
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Generate text completion (synchronous).
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Generated text
        """
        return self.provider.generate(prompt, system_prompt, **kwargs)
    
    async def generate_async(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Generate text completion (asynchronous).
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            **kwargs: Additional parameters
            
        Returns:
            Generated text
        """
        return await self.provider.generate_with_semaphore(prompt, system_prompt, **kwargs)
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> str:
        """
        Generate chat completion (synchronous).
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            **kwargs: Additional parameters
            
        Returns:
            Generated response
        """
        return self.provider.chat(messages, **kwargs)
    
    async def chat_async(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> str:
        """
        Generate chat completion (asynchronous).
        
        Args:
            messages: List of message dictionaries
            **kwargs: Additional parameters
            
        Returns:
            Generated response
        """
        return await self.provider.chat_with_semaphore(messages, **kwargs)
    
    async def generate_batch_async(
        self,
        prompts: List[str],
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> List[str]:
        """
        Generate completions for multiple prompts concurrently.
        
        Automatically handles concurrency limits based on provider type:
        - API-based providers: up to max_concurrent (default 5)
        - Local models: sequential processing (max_concurrent = 1)
        
        Args:
            prompts: List of prompts
            system_prompt: Optional system prompt applied to all
            **kwargs: Additional parameters
            
        Returns:
            List of generated texts in the same order as input
        """
        # Create tasks for all prompts
        tasks = [
            self.provider.generate_with_semaphore(prompt, system_prompt, **kwargs)
            for prompt in prompts
        ]
        
        # Execute all tasks concurrently (semaphore controls actual concurrency)
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        generations = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                warnings.warn(
                    f"Generation failed for prompt {i}: {str(result)}",
                    UserWarning
                )
                generations.append("")
            else:
                generations.append(result)
        
        return generations
    
    def generate_batch(
        self,
        prompts: List[str],
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> List[str]:
        """
        Generate completions for multiple prompts (synchronous wrapper).
        
        Args:
            prompts: List of prompts
            system_prompt: Optional system prompt
            **kwargs: Additional parameters
            
        Returns:
            List of generated texts
        """
        return asyncio.run(self.generate_batch_async(prompts, system_prompt, **kwargs))
    
    def update_config(self, **kwargs) -> None:
        """
        Update provider configuration at runtime.
        
        Args:
            **kwargs: Configuration parameters to update
        """
        self.provider.update_config(**kwargs)
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get current provider configuration.
        
        Returns:
            Dictionary with current configuration
        """
        return self.provider.get_config()
    
    def get_provider_info(self) -> Dict[str, Any]:
        """
        Get information about the current provider.
        
        Returns:
            Dictionary with provider information
        """
        return {
            'provider_name': self.provider.provider_name,
            'is_local': self.provider.is_local,
            'max_concurrent': self.provider.max_concurrent,
            'supports_streaming': self.provider.supports_streaming,
            'config': self.get_config(),
        }
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model.
        
        Returns:
            Dictionary with model information
        """
        return self.provider.get_model_info()
    
    @staticmethod
    def list_providers() -> List[str]:
        """
        List all available providers.
        
        Returns:
            List of provider names
        """
        return list(PROVIDER_REGISTRY.keys())
    
    @staticmethod
    def get_provider_class(provider_name: str) -> Type[BaseLLMProvider]:
        """
        Get provider class by name.
        
        Args:
            provider_name: Name of the provider
            
        Returns:
            Provider class
            
        Raises:
            ValueError: If provider not found
        """
        provider_name = provider_name.lower()
        if provider_name not in PROVIDER_REGISTRY:
            available = ', '.join(PROVIDER_REGISTRY.keys())
            raise ValueError(
                f"Unknown provider '{provider_name}'. "
                f"Available providers: {available}"
            )
        return PROVIDER_REGISTRY[provider_name]
    
    def __repr__(self) -> str:
        return f"<LLMRouter(provider='{self.provider_name}')>"


# Convenience functions for quick usage
def generate_text(
    prompt: str,
    provider: str = 'ollama',
    system_prompt: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
    **kwargs
) -> str:
    """
    Quick text generation.
    
    Args:
        prompt: User prompt
        provider: Provider name (default: 'ollama')
        system_prompt: Optional system prompt
        config: Optional provider configuration
        **kwargs: Additional parameters
        
    Returns:
        Generated text
    """
    router = LLMRouter(provider, config)
    return router.generate(prompt, system_prompt, **kwargs)


async def generate_text_async(
    prompt: str,
    provider: str = 'ollama',
    system_prompt: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
    **kwargs
) -> str:
    """
    Quick async text generation.
    
    Args:
        prompt: User prompt
        provider: Provider name (default: 'ollama')
        system_prompt: Optional system prompt
        config: Optional provider configuration
        **kwargs: Additional parameters
        
    Returns:
        Generated text
    """
    router = LLMRouter(provider, config)
    return await router.generate_async(prompt, system_prompt, **kwargs)


def chat_completion(
    messages: List[Dict[str, str]],
    provider: str = 'ollama',
    config: Optional[Dict[str, Any]] = None,
    **kwargs
) -> str:
    """
    Quick chat completion.
    
    Args:
        messages: List of message dictionaries
        provider: Provider name (default: 'ollama')
        config: Optional provider configuration
        **kwargs: Additional parameters
        
    Returns:
        Generated response
    """
    router = LLMRouter(provider, config)
    return router.chat(messages, **kwargs)


async def chat_completion_async(
    messages: List[Dict[str, str]],
    provider: str = 'ollama',
    config: Optional[Dict[str, Any]] = None,
    **kwargs
) -> str:
    """
    Quick async chat completion.
    
    Args:
        messages: List of message dictionaries
        provider: Provider name (default: 'ollama')
        config: Optional provider configuration
        **kwargs: Additional parameters
        
    Returns:
        Generated response
    """
    router = LLMRouter(provider, config)
    return await router.chat_async(messages, **kwargs)

