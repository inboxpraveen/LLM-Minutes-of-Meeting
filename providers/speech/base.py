"""
Base abstract class for all speech transcription providers.
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import asyncio
from pathlib import Path


class BaseSpeechProvider(ABC):
    """
    Abstract base class for all speech transcription providers.
    
    Attributes:
        provider_name: Name of the provider
        is_local: Whether the provider runs locally or uses API
        max_concurrent: Maximum concurrent transcriptions allowed
        config: Provider-specific configuration
    """
    
    provider_name: str = "base"
    is_local: bool = False
    max_concurrent: int = 5
    
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
    async def transcribe_async(self, audio_path: str) -> str:
        """
        Asynchronously transcribe audio file to text.
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            Transcribed text as string
            
        Raises:
            FileNotFoundError: If audio file doesn't exist
            ValueError: If transcription fails
        """
        pass
    
    async def transcribe_with_semaphore(self, audio_path: str) -> str:
        """
        Transcribe with concurrency control.
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            Transcribed text
        """
        async with self._semaphore:
            return await self.transcribe_async(audio_path)
    
    def transcribe(self, audio_path: str) -> str:
        """
        Synchronous wrapper for transcription.
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            Transcribed text
        """
        return asyncio.run(self.transcribe_async(audio_path))
    
    def _validate_audio_file(self, audio_path: str) -> Path:
        """
        Validate that audio file exists and is accessible.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Path object
            
        Raises:
            FileNotFoundError: If file doesn't exist
        """
        path = Path(audio_path)
        if not path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        if not path.is_file():
            raise ValueError(f"Path is not a file: {audio_path}")
        return path
    
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
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(provider='{self.provider_name}', is_local={self.is_local})>"

