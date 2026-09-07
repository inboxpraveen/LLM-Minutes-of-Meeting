"""Process-level configuration.

Everything a user is expected to change lives in the admin screen, not here.
These values only cover things that must be known before the database exists.
"""
import os

from dotenv import load_dotenv

load_dotenv(encoding="utf-8-sig")

from app.paths import data_dir, logs_dir, uploads_dir  # noqa: E402
from app.security import flask_secret_key  # noqa: E402


def _bool(name: str, default: bool = False) -> bool:
    return os.environ.get(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


class Config:
    DATA_DIR = str(data_dir())
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "").strip() or str(uploads_dir())
    LOG_DIR = str(logs_dir())

    SECRET_KEY = flask_secret_key()
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = _bool("SESSION_COOKIE_SECURE")
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SECURE = SESSION_COOKIE_SECURE
    WTF_CSRF_TIME_LIMIT = None

    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("DATABASE_URL", "").strip() or f"sqlite:///{data_dir() / 'mom.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "").strip() or "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND = (
        os.environ.get("CELERY_RESULT_BACKEND", "").strip() or CELERY_BROKER_URL
    )

    ALLOWED_EXTENSIONS = {
        "mp3", "wav", "m4a", "aac", "flac", "ogg", "opus", "wma",
        "mp4", "mkv", "mov", "webm", "avi",
    }

    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").strip().upper()
    LOG_FORMAT = os.environ.get("LOG_FORMAT", "console").strip().lower()  # console | json
    BEHIND_PROXY = _bool("BEHIND_PROXY")
    APP_VERSION = os.environ.get("APP_VERSION", "3.0.0")
