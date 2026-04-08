from app.providers.speech.base import BaseSpeechProvider
from app.models import SystemConfig


def get_speech_provider() -> BaseSpeechProvider:
    """Return the configured speech provider instance."""
    provider_name = SystemConfig.get("speech_provider", "deepgram").lower()

    if provider_name == "deepgram":
        from app.providers.speech.deepgram_provider import DeepgramProvider
        api_key = SystemConfig.get("deepgram_api_key", "")
        return DeepgramProvider(api_key=api_key)

    elif provider_name == "assemblyai":
        from app.providers.speech.assemblyai_provider import AssemblyAIProvider
        api_key = SystemConfig.get("assemblyai_api_key", "")
        return AssemblyAIProvider(api_key=api_key)

    elif provider_name == "sarvam":
        from app.providers.speech.sarvam_provider import SarvamProvider
        api_key = SystemConfig.get("sarvam_api_key", "")
        return SarvamProvider(api_key=api_key)

    elif provider_name == "elevenlabs":
        from app.providers.speech.elevenlabs_provider import ElevenLabsProvider
        api_key = SystemConfig.get("elevenlabs_api_key", "")
        return ElevenLabsProvider(api_key=api_key)

    else:
        raise ValueError(f"Unknown speech provider: {provider_name!r}")
