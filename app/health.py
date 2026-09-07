"""Dependency checks shared by /readyz and the admin System page."""
import logging
import os
import shutil
import subprocess

from flask import current_app
from sqlalchemy import text

from app.extensions import celery, db
from app.utils.audio import ffmpeg_available

log = logging.getLogger("mom.health")

_NO_WINDOW = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}


def check_database() -> dict:
    try:
        db.session.execute(text("SELECT 1"))
        engine = db.engine.url.get_backend_name()
        return _ok(f"Connected ({engine})")
    except Exception as exc:
        return _fail(str(exc))


def check_broker() -> dict:
    try:
        connection = celery.connection()
        connection.ensure_connection(max_retries=1, timeout=3)
        connection.release()
        return _ok("Reachable")
    except Exception as exc:
        return _fail(f"Unreachable: {exc}")


def check_workers() -> dict:
    try:
        replies = celery.control.ping(timeout=1.5) or []
    except Exception as exc:
        return _fail(f"Cannot reach the broker: {exc}")
    if not replies:
        return _fail("No worker is running. Jobs will stay queued.")
    return _ok(f"{len(replies)} online: {', '.join(sorted(name for r in replies for name in r))}")


def check_ffmpeg() -> dict:
    if not ffmpeg_available():
        return _fail("Not found on PATH. Audio cannot be converted.")
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            timeout=15, **_NO_WINDOW,
        )
        return _ok(result.stdout.decode(errors="replace").splitlines()[0][:80])
    except Exception:
        return _ok("Available")


def check_storage() -> dict:
    try:
        usage = shutil.disk_usage(current_app.config["DATA_DIR"])
    except OSError as exc:
        return _fail(str(exc))
    free_gb = usage.free / 1024 ** 3
    message = f"{free_gb:.1f} GB free of {usage.total / 1024 ** 3:.1f} GB"
    return _ok(message) if free_gb >= 1 else _fail(f"Low disk space: {message}")


def check_providers() -> dict:
    from app import settings

    missing = []
    if not settings.get("llm_base_url") or not settings.get("llm_model"):
        missing.append("LLM provider")
    provider = settings.get("speech_provider")
    key_needed = {
        "deepgram": "deepgram_api_key",
        "assemblyai": "assemblyai_api_key",
        "elevenlabs": "elevenlabs_api_key",
        "sarvam": "sarvam_api_key",
        "openai_compatible": "stt_base_url",
    }.get(provider)
    if key_needed and not settings.get(key_needed):
        missing.append("Speech provider")

    if missing:
        return _fail(f"Not configured yet: {' and '.join(missing)}")
    return _ok("Configured")


def full_report() -> dict:
    return {
        "Database": check_database(),
        "Job queue": check_broker(),
        "Workers": check_workers(),
        "ffmpeg": check_ffmpeg(),
        "Storage": check_storage(),
        "AI providers": check_providers(),
    }


def readiness() -> tuple[bool, dict]:
    """Ready means the app can accept and queue work right now."""
    checks = {"database": check_database(), "broker": check_broker(), "ffmpeg": check_ffmpeg()}
    return all(c["ok"] for c in checks.values()), checks


def _ok(detail: str) -> dict:
    return {"ok": True, "detail": detail}


def _fail(detail: str) -> dict:
    return {"ok": False, "detail": detail}
