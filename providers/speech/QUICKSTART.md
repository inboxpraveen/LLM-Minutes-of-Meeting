# Quick Reference Guide - Speech Providers

## Installation

```bash
# Core dependencies
pip install torch transformers

# Choose your providers (install only what you need):
pip install faster-whisper              # Faster Whisper (local)
pip install deepgram-sdk                 # Deepgram
pip install assemblyai                   # AssemblyAI
pip install together                     # Together AI
pip install elevenlabs requests          # ElevenLabs
```

## Quick Start

```python
# Simple usage - local model (no API key needed)
from providers.speech import get_transcription
text = get_transcription('audio.wav', provider='faster_whisper')

# API provider (requires API key in env.config)
text = get_transcription('audio.wav', provider='deepgram')

# Batch processing
from providers.speech import get_batch_transcriptions
files = ['audio1.wav', 'audio2.wav', 'audio3.wav']
texts = get_batch_transcriptions(files, provider='assemblyai')
```

## Configuration

Edit `env.config`:
```ini
DEEPGRAM_API_KEY=your_key_here
ASSEMBLYAI_API_KEY=your_key_here
TOGETHER_API_KEY=your_key_here
ELEVENLABS_API_KEY=your_key_here
```

## Available Providers

| Provider | Type | API Key Required | Max Concurrent | Best For |
|----------|------|-----------------|----------------|----------|
| faster_whisper | Local | No | 1 | Offline, privacy-focused |
| parakeet | Local | No | 1 | Lightweight, fast local |
| deepgram | API | Yes | 5 | High accuracy, fast |
| assemblyai | API | Yes | 5 | Speaker diarization |
| togetherai | API | Yes | 5 | Cost-effective |
| elevenlabs | API | Yes | 5 | Multilingual |

## Advanced Usage

```python
from providers.speech import SpeechTranscriptionRouter

# Custom configuration
config = {
    'model_size': 'base',      # For faster_whisper
    'language': 'en',
    'max_concurrent': 10       # Override default
}

router = SpeechTranscriptionRouter('faster_whisper', config)
text = router.transcribe('audio.wav')

# Async usage
import asyncio
async def transcribe():
    return await router.transcribe_async('audio.wav')

text = asyncio.run(transcribe())
```

## Concurrency Behavior

- **API Providers**: Process up to 5 files concurrently (configurable)
- **Local Models**: Process 1 file at a time (sequential)

This is automatically managed by the system!

## Common Issues

**"API key not found" warning**
→ Add your API key to `env.config`

**"Module not found" error**
→ Install the provider's dependencies: `pip install <provider-sdk>`

**Slow local transcription**
→ Ensure GPU is available and being used (check with `torch.cuda.is_available()`)

**CUDA out of memory**
→ Use smaller model size: `config = {'model_size': 'base'}`

## File Structure

```
providers/speech/
├── __init__.py              # Import this
├── base.py                  # Base class (internal)
├── config.py                # Config management (internal)
├── router.py                # Main router (internal)
├── <provider>.py            # Provider implementations (internal)
├── README.md                # Full documentation
├── examples.py              # Usage examples
└── requirements.txt         # Dependencies
```

## Examples

Run examples:
```bash
python providers/speech/examples.py
```

## More Information

- Full documentation: `providers/speech/README.md`
- Implementation details: `providers/speech/IMPLEMENTATION_SUMMARY.md`
- Examples: `providers/speech/examples.py`

## Provider-Specific Config

**Faster Whisper**
```python
config = {
    'model_size': 'base',  # tiny, base, small, medium, large-v2, large-v3
    'device': 'auto',      # auto, cuda, cpu
    'language': 'en',      # language code or None for auto-detect
    'vad_filter': True     # Voice activity detection
}
```

**Deepgram**
```python
config = {
    'model': 'nova-2',     # nova-2, base, enhanced
    'language': 'en',
    'max_concurrent': 5
}
```

**AssemblyAI**
```python
config = {
    'language_code': 'en',
    'speaker_labels': True,  # Enable speaker diarization
    'max_concurrent': 5
}
```

**Parakeet**
```python
config = {
    'model_name': 'nvidia/parakeet-tdt-0.6b',
    'device': 'auto',
    'language': 'en'
}
```

## List Available Providers

```python
from providers.speech import list_available_providers, get_provider_info

# List all providers
print(list_available_providers())

# Get detailed info
info = get_provider_info('deepgram')
print(info)
```

## Support

For issues, refer to:
1. `README.md` for comprehensive documentation
2. `examples.py` for working code examples
3. Provider's official documentation for API-specific issues

