"""
ElevenLabs speech transcription provider.
https://elevenlabs.io/
"""
import asyncio
import warnings
from typing import Optional, Dict, Any

from .base import BaseSpeechProvider
from .config import get_config


class ElevenLabsProvider(BaseSpeechProvider):
    """
    ElevenLabs API-based speech transcription provider.
    Note: ElevenLabs primarily focuses on TTS, but supports transcription via their API.
    """
    
    provider_name = "elevenlabs"
    is_local = False
    max_concurrent = 5
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize ElevenLabs provider.
        
        Args:
            config: Optional configuration dictionary. Supported keys:
                - api_key: ElevenLabs API key (overrides env.config)
                - model: Model to use (default: 'eleven_multilingual_v2')
                - language: Language code (default: 'en')
                - max_concurrent: Max concurrent requests (default: 5)
        """
        super().__init__(config)
        
        # Set defaults
        self.config.setdefault('model', 'eleven_multilingual_v2')
        self.config.setdefault('language', 'en')
        
        if 'max_concurrent' in self.config:
            self.max_concurrent = self.config['max_concurrent']
            self._semaphore = asyncio.Semaphore(self.max_concurrent)
    
    def _validate_config(self) -> None:
        """Validate ElevenLabs configuration and API key."""
        speech_config = get_config()
        
        # Check for API key in config or global config
        api_key = self.config.get('api_key') or speech_config.get_api_key('elevenlabs')
        
        if not api_key:
            warnings.warn(
                "ElevenLabs API key not found. Please set ELEVENLABS_API_KEY in env.config "
                "or provide 'api_key' in provider config.",
                UserWarning
            )
        else:
            self.config['api_key'] = api_key
    
    async def transcribe_async(self, audio_path: str) -> str:
        """
        Transcribe audio using ElevenLabs API.
        
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
                "ElevenLabs API key is required. Set ELEVENLABS_API_KEY in env.config "
                "or provide 'api_key' in config."
            )
        
        try:
            # Import elevenlabs SDK
            from elevenlabs import ElevenLabs
            
            # Initialize client
            client = ElevenLabs(api_key=api_key)
            
            # Read audio file
            with open(audio_file, 'rb') as f:
                audio_data = f.read()
            
            # Run transcription in executor
            # Note: ElevenLabs' Python SDK may vary - this is a generic implementation
            loop = asyncio.get_event_loop()
            
            # Using their speech-to-text endpoint (if available)
            # This is a placeholder - actual implementation depends on ElevenLabs SDK version
            response = await loop.run_in_executor(
                None,
                lambda: self._sync_transcribe(client, audio_file)
            )
            
            return response
            
        except ImportError:
            raise ImportError(
                "ElevenLabs SDK not installed. Install with: pip install elevenlabs"
            )
        except Exception as e:
            raise ValueError(f"ElevenLabs transcription failed: {str(e)}")
    
    def _sync_transcribe(self, client, audio_file):
        """
        Synchronous transcription helper.
        
        Note: This is a placeholder implementation. The actual API call
        depends on ElevenLabs SDK's transcription capabilities.
        """
        # Placeholder for actual API call
        # ElevenLabs may not have direct transcription API in their SDK
        # You may need to use their REST API directly
        import requests
        
        api_key = self.config.get('api_key')
        
        # Example REST API call (adjust based on actual ElevenLabs API)
        url = "https://api.elevenlabs.io/v1/speech-to-text"
        headers = {
            "xi-api-key": api_key,
        }
        
        with open(audio_file, 'rb') as f:
            files = {'audio': f}
            response = requests.post(url, headers=headers, files=files)
        
        if response.status_code == 200:
            return response.json().get('text', '')
        else:
            raise ValueError(f"API request failed: {response.status_code} - {response.text}")

