import os
import tempfile

from openai import OpenAI

from app.providers.speech.base import BaseSpeechProvider
from app.utils.audio import split_audio

UPLOAD_LIMIT_BYTES = 24 * 1024 * 1024  # OpenAI and Groq both reject uploads above 25 MB


class OpenAICompatibleSpeechProvider(BaseSpeechProvider):
    """Any /v1/audio/transcriptions endpoint: OpenAI, Groq, Speaches, LocalAI.

    Long recordings are split into parts so the upload limit never applies.
    Diarization is not part of this API, so transcripts have no speaker labels.
    """

    name = "openai_compatible"
    label = "OpenAI-compatible endpoint"

    def transcribe(self, audio_path: str) -> str:
        base_url = self._setting("stt_base_url")
        if not base_url:
            raise RuntimeError("No STT base URL configured. Set one in Settings → Speech provider.")

        client = OpenAI(
            base_url=base_url,
            api_key=self._setting("stt_api_key") or "not-needed",
            timeout=1800,
            max_retries=3,
        )
        model = self._setting("stt_model", "whisper-large-v3-turbo")

        if os.path.getsize(audio_path) <= UPLOAD_LIMIT_BYTES:
            return self._send(client, model, audio_path)

        chunk_seconds = int(self._setting("stt_chunk_seconds", "600") or 600)
        with tempfile.TemporaryDirectory() as tmp:
            parts = split_audio(audio_path, chunk_seconds, tmp)
            return " ".join(filter(None, (self._send(client, model, part) for part in parts))).strip()

    def _send(self, client: OpenAI, model: str, path: str) -> str:
        options = {"language": self.language} if self.language else {}
        with open(path, "rb") as handle:
            result = client.audio.transcriptions.create(
                file=handle, model=model, response_format="text", **options
            )
        return (result if isinstance(result, str) else getattr(result, "text", "")).strip()
