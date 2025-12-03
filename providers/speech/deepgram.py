"""
Deepgram speech transcription provider.
https://deepgram.com/
"""
import asyncio
import warnings
from typing import Optional, Dict, Any
from pathlib import Path

from .base import BaseSpeechProvider
from .config import get_config


class DeepgramProvider(BaseSpeechProvider):
    """
    Deepgram API-based speech transcription provider.
    Supports real-time and pre-recorded audio transcription.
    """
    
    provider_name = "deepgram"
    is_local = False
    max_concurrent = 5
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Deepgram provider.
        
        Args:
            config: Optional configuration dictionary. Supported keys:
                - api_key: Deepgram API key (overrides env.config)
                - model: Model to use (default: 'nova-2')
                - language: Language code (default: 'en')
                - max_concurrent: Max concurrent requests (default: 5)
        """
        super().__init__(config)
        
        # Set defaults
        self.config.setdefault('model', 'nova-2')
        self.config.setdefault('language', 'en')
        
        if 'max_concurrent' in self.config:
            self.max_concurrent = self.config['max_concurrent']
            self._semaphore = asyncio.Semaphore(self.max_concurrent)
    
    def _validate_config(self) -> None:
        """Validate Deepgram configuration and API key."""
        speech_config = get_config()
        
        # Check for API key in config or global config
        api_key = self.config.get('api_key') or speech_config.get_api_key('deepgram')
        
        if not api_key:
            warnings.warn(
                "Deepgram API key not found. Please set DEEPGRAM_API_KEY in env.config "
                "or provide 'api_key' in provider config.",
                UserWarning
            )
        else:
            self.config['api_key'] = api_key
    
    async def transcribe_async(self, audio_path: str) -> str:
        """
        Transcribe audio using Deepgram API.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Transcribed text
            
        Raises:
            ValueError: If API key is missing or transcription fails
        """
        audio_file = self._validate_audio_file(audio_path)
        
        api_key = self.config.get('api_key')
        if not api_key:
            raise ValueError(
                "Deepgram API key is required. Set DEEPGRAM_API_KEY in env.config "
                "or provide 'api_key' in config."
            )
        
        try:
            # Import deepgram SDK
            from deepgram import DeepgramClient, PrerecordedOptions, FileSource
            
            # Initialize client
            client = DeepgramClient(api_key)
            
            # Read audio file
            with open(audio_file, 'rb') as f:
                buffer_data = f.read()
            
            payload: FileSource = {
                "buffer": buffer_data,
            }
            
            # Configure options
            options = PrerecordedOptions(
                model=self.config.get('model', 'nova-2'),
                language=self.config.get('language', 'en'),
                smart_format=True,
            )
            
            # Run transcription in executor to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: client.listen.prerecorded.v("1").transcribe_file(payload, options)
            )
            
            # Extract transcript
            transcript = response.results.channels[0].alternatives[0].transcript
            
            return transcript
            
        except ImportError:
            raise ImportError(
                "Deepgram SDK not installed. Install with: pip install deepgram-sdk"
            )
        except Exception as e:
            raise ValueError(f"Deepgram transcription failed: {str(e)}")

