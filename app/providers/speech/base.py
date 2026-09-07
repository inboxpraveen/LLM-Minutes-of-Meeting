import math
import os
import struct
import tempfile
import wave
from abc import ABC, abstractmethod
from collections.abc import Iterable

_TRUE = {"1", "true", "yes", "on"}


class BaseSpeechProvider(ABC):
    """A speech-to-text backend.

    `transcribe` returns plain text, speaker-labelled as `[Speaker 0]: …` when
    the provider supports diarization and it is enabled.
    """

    name = "base"
    label = "Speech provider"

    def __init__(self, config: dict):
        self.config = config
        self.language = (config.get("speech_language") or "").strip()
        self.diarize = str(config.get("diarization_enabled", "true")).strip().lower() in _TRUE

    @abstractmethod
    def transcribe(self, audio_path: str) -> str:
        ...

    def check(self) -> str:
        """Send a one-second sample to confirm credentials and connectivity."""
        with tempfile.TemporaryDirectory() as tmp:
            sample = os.path.join(tmp, "sample.wav")
            write_test_tone(sample)
            self.transcribe(sample)
        return f"{self.label} accepted the request."

    def _require_key(self, key: str, human_name: str) -> str:
        value = (self.config.get(key) or "").strip()
        if not value:
            raise RuntimeError(f"No {human_name} API key configured. Add one in Settings → Speech provider.")
        return value

    def _setting(self, key: str, default: str = "") -> str:
        return (self.config.get(key) or "").strip() or default


def merge_turns(segments: Iterable[tuple[object | None, str]]) -> str:
    """Collapse per-word or per-utterance results into readable speaker turns.

    Consecutive turns by one speaker are joined. When only one speaker is
    present the labels are dropped entirely.
    """
    collapsed: list[tuple[object | None, list[str]]] = []
    for speaker, text in segments:
        text = (text or "").strip()
        if not text:
            continue
        if collapsed and collapsed[-1][0] == speaker:
            collapsed[-1][1].append(text)
        else:
            collapsed.append((speaker, [text]))

    if not collapsed:
        return ""

    speakers = {speaker for speaker, _ in collapsed if speaker is not None}
    if len(speakers) < 2:
        return " ".join(" ".join(parts) for _, parts in collapsed)
    return "\n\n".join(f"[{_label(speaker)}]: {' '.join(parts)}" for speaker, parts in collapsed)


def _label(speaker) -> str:
    if speaker is None:
        return "Unknown"
    return f"Speaker {speaker}" if isinstance(speaker, int) else str(speaker)


def write_test_tone(path: str, seconds: float = 1.0, rate: int = 16000) -> None:
    """A quiet tone: enough for a provider to accept the request, no words to bill."""
    frames = b"".join(
        struct.pack("<h", int(1200 * math.sin(2 * math.pi * 440 * n / rate)))
        for n in range(int(rate * seconds))
    )
    with wave.open(path, "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(rate)
        handle.writeframes(frames)
