from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db

ACTIVE_STATUSES = ("queued", "converting", "transcribing", "summarizing")
TERMINAL_STATUSES = ("completed", "failed", "cancelled")


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def as_utc(value: datetime | None) -> datetime | None:
    """SQLite hands back naive datetimes; compare them as UTC."""
    if value is not None and value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="user")
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=utcnow)
    last_login_at = db.Column(db.DateTime)
    failed_logins = db.Column(db.Integer, nullable=False, default=0)
    locked_until = db.Column(db.DateTime)

    meetings = db.relationship("Meeting", backref="owner", lazy="dynamic")

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    @property
    def is_locked(self) -> bool:
        locked = as_utc(self.locked_until)
        return bool(locked and locked > utcnow())

    def __repr__(self) -> str:
        return f"<User {self.username} ({self.role})>"


class Meeting(db.Model):
    __tablename__ = "meetings"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    title = db.Column(db.String(200), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.BigInteger)
    duration_seconds = db.Column(db.Float)

    status = db.Column(db.String(20), nullable=False, default="queued", index=True)
    task_id = db.Column(db.String(255), index=True)
    progress = db.Column(db.Integer, default=0)
    error_message = db.Column(db.Text)
    cancel_requested = db.Column(db.Boolean, nullable=False, default=False)

    transcript = db.Column(db.Text)
    minutes_of_meeting = db.Column(db.Text)  # Markdown
    speech_provider = db.Column(db.String(40))
    llm_model = db.Column(db.String(120))

    created_at = db.Column(db.DateTime, default=utcnow, index=True)
    started_at = db.Column(db.DateTime)
    finished_at = db.Column(db.DateTime)
    expires_at = db.Column(db.DateTime, index=True)
    source_deleted_at = db.Column(db.DateTime)

    events = db.relationship(
        "MeetingEvent",
        backref="meeting",
        lazy="dynamic",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    @property
    def is_active(self) -> bool:
        return self.status in ACTIVE_STATUSES

    @property
    def has_source_file(self) -> bool:
        return self.source_deleted_at is None

    @property
    def duration_label(self) -> str:
        if not self.duration_seconds:
            return "—"
        total = int(self.duration_seconds)
        return f"{total // 3600}h {total % 3600 // 60}m" if total >= 3600 else f"{total // 60}m {total % 60}s"

    def log(self, message: str, level: str = "info") -> None:
        db.session.add(MeetingEvent(meeting_id=self.id, level=level, message=message[:500]))

    def __repr__(self) -> str:
        return f"<Meeting {self.id}: {self.title} [{self.status}]>"


class MeetingEvent(db.Model):
    __tablename__ = "meeting_events"

    id = db.Column(db.Integer, primary_key=True)
    meeting_id = db.Column(
        db.Integer, db.ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    level = db.Column(db.String(10), nullable=False, default="info")
    message = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow)

    def __repr__(self) -> str:
        return f"<MeetingEvent {self.meeting_id}: {self.message[:40]}>"


class SystemConfig(db.Model):
    __tablename__ = "system_config"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    value = db.Column(db.Text)
    description = db.Column(db.String(255))
    is_sensitive = db.Column(db.Boolean, default=False)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)
    updated_by = db.Column(db.Integer, db.ForeignKey("users.id"))

    def __repr__(self) -> str:
        return f"<SystemConfig {self.key}>"
