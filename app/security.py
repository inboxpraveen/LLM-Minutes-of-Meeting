"""Local key material and encryption for settings stored at rest.

The key lives in the OS data directory and never leaves the machine. It is
generated on first run and reused afterwards.
"""
import base64
import hashlib
import os
import secrets
import stat

from cryptography.fernet import Fernet, InvalidToken

from app.paths import data_dir

_KEY_FILE = "instance.key"
_PREFIX = "enc:v1:"


def _load_or_create_key() -> bytes:
    """Create the key exactly once, even if several processes start together.

    Two processes generating different keys would silently break decryption of
    anything the other one saved.
    """
    path = data_dir() / _KEY_FILE
    existing = _read_key(path)
    if existing:
        return existing

    candidate = secrets.token_bytes(32)
    try:
        handle = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, stat.S_IRUSR | stat.S_IWUSR)
    except FileExistsError:
        return _read_key(path) or candidate
    with os.fdopen(handle, "w", encoding="utf-8") as file:
        file.write(candidate.hex())
    return candidate


def _read_key(path) -> bytes | None:
    try:
        raw = path.read_text(encoding="utf-8").strip()
        return bytes.fromhex(raw) if raw else None
    except (OSError, ValueError):
        return None


_MASTER = _load_or_create_key()
_FERNET = Fernet(base64.urlsafe_b64encode(hashlib.sha256(b"mom-ai/settings" + _MASTER).digest()))


def flask_secret_key() -> str:
    return os.environ.get("SECRET_KEY", "").strip() or hashlib.sha256(b"mom-ai/session" + _MASTER).hexdigest()


def encrypt(value: str) -> str:
    if not value:
        return ""
    return _PREFIX + _FERNET.encrypt(value.encode("utf-8")).decode("ascii")


def decrypt(value: str) -> str:
    if not value or not value.startswith(_PREFIX):
        return value or ""
    try:
        return _FERNET.decrypt(value[len(_PREFIX):].encode("ascii")).decode("utf-8")
    except InvalidToken:
        return ""


def mask(value: str) -> str:
    """Render a secret for display without revealing it."""
    if not value:
        return ""
    return f"{'•' * 8}{value[-4:]}" if len(value) > 8 else "•" * 8
