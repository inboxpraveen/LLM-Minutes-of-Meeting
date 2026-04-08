"""
Celery worker entry point.

Run worker:
    celery -A celery_worker:celery worker -l info

Run beat scheduler (periodic tasks):
    celery -A celery_worker:celery beat -l info

Run both (development only):
    celery -A celery_worker:celery worker --beat -l info
"""
from app import create_app
from app.extensions import celery  # noqa: F401 – re-exported for Celery CLI

flask_app = create_app()

# Import task modules so Celery discovers and registers them
import app.tasks.process  # noqa: F401, E402
import app.tasks.cleanup  # noqa: F401, E402
