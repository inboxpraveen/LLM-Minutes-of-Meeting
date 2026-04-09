import os
from dotenv import load_dotenv

# utf-8-sig strips a UTF-8 BOM if present (common when saving .env on Windows).
load_dotenv(encoding="utf-8-sig")


def _resolve_llm_base_url() -> tuple[str, str]:
    """Return (base_url, api_key). OpenRouter keys (sk-or-v1-...) are invalid on api.openai.com."""
    base = os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1").strip()
    key = os.environ.get("LLM_API_KEY", "").strip()
    if key.startswith("sk-or-v1-") and "api.openai.com" in base:
        base = "https://openrouter.ai/api/v1"
    return base, key


_LLM_BASE_URL, _LLM_API_KEY = _resolve_llm_base_url()


class Config:
    # ── Security ────────────────────────────────────────────────────────────
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-in-production")

    # ── Database ────────────────────────────────────────────────────────────
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'app.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ── Celery ───────────────────────────────────────────────────────────────
    CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND = os.environ.get(
        "CELERY_RESULT_BACKEND", "redis://localhost:6379/0"
    )

    # ── File Upload ──────────────────────────────────────────────────────────
    UPLOAD_FOLDER = os.environ.get(
        "UPLOAD_FOLDER", os.path.join(BASE_DIR, "data", "uploads")
    )
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_UPLOAD_SIZE_MB", "500")) * 1024 * 1024
    ALLOWED_EXTENSIONS = {"mp4", "mp3", "wav", "m4a", "webm", "ogg", "mkv"}

    # ── Default Admin Seed Credentials ──────────────────────────────────────
    ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin@123")
    ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@example.com")

    # ── LLM (OpenAI-compatible) ───────────────────────────────────────────
    LLM_BASE_URL = _LLM_BASE_URL
    LLM_API_KEY = _LLM_API_KEY
    LLM_MODEL = os.environ.get("LLM_MODEL", "gpt-4o-mini")

    # ── Speech Provider ───────────────────────────────────────────────────
    SPEECH_PROVIDER = os.environ.get("SPEECH_PROVIDER", "deepgram")
    DEEPGRAM_API_KEY = os.environ.get("DEEPGRAM_API_KEY", "")
    ASSEMBLYAI_API_KEY = os.environ.get("ASSEMBLYAI_API_KEY", "")
    SARVAM_API_KEY = os.environ.get("SARVAM_API_KEY", "")
    ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY", "")

    # ── Meeting Retention ─────────────────────────────────────────────────
    MEETING_RETENTION_DAYS = int(os.environ.get("MEETING_RETENTION_DAYS", "30"))
