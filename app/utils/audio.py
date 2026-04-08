import os
import subprocess
import tempfile


def convert_to_wav(input_path: str, output_dir: str = None) -> str:
    """
    Convert any audio/video file to mono 16-kHz WAV using ffmpeg.

    Returns the path to the converted WAV file. Caller is responsible for
    deleting it when no longer needed.
    """
    if output_dir is None:
        output_dir = tempfile.gettempdir()

    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    output_path = os.path.join(output_dir, f"{base_name}_converted.wav")

    cmd = [
        "ffmpeg",
        "-y",                   # overwrite
        "-i", input_path,
        "-ar", "16000",         # 16 kHz sample rate
        "-ac", "1",             # mono
        "-vn",                  # no video
        output_path,
    ]

    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=600,
    )

    if result.returncode != 0:
        stderr = result.stderr.decode("utf-8", errors="replace")
        raise RuntimeError(f"ffmpeg conversion failed:\n{stderr}")

    return output_path


def get_audio_duration(audio_path: str) -> float:
    """Return duration of an audio file in seconds using ffprobe."""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        audio_path,
    ]
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
    )
    if result.returncode == 0:
        try:
            return float(result.stdout.decode().strip())
        except ValueError:
            pass
    return 0.0
