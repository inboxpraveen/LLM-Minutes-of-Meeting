"""Application logging: console, rotating file, and a request id on every line."""
import logging
import logging.handlers
import uuid
from pathlib import Path

from flask import Flask, g, has_request_context, request
from pythonjsonlogger.json import JsonFormatter

CONSOLE_FORMAT = "%(asctime)s %(levelname)-7s [%(request_id)s] %(name)s: %(message)s"
JSON_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s %(request_id)s"
_NOISY = ("werkzeug", "httpx", "httpcore", "urllib3", "openai._base_client", "faster_whisper")


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = getattr(g, "request_id", "-") if has_request_context() else "-"
        return True


def configure_logging(level: str = "INFO", fmt: str = "console", log_dir: str | None = None) -> None:
    formatter = (
        JsonFormatter(JSON_FORMAT, rename_fields={"asctime": "time", "levelname": "level"})
        if fmt == "json"
        else logging.Formatter(CONSOLE_FORMAT, datefmt="%Y-%m-%d %H:%M:%S")
    )

    root = logging.getLogger()
    root.setLevel(level)
    for handler in list(root.handlers):
        root.removeHandler(handler)

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    console.addFilter(RequestIdFilter())
    root.addHandler(console)

    if log_dir:
        Path(log_dir).mkdir(parents=True, exist_ok=True)
        rotating = logging.handlers.RotatingFileHandler(
            Path(log_dir) / "app.log", maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
        )
        rotating.setFormatter(formatter)
        rotating.addFilter(RequestIdFilter())
        root.addHandler(rotating)

    for name in _NOISY:
        logging.getLogger(name).setLevel(logging.WARNING)


def register_request_logging(app: Flask) -> None:
    log = logging.getLogger("mom.request")

    @app.before_request
    def _assign_request_id():
        g.request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]

    @app.after_request
    def _log_request(response):
        if request.path.startswith("/static/") or request.path in ("/healthz", "/metrics"):
            return response
        log.info(
            "%s %s %s", request.method, request.full_path.rstrip("?"), response.status_code,
            extra={"method": request.method, "path": request.path, "status": response.status_code},
        )
        response.headers["X-Request-ID"] = getattr(g, "request_id", "-")
        return response
