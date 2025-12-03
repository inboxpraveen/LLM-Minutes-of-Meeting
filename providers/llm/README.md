# LLM Providers

A unified, standardized interface for multiple Large Language Model providers, supporting both API-based services and local models.

## Features

- **Multiple Providers**: Support for 4 different LLM providers
- **Unified Interface**: Same API for all providers
- **Async Support**: Built-in async/await support with intelligent concurrency control
- **Batch Processing**: Efficiently process multiple prompts
- **Configuration Management**: Centralized configuration via `env.config`
- **Chat & Completion**: Support for both text generation and chat interfaces
- **Type Safety**: Full type hints throughout
- **Error Handling**: Graceful error handling with warnings

## Available Providers

### API-Based Providers (Cloud)
- **OpenAI** - GPT-3.5, GPT-4, and other OpenAI models
- **Google Gemini** - Gemini Pro and other Google AI models
- **Grok** - xAI's Grok models with OpenAI-compatible API

### Local Model Providers
- **Ollama** - Run models locally (Llama 2, Mistral, CodeLlama, Phi, etc.)

## Installation

### Core Dependencies
```bash
pip install asyncio
```

### Provider-Specific Dependencies

**For API-based providers:**
```bash
# OpenAI
pip install openai

# Google Gemini
pip install google-generativeai

# Grok (uses OpenAI SDK)
pip install openai
```

**For local models:**
```bash
# Ollama
pip install ollama

# Also install Ollama itself: https://ollama.ai/
```

## Configuration

1. Edit `env.config` and add your API keys:

```ini
# env.config
OPENAI_API_KEY=your_key_here
GEMINI_API_KEY=your_key_here
GROK_API_KEY=your_key_here
```

**Note:** Ollama runs locally and doesn't require an API key.

## Quick Start

### Simple Text Generation

```python
from providers.llm import generate_text

# Using local model (default)
text = generate_text('Explain quantum computing', provider='ollama')

# Using API provider
text = generate_text('Explain AI', provider='openai')
```

### Chat Completion

```python
from providers.llm import chat_completion

messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What is machine learning?"}
]

response = chat_completion(messages, provider='gemini')
print(response)
```

### Async Usage

```python
import asyncio
from providers.llm import generate_text_async

async def generate():
    text = await generate_text_async(
        'Write a poem about AI',
        provider='openai'
    )
    print(text)

asyncio.run(generate())
```

### Advanced Usage with Custom Configuration

```python
from providers.llm import LLMRouter

# Initialize router with custom config
config = {
    'model': 'gpt-4',
    'temperature': 0.8,
    'max_tokens': 500
}

router = LLMRouter('openai', config=config)

# Generate text
text = router.generate('Explain neural networks')

# Chat
messages = [{"role": "user", "content": "Hello!"}]
response = router.chat(messages)

# Update config at runtime
router.update_config(temperature=0.5)
```

### Batch Processing

```python
from providers.llm import LLMRouter

router = LLMRouter('ollama')

prompts = [
    'What is Python?',
    'What is JavaScript?',
    'What is Rust?'
]

# Batch generation (handles concurrency automatically)
results = router.generate_batch(prompts)

for prompt, result in zip(prompts, results):
    print(f"Q: {prompt}")
    print(f"A: {result}\n")
```

### Async Batch Processing

```python
import asyncio
from providers.llm import LLMRouter

async def batch_generate():
    router = LLMRouter('openai')
    
    prompts = [
        'Explain machine learning',
        'Explain deep learning',
        'Explain neural networks'
    ]
    
    results = await router.generate_batch_async(prompts)
    return results

results = asyncio.run(batch_generate())
```

## Provider-Specific Configuration

### OpenAI
```python
config = {
    'model': 'gpt-4',           # gpt-3.5-turbo, gpt-4, gpt-4-turbo
    'temperature': 0.7,
    'max_tokens': 1000,
    'top_p': 1.0,
    'frequency_penalty': 0.0,
    'presence_penalty': 0.0,
    'max_concurrent': 5
}
router = LLMRouter('openai', config)
```

### Google Gemini
```python
config = {
    'model': 'gemini-pro',      # gemini-pro, gemini-pro-vision
    'temperature': 0.7,
    'max_tokens': 1000,
    'top_p': 0.95,
    'top_k': 40,
    'max_concurrent': 5
}
router = LLMRouter('gemini', config)
```

### Grok (xAI)
```python
config = {
    'model': 'grok-beta',
    'temperature': 0.7,
    'max_tokens': 1000,
    'top_p': 1.0,
    'base_url': 'https://api.x.ai/v1',
    'max_concurrent': 5
}
router = LLMRouter('grok', config)
```

### Ollama
```python
config = {
    'model': 'llama2',          # llama2, mistral, codellama, phi, etc.
    'host': 'http://localhost:11434',
    'temperature': 0.7,
    'top_p': 0.9,
    'top_k': 40,
    'num_predict': 1000,
    'repeat_penalty': 1.1
}
router = LLMRouter('ollama', config)
```

## Ollama-Specific Features

