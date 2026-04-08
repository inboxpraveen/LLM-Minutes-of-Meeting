from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from app.extensions import db
from app.models import User, SystemConfig

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required(f):
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated


@admin_bp.route("/settings", methods=["GET", "POST"])
@admin_required
def settings():
    if request.method == "POST":
        tab = request.form.get("tab", "llm")

        if tab == "llm":
            SystemConfig.set("llm_base_url", request.form.get("llm_base_url", ""), updated_by=current_user.id)
            SystemConfig.set("llm_model", request.form.get("llm_model", ""), updated_by=current_user.id)
            api_key = request.form.get("llm_api_key", "")
            if api_key and api_key != "••••••••":
                SystemConfig.set("llm_api_key", api_key, is_sensitive=True, updated_by=current_user.id)

        elif tab == "speech":
            SystemConfig.set("speech_provider", request.form.get("speech_provider", "deepgram"), updated_by=current_user.id)
            for provider in ["deepgram", "assemblyai", "sarvam", "elevenlabs"]:
                key_val = request.form.get(f"{provider}_api_key", "")
                if key_val and key_val != "••••••••":
                    SystemConfig.set(f"{provider}_api_key", key_val, is_sensitive=True, updated_by=current_user.id)

        elif tab == "storage":
            retention = request.form.get("meeting_retention_days", "30")
            try:
                retention = max(1, int(retention))
            except ValueError:
                retention = 30
            SystemConfig.set("meeting_retention_days", str(retention), updated_by=current_user.id)

        flash("Settings saved.", "success")
        return redirect(url_for("admin.settings", tab=tab))

    tab = request.args.get("tab", "llm")
    config = {row.key: row for row in SystemConfig.query.all()}
    return render_template("admin/settings.html", config=config, active_tab=tab)


@admin_bp.route("/users")
@admin_required
def users():
    all_users = User.query.order_by(User.created_at.desc()).all()
    return render_template("admin/users.html", users=all_users)


@admin_bp.route("/users/create", methods=["POST"])
@admin_required
def create_user():
    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    role = request.form.get("role", "user")

    if not username or not email or not password:
        flash("Username, email, and password are required.", "error")
        return redirect(url_for("admin.users"))

    if User.query.filter_by(username=username).first():
        flash(f'Username "{username}" is already taken.', "error")
        return redirect(url_for("admin.users"))

    if User.query.filter_by(email=email).first():
        flash(f'Email "{email}" is already in use.', "error")
        return redirect(url_for("admin.users"))

    user = User(username=username, email=email, role=role, is_active=True)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    flash(f'User "{username}" created successfully.', "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/toggle", methods=["POST"])
@admin_required
def toggle_user(user_id: int):
    user = db.session.get(User, user_id)
    if not user:
        abort(404)
    if user.id == current_user.id:
        flash("You cannot deactivate your own account.", "error")
        return redirect(url_for("admin.users"))
    user.is_active = not user.is_active
    db.session.commit()
    status = "activated" if user.is_active else "deactivated"
    flash(f'User "{user.username}" {status}.', "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/role", methods=["POST"])
@admin_required
def change_role(user_id: int):
    user = db.session.get(User, user_id)
    if not user:
        abort(404)
    if user.id == current_user.id:
        flash("You cannot change your own role.", "error")
        return redirect(url_for("admin.users"))
    new_role = request.form.get("role", "user")
    if new_role not in ("admin", "user"):
        flash("Invalid role.", "error")
        return redirect(url_for("admin.users"))
    user.role = new_role
    db.session.commit()
    flash(f'Role for "{user.username}" changed to {new_role}.', "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/delete", methods=["POST"])
@admin_required
def delete_user(user_id: int):
    user = db.session.get(User, user_id)
    if not user:
        abort(404)
    if user.id == current_user.id:
        flash("You cannot delete your own account.", "error")
        return redirect(url_for("admin.users"))
    db.session.delete(user)
    db.session.commit()
    flash(f'User "{user.username}" deleted.', "success")
    return redirect(url_for("admin.users"))
