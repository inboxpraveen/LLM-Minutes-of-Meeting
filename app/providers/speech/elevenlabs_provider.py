from app.providers.speech.base import BaseSpeechProvider, merge_turns


class ElevenLabsProvider(BaseSpeechProvider):
    name = "elevenlabs"
    label = "ElevenLabs Scribe"

    def transcribe(self, audio_path: str) -> str:
        from elevenlabs import ElevenLabs

        client = ElevenLabs(api_key=self._require_key("elevenlabs_api_key", "ElevenLabs"))
        options = {
            "model_id": self._setting("elevenlabs_model", "scribe_v2"),
            "diarize": self.diarize,
            "timestamps_granularity": "word",
        }
        if self.language:
            options["language_code"] = self.language

        with open(audio_path, "rb") as handle:
            response = client.speech_to_text.convert(file=handle, **options)
        return _extract(response)


def _extract(response) -> str:
    transcripts = getattr(response, "transcripts", None)
    if transcripts:
        return _merge_channels(transcripts)

    words = getattr(response, "words", None)
    if words:
        text = merge_turns((getattr(w, "speaker_id", None), w.text) for w in words if _is_word(w))
        if text:
            return text

    text = getattr(response, "text", None)
    if text is None and isinstance(response, dict):
        text = response.get("text")
    return (text or "").strip()


def _merge_channels(transcripts) -> str:
    """Stereo conference recordings arrive as one transcript per channel."""
    words = [
        {"speaker": f"Speaker {t.channel_index}", "text": w.text, "start": getattr(w, "start", 0.0) or 0.0}
        for t in transcripts
        for w in (t.words or [])
        if _is_word(w)
    ]
    if not words:
        return " ".join(t.text for t in transcripts if t.text).strip()

    words.sort(key=lambda w: w["start"])
    return merge_turns((w["speaker"], w["text"]) for w in words)


def _is_word(word) -> bool:
    return getattr(word, "type", "word") == "word"
