"""
Base abstract class for all LLM providers.
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
import asyncio
from pathlib import Path


class BaseLLMProvider(ABC):
    """
    Abstract base class for all LLM providers.
    
    Attributes:
        provider_name: Name of the provider
        is_local: Whether the provider runs locally or uses API
        max_concurrent: Maximum concurrent requests allowed
        config: Provider-specific configuration
    """
    
    provider_name: str = "base"
    is_local: bool = False
    max_concurrent: int = 5
    supports_streaming: bool = False
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the provider with custom configuration.
        
        Args:
            config: Optional dictionary with provider-specific configuration
        """
        self.config = config or {}
        self._semaphore = asyncio.Semaphore(self.max_concurrent if not self.is_local else 1)
        self._validate_config()
    
    @abstractmethod
    def _validate_config(self) -> None:
        """
        Validate provider configuration and API keys.
        Should raise ValueError or Warning if configuration is invalid.
        """
        pass
    
    @abstractmethod
    async def generate_async(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Asynchronously generate text completion from the LLM.
        
        Args:
            prompt: User prompt/input text
            system_prompt: Optional system prompt for instructing the model
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Generated text as string
            
        Raises:
            ValueError: If generation fails
        """
        pass
    
    async def generate_with_semaphore(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Generate with concurrency control.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            **kwargs: Additional parameters
            
        Returns:
            Generated text
        """
        async with self._semaphore:
            return await self.generate_async(prompt, system_prompt, **kwargs)
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Synchronous wrapper for text generation.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            **kwargs: Additional parameters
            
        Returns:
            Generated text
        """
        return asyncio.run(self.generate_async(prompt, system_prompt, **kwargs))
    
    async def chat_async(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> str:
        """
        Asynchronously generate chat completion.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
                     Example: [{"role": "user", "content": "Hello"}]
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Generated response text
            
        Raises:
            ValueError: If chat generation fails
        """
        # Default implementation: convert messages to prompt
        system_prompt = None
        user_prompt = ""
        
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "system":
                system_prompt = content
            elif role == "user":
                user_prompt += content + "\n"
            elif role == "assistant":
                user_prompt += f"Assistant: {content}\n"
        
        return await self.generate_async(user_prompt.strip(), system_prompt, **kwargs)
    
    async def chat_with_semaphore(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> str:
        """
        Chat generation with concurrency control.
        
        Args:
            messages: List of message dictionaries
            **kwargs: Additional parameters
            
        Returns:
            Generated response
        """
        async with self._semaphore:
            return await self.chat_async(messages, **kwargs)
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> str:
        """
        Synchronous wrapper for chat generation.
        
        Args:
            messages: List of message dictionaries
            **kwargs: Additional parameters
            
        Returns:
            Generated response
        """
        return asyncio.run(self.chat_async(messages, **kwargs))
    
    def update_config(self, **kwargs) -> None:
        """
        Update provider configuration at runtime.
        
        Args:
            **kwargs: Configuration parameters to update
        """
        self.config.update(kwargs)
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get current provider configuration.
        
        Returns:
            Dictionary with current configuration
        """
        return self.config.copy()
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model.
        
        Returns:
            Dictionary with model information
        """
        return {
            'provider': self.provider_name,
            'model': self.config.get('model', 'default'),
            'is_local': self.is_local,
            'supports_streaming': self.supports_streaming,
        }
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(provider='{self.provider_name}', is_local={self.is_local})>"

