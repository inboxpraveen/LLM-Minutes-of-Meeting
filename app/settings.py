"""Runtime settings.

Every setting is editable from the admin screen and stored in the database.
Environment variables are only used to seed a value the first time the app
starts, so a fresh install works with an entirely empty .env file.
"""
import os
from dataclasses import dataclass

from app.extensions import db
from app.security import decrypt, encrypt

DEFAULT_MINUTES_PROMPT = """You are an expert meeting analyst. Given a meeting transcript, produce \
well-structured Minutes of Meeting in Markdown using exactly these sections:

## Summary
A concise 2-4 sentence overview.

## Attendees
Names or speaker labels present, with roles when stated. Write "Not specified" if unknown.

## Key Discussion Points
Bullet list of the main topics.

## Decisions Made
Numbered list of decisions reached. Write "None recorded" if there were none.

## Action Items
A table with columns: | Task | Owner | Due date |

## Next Steps
What happens after this meeting.

Use only information present in the transcript. Never invent names, dates or commitments."""


@dataclass(frozen=True)
class Setting:
    key: str
    group: str
    label: str
    kind: str = "text"  # text | password | url | number | select | textarea | bool
    default: str = ""
    help: str = ""
    choices: tuple = ()
    env: str = ""
    depends_on: str = ""  # only shown when speech_provider matches this value


SPEECH_PROVIDERS = (
    ("deepgram", "Deepgram"),
    ("assemblyai", "AssemblyAI"),
    ("elevenlabs", "ElevenLabs Scribe"),
    ("sarvam", "Sarvam AI"),
    ("openai_compatible", "OpenAI-compatible endpoint"),
    ("local_whisper", "Local Whisper (no API key)"),
)

