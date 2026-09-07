from app.providers.speech.assemblyai_provider import AssemblyAIProvider
from app.providers.speech.base import BaseSpeechProvider
from app.providers.speech.deepgram_provider import DeepgramProvider
from app.providers.speech.elevenlabs_provider import ElevenLabsProvider
from app.providers.speech.local_whisper_provider import LocalWhisperProvider
from app.providers.speech.openai_compatible_provider import OpenAICompatibleSpeechProvider
from app.providers.speech.sarvam_provider import SarvamProvider

PROVIDERS: dict[str, type[BaseSpeechProvider]] = {
    p.name: p
    for p in (
        DeepgramProvider,
        AssemblyAIProvider,
        ElevenLabsProvider,
        SarvamProvider,
        OpenAICompatibleSpeechProvider,
        LocalWhisperProvider,
    )
}


def get_speech_provider(config: dict) -> BaseSpeechProvider:
    name = (config.get("speech_provider") or "deepgram").strip().lower()
    provider = PROVIDERS.get(name)
    if provider is None:
        raise RuntimeError(f"Unknown speech provider {name!r}. Choose one in Settings → Speech provider.")
    return provider(config)
