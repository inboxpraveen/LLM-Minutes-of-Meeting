import os
from flask import Flask
from app.config import Config
from app.extensions import db, login_manager, celery


def create_app(config_class=Config) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)

    # Ensure required directories exist
    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # Init extensions
    db.init_app(app)
    login_manager.init_app(app)

    # Configure Celery
    celery.conf.update(
        broker_url=app.config["CELERY_BROKER_URL"],
        result_backend=app.config["CELERY_RESULT_BACKEND"],
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        task_track_started=True,
        beat_schedule={
            "cleanup-expired-meetings": {
                "task": "app.tasks.cleanup.cleanup_expired_meetings",
                "schedule": 3600.0,  # every hour
            }
        },
    )

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask

    # Register blueprints
    from app.auth.routes import auth_bp
    from app.dashboard.routes import dashboard_bp
    from app.meetings.routes import meetings_bp
    from app.admin.routes import admin_bp
    from app.api.routes import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(meetings_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)

    # User loader for Flask-Login
    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Create tables and seed data
    with app.app_context():
        db.create_all()
        _seed_defaults(app)

    return app


def _seed_defaults(app: Flask) -> None:
    from app.models import User, SystemConfig
    from app.config import Config

    # Seed admin user
    admin = User.query.filter_by(username=app.config["ADMIN_USERNAME"]).first()
    if not admin:
        admin = User(
            username=app.config["ADMIN_USERNAME"],
            email=app.config["ADMIN_EMAIL"],
            role="admin",
            is_active=True,
        )
        admin.set_password(app.config["ADMIN_PASSWORD"])
        db.session.add(admin)
        db.session.commit()

    # Seed default system config (only if keys don't exist)
    defaults = [
        ("llm_base_url", app.config["LLM_BASE_URL"], "LLM API base URL (OpenAI-compatible)", False),
        ("llm_api_key", app.config["LLM_API_KEY"], "LLM API key", True),
        ("llm_model", app.config["LLM_MODEL"], "LLM model name", False),
        ("speech_provider", app.config["SPEECH_PROVIDER"], "Active speech-to-text provider", False),
        ("deepgram_api_key", app.config["DEEPGRAM_API_KEY"], "Deepgram API key", True),
        ("assemblyai_api_key", app.config["ASSEMBLYAI_API_KEY"], "AssemblyAI API key", True),
        ("sarvam_api_key", app.config["SARVAM_API_KEY"], "Sarvam AI API key", True),
        ("elevenlabs_api_key", app.config["ELEVENLABS_API_KEY"], "ElevenLabs API key", True),
        ("meeting_retention_days", str(app.config["MEETING_RETENTION_DAYS"]), "Days before uploaded files are auto-deleted", False),
        ("max_upload_size_mb", str(app.config.get("MAX_CONTENT_LENGTH", 500 * 1024 * 1024) // (1024 * 1024)), "Maximum upload file size in MB", False),
    ]
    for key, value, description, is_sensitive in defaults:
        if not SystemConfig.query.filter_by(key=key).first():
            db.session.add(
                SystemConfig(
                    key=key,
                    value=value,
                    description=description,
                    is_sensitive=is_sensitive,
                )
            )
    db.session.commit()
