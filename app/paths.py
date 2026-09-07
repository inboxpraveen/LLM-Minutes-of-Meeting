"""OS-aware locations for everything the app writes to disk."""
import os
from pathlib import Path

from platformdirs import user_data_dir

APP_NAME = "MoM-AI"


def _base() -> Path:
    override = os.environ.get("MOM_DATA_DIR", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    return Path(user_data_dir(APP_NAME, appauthor=False, roaming=False))


def data_dir() -> Path:
    return _ensure(_base())


def uploads_dir() -> Path:
    return _ensure(_base() / "uploads")


def logs_dir() -> Path:
    return _ensure(_base() / "logs")


def models_dir() -> Path:
    return _ensure(_base() / "models")


def _ensure(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path
