import logging

from app.paths import models_dir
from app.providers.speech.base import BaseSpeechProvider

log = logging.getLogger("mom.whisper")
_MODELS: dict[tuple, object] = {}

MISSING = (
    "Local Whisper is not installed in this image. Rebuild with "
    "WITH_LOCAL_WHISPER=true, or run: pip install -r requirements-local.txt"
)


class LocalWhisperProvider(BaseSpeechProvider):
    """faster-whisper running on this machine. No API key and no network calls,
    apart from downloading the model once. Speaker diarization is not available."""

    name = "local_whisper"
    label = "Local Whisper"

    def transcribe(self, audio_path: str) -> str:
        model = self._load()
        segments, _info = model.transcribe(
            audio_path,
            beam_size=5,
            vad_filter=True,
            language=self.language or None,
        )
        return " ".join(segment.text.strip() for segment in segments).strip()

    def check(self) -> str:
        _import_model_class()
        size = self._setting("whisper_model", "base")
        cached = (models_dir() / f"models--Systran--faster-whisper-{size}").exists()
        return (
            f"Local Whisper is available. Model '{size}' is "
            + ("cached and ready." if cached else "downloaded on the first transcription.")
        )

    def _load(self):
        key = (
            self._setting("whisper_model", "base"),
            self._setting("whisper_device", "auto"),
            self._setting("whisper_compute_type", "int8"),
        )
        if key not in _MODELS:
            log.info("Loading Whisper model %s on %s (%s)", *key)
            _MODELS.clear()
            _MODELS[key] = _import_model_class()(
                key[0], device=key[1], compute_type=key[2], download_root=str(models_dir())
            )
        return _MODELS[key]


def _import_model_class():
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise RuntimeError(MISSING) from exc
    return WhisperModel
