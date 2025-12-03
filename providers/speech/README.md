# Speech Transcription Providers

A unified, standardized interface for multiple speech-to-text providers, supporting both API-based services and local models.

## Features

- **Multiple Providers**: Support for 6 different speech transcription providers
- **Unified Interface**: Same API for all providers
- **Async Support**: Built-in async/await support with intelligent concurrency control
- **Batch Processing**: Efficiently process multiple audio files
- **Configuration Management**: Centralized configuration via `env.config`
- **Type Safety**: Full type hints throughout
- **Error Handling**: Graceful error handling with warnings

## Available Providers

### API-Based Providers (Cloud)
- **Deepgram** - High-quality, fast transcription with multiple models
- **AssemblyAI** - Advanced transcription with speaker diarization
- **Together AI** - Whisper models via Together AI platform
- **ElevenLabs** - Multilingual transcription support

### Local Model Providers
- **Faster Whisper** - Efficient local transcription using CTranslate2
- **Parakeet TDT 0.6B** - NVIDIA's lightweight transcription model

## Installation

### Core Dependencies
```bash
pip install torch transformers
```

### Provider-Specific Dependencies

**For API-based providers:**
```bash
# Deepgram
pip install deepgram-sdk

# AssemblyAI
pip install assemblyai

# Together AI
pip install together

# ElevenLabs
pip install elevenlabs requests
```

**For local models:**
```bash
# Faster Whisper
pip install faster-whisper

# Parakeet (choose one)
pip install transformers  # For transformers-based loading
# OR
pip install nemo_toolkit[asr]  # For NeMo-based loading
```

## Configuration

1. Copy `env.config.example` to `env.config`
2. Add your API keys for the providers you want to use:

```ini
# env.config
DEEPGRAM_API_KEY=your_key_here
ASSEMBLYAI_API_KEY=your_key_here
TOGETHER_API_KEY=your_key_here
ELEVENLABS_API_KEY=your_key_here
```

**Note:** Local models (faster_whisper, parakeet) don't require API keys.

## Quick Start

### Simple Usage

```python
from providers.speech import get_transcription

# Using local model (default)
text = get_transcription('audio.wav', provider='faster_whisper')

# Using API provider
text = get_transcription('audio.wav', provider='deepgram')
```

### Async Usage

```python
import asyncio
from providers.speech import get_transcription_async

async def transcribe():
    text = await get_transcription_async('audio.wav', provider='assemblyai')
    print(text)

asyncio.run(transcribe())
```

### Batch Processing

```python
from providers.speech import get_batch_transcriptions

audio_files = ['audio1.wav', 'audio2.wav', 'audio3.wav']
transcriptions = get_batch_transcriptions(audio_files, provider='deepgram')

for file, text in zip(audio_files, transcriptions):
    print(f"{file}: {text}")
```

### Advanced Usage with Custom Configuration

```python
from providers.speech import SpeechTranscriptionRouter

# Initialize router with custom config
config = {
    'model': 'nova-2',
    'language': 'en',
    'max_concurrent': 10  # Override default concurrency
}

router = SpeechTranscriptionRouter('deepgram', config=config)

# Single file
text = router.transcribe('audio.wav')

# Batch processing
texts = router.transcribe_batch(['audio1.wav', 'audio2.wav'])

# Update config at runtime
router.update_config(language='es')
```

### Async Batch Processing

```python
import asyncio
from providers.speech import SpeechTranscriptionRouter

async def batch_transcribe():
    router = SpeechTranscriptionRouter('faster_whisper')
    audio_files = ['audio1.wav', 'audio2.wav', 'audio3.wav']
    
    results = await router.transcribe_batch_async(audio_files)
    return results

results = asyncio.run(batch_transcribe())
```

## Provider-Specific Configuration

### Deepgram
```python
config = {
    'model': 'nova-2',  # or 'base', 'enhanced', etc.
    'language': 'en',
    'max_concurrent': 5
}
router = SpeechTranscriptionRouter('deepgram', config)
```

### AssemblyAI
```python
config = {
    'language_code': 'en',
    'speaker_labels': True,  # Enable speaker diarization
    'max_concurrent': 5
}
router = SpeechTranscriptionRouter('assemblyai', config)
```

