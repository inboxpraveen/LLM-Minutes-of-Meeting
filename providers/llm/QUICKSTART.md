# Quick Reference Guide - LLM Providers

## Installation

```bash
# Core (always install)
pip install asyncio

# Choose your providers (install only what you need):
pip install openai                  # OpenAI
pip install google-generativeai     # Google Gemini
pip install ollama                  # Ollama (also install from ollama.ai)
```

## Quick Start

```python
# Simple generation - local model (no API key needed)
from providers.llm import generate_text
text = generate_text('Explain AI', provider='ollama')

# API provider (requires API key in env.config)
text = generate_text('Explain AI', provider='openai')

# Chat completion
from providers.llm import chat_completion
messages = [{"role": "user", "content": "Hello!"}]
response = chat_completion(messages, provider='gemini')
```

## Configuration

Edit `env.config`:
```ini
OPENAI_API_KEY=your_key_here
GEMINI_API_KEY=your_key_here
GROK_API_KEY=your_key_here
```

## Available Providers

| Provider | Type | API Key Required | Max Concurrent | Best For |
|----------|------|-----------------|----------------|----------|
| ollama | Local | No | 1 | Privacy, offline, customization |
| openai | API | Yes | 5 | GPT-4, high quality |
| gemini | API | Yes | 5 | Google AI, multimodal |
| grok | API | Yes | 5 | xAI models |

## Advanced Usage

```python
from providers.llm import LLMRouter

# Custom configuration
config = {
    'model': 'gpt-4',
    'temperature': 0.7,
    'max_tokens': 1000
}

router = LLMRouter('openai', config)
text = router.generate('Explain neural networks')

# Async usage
import asyncio
async def generate():
    return await router.generate_async('Hello')

text = asyncio.run(generate())
```

## Concurrency Behavior

- **API Providers**: Process up to 5 requests concurrently (configurable)
- **Local Models**: Process 1 request at a time (sequential)

This is automatically managed by the system!

## Common Issues

**"API key not found" warning**
→ Add your API key to `env.config`

**"Module not found" error**
→ Install the provider's SDK: `pip install <provider-name>`

**"Could not connect to Ollama" error**
→ Start Ollama: `ollama serve`
→ Pull a model: `ollama pull llama2`

**Slow local generation**
→ Use smaller models: `ollama pull phi`
→ Reduce max_tokens in config

## Provider-Specific Config

**OpenAI**
```python
config = {
    'model': 'gpt-4',      # gpt-3.5-turbo, gpt-4
    'temperature': 0.7,
    'max_tokens': 1000
}
```

**Gemini**
```python
config = {
    'model': 'gemini-pro',
    'temperature': 0.7,
    'max_tokens': 1000
}
```

**Ollama**
```python
config = {
    'model': 'llama2',     # llama2, mistral, phi, codellama
    'temperature': 0.7,
    'num_predict': 1000
}
```

## List Providers & Models

```python
from providers.llm import list_available_providers, get_provider_info

# List all providers
print(list_available_providers())

# Get detailed info
info = get_provider_info('openai')
print(info)

# For Ollama: list local models
from providers.llm import OllamaProvider
ollama = OllamaProvider()
models = ollama.list_models()
```

## Minutes of Meeting Example

```python
from providers.llm import generate_text

conversation = """
Manager: We need to finalize the Q4 roadmap.
Developer: I'll complete the API by Dec 15th.
"""

system_prompt = """
Provide a summary with action items and deadlines.
"""

summary = generate_text(
    conversation,
    system_prompt=system_prompt,
    provider='ollama'
)
```

## More Information

- Full documentation: `providers/llm/README.md`
- Examples: `providers/llm/examples.py`
- Run examples: `python providers/llm/examples.py`

## Support

For issues, refer to:
1. `README.md` for comprehensive documentation
2. `examples.py` for working code examples
3. Provider's official documentation for API-specific issues

