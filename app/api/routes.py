from flask import Blueprint, Response, abort, jsonify
from flask_login import current_user, login_required
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app import health
from app.extensions import db
from app.metrics import refresh_status_gauge
from app.models import Meeting, MeetingEvent

api_bp = Blueprint("api", __name__)


@api_bp.route("/healthz")
def healthz():
    """Liveness: the process is up and serving."""
    return jsonify({"status": "ok"})


@api_bp.route("/readyz")
def readyz():
    """Readiness: the app can accept and queue work."""
    ready, checks = health.readiness()
    return jsonify({"status": "ready" if ready else "not ready", "checks": checks}), 200 if ready else 503


@api_bp.route("/metrics")
def metrics():
    refresh_status_gauge()
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


@api_bp.route("/api/v1/meetings/<int:meeting_id>/status")
@login_required
def meeting_status(meeting_id: int):
    meeting = _get_meeting(meeting_id)
    events = (
        meeting.events.order_by(MeetingEvent.created_at.desc(), MeetingEvent.id.desc()).limit(20).all()
    )
    return jsonify(
        {
            "id": meeting.id,
            "status": meeting.status,
            "progress": meeting.progress or 0,
            "error_message": meeting.error_message,
            "has_transcript": bool(meeting.transcript),
            "has_minutes": bool(meeting.minutes_of_meeting),
            "events": [
                {
                    "level": e.level,
                    "message": e.message,
                    "at": e.created_at.isoformat() if e.created_at else None,
                }
                for e in events
            ],
        }
    )


@api_bp.route("/api/v1/meetings")
@login_required
def meetings_list():
    query = db.session.query(Meeting)
    if not current_user.is_admin:
        query = query.filter(Meeting.user_id == current_user.id)
    meetings = query.order_by(Meeting.created_at.desc()).limit(50).all()
    return jsonify(
        [
            {
                "id": m.id,
                "title": m.title,
                "status": m.status,
                "progress": m.progress or 0,
                "duration_seconds": m.duration_seconds,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in meetings
        ]
    )


def _get_meeting(meeting_id: int) -> Meeting:
    query = db.session.query(Meeting).filter(Meeting.id == meeting_id)
    if not current_user.is_admin:
        query = query.filter(Meeting.user_id == current_user.id)
    meeting = query.first()
    if meeting is None:
        abort(404)
    return meeting
