from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Meeting

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
@login_required
def index():
    q = Meeting.query.filter_by(user_id=current_user.id)

    total = q.count()
    completed = q.filter_by(status="completed").count()
    processing = db.session.query(Meeting).filter(
        Meeting.user_id == current_user.id,
        Meeting.status.in_(["pending", "processing", "transcribing", "summarizing"]),
    ).count()
    failed = q.filter_by(status="failed").count()

    recent = (
        Meeting.query.filter_by(user_id=current_user.id)
        .order_by(Meeting.created_at.desc())
        .limit(10)
        .all()
    )

    stats = {
        "total": total,
        "completed": completed,
        "processing": processing,
        "failed": failed,
    }
    return render_template("dashboard/index.html", stats=stats, recent=recent)
