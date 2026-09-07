import logging
import os
import shutil
import subprocess

log = logging.getLogger("mom.audio")

_NO_WINDOW = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}


def ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def _run(cmd: list[str], timeout: int) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, timeout=timeout, **_NO_WINDOW)


def convert_to_wav(input_path: str, output_dir: str, timeout: int = 7200) -> str:
    """Normalise any recording to mono 16 kHz WAV, the format every provider accepts."""
    if not ffmpeg_available():
        raise RuntimeError(
            "ffmpeg was not found. Install it and make sure it is on PATH, "
            "or run the app with Docker where it is already included."
        )

    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "audio.wav")
    result = _run(
        ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", input_path,
         "-ar", "16000", "-ac", "1", "-vn", output_path],
        timeout,
    )
    if result.returncode != 0 or not os.path.exists(output_path):
        raise RuntimeError(f"ffmpeg could not read the recording: {_tail(result.stderr)}")
    return output_path


def probe_duration(path: str) -> float:
    if shutil.which("ffprobe") is None:
        return 0.0
    result = _run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        60,
    )
    try:
        return float(result.stdout.decode().strip())
    except (ValueError, AttributeError):
        return 0.0


def split_audio(wav_path: str, chunk_seconds: int, output_dir: str, timeout: int = 3600) -> list[str]:
    """Cut a WAV into fixed-length parts for endpoints with upload size limits."""
    os.makedirs(output_dir, exist_ok=True)
    pattern = os.path.join(output_dir, "part_%04d.wav")
    result = _run(
        ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", wav_path,
         "-f", "segment", "-segment_time", str(chunk_seconds),
         "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", pattern],
        timeout,
    )
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg could not split the audio: {_tail(result.stderr)}")

    parts = sorted(
        os.path.join(output_dir, name) for name in os.listdir(output_dir) if name.startswith("part_")
    )
    if not parts:
        raise RuntimeError("Audio splitting produced no output.")
    return parts


def _tail(stderr: bytes, limit: int = 400) -> str:
    return stderr.decode("utf-8", errors="replace").strip()[-limit:] or "no details available"
