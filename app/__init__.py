import logging
import os
import shutil
from pathlib import Path

from flask import Flask, redirect, render_template, request, url_for
from werkzeug.middleware.proxy_fix import ProxyFix

from app.config import Config
from app.extensions import celery, csrf, db, login_manager, sync_schema
from app.logging_setup import configure_logging, register_request_logging
from app.metrics import register_http_metrics

log = logging.getLogger("mom.app")

PUBLIC_ENDPOINTS = {"auth.setup", "auth.login", "api.healthz", "api.readyz", "api.metrics", "static"}


def create_app(config_class=Config) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)

    configure_logging(app.config["LOG_LEVEL"], app.config["LOG_FORMAT"], app.config["LOG_DIR"])
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    if app.config["BEHIND_PROXY"]:
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    _register_blueprints(app)
    register_request_logging(app)
    register_http_metrics(app)
    _register_errors(app)

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    with app.app_context():
        _adopt_legacy_database(app)
        sync_schema()
        from app import settings
        settings.seed_from_env()
        app.config["SETUP_COMPLETE"] = _has_admin()
        _configure_celery(app, settings.get_int("job_time_limit_seconds"))

    @app.before_request
    def _require_setup():
        if app.config.get("SETUP_COMPLETE") or request.endpoint in PUBLIC_ENDPOINTS:
            return None
        if not _has_admin():
            return redirect(url_for("auth.setup"))
        app.config["SETUP_COMPLETE"] = True
        return None

    @app.context_processor
    def _globals():
        from app import settings
        return {
            "app_version": app.config["APP_VERSION"],
            "speech_provider_name": _safe_setting(settings, "speech_provider"),
        }

    from app.icons import icon
    from app.utils.text import format_bytes

    app.jinja_env.globals["icon"] = icon
    app.jinja_env.filters["markdown"] = _markdown_filter
    app.jinja_env.filters["filesize"] = format_bytes
    return app


def _safe_setting(settings_module, key: str) -> str:
    try:
        return settings_module.get(key)
    except Exception:  # settings are unavailable while the database is being created
        return ""


def _markdown_filter(value: str):
    """Safe to mark as markup: render_markdown sanitises before returning."""
    from markupsafe import Markup

    from app.utils.text import render_markdown
    return Markup(render_markdown(value))


def _has_admin() -> bool:
    from app.models import User
    return db.session.query(User.id).filter_by(role="admin").first() is not None


def _register_blueprints(app: Flask) -> None:
    from app.admin.routes import admin_bp
    from app.api.routes import api_bp
    from app.auth.routes import auth_bp
    from app.dashboard.routes import dashboard_bp
    from app.meetings.routes import meetings_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(meetings_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)
    csrf.exempt(api_bp)


def _register_errors(app: Flask) -> None:
    def page(code: int, title: str, message: str):
        def handler(_error):
            return render_template("error.html", code=code, title=title, message=message), code
        return handler

    app.register_error_handler(403, page(403, "Not allowed", "You do not have access to this page."))
    app.register_error_handler(404, page(404, "Not found", "That page does not exist."))
    app.register_error_handler(
        413, page(413, "File too large", "The upload exceeds the configured maximum size.")
    )

    @app.errorhandler(500)
    def _server_error(error):
        log.exception("Unhandled error: %s", error)
        return render_template(
            "error.html", code=500, title="Something went wrong",
            message="The error has been written to the application log.",
        ), 500


def _configure_celery(app: Flask, time_limit: int) -> None:
    time_limit = max(600, time_limit)
    celery.conf.update(
        broker_url=app.config["CELERY_BROKER_URL"],
        result_backend=app.config["CELERY_RESULT_BACKEND"],
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        task_track_started=True,
        task_acks_late=True,
        task_reject_on_worker_lost=True,
        worker_prefetch_multiplier=1,
        worker_max_tasks_per_child=20,
        task_time_limit=time_limit + 300,
        task_soft_time_limit=time_limit,
        # Must exceed the hard time limit: with acks_late, Redis redelivers any task
        # still unacknowledged after this, which would run a long meeting twice.
        broker_transport_options={"visibility_timeout": time_limit + 900},
        broker_connection_retry_on_startup=True,
        result_expires=86400,
        beat_schedule={
            "maintenance": {"task": "app.tasks.maintenance.run_maintenance", "schedule": 900.0},
        },
    )

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask


def _adopt_legacy_database(app: Flask) -> None:
    """Carry a pre-3.0 SQLite database into the OS data directory once."""
    uri = app.config["SQLALCHEMY_DATABASE_URI"]
    if not uri.startswith("sqlite:///"):
        return
    target = Path(uri.replace("sqlite:///", "", 1))
    legacy = Path(app.root_path).parent / "instance" / "app.db"
    if target.exists() or not legacy.exists():
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(legacy, target)
    log.info("Imported existing database from %s", legacy)