SETTINGS: tuple[Setting, ...] = (
    # ── LLM ───────────────────────────────────────────────────────────────
    Setting("llm_base_url", "llm", "Base URL", "url", "",
            "Any OpenAI-compatible endpoint. Pick a preset above or type your own.",
            env="LLM_BASE_URL"),
    Setting("llm_api_key", "llm", "API key", "password", "",
            "Stored encrypted on this machine.", env="LLM_API_KEY"),
    Setting("llm_model", "llm", "Model", "text", "",
            "Exact model id as the provider expects it.", env="LLM_MODEL"),
    Setting("llm_temperature", "llm", "Temperature", "number", "0.2",
            "Lower values give more consistent minutes."),
    Setting("llm_max_output_tokens", "llm", "Max output tokens", "number", "4000"),
    Setting("llm_timeout_seconds", "llm", "Request timeout (seconds)", "number", "300"),

    # ── Speech ────────────────────────────────────────────────────────────
    Setting("speech_provider", "speech", "Active provider", "select", "deepgram",
            "Only the selected provider is used for transcription.",
            choices=SPEECH_PROVIDERS, env="SPEECH_PROVIDER"),
    Setting("speech_language", "speech", "Language", "text", "",
            "ISO code such as en or hi. Leave blank to auto-detect."),
    Setting("diarization_enabled", "speech", "Speaker diarization", "bool", "true",
            "Label who said what. Improves attribution of decisions and action items."),

    Setting("deepgram_api_key", "speech", "Deepgram API key", "password", "",
            env="DEEPGRAM_API_KEY", depends_on="deepgram"),
    Setting("deepgram_model", "speech", "Deepgram model", "text", "nova-3",
            depends_on="deepgram"),

    Setting("assemblyai_api_key", "speech", "AssemblyAI API key", "password", "",
            env="ASSEMBLYAI_API_KEY", depends_on="assemblyai"),
    Setting("assemblyai_model", "speech", "AssemblyAI model", "select", "universal",
            choices=(("universal", "universal"), ("slam_1", "slam_1"), ("best", "best"), ("nano", "nano")),
            depends_on="assemblyai"),

    Setting("elevenlabs_api_key", "speech", "ElevenLabs API key", "password", "",
            env="ELEVENLABS_API_KEY", depends_on="elevenlabs"),
    Setting("elevenlabs_model", "speech", "ElevenLabs model", "text", "scribe_v2",
            depends_on="elevenlabs"),

    Setting("sarvam_api_key", "speech", "Sarvam API key", "password", "",
            env="SARVAM_API_KEY", depends_on="sarvam"),
    Setting("sarvam_model", "speech", "Sarvam model", "text", "saaras:v3",
            "Batch job API. saarika:v2.5 is the legacy model.", depends_on="sarvam"),

    Setting("stt_base_url", "speech", "STT base URL", "url", "",
            "OpenAI-compatible /audio/transcriptions endpoint. "
            "Works with OpenAI, Groq and local servers such as Speaches or LocalAI.",
            depends_on="openai_compatible"),
    Setting("stt_api_key", "speech", "STT API key", "password", "", depends_on="openai_compatible"),
    Setting("stt_model", "speech", "STT model", "text", "whisper-large-v3-turbo",
            depends_on="openai_compatible"),

    Setting("whisper_model", "speech", "Whisper model", "select", "base",
            "Larger models are more accurate and slower. Downloaded once, then cached locally.",
            choices=(("tiny", "tiny"), ("base", "base"), ("small", "small"), ("medium", "medium"),
                     ("large-v3", "large-v3"), ("distil-large-v3", "distil-large-v3")),
            depends_on="local_whisper"),
    Setting("whisper_device", "speech", "Device", "select", "auto",
            choices=(("auto", "auto"), ("cpu", "cpu"), ("cuda", "cuda")), depends_on="local_whisper"),
    Setting("whisper_compute_type", "speech", "Compute type", "select", "int8",
            "int8 is the safest choice on CPU. Use float16 on a GPU.",
            choices=(("int8", "int8"), ("int8_float16", "int8_float16"),
                     ("float16", "float16"), ("float32", "float32")),
            depends_on="local_whisper"),

    # ── Processing ────────────────────────────────────────────────────────
    Setting("minutes_prompt", "processing", "Minutes prompt", "textarea", DEFAULT_MINUTES_PROMPT,
            "Instructions sent to the LLM. Change the sections to match how your team writes minutes."),
    Setting("transcript_chunk_chars", "processing", "Transcript chunk size (characters)", "number", "48000",
            "Longer transcripts are summarised in chunks and then merged, so meeting length "
            "is not limited by the model context window."),
    Setting("stt_chunk_seconds", "processing", "Audio chunk length (seconds)", "number", "600",
            "Used when a transcription endpoint has an upload size limit."),
    Setting("job_time_limit_seconds", "processing", "Job time limit (seconds)", "number", "10800",
            "A job running longer than this is marked failed."),

    # ── Storage ───────────────────────────────────────────────────────────
    Setting("meeting_retention_days", "storage", "Retention period (days)", "number", "30",
            "Uploaded recordings are deleted after this many days. "
            "Transcripts and minutes are always kept.", env="MEETING_RETENTION_DAYS"),
    Setting("max_upload_size_mb", "storage", "Maximum upload size (MB)", "number", "2048",
            env="MAX_UPLOAD_SIZE_MB"),
    Setting("keep_source_after_processing", "storage", "Keep recording after processing", "bool", "true",
            "Turn off to delete the recording as soon as the minutes are generated."),
)

BY_KEY = {s.key: s for s in SETTINGS}
GROUPS = ("llm", "speech", "processing", "storage")