### Faster Whisper
```python
config = {
    'model_size': 'base',  # tiny, base, small, medium, large-v2, large-v3
    'device': 'cuda',  # or 'cpu', 'auto'
    'compute_type': 'float16',  # or 'int8', 'float32'
    'language': 'en',  # or None for auto-detection
    'beam_size': 5,
    'vad_filter': True
}
router = SpeechTranscriptionRouter('faster_whisper', config)
```

### Parakeet
```python
config = {
    'model_name': 'nvidia/parakeet-tdt-0.6b',
    'device': 'cuda',  # or 'cpu', 'auto'
    'language': 'en'
}
router = SpeechTranscriptionRouter('parakeet', config)
```

## Concurrency Control

The system automatically manages concurrency based on provider type:

- **API Providers**: Default 5 concurrent requests (configurable)
- **Local Models**: Sequential processing (1 at a time) to manage resources

You can customize concurrency per provider:

```python
config = {'max_concurrent': 10}
router = SpeechTranscriptionRouter('deepgram', config)
```

## Error Handling

The system provides graceful error handling:

```python
from providers.speech import get_transcription

try:
    text = get_transcription('audio.wav', provider='deepgram')
except FileNotFoundError:
    print("Audio file not found")
except ValueError as e:
    print(f"Transcription failed: {e}")
```

For batch processing, errors are caught and warned, returning empty strings for failed files:

```python
# Failed transcriptions return empty string with warning
results = get_batch_transcriptions(['audio1.wav', 'missing.wav'])
# Results: ['transcription text', '']
```

## Utility Functions

### List Available Providers
```python
from providers.speech import list_available_providers

providers = list_available_providers()
print(providers)
# Output: ['deepgram (API)', 'assemblyai (API)', ..., 'faster_whisper (Local)']
```

### Get Provider Information
```python
from providers.speech import get_provider_info

# Info for specific provider
info = get_provider_info('deepgram')
print(info)
# {'name': 'deepgram', 'is_local': False, 'max_concurrent': 5, 'requires_api_key': True}

# Info for all providers
all_info = get_provider_info()
```

### Check Configuration
```python
from providers.speech import get_config

config = get_config()
print(config.get_all_config())  # Shows all config with masked API keys
```

## Architecture

```
providers/speech/
├── __init__.py          # Public API exports
├── base.py              # Abstract base class
├── config.py            # Configuration management
├── router.py            # Main router and orchestrator
├── deepgram.py          # Deepgram provider
├── assemblyai.py        # AssemblyAI provider
├── togetherai.py        # Together AI provider
├── elevenlabs.py        # ElevenLabs provider
├── faster_whisper.py    # Faster Whisper provider
└── parakeet.py          # Parakeet provider
```

## Creating Custom Providers

You can extend the system with custom providers:

```python
from providers.speech.base import BaseSpeechProvider

class CustomProvider(BaseSpeechProvider):
    provider_name = "custom"
    is_local = False
    max_concurrent = 5
    
    def _validate_config(self):
        # Validate your config
        pass
    
    async def transcribe_async(self, audio_path: str) -> str:
        # Implement transcription logic
        pass
```

Then register it:

```python
from providers.speech import PROVIDER_REGISTRY
PROVIDER_REGISTRY['custom'] = CustomProvider
```

## Performance Considerations

- **Local Models**: First run downloads models (can be large). Subsequent runs are faster.
- **API Providers**: Network latency affects speed. Batch processing with concurrency helps.
- **GPU Acceleration**: Local models benefit significantly from GPU. Use CUDA when available.
- **Memory**: Local models require significant RAM/VRAM. Monitor resource usage.

## Troubleshooting

### API Key Not Found Warning
```
Solution: Add your API key to env.config or set as environment variable
```

### Import Error for Provider SDK
```
Solution: Install the required package (see Installation section)
```

### CUDA Out of Memory
```
Solution: 
- Use smaller model size (e.g., 'base' instead of 'large')
- Set compute_type='int8' for Faster Whisper
- Process files sequentially instead of in batch
```

### Slow Transcription with Local Models
```
Solution:
- Ensure GPU is being used (check with torch.cuda.is_available())
- Use smaller model sizes
- Enable VAD filtering to skip silence
```

## License

See main project LICENSE file.

