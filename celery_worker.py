"""Celery entry point.

    celery -A celery_worker:celery worker -l info
    celery -A celery_worker:celery beat -l info
"""
from app import create_app
from app.extensions import celery

flask_app = create_app()

import app.tasks.maintenance  # noqa: E402,F401
import app.tasks.process  # noqa: E402,F401

__all__ = ["celery", "flask_app"]
