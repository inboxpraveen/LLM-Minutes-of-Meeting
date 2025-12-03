"""
Speech transcription providers module.

This module provides a unified interface for various speech-to-text providers,
including both API-based services and local models.

Available Providers:
    - deepgram: Deepgram API (requires DEEPGRAM_API_KEY)
    - assemblyai: AssemblyAI API (requires ASSEMBLYAI_API_KEY)
    - togetherai: Together AI API (requires TOGETHER_API_KEY)
    - elevenlabs: ElevenLabs API (requires ELEVENLABS_API_KEY)
    - faster_whisper: Local Faster Whisper model (no API key needed)
    - parakeet: Local NVIDIA Parakeet model (no API key needed)

Quick Start:
    >>> from providers.speech import get_transcription
    >>> text = get_transcription('audio.wav', provider='faster_whisper')
    
    >>> # Batch processing
    >>> from providers.speech import get_batch_transcriptions
    >>> texts = get_batch_transcriptions(['audio1.wav', 'audio2.wav'], provider='deepgram')
    
    >>> # Advanced usage with custom config
    >>> from providers.speech import SpeechTranscriptionRouter
    >>> router = SpeechTranscriptionRouter('deepgram', config={'model': 'nova-2'})
    >>> text = router.transcribe('audio.wav')
    
    >>> # Async usage
    >>> import asyncio
    >>> from providers.speech import get_transcription_async
    >>> text = asyncio.run(get_transcription_async('audio.wav', provider='assemblyai'))

Configuration:
    API keys should be set in env.config file or as environment variables:
    - DEEPGRAM_API_KEY=your_key_here
    - ASSEMBLYAI_API_KEY=your_key_here
    - TOGETHER_API_KEY=your_key_here
    - ELEVENLABS_API_KEY=your_key_here

For more information, see individual provider documentation.
"""

from .base import BaseSpeechProvider
from .config import SpeechConfig, get_config, reset_config
from .router import (
    SpeechTranscriptionRouter,
    get_transcription,
    get_transcription_async,
    get_batch_transcriptions,
    get_batch_transcriptions_async,
    PROVIDER_REGISTRY,
)

# Import all providers for direct access if needed
from .deepgram import DeepgramProvider
from .assemblyai import AssemblyAIProvider
from .togetherai import TogetherAIProvider
from .elevenlabs import ElevenLabsProvider
from .faster_whisper import FasterWhisperProvider
from .parakeet import ParakeetProvider


__all__ = [
    # Main classes
    'SpeechTranscriptionRouter',
    'BaseSpeechProvider',
    'SpeechConfig',
    
    # Convenience functions
    'get_transcription',
    'get_transcription_async',
    'get_batch_transcriptions',
    'get_batch_transcriptions_async',
    'get_config',
    'reset_config',
    
    # Provider classes
    'DeepgramProvider',
    'AssemblyAIProvider',
    'TogetherAIProvider',
    'ElevenLabsProvider',
    'FasterWhisperProvider',
    'ParakeetProvider',
    
    # Registry
    'PROVIDER_REGISTRY',
]


__version__ = '1.0.0'


def list_available_providers():
    """
    List all available speech transcription providers.
    
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
            'requires_api_key': not provider_class.is_local,
        }
    else:
        # Return info for all providers
        return {
            name: {
                'is_local': provider_class.is_local,
                'max_concurrent': provider_class.max_concurrent,
                'requires_api_key': not provider_class.is_local,
            }
            for name, provider_class in PROVIDER_REGISTRY.items()
        }
