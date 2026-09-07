from app.providers.speech.base import BaseSpeechProvider, merge_turns


class AssemblyAIProvider(BaseSpeechProvider):
    name = "assemblyai"
    label = "AssemblyAI"

    def transcribe(self, audio_path: str) -> str:
        import assemblyai as aai

        aai.settings.api_key = self._require_key("assemblyai_api_key", "AssemblyAI")

        options = {
            "speech_model": self._setting("assemblyai_model", "universal"),
            "punctuate": True,
            "format_text": True,
            "speaker_labels": self.diarize,
        }
        if self.language:
            options["language_code"] = self.language
        else:
            options["language_detection"] = True

        transcript = aai.Transcriber(config=aai.TranscriptionConfig(**options)).transcribe(audio_path)
        if transcript.status == aai.TranscriptStatus.error:
            raise RuntimeError(f"AssemblyAI could not transcribe the recording: {transcript.error}")

        if self.diarize and transcript.utterances:
            text = merge_turns((u.speaker, u.text) for u in transcript.utterances)
            if text:
                return text
        return (transcript.text or "").strip()
