"""
Main router and orchestrator for speech transcription providers.
Provides factory pattern and batch processing capabilities.
"""
import asyncio
from typing import Optional, Dict, Any, List, Union, Type
from pathlib import Path
import warnings

from .base import BaseSpeechProvider
from .config import get_config

# Import all providers
from .deepgram import DeepgramProvider
from .assemblyai import AssemblyAIProvider
from .togetherai import TogetherAIProvider
from .elevenlabs import ElevenLabsProvider
from .faster_whisper import FasterWhisperProvider
from .parakeet import ParakeetProvider


# Provider registry
PROVIDER_REGISTRY: Dict[str, Type[BaseSpeechProvider]] = {
    'deepgram': DeepgramProvider,
    'assemblyai': AssemblyAIProvider,
    'togetherai': TogetherAIProvider,
    'elevenlabs': ElevenLabsProvider,
    'faster_whisper': FasterWhisperProvider,
    'parakeet': ParakeetProvider,
}


class SpeechTranscriptionRouter:
    """
    Main router for speech transcription providers.
    Handles provider selection, initialization, and orchestration.
    """
    
    def __init__(self, provider_name: str = 'faster_whisper', config: Optional[Dict[str, Any]] = None):
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
        self.provider: BaseSpeechProvider = provider_class(config)
    
    def transcribe(self, audio_path: str) -> str:
        """
        Transcribe a single audio file (synchronous).
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Transcribed text
        """
        return self.provider.transcribe(audio_path)
    
    async def transcribe_async(self, audio_path: str) -> str:
        """
        Transcribe a single audio file (asynchronous).
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Transcribed text
        """
        return await self.provider.transcribe_with_semaphore(audio_path)
    
    async def transcribe_batch_async(self, audio_paths: List[str]) -> List[str]:
        """
        Transcribe multiple audio files concurrently.
        
        Automatically handles concurrency limits based on provider type:
        - API-based providers: up to max_concurrent (default 5)
        - Local models: sequential processing (max_concurrent = 1)
        
        Args:
            audio_paths: List of paths to audio files
            
        Returns:
            List of transcribed texts in the same order as input
        """
        # Create tasks for all files
        tasks = [
            self.provider.transcribe_with_semaphore(audio_path)
            for audio_path in audio_paths
        ]
        
        # Execute all tasks concurrently (semaphore controls actual concurrency)
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        transcriptions = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                warnings.warn(
                    f"Transcription failed for {audio_paths[i]}: {str(result)}",
                    UserWarning
                )
                transcriptions.append("")
            else:
                transcriptions.append(result)
        
        return transcriptions
    
    def transcribe_batch(self, audio_paths: List[str]) -> List[str]:
        """
        Transcribe multiple audio files (synchronous wrapper).
        
        Args:
            audio_paths: List of paths to audio files
            
        Returns:
            List of transcribed texts
        """
        return asyncio.run(self.transcribe_batch_async(audio_paths))
    
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
            'config': self.get_config(),
        }
    
    @staticmethod
    def list_providers() -> List[str]:
        """
        List all available providers.
        
        Returns:
            List of provider names
        """
        return list(PROVIDER_REGISTRY.keys())
    
    @staticmethod
    def get_provider_class(provider_name: str) -> Type[BaseSpeechProvider]:
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
        return f"<SpeechTranscriptionRouter(provider='{self.provider_name}')>"


# Convenience functions for quick usage
def get_transcription(
    audio_path: str,
    provider: str = 'faster_whisper',
    config: Optional[Dict[str, Any]] = None
) -> str:
    """
    Quick transcription of a single audio file.
    
    Args:
        audio_path: Path to audio file
        provider: Provider name (default: 'faster_whisper')
        config: Optional provider configuration
        
    Returns:
        Transcribed text
    """
    router = SpeechTranscriptionRouter(provider, config)
    return router.transcribe(audio_path)


async def get_transcription_async(
    audio_path: str,
    provider: str = 'faster_whisper',
    config: Optional[Dict[str, Any]] = None
) -> str:
    """
    Quick async transcription of a single audio file.
    
    Args:
        audio_path: Path to audio file
        provider: Provider name (default: 'faster_whisper')
        config: Optional provider configuration
        
    Returns:
        Transcribed text
    """
    router = SpeechTranscriptionRouter(provider, config)
    return await router.transcribe_async(audio_path)


def get_batch_transcriptions(
    audio_paths: List[str],
    provider: str = 'faster_whisper',
    config: Optional[Dict[str, Any]] = None
) -> List[str]:
    """
    Quick batch transcription of multiple audio files.
    
    Args:
        audio_paths: List of paths to audio files
        provider: Provider name (default: 'faster_whisper')
        config: Optional provider configuration
        
    Returns:
        List of transcribed texts
    """
    router = SpeechTranscriptionRouter(provider, config)
    return router.transcribe_batch(audio_paths)


async def get_batch_transcriptions_async(
    audio_paths: List[str],
    provider: str = 'faster_whisper',
    config: Optional[Dict[str, Any]] = None
) -> List[str]:
    """
    Quick async batch transcription of multiple audio files.
    
    Args:
        audio_paths: List of paths to audio files
        provider: Provider name (default: 'faster_whisper')
        config: Optional provider configuration
        
    Returns:
        List of transcribed texts
    """
    router = SpeechTranscriptionRouter(provider, config)
    return await router.transcribe_batch_async(audio_paths)

