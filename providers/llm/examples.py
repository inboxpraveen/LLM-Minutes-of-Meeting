"""
Example usage of the LLM providers.

This file demonstrates various ways to use the LLM provider system.
Run this file to test your setup.
"""

import asyncio


def example_basic_generation():
    """Example: Basic text generation."""
    print("=" * 60)
    print("Example 1: Basic Text Generation")
    print("=" * 60)
    
    from providers.llm import generate_text
    
    # Using local model (default)
    try:
        text = generate_text(
            'Explain quantum computing in simple terms',
            provider='ollama'
        )
        print(f"✅ Generated text: {text[:200]}...")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("   Make sure Ollama is running: ollama serve")


def example_api_provider():
    """Example: Using an API-based provider."""
    print("\n" + "=" * 60)
    print("Example 2: API Provider (OpenAI)")
    print("=" * 60)
    
    from providers.llm import generate_text
    
    try:
        # Make sure OPENAI_API_KEY is set in env.config
        text = generate_text(
            'What is artificial intelligence?',
            provider='openai'
        )
        print(f"✅ Generated text: {text[:200]}...")
    except ValueError as e:
        print(f"❌ Error: {e}")
        print("   Make sure to set OPENAI_API_KEY in env.config")


def example_chat_completion():
    """Example: Chat completion."""
    print("\n" + "=" * 60)
    print("Example 3: Chat Completion")
    print("=" * 60)
    
    from providers.llm import chat_completion
    
    messages = [
        {"role": "system", "content": "You are a helpful coding assistant."},
        {"role": "user", "content": "How do I create a REST API in Python?"}
    ]
    
    try:
        response = chat_completion(messages, provider='ollama')
        print(f"✅ Chat response: {response[:200]}...")
    except Exception as e:
        print(f"❌ Error: {e}")


def example_custom_config():
    """Example: Using custom configuration."""
    print("\n" + "=" * 60)
    print("Example 4: Custom Configuration")
    print("=" * 60)
    
    from providers.llm import LLMRouter
    
    # Configure with custom settings
    config = {
        'model': 'llama2',
        'temperature': 0.8,
        'num_predict': 200
    }
    
    router = LLMRouter('ollama', config=config)
    
    print(f"✅ Router created: {router}")
    print(f"   Provider info: {router.get_provider_info()}")
    print(f"   Model info: {router.get_model_info()}")
    
    # Update config at runtime
    router.update_config(temperature=0.5)
    print(f"   Updated config: {router.get_config()}")


async def example_async_generation():
    """Example: Async text generation."""
    print("\n" + "=" * 60)
    print("Example 5: Async Text Generation")
    print("=" * 60)
    
    from providers.llm import generate_text_async
    
    try:
        text = await generate_text_async(
            'Write a haiku about programming',
            provider='ollama'
        )
        print(f"✅ Async generated: {text}")
    except Exception as e:
        print(f"❌ Error: {e}")


def example_batch_processing():
    """Example: Batch processing multiple prompts."""
    print("\n" + "=" * 60)
    print("Example 6: Batch Processing")
    print("=" * 60)
    
    from providers.llm import LLMRouter
    
    prompts = [
        'What is Python?',
        'What is JavaScript?',
        'What is Rust?'
    ]
    
    try:
        router = LLMRouter('ollama')
        print(f"📝 Processing {len(prompts)} prompts...")
        
        results = router.generate_batch(
            prompts,
            system_prompt="Answer in one sentence."
        )
        
        for prompt, result in zip(prompts, results):
            print(f"✅ Q: {prompt}")
            print(f"   A: {result[:100]}...")
            print()
    except Exception as e:
        print(f"❌ Error: {e}")


async def example_async_batch():
    """Example: Async batch processing."""
    print("\n" + "=" * 60)
    print("Example 7: Async Batch Processing")
    print("=" * 60)
    
    from providers.llm import LLMRouter
    
    prompts = [
        'Explain machine learning',
        'Explain deep learning'
    ]
    
    try:
        router = LLMRouter('ollama')
        results = await router.generate_batch_async(
            prompts,
            system_prompt="Explain in 2 sentences."
        )
        
        print(f"✅ Processed {len(results)} prompts")
        for i, result in enumerate(results):
            print(f"   Result {i+1}: {result[:100]}...")
    except Exception as e:
        print(f"❌ Error: {e}")


