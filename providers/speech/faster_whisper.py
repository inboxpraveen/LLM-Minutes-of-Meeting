"""
Faster Whisper speech transcription provider.
https://github.com/guillaumekln/faster-whisper
Local model-based transcription using CTranslate2.
"""
import asyncio
import warnings
from typing import Optional, Dict, Any
import torch

from .base import BaseSpeechProvider
from .config import get_config


class FasterWhisperProvider(BaseSpeechProvider):
    """
    Faster Whisper local model provider.
    Uses CTranslate2 for efficient local transcription.
    Processes requests sequentially due to local resource constraints.
    """
    
    provider_name = "faster_whisper"
    is_local = True
    max_concurrent = 1  # Local model processes sequentially
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Faster Whisper provider.
        
        Args:
            config: Optional configuration dictionary. Supported keys:
                - model_size: Model size (default: 'base')
                  Options: 'tiny', 'base', 'small', 'medium', 'large-v2', 'large-v3'
                - device: Device to use (default: 'auto' - cuda if available, else cpu)
                - compute_type: Compute type (default: 'float16' for GPU, 'int8' for CPU)
                - language: Language code (default: None for auto-detection)
                - beam_size: Beam size for decoding (default: 5)
                - vad_filter: Enable VAD filtering (default: True)
        """
        super().__init__(config)
        
        # Set defaults
        self.config.setdefault('model_size', 'base')
        self.config.setdefault('device', 'auto')
        self.config.setdefault('language', None)
        self.config.setdefault('beam_size', 5)
        self.config.setdefault('vad_filter', True)
        
        # Determine device and compute type
        if self.config['device'] == 'auto':
            self.config['device'] = 'cuda' if torch.cuda.is_available() else 'cpu'
        
        if 'compute_type' not in self.config:
            self.config['compute_type'] = 'float16' if self.config['device'] == 'cuda' else 'int8'
        
        # Model will be loaded on first use (lazy loading)
        self._model = None
    
    def _validate_config(self) -> None:
        """Validate Faster Whisper configuration."""
        valid_sizes = ['tiny', 'tiny.en', 'base', 'base.en', 'small', 'small.en', 
                       'medium', 'medium.en', 'large-v1', 'large-v2', 'large-v3']
        
        model_size = self.config.get('model_size')
        if model_size not in valid_sizes:
            warnings.warn(
                f"Model size '{model_size}' may not be valid. "
                f"Valid options: {', '.join(valid_sizes)}",
                UserWarning
            )
    
    def _load_model(self):
        """Lazy load the Faster Whisper model."""
        if self._model is not None:
            return self._model
        
        try:
            from faster_whisper import WhisperModel
            
            self._model = WhisperModel(
                self.config['model_size'],
                device=self.config['device'],
                compute_type=self.config['compute_type'],
            )
            
            return self._model
            
        except ImportError:
            raise ImportError(
                "Faster Whisper not installed. Install with: pip install faster-whisper"
            )
    
    async def transcribe_async(self, audio_path: str) -> str:
        """
        Transcribe audio using Faster Whisper model.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Transcribed text
            
        Raises:
            ValueError: If transcription fails
        """
        audio_file = self._validate_audio_file(audio_path)
        
        try:
            # Load model if not already loaded
            model = self._load_model()
            
            # Run transcription in executor to avoid blocking
            loop = asyncio.get_event_loop()
            segments, info = await loop.run_in_executor(
                None,
                lambda: model.transcribe(
                    str(audio_file),
                    language=self.config.get('language'),
                    beam_size=self.config.get('beam_size', 5),
                    vad_filter=self.config.get('vad_filter', True),
                )
            )
            
            # Combine all segments into full transcript
            transcript = " ".join([segment.text for segment in segments])
            
            return transcript.strip()
            
        except Exception as e:
            raise ValueError(f"Faster Whisper transcription failed: {str(e)}")
    
    def __del__(self):
        """Cleanup model resources."""
        if self._model is not None:
            del self._model
            self._model = None
            
            # Clear CUDA cache if available
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

