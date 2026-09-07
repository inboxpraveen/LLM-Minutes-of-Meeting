import logging
from datetime import timedelta

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.extensions import db
from app.models import User, utcnow

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")
log = logging.getLogger("mom.auth")

MAX_ATTEMPTS = 5
LOCKOUT_MINUTES = 15
MIN_PASSWORD_LENGTH = 8


@auth_bp.route("/setup", methods=["GET", "POST"])
def setup():
    """First run: create the administrator account. Disabled once one exists."""
    if db.session.query(User.id).filter_by(role="admin").first():
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        error = _validate_new_account(username, email, password, confirm)
        if error:
            flash(error, "error")
            return render_template("auth/setup.html", username=username, email=email)

        admin = User(username=username, email=email, role="admin", is_active=True)
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
        current_app.config["SETUP_COMPLETE"] = True

        login_user(admin)
        log.info("Administrator account %s created", username)
        flash("Welcome. Add your AI provider keys to start processing meetings.", "success")
        return redirect(url_for("admin.settings_page"))

    return render_template("auth/setup.html", username="", email="")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))
    if not db.session.query(User.id).filter_by(role="admin").first():
        return redirect(url_for("auth.setup"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = db.session.query(User).filter_by(username=username).first()

        if user and user.is_locked:
            flash(f"Too many failed attempts. Try again in {LOCKOUT_MINUTES} minutes.", "error")
        elif user and user.is_active and user.check_password(password):
            user.failed_logins = 0
            user.locked_until = None
            user.last_login_at = utcnow()
            db.session.commit()
            login_user(user, remember=bool(request.form.get("remember")))
            log.info("User %s signed in", username)
            return redirect(_safe_next() or url_for("dashboard.index"))
        else:
            if user:
                user.failed_logins = (user.failed_logins or 0) + 1
                if user.failed_logins >= MAX_ATTEMPTS:
                    user.locked_until = utcnow() + timedelta(minutes=LOCKOUT_MINUTES)
                    user.failed_logins = 0
                db.session.commit()
            log.warning("Failed sign-in for %r", username)
            flash("Incorrect username or password.", "error")

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been signed out.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/account", methods=["GET", "POST"])
@login_required
def account():
    if request.method == "POST":
        current = request.form.get("current_password", "")
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if not current_user.check_password(current):
            flash("Your current password is not correct.", "error")
        elif len(password) < MIN_PASSWORD_LENGTH:
            flash(f"Choose a password of at least {MIN_PASSWORD_LENGTH} characters.", "error")
        elif password != confirm:
            flash("The two passwords do not match.", "error")
        else:
            current_user.set_password(password)
            db.session.commit()
            flash("Password updated.", "success")
            return redirect(url_for("auth.account"))

    return render_template("auth/account.html")


def _validate_new_account(username: str, email: str, password: str, confirm: str) -> str | None:
    if not username or not email:
        return "A username and an email address are required."
    if len(password) < MIN_PASSWORD_LENGTH:
        return f"Choose a password of at least {MIN_PASSWORD_LENGTH} characters."
    if password != confirm:
        return "The two passwords do not match."
    return None


def _safe_next() -> str | None:
    target = request.args.get("next", "")
    return target if target.startswith("/") and not target.startswith("//") else None
