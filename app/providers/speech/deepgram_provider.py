from app.providers.speech.base import BaseSpeechProvider


class DeepgramProvider(BaseSpeechProvider):
    """
    Speech-to-text via Deepgram Nova-3.

    Uses the current deepgram-sdk v3 API:
        client.listen.v1.media.transcribe_file(request=bytes, **kwargs)

    Transcript extraction priority:
      1. Diarized utterances  → speaker-labelled blocks  (best for MoM)
      2. Paragraph transcript → readable formatted text
      3. Raw transcript       → plain string fallback
    """

    provider_name = "deepgram"

    def transcribe_file(self, audio_path: str) -> str:
        try:
            from deepgram import DeepgramClient
        except ImportError as exc:
            raise RuntimeError(
                "deepgram-sdk is not installed. Run: pip install deepgram-sdk"
            ) from exc

        if not self.validate_key():
            raise RuntimeError("Deepgram API key is not configured.")

        client = DeepgramClient(api_key=self.api_key)

        with open(audio_path, "rb") as f:
            audio_bytes = f.read()

        # Current SDK: keyword args inline, no PrerecordedOptions / FileSource needed
        response = client.listen.v1.media.transcribe_file(
            request=audio_bytes,
            model="nova-3",
            smart_format=True,
            punctuate=True,
            paragraphs=True,
            diarize=True,       # adds speaker IDs to every word
            utterances=True,    # groups words into speaker turns (requires diarize)
        )

        return self._extract_transcript(response)

    # ── Response parsing ────────────────────────────────────────────────────

    @staticmethod
    def _extract_transcript(response) -> str:
        results = _get(response, "results")
        if results is None:
            raise RuntimeError("Deepgram response is missing 'results'")

        # 1. Diarized utterances — speaker-labelled blocks
        utterances = _get(results, "utterances")
        if utterances:
            transcript = DeepgramProvider._build_diarized_transcript(utterances)
            if transcript:
                return transcript

        # 2. Paragraph-formatted transcript (nicer sentence breaks)
        try:
            para_text = _get(_get(_get(results, "channels")[0], "alternatives")[0].paragraphs, "transcript")
            if para_text:
                return para_text.strip()
        except (AttributeError, IndexError, TypeError, KeyError):
            pass

        # 3. Raw transcript fallback
        try:
            channels = _get(results, "channels")
            raw = _get(_get(channels[0], "alternatives")[0], "transcript")
            if raw:
                return raw.strip()
        except (AttributeError, IndexError, TypeError, KeyError):
            pass

        raise RuntimeError("Could not extract a transcript from the Deepgram response")

    @staticmethod
    def _build_diarized_transcript(utterances) -> str:
        """
        Collapse diarized utterances into labelled speaker turns.

        Deepgram's utterances already arrive in time order and carry a
        `speaker` integer (0, 1, 2 …).  Consecutive turns by the same
        speaker are joined so the LLM sees natural paragraphs.

        Output format (multiple speakers):
            [Speaker 0]: Let's get started everyone.
            [Speaker 1]: Thanks, here are the numbers.

        Output format (single speaker — no label clutter):
            Let's get started. Here are the numbers.
        """
        segments: list[tuple[int | None, list[str]]] = []
        current_speaker: int | None = None
        current_parts: list[str] = []

        for utt in utterances:
            speaker = _get(utt, "speaker")
            text = (_get(utt, "transcript") or "").strip()
            if not text:
                continue
            if speaker != current_speaker:
                if current_parts:
                    segments.append((current_speaker, current_parts))
                current_speaker = speaker
                current_parts = [text]
            else:
                current_parts.append(text)

        if current_parts:
            segments.append((current_speaker, current_parts))

        if not segments:
            return ""

        unique_speakers = {s for s, _ in segments if s is not None}
        if len(unique_speakers) > 1:
            return "\n\n".join(
                f"[Speaker {spk}]: {' '.join(parts)}"
                for spk, parts in segments
            )
        return " ".join(" ".join(parts) for _, parts in segments)


# ── Helpers ─────────────────────────────────────────────────────────────────

def _get(obj, key):
    """
    Unified attribute / dict accessor.
    Deepgram SDK objects support both styles across versions.
    """
    if obj is None:
        return None
    if hasattr(obj, key):
        return getattr(obj, key)
    if isinstance(obj, dict):
        return obj.get(key)
    return None
