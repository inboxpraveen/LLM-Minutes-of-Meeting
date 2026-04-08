from abc import ABC, abstractmethod


class BaseSpeechProvider(ABC):
    """Abstract base for all speech-to-text providers."""

    provider_name: str = "base"

    def __init__(self, api_key: str):
        self.api_key = api_key

    @abstractmethod
    def transcribe_file(self, audio_path: str) -> str:
        """
        Transcribe a local audio file.

        Args:
            audio_path: Absolute path to the audio file (WAV/MP3/etc.)

        Returns:
            The full transcript as a plain string.

        Raises:
            RuntimeError: If transcription fails.
        """
        ...

    def validate_key(self) -> bool:
        """Return True if api_key is non-empty (basic sanity check)."""
        return bool(self.api_key and self.api_key.strip())
