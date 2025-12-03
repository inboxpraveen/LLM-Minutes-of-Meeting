"""
Together AI speech transcription provider.
https://www.together.ai/
"""
import asyncio
import warnings
from typing import Optional, Dict, Any

from .base import BaseSpeechProvider
from .config import get_config


class TogetherAIProvider(BaseSpeechProvider):
    """
    Together AI API-based speech transcription provider.
    Uses Together AI's Whisper models for transcription.
    """
    
    provider_name = "togetherai"
    is_local = False
    max_concurrent = 5
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Together AI provider.
        
        Args:
            config: Optional configuration dictionary. Supported keys:
                - api_key: Together AI API key (overrides env.config)
                - model: Model to use (default: 'whisper-large-v3')
                - language: Language code (default: 'en')
                - max_concurrent: Max concurrent requests (default: 5)
        """
        super().__init__(config)
        
        # Set defaults
        self.config.setdefault('model', 'whisper-large-v3')
        self.config.setdefault('language', 'en')
        
        if 'max_concurrent' in self.config:
            self.max_concurrent = self.config['max_concurrent']
            self._semaphore = asyncio.Semaphore(self.max_concurrent)
    
    def _validate_config(self) -> None:
        """Validate Together AI configuration and API key."""
        speech_config = get_config()
        
        # Check for API key in config or global config
        api_key = self.config.get('api_key') or speech_config.get_api_key('togetherai')
        
        if not api_key:
            warnings.warn(
                "Together AI API key not found. Please set TOGETHER_API_KEY in env.config "
                "or provide 'api_key' in provider config.",
                UserWarning
            )
        else:
            self.config['api_key'] = api_key
    
    async def transcribe_async(self, audio_path: str) -> str:
        """
        Transcribe audio using Together AI API.
        
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
                "Together AI API key is required. Set TOGETHER_API_KEY in env.config "
                "or provide 'api_key' in config."
            )
        
        try:
            # Import together SDK
            from together import Together
            
            # Initialize client
            client = Together(api_key=api_key)
            
            # Read audio file
            with open(audio_file, 'rb') as f:
                audio_data = f.read()
            
            # Run transcription in executor
            loop = asyncio.get_event_loop()
            
            # Together AI uses OpenAI-compatible API
            response = await loop.run_in_executor(
                None,
                lambda: client.audio.transcriptions.create(
                    file=(audio_file.name, audio_data),
                    model=self.config.get('model', 'whisper-large-v3'),
                    language=self.config.get('language', 'en'),
                )
            )
            
            return response.text
            
        except ImportError:
            raise ImportError(
                "Together AI SDK not installed. Install with: pip install together"
            )
        except Exception as e:
            raise ValueError(f"Together AI transcription failed: {str(e)}")

