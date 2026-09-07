"""Prometheus metrics exposed on /metrics."""
import time

from flask import Flask, g, request
from prometheus_client import Counter, Gauge, Histogram

HTTP_REQUESTS = Counter(
    "mom_http_requests_total", "HTTP requests", ["method", "endpoint", "status"]
)
HTTP_LATENCY = Histogram(
    "mom_http_request_seconds", "HTTP request duration", ["endpoint"]
)
MEETINGS_UPLOADED = Counter("mom_meetings_uploaded_total", "Recordings accepted for processing")
MEETINGS_BY_STATUS = Gauge("mom_meetings", "Meetings by status", ["status"])


def register_http_metrics(app: Flask) -> None:
    @app.before_request
    def _start_timer():
        g.metrics_start = time.perf_counter()

    @app.after_request
    def _record(response):
        endpoint = request.endpoint or "unknown"
        if endpoint != "static":
            HTTP_REQUESTS.labels(request.method, endpoint, response.status_code).inc()
            started = getattr(g, "metrics_start", None)
            if started is not None:
                HTTP_LATENCY.labels(endpoint).observe(time.perf_counter() - started)
        return response


def refresh_status_gauge() -> None:
    from sqlalchemy import func

    from app.extensions import db
    from app.models import Meeting

    counts = dict(db.session.query(Meeting.status, func.count(Meeting.id)).group_by(Meeting.status).all())
    for status in ("queued", "converting", "transcribing", "summarizing", "completed", "failed", "cancelled"):
        MEETINGS_BY_STATUS.labels(status).set(counts.get(status, 0))
