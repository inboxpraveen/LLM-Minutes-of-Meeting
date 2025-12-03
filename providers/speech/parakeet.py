"""
Parakeet TDT 0.6B speech transcription provider.
NVIDIA's Parakeet model for speech recognition.
https://catalog.ngc.nvidia.com/orgs/nvidia/teams/nemo/models/parakeet-tdt-0.6b
"""
import asyncio
import warnings
from typing import Optional, Dict, Any
import torch

from .base import BaseSpeechProvider
from .config import get_config


class ParakeetProvider(BaseSpeechProvider):
    """
    Parakeet TDT 0.6B local model provider.
    Uses NVIDIA's Parakeet model for efficient speech recognition.
    Processes requests sequentially due to local resource constraints.
    """
    
    provider_name = "parakeet"
    is_local = True
    max_concurrent = 1  # Local model processes sequentially
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Parakeet provider.
        
        Args:
            config: Optional configuration dictionary. Supported keys:
                - model_name: Model identifier (default: 'nvidia/parakeet-tdt-0.6b')
                - device: Device to use (default: 'auto' - cuda if available, else cpu)
                - batch_size: Batch size for processing (default: 1)
                - language: Language code (default: 'en')
        """
        super().__init__(config)
        
        # Set defaults
        self.config.setdefault('model_name', 'nvidia/parakeet-tdt-0.6b')
        self.config.setdefault('device', 'auto')
        self.config.setdefault('batch_size', 1)
        self.config.setdefault('language', 'en')
        
        # Determine device
        if self.config['device'] == 'auto':
            self.config['device'] = 'cuda' if torch.cuda.is_available() else 'cpu'
        
        # Model will be loaded on first use (lazy loading)
        self._model = None
        self._processor = None
    
    def _validate_config(self) -> None:
        """Validate Parakeet configuration."""
        if self.config['device'] == 'cpu':
            warnings.warn(
                "Parakeet model is running on CPU. This may be significantly slower. "
                "GPU is recommended for optimal performance.",
                UserWarning
            )
    
    def _load_model(self):
        """Lazy load the Parakeet model."""
        if self._model is not None and self._processor is not None:
            return self._model, self._processor
        
        try:
            from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor
            
            device = self.config['device']
            torch_dtype = torch.float16 if device == 'cuda' else torch.float32
            
            # Load model
            self._model = AutoModelForSpeechSeq2Seq.from_pretrained(
                self.config['model_name'],
                torch_dtype=torch_dtype,
                low_cpu_mem_usage=True,
                use_safetensors=True,
            )
            self._model.to(device)
            
            # Load processor
            self._processor = AutoProcessor.from_pretrained(self.config['model_name'])
            
            return self._model, self._processor
            
        except ImportError:
            raise ImportError(
                "Transformers library not installed. Install with: pip install transformers"
            )
        except Exception as e:
            # Fallback: try loading with nemo toolkit
            try:
                import nemo.collections.asr as nemo_asr
                
                self._model = nemo_asr.models.EncDecRNNTBPEModel.from_pretrained(
                    model_name=self.config['model_name']
                )
                self._model.to(self.config['device'])
                
                return self._model, None
                
            except ImportError:
                raise ImportError(
                    "Neither transformers nor NeMo toolkit installed. "
                    "Install with: pip install transformers OR pip install nemo_toolkit[asr]"
                )
            except Exception as nemo_error:
                raise ValueError(
                    f"Failed to load Parakeet model with both transformers and NeMo: "
                    f"transformers error: {str(e)}, NeMo error: {str(nemo_error)}"
                )
    
    async def transcribe_async(self, audio_path: str) -> str:
        """
        Transcribe audio using Parakeet model.
        
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
            model, processor = self._load_model()
            
            # Run transcription in executor to avoid blocking
            loop = asyncio.get_event_loop()
            
            if processor is not None:
                # Using transformers pipeline
                transcript = await loop.run_in_executor(
                    None,
                    lambda: self._transcribe_with_transformers(str(audio_file), model, processor)
                )
            else:
                # Using NeMo toolkit
                transcript = await loop.run_in_executor(
                    None,
                    lambda: self._transcribe_with_nemo(str(audio_file), model)
                )
            
            return transcript.strip()
            
        except Exception as e:
            raise ValueError(f"Parakeet transcription failed: {str(e)}")
    
    def _transcribe_with_transformers(self, audio_path: str, model, processor):
        """Transcribe using transformers pipeline."""
        from transformers import pipeline
        
        speech_pipeline = pipeline(
            "automatic-speech-recognition",
            model=model,
            tokenizer=processor.tokenizer,
            feature_extractor=processor.feature_extractor,
            torch_dtype=torch.float16 if self.config['device'] == 'cuda' else torch.float32,
            device=self.config['device'],
        )
        
        result = speech_pipeline(audio_path, return_timestamps=False)
        return result['text']
    
    def _transcribe_with_nemo(self, audio_path: str, model):
        """Transcribe using NeMo toolkit."""
        transcriptions = model.transcribe([audio_path])
        return transcriptions[0] if transcriptions else ""
    
    def __del__(self):
        """Cleanup model resources."""
        if self._model is not None:
            del self._model
            self._model = None
        
        if self._processor is not None:
            del self._processor
            self._processor = None
        
        # Clear CUDA cache if available
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

