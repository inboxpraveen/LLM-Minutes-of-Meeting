from flask import Blueprint, render_template
from flask_login import current_user, login_required
from sqlalchemy import func

from app import health
from app.extensions import db
from app.models import ACTIVE_STATUSES, Meeting

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
@login_required
def index():
    query = db.session.query(Meeting)
    if not current_user.is_admin:
        query = query.filter(Meeting.user_id == current_user.id)

    counts = dict(
        query.with_entities(Meeting.status, func.count(Meeting.id)).group_by(Meeting.status).all()
    )
    stats = {
        "total": sum(counts.values()),
        "completed": counts.get("completed", 0),
        "processing": sum(counts.get(status, 0) for status in ACTIVE_STATUSES),
        "failed": counts.get("failed", 0),
    }
    recent = query.order_by(Meeting.created_at.desc()).limit(8).all()
    return render_template(
        "dashboard/index.html",
        stats=stats,
        recent=recent,
        providers_ready=health.check_providers()["ok"],
    )
