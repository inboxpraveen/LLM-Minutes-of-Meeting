"""
Example usage of the speech transcription providers.

This file demonstrates various ways to use the speech provider system.
Run this file to test your setup.
"""

import asyncio
from pathlib import Path


def example_basic_usage():
    """Example: Basic usage with default provider."""
    print("=" * 60)
    print("Example 1: Basic Usage")
    print("=" * 60)
    
    from providers.speech import get_transcription
    
    # Using faster_whisper (default, local model, no API key needed)
    audio_path = "path/to/your/audio.wav"
    
    # Check if file exists (for demo purposes)
    if not Path(audio_path).exists():
        print(f"⚠️  Audio file not found: {audio_path}")
        print("   Please provide a valid audio file path.")
        return
    
    try:
        text = get_transcription(audio_path, provider='faster_whisper')
        print(f"✅ Transcription: {text}")
    except Exception as e:
        print(f"❌ Error: {e}")


def example_api_provider():
    """Example: Using an API-based provider."""
    print("\n" + "=" * 60)
    print("Example 2: API Provider (Deepgram)")
    print("=" * 60)
    
    from providers.speech import get_transcription
    
    audio_path = "path/to/your/audio.wav"
    
    if not Path(audio_path).exists():
        print(f"⚠️  Audio file not found: {audio_path}")
        return
    
    try:
        # Make sure DEEPGRAM_API_KEY is set in env.config
        text = get_transcription(audio_path, provider='deepgram')
        print(f"✅ Transcription: {text}")
    except ValueError as e:
        print(f"❌ Error: {e}")
        print("   Make sure to set DEEPGRAM_API_KEY in env.config")


def example_custom_config():
    """Example: Using custom configuration."""
    print("\n" + "=" * 60)
    print("Example 3: Custom Configuration")
    print("=" * 60)
    
    from providers.speech import SpeechTranscriptionRouter
    
    # Configure Faster Whisper with custom settings
    config = {
        'model_size': 'base',
        'device': 'auto',
        'language': 'en',
        'beam_size': 5
    }
    
    router = SpeechTranscriptionRouter('faster_whisper', config=config)
    
    print(f"✅ Router created: {router}")
    print(f"   Provider info: {router.get_provider_info()}")
    
    # Update config at runtime
    router.update_config(language='es')
    print(f"   Updated config: {router.get_config()}")


async def example_async_usage():
    """Example: Async transcription."""
    print("\n" + "=" * 60)
    print("Example 4: Async Transcription")
    print("=" * 60)
    
    from providers.speech import get_transcription_async
    
    audio_path = "path/to/your/audio.wav"
    
    if not Path(audio_path).exists():
        print(f"⚠️  Audio file not found: {audio_path}")
        return
    
    try:
        text = await get_transcription_async(audio_path, provider='faster_whisper')
        print(f"✅ Async transcription: {text}")
    except Exception as e:
        print(f"❌ Error: {e}")


def example_batch_processing():
    """Example: Batch processing multiple files."""
    print("\n" + "=" * 60)
    print("Example 5: Batch Processing")
    print("=" * 60)
    
    from providers.speech import get_batch_transcriptions
    
    audio_files = [
        "path/to/audio1.wav",
        "path/to/audio2.wav",
        "path/to/audio3.wav"
    ]
    
    # Check if files exist
    existing_files = [f for f in audio_files if Path(f).exists()]
    
    if not existing_files:
        print(f"⚠️  No audio files found in the list")
        print("   Please provide valid audio file paths.")
        return
    
    try:
        print(f"📝 Processing {len(existing_files)} files...")
        results = get_batch_transcriptions(existing_files, provider='faster_whisper')
        
        for file, text in zip(existing_files, results):
            print(f"✅ {Path(file).name}: {text[:100]}...")
    except Exception as e:
        print(f"❌ Error: {e}")


async def example_async_batch():
    """Example: Async batch processing."""
    print("\n" + "=" * 60)
    print("Example 6: Async Batch Processing")
    print("=" * 60)
    
    from providers.speech import SpeechTranscriptionRouter
    
    audio_files = [
        "path/to/audio1.wav",
        "path/to/audio2.wav",
    ]
    
    existing_files = [f for f in audio_files if Path(f).exists()]
    
    if not existing_files:
        print(f"⚠️  No audio files found")
        return
    
    try:
        router = SpeechTranscriptionRouter('faster_whisper')
        results = await router.transcribe_batch_async(existing_files)
        
        print(f"✅ Processed {len(results)} files")
        for file, text in zip(existing_files, results):
            print(f"   {Path(file).name}: {text[:100]}...")
    except Exception as e:
        print(f"❌ Error: {e}")


def example_list_providers():
    """Example: List available providers."""
    print("\n" + "=" * 60)
    print("Example 7: List Available Providers")
    print("=" * 60)
    
    from providers.speech import list_available_providers, get_provider_info
    
    providers = list_available_providers()
    print("📋 Available providers:")
    for provider in providers:
        print(f"   • {provider}")
    
    print("\n📊 Provider details:")
    all_info = get_provider_info()
    for name, info in all_info.items():
        provider_type = "Local" if info['is_local'] else "API"
        requires_key = "Yes" if info['requires_api_key'] else "No"
        print(f"   • {name:15} - Type: {provider_type:5} | API Key: {requires_key:3} | Max Concurrent: {info['max_concurrent']}")


def example_error_handling():
    """Example: Proper error handling."""
    print("\n" + "=" * 60)
    print("Example 8: Error Handling")
    print("=" * 60)
    
    from providers.speech import get_transcription
    
    try:
        # Try with non-existent file
        text = get_transcription("nonexistent.wav", provider='faster_whisper')
    except FileNotFoundError as e:
        print(f"✅ Caught FileNotFoundError: {e}")
    
    try:
        # Try with invalid provider
        text = get_transcription("audio.wav", provider='invalid_provider')
    except ValueError as e:
        print(f"✅ Caught ValueError: {e}")
    
    try:
        # Try API provider without key
        text = get_transcription("audio.wav", provider='deepgram')
    except ValueError as e:
        print(f"✅ Caught ValueError (missing API key): {e}")


def main():
    """Run all examples."""
    print("\n" + "🎙️  Speech Provider System - Examples" + "\n")
    
    # Run synchronous examples
    example_basic_usage()
    example_api_provider()
    example_custom_config()
    example_batch_processing()
    example_list_providers()
    example_error_handling()
    
    # Run async examples
    print("\n" + "⏳ Running async examples...")
    asyncio.run(example_async_usage())
    asyncio.run(example_async_batch())
    
    print("\n" + "=" * 60)
    print("✅ All examples completed!")
    print("=" * 60)
    print("\n📚 For more information, see providers/speech/README.md")


if __name__ == "__main__":
    main()