### List Available Models
```python
from providers.llm import OllamaProvider

ollama = OllamaProvider()
models = ollama.list_models()
print("Available models:", models)
```

### Pull/Download Models
```python
from providers.llm import OllamaProvider

ollama = OllamaProvider()
ollama.pull_model('llama2')  # Download llama2 model
ollama.pull_model('mistral')  # Download mistral model
```

## Concurrency Control

The system automatically manages concurrency based on provider type:

- **API Providers**: Default 5 concurrent requests (configurable)
- **Local Models**: Sequential processing (1 at a time) to manage resources

You can customize concurrency per provider:

```python
config = {'max_concurrent': 10}
router = LLMRouter('openai', config)
```

## Error Handling

The system provides graceful error handling:

```python
from providers.llm import generate_text

try:
    text = generate_text('Explain AI', provider='openai')
except ValueError as e:
    print(f"Generation failed: {e}")
```

For batch processing, errors are caught and warned, returning empty strings for failed generations:

```python
# Failed generations return empty string with warning
results = router.generate_batch(['prompt1', 'prompt2'])
```

## Utility Functions

### List Available Providers
```python
from providers.llm import list_available_providers

providers = list_available_providers()
print(providers)
# Output: ['openai (API)', 'gemini (API)', 'grok (API)', 'ollama (Local)']
```

### Get Provider Information
```python
from providers.llm import get_provider_info

# Info for specific provider
info = get_provider_info('openai')
print(info)
# {'name': 'openai', 'is_local': False, 'max_concurrent': 5, ...}

# Info for all providers
all_info = get_provider_info()
```

### Check Model Information
```python
router = LLMRouter('openai', config={'model': 'gpt-4'})
model_info = router.get_model_info()
print(model_info)
# {'provider': 'openai', 'model': 'gpt-4', 'is_local': False, ...}
```

## Common Use Cases

### Minutes of Meeting Generation
```python
from providers.llm import generate_text

conversation = """
User: We need to finalize the Q4 roadmap.
Manager: Let's prioritize the API improvements.
Developer: I can complete that by December 15th.
"""

system_prompt = """
Analyze the conversation and provide a comprehensive summary in bullet points.
Include action items and deadlines.
"""

summary = generate_text(
    conversation,
    system_prompt=system_prompt,
    provider='ollama',
    model='llama2'
)

print(summary)
```

### Code Generation
```python
from providers.llm import generate_text

prompt = "Write a Python function to calculate Fibonacci numbers"

code = generate_text(
    prompt,
    provider='openai',
    config={'model': 'gpt-4', 'temperature': 0.2}
)

print(code)
```

### Multi-Turn Conversation
```python
from providers.llm import LLMRouter

router = LLMRouter('gemini')

# Build conversation
messages = [
    {"role": "system", "content": "You are a helpful coding assistant."},
    {"role": "user", "content": "How do I create a REST API in Python?"},
]

response1 = router.chat(messages)
print("Assistant:", response1)

# Continue conversation
messages.append({"role": "assistant", "content": response1})
messages.append({"role": "user", "content": "Can you show me an example with FastAPI?"})

response2 = router.chat(messages)
print("Assistant:", response2)
```

## Architecture

```
providers/llm/
├── __init__.py          # Public API exports
├── base.py              # Abstract base class
├── config.py            # Configuration management
├── router.py            # Main router and orchestrator
├── openai.py            # OpenAI provider
├── gemini.py            # Google Gemini provider
├── grok.py              # Grok (xAI) provider
└── ollama.py            # Ollama local provider
```

## Performance Considerations

- **Local Models**: First run may download models (can be large). Subsequent runs are faster.
- **API Providers**: Network latency affects speed. Batch processing with concurrency helps.
- **Ollama**: Requires Ollama service running. Check with `ollama list`.
- **Memory**: Local models require significant RAM. Monitor resource usage.

## Troubleshooting

### API Key Not Found Warning
```
Solution: Add your API key to env.config or set as environment variable
```

### Import Error for Provider SDK
```
Solution: Install the required package (see Installation section)
```

### Ollama Connection Error
```
Solution:
1. Install Ollama from https://ollama.ai/
2. Start Ollama: `ollama serve`
3. Pull a model: `ollama pull llama2`
4. Verify it's running: `ollama list`
```

### Slow Generation with Ollama
```
Solution:
- Ensure Ollama is using GPU (if available)
- Use smaller models (e.g., 'phi' instead of 'llama2:70b')
- Reduce num_predict in config
```

## Integration with Existing Code

Replace the old `summary.py` approach:

```python
# Old approach
from summary import get_minutes_of_meeting
summary = get_minutes_of_meeting(conversation)

# New standardized approach
from providers.llm import generate_text

system_prompt = """
Analyze the conversation and provide comprehensive summary in bullet points.
Stick to facts and ensure all points are clear and thorough.
"""

summary = generate_text(
    conversation,
    system_prompt=system_prompt,
    provider='ollama',
    config={'model': 'llama2'}
)
```

## License

See main project LICENSE file.