def example_multi_turn_chat():
    """Example: Multi-turn conversation."""
    print("\n" + "=" * 60)
    print("Example 8: Multi-Turn Conversation")
    print("=" * 60)
    
    from providers.llm import LLMRouter
    
    try:
        router = LLMRouter('ollama')
        
        # Start conversation
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is Python?"}
        ]
        
        response1 = router.chat(messages)
        print(f"✅ Turn 1:")
        print(f"   User: What is Python?")
        print(f"   Assistant: {response1[:150]}...")
        
        # Continue conversation
        messages.append({"role": "assistant", "content": response1})
        messages.append({"role": "user", "content": "What are its main uses?"})
        
        response2 = router.chat(messages)
        print(f"\n✅ Turn 2:")
        print(f"   User: What are its main uses?")
        print(f"   Assistant: {response2[:150]}...")
        
    except Exception as e:
        print(f"❌ Error: {e}")


def example_list_providers():
    """Example: List available providers."""
    print("\n" + "=" * 60)
    print("Example 9: List Available Providers")
    print("=" * 60)
    
    from providers.llm import list_available_providers, get_provider_info
    
    providers = list_available_providers()
    print("📋 Available providers:")
    for provider in providers:
        print(f"   • {provider}")
    
    print("\n📊 Provider details:")
    all_info = get_provider_info()
    for name, info in all_info.items():
        provider_type = "Local" if info['is_local'] else "API"
        requires_key = "Yes" if info['requires_api_key'] else "No"
        streaming = "Yes" if info['supports_streaming'] else "No"
        print(f"   • {name:15} - Type: {provider_type:5} | API Key: {requires_key:3} | Streaming: {streaming:3} | Max Concurrent: {info['max_concurrent']}")


def example_ollama_features():
    """Example: Ollama-specific features."""
    print("\n" + "=" * 60)
    print("Example 10: Ollama-Specific Features")
    print("=" * 60)
    
    from providers.llm import OllamaProvider
    
    try:
        ollama = OllamaProvider()
        
        # List available models
        models = ollama.list_models()
        if models:
            print(f"✅ Available Ollama models:")
            for model in models[:5]:  # Show first 5
                print(f"   • {model}")
        else:
            print("⚠️  No models found. Pull a model with: ollama pull llama2")
        
        # Example: Pull a model (commented out to avoid long download)
        # print("\n📥 Pulling model 'phi'...")
        # ollama.pull_model('phi')
        
    except Exception as e:
        print(f"❌ Error: {e}")


def example_minutes_of_meeting():
    """Example: Generate minutes of meeting from conversation."""
    print("\n" + "=" * 60)
    print("Example 11: Minutes of Meeting Generation")
    print("=" * 60)
    
    from providers.llm import generate_text
    
    conversation = """
    Manager: Good morning team. Let's discuss the Q4 roadmap.
    Developer: I think we should prioritize the API improvements.
    Designer: I agree, and we also need to update the UI components.
    Manager: Sounds good. Developer, can you handle the API work?
    Developer: Yes, I can complete that by December 15th.
    Manager: Great. Designer, you can start on the UI after that?
    Designer: Yes, I'll need about 2 weeks for the complete redesign.
    Manager: Perfect. Let's reconvene next Monday to track progress.
    """
    
    system_prompt = """
    Analyze the conversation and provide a comprehensive summary with:
    1. Main discussion points
    2. Decisions made
    3. Action items with assignees and deadlines
    Format as bullet points.
    """
    
    try:
        summary = generate_text(
            conversation,
            system_prompt=system_prompt,
            provider='ollama'
        )
        
        print("✅ Meeting Summary:")
        print(summary)
        
    except Exception as e:
        print(f"❌ Error: {e}")


def example_error_handling():
    """Example: Proper error handling."""
    print("\n" + "=" * 60)
    print("Example 12: Error Handling")
    print("=" * 60)
    
    from providers.llm import generate_text
    
    try:
        # Try with invalid provider
        text = generate_text("Hello", provider='invalid_provider')
    except ValueError as e:
        print(f"✅ Caught ValueError: {e}")
    
    try:
        # Try API provider without key
        text = generate_text("Hello", provider='openai')
    except ValueError as e:
        print(f"✅ Caught ValueError (missing API key): {e}")


def main():
    """Run all examples."""
    print("\n" + "🤖 LLM Provider System - Examples" + "\n")
    
    # Run synchronous examples
    example_basic_generation()
    example_api_provider()
    example_chat_completion()
    example_custom_config()
    example_batch_processing()
    example_multi_turn_chat()
    example_list_providers()
    example_ollama_features()
    example_minutes_of_meeting()
    example_error_handling()
    
    # Run async examples
    print("\n" + "⏳ Running async examples...")
    asyncio.run(example_async_generation())
    asyncio.run(example_async_batch())
    
    print("\n" + "=" * 60)
    print("✅ All examples completed!")
    print("=" * 60)
    print("\n📚 For more information, see providers/llm/README.md")


if __name__ == "__main__":
    main()

