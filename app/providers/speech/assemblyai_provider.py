from app.providers.speech.base import BaseSpeechProvider


class AssemblyAIProvider(BaseSpeechProvider):
    """Speech-to-text via AssemblyAI."""

    provider_name = "assemblyai"

    def transcribe_file(self, audio_path: str) -> str:
        try:
            import assemblyai as aai
        except ImportError as exc:
            raise RuntimeError("assemblyai is not installed. Run: pip install assemblyai") from exc

        if not self.validate_key():
            raise RuntimeError("AssemblyAI API key is not configured.")

        aai.settings.api_key = self.api_key

        config = aai.TranscriptionConfig(
            speech_model=aai.SpeechModel.best,
            punctuate=True,
            format_text=True,
        )
        transcriber = aai.Transcriber(config=config)
        transcript = transcriber.transcribe(audio_path)

        if transcript.status == aai.TranscriptStatus.error:
            raise RuntimeError(f"AssemblyAI transcription failed: {transcript.error}")

        return (transcript.text or "").strip()
