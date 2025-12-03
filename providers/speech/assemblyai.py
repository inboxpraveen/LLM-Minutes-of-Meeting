"""
AssemblyAI speech transcription provider.
https://www.assemblyai.com/
"""
import asyncio
import warnings
from typing import Optional, Dict, Any
import time

from .base import BaseSpeechProvider
from .config import get_config


class AssemblyAIProvider(BaseSpeechProvider):
    """
    AssemblyAI API-based speech transcription provider.
    Supports high-quality audio transcription with various features.
    """
    
    provider_name = "assemblyai"
    is_local = False
    max_concurrent = 5
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize AssemblyAI provider.
        
        Args:
            config: Optional configuration dictionary. Supported keys:
                - api_key: AssemblyAI API key (overrides env.config)
                - language_code: Language code (default: 'en')
                - speaker_labels: Enable speaker diarization (default: False)
                - max_concurrent: Max concurrent requests (default: 5)
        """
        super().__init__(config)
        
        # Set defaults
        self.config.setdefault('language_code', 'en')
        self.config.setdefault('speaker_labels', False)
        
        if 'max_concurrent' in self.config:
            self.max_concurrent = self.config['max_concurrent']
            self._semaphore = asyncio.Semaphore(self.max_concurrent)
    
    def _validate_config(self) -> None:
        """Validate AssemblyAI configuration and API key."""
        speech_config = get_config()
        
        # Check for API key in config or global config
        api_key = self.config.get('api_key') or speech_config.get_api_key('assemblyai')
        
        if not api_key:
            warnings.warn(
                "AssemblyAI API key not found. Please set ASSEMBLYAI_API_KEY in env.config "
                "or provide 'api_key' in provider config.",
                UserWarning
            )
        else:
            self.config['api_key'] = api_key
    
    async def transcribe_async(self, audio_path: str) -> str:
        """
        Transcribe audio using AssemblyAI API.
        
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
                "AssemblyAI API key is required. Set ASSEMBLYAI_API_KEY in env.config "
                "or provide 'api_key' in config."
            )
        
        try:
            # Import assemblyai SDK
            import assemblyai as aai
            
            # Configure client
            aai.settings.api_key = api_key
            
            # Create transcriber
            transcriber = aai.Transcriber()
            
            # Configure transcription options
            config_obj = aai.TranscriptionConfig(
                language_code=self.config.get('language_code', 'en'),
                speaker_labels=self.config.get('speaker_labels', False),
            )
            
            # Run transcription in executor
            loop = asyncio.get_event_loop()
            transcript = await loop.run_in_executor(
                None,
                lambda: transcriber.transcribe(str(audio_file), config=config_obj)
            )
            
            # Check for errors
            if transcript.status == aai.TranscriptStatus.error:
                raise ValueError(f"Transcription failed: {transcript.error}")
            
            return transcript.text
            
        except ImportError:
            raise ImportError(
                "AssemblyAI SDK not installed. Install with: pip install assemblyai"
            )
        except Exception as e:
            raise ValueError(f"AssemblyAI transcription failed: {str(e)}")