LLM_PRESETS = (
    ("OpenAI", "https://api.openai.com/v1", "gpt-4o-mini"),
    ("OpenRouter", "https://openrouter.ai/api/v1", "openai/gpt-4o-mini"),
    ("Groq", "https://api.groq.com/openai/v1", "llama-3.3-70b-versatile"),
    ("Together AI", "https://api.together.xyz/v1", "meta-llama/Llama-3.3-70B-Instruct-Turbo"),
    ("Fireworks AI", "https://api.fireworks.ai/inference/v1", "accounts/fireworks/models/llama-v3p3-70b-instruct"),
    ("DeepInfra", "https://api.deepinfra.com/v1/openai", "meta-llama/Llama-3.3-70B-Instruct"),
    ("Mistral", "https://api.mistral.ai/v1", "mistral-large-latest"),
    ("Cerebras", "https://api.cerebras.ai/v1", "llama-3.3-70b"),
    ("Anthropic", "https://api.anthropic.com/v1/", "claude-sonnet-4-5"),
    ("Google Gemini", "https://generativelanguage.googleapis.com/v1beta/openai/", "gemini-2.5-flash"),
    ("Ollama (local)", "http://localhost:11434/v1", "llama3.2"),
    ("LM Studio (local)", "http://localhost:1234/v1", "local-model"),
    ("vLLM / llama.cpp (local)", "http://localhost:8000/v1", "local-model"),
)

STT_PRESETS = (
    ("OpenAI", "https://api.openai.com/v1", "gpt-4o-transcribe"),
    ("Groq", "https://api.groq.com/openai/v1", "whisper-large-v3-turbo"),
    ("Speaches / LocalAI (local)", "http://localhost:8000/v1", "Systran/faster-whisper-large-v3"),
)

_TRUE = {"1", "true", "yes", "on"}


def _row(key: str):
    from app.models import SystemConfig
    return db.session.query(SystemConfig).filter_by(key=key).first()


def get(key: str) -> str:
    spec = BY_KEY.get(key)
    row = _row(key)
    if row is None or row.value is None:
        return spec.default if spec else ""
    value = decrypt(row.value) if row.is_sensitive else row.value
    if not value and spec and spec.kind in ("number", "select", "bool"):
        return spec.default
    return value


def get_int(key: str) -> int:
    spec = BY_KEY.get(key)
    try:
        return int(float(get(key)))
    except (TypeError, ValueError):
        return int(float(spec.default)) if spec and spec.default else 0


def get_float(key: str) -> float:
    spec = BY_KEY.get(key)
    try:
        return float(get(key))
    except (TypeError, ValueError):
        return float(spec.default) if spec and spec.default else 0.0


def get_bool(key: str) -> bool:
    return str(get(key)).strip().lower() in _TRUE


def snapshot() -> dict:
    """All settings as a plain dict, decrypted. Used by background jobs."""
    from app.models import SystemConfig
    stored = {r.key: (decrypt(r.value) if r.is_sensitive else r.value) for r in db.session.query(SystemConfig).all()}
    return {s.key: stored.get(s.key) if stored.get(s.key) not in (None, "") else s.default for s in SETTINGS}


def save(values: dict, user_id: int | None = None, clear: set | None = None) -> None:
    """Persist submitted settings.

    A blank password field keeps the stored secret, since the form never renders
    it back. Keys listed in `clear` are erased instead.
    """
    from app.models import SystemConfig

    clear = clear or set()
    for key, raw in values.items():
        spec = BY_KEY.get(key)
        if spec is None:
            continue
        value = "" if raw is None else str(raw).strip()
        sensitive = spec.kind == "password"
        if sensitive and not value and key not in clear:
            continue

        row = _row(key)
        if row is None:
            row = SystemConfig(key=key, is_sensitive=sensitive)
            db.session.add(row)
        row.value = encrypt(value) if sensitive else value
        row.is_sensitive = sensitive
        row.description = spec.label
        row.updated_by = user_id
    db.session.commit()


def seed_from_env() -> None:
    """Create missing rows once, taking a value from the environment if provided."""
    from app.models import SystemConfig

    existing = {r.key for r in db.session.query(SystemConfig.key).all()}
    created = False
    for spec in SETTINGS:
        if spec.key in existing:
            continue
        value = (os.environ.get(spec.env, "").strip() if spec.env else "") or spec.default
        sensitive = spec.kind == "password"
        db.session.add(
            SystemConfig(
                key=spec.key,
                value=encrypt(value) if (sensitive and value) else value,
                description=spec.label,
                is_sensitive=sensitive,
            )
        )
        created = True
    if created:
        db.session.commit()
