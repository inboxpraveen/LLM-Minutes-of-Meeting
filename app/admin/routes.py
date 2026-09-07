import logging
from functools import wraps
from pathlib import Path

from flask import (
    Blueprint, abort, current_app, flash, jsonify, redirect,
    render_template, request, url_for,
)
from flask_login import current_user, login_required
from sqlalchemy import func

from app import health, settings
from app.extensions import db
from app.models import Meeting, SystemConfig, User
from app.utils.storage import remove_recording

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")
log = logging.getLogger("mom.admin")

LOG_TAIL_LINES = 300


def admin_required(view):
    @wraps(view)
    @login_required
    def wrapper(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return view(*args, **kwargs)
    return wrapper


@admin_bp.route("/settings", methods=["GET", "POST"])
@admin_required
def settings_page():
    active = request.args.get("tab", "llm")

    if request.method == "POST":
        group = request.form.get("group", "llm")
        submitted = {}
        for spec in settings.SETTINGS:
            if spec.group != group:
                continue
            if spec.kind == "bool":
                submitted[spec.key] = "true" if request.form.get(spec.key) else "false"
            else:
                submitted[spec.key] = request.form.get(spec.key, "")
        cleared = {key for key in submitted if request.form.get(f"{key}__clear")}
        settings.save(submitted, current_user.id, clear=cleared)
        log.info("%s updated the %s settings", current_user.username, group)
        flash("Settings saved.", "success")
        return redirect(url_for("admin.settings_page", tab=group))

    return render_template(
        "admin/settings.html",
        active_tab=active if active in settings.GROUPS else "llm",
        groups=settings.GROUPS,
        specs=settings.SETTINGS,
        values={spec.key: settings.get(spec.key) for spec in settings.SETTINGS},
        llm_presets=settings.LLM_PRESETS,
        stt_presets=settings.STT_PRESETS,
    )


@admin_bp.route("/settings/test/<target>", methods=["POST"])
@admin_required
def test_provider(target: str):
    """Send one tiny request so misconfiguration is caught here, not mid-meeting.

    Unsaved form values are used when present, so a key can be verified before saving.
    """
    config = settings.snapshot()
    config.update(_submitted_overrides())
    try:
        if target == "llm":
            from app.providers.llm import get_llm_client
            message = get_llm_client(config).check()
        elif target == "speech":
            from app.providers.speech import get_speech_provider
            message = get_speech_provider(config).check()
        else:
            abort(404)
    except Exception as exc:
        return jsonify({"ok": False, "message": str(exc) or exc.__class__.__name__}), 200
    return jsonify({"ok": True, "message": message})


@admin_bp.route("/system")
@admin_required
def system():
    status_counts = dict(
        db.session.query(Meeting.status, func.count(Meeting.id)).group_by(Meeting.status).all()
    )
    recent_failures = (
        db.session.query(Meeting)
        .filter(Meeting.status == "failed")
        .order_by(Meeting.created_at.desc())
        .limit(5)
        .all()
    )
    return render_template(
        "admin/system.html",
        checks=health.full_report(),
        status_counts=status_counts,
        recent_failures=recent_failures,
        data_dir=current_app.config["DATA_DIR"],
        upload_bytes=_directory_size(current_app.config["UPLOAD_FOLDER"]),
        log_lines=_tail_log(current_app.config["LOG_DIR"]),
    )


@admin_bp.route("/users")
@admin_required
def users():
    return render_template(
        "admin/users.html", users=db.session.query(User).order_by(User.created_at.desc()).all()
    )


@admin_bp.route("/users/create", methods=["POST"])
@admin_required
def create_user():
    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    role = request.form.get("role", "user")

    if not username or not email or len(password) < 8:
        flash("A username, an email address and a password of at least 8 characters are required.", "error")
    elif role not in ("admin", "user"):
        flash("Choose a valid role.", "error")
    elif db.session.query(User).filter((User.username == username) | (User.email == email)).first():
        flash("That username or email address is already in use.", "error")
    else:
        user = User(username=username, email=email, role=role, is_active=True)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash(f'User "{username}" created.', "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/toggle", methods=["POST"])
@admin_required
def toggle_user(user_id: int):
    user = _other_user(user_id, "deactivate your own account")
    if user:
        user.is_active = not user.is_active
        db.session.commit()
        flash(f'"{user.username}" was {"activated" if user.is_active else "deactivated"}.', "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/role", methods=["POST"])
@admin_required
def change_role(user_id: int):
    user = _other_user(user_id, "change your own role")
    role = request.form.get("role", "user")
    if user and role in ("admin", "user"):
        user.role = role
        db.session.commit()
        flash(f'"{user.username}" is now {role}.', "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/password", methods=["POST"])
@admin_required
def reset_password(user_id: int):
    user = db.session.get(User, user_id) or abort(404)
    password = request.form.get("password", "")
    if len(password) < 8:
        flash("Choose a password of at least 8 characters.", "error")
    else:
        user.set_password(password)
        user.failed_logins = 0
        user.locked_until = None
        db.session.commit()
        flash(f'Password reset for "{user.username}".', "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/delete", methods=["POST"])
@admin_required
def delete_user(user_id: int):
    user = _other_user(user_id, "delete your own account")
    if user:
        for meeting in db.session.query(Meeting).filter_by(user_id=user.id).all():
            remove_recording(meeting)
            db.session.delete(meeting)
        # Settings this user saved outlive them; keep the rows, drop the reference.
        db.session.query(SystemConfig).filter_by(updated_by=user.id).update({"updated_by": None})
        db.session.delete(user)
        db.session.commit()
        flash(f'User "{user.username}" and their meetings were deleted.', "success")
    return redirect(url_for("admin.users"))


def _submitted_overrides() -> dict:
    group = request.form.get("group", "")
    overrides = {}
    for spec in settings.SETTINGS:
        if spec.kind == "bool":
            if spec.group == group:
                overrides[spec.key] = "true" if request.form.get(spec.key) else "false"
        elif spec.key in request.form:
            value = request.form.get(spec.key, "").strip()
            if value or spec.kind != "password":
                overrides[spec.key] = value
    return overrides


def _other_user(user_id: int, action: str) -> User | None:
    user = db.session.get(User, user_id)
    if user is None:
        abort(404)
    if user.id == current_user.id:
        flash(f"You cannot {action}.", "error")
        return None
    return user


def _directory_size(path: str) -> int:
    try:
        return sum(f.stat().st_size for f in Path(path).glob("*") if f.is_file())
    except OSError:
        return 0


def _tail_log(log_dir: str) -> list[str]:
    path = Path(log_dir) / "app.log"
    if not path.exists():
        return []
    try:
        with path.open("rb") as handle:
            handle.seek(max(0, path.stat().st_size - 120_000))
            tail = handle.read().decode("utf-8", errors="replace")
        return tail.splitlines()[-LOG_TAIL_LINES:]
    except OSError as exc:
        return [f"Could not read the log file: {exc}"]
