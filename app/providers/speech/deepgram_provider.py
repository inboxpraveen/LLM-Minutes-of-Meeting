from app.providers.speech.base import BaseSpeechProvider, merge_turns


class DeepgramProvider(BaseSpeechProvider):
    name = "deepgram"
    label = "Deepgram"

    def transcribe(self, audio_path: str) -> str:
        from deepgram import DeepgramClient

        client = DeepgramClient(api_key=self._require_key("deepgram_api_key", "Deepgram"))
        with open(audio_path, "rb") as handle:
            audio = handle.read()

        options = {
            "model": self._setting("deepgram_model", "nova-3"),
            "smart_format": True,
            "punctuate": True,
            "paragraphs": True,
            "diarize": self.diarize,
            "utterances": self.diarize,
        }
        if self.language:
            options["language"] = self.language

        return _extract(client.listen.v1.media.transcribe_file(request=audio, **options))


def _extract(response) -> str:
    results = _get(response, "results")
    if results is None:
        raise RuntimeError("Deepgram returned a response without results.")

    utterances = _get(results, "utterances")
    if utterances:
        text = merge_turns((_get(u, "speaker"), _get(u, "transcript")) for u in utterances)
        if text:
            return text

    alternative = _first_alternative(results)
    if alternative is not None:
        paragraphs = _get(alternative, "paragraphs")
        formatted = _get(paragraphs, "transcript") if paragraphs is not None else None
        if formatted:
            return formatted.strip()
        raw = _get(alternative, "transcript")
        if raw:
            return raw.strip()
    return ""


def _first_alternative(results):
    channels = _get(results, "channels") or []
    alternatives = _get(channels[0], "alternatives") if channels else None
    return alternatives[0] if alternatives else None


def _get(obj, key):
    """Deepgram models expose attributes; raw dicts appear in some responses."""
    if obj is None:
        return None
    if isinstance(obj, dict):
        return obj.get(key)
    return getattr(obj, key, None)
