from flask import Blueprint, jsonify, abort
from flask_login import login_required, current_user
from app.models import Meeting

api_bp = Blueprint("api", __name__, url_prefix="/api/v1")


@api_bp.route("/meetings/<int:meeting_id>/status")
@login_required
def meeting_status(meeting_id: int):
    meeting = Meeting.query.filter_by(
        id=meeting_id, user_id=current_user.id
    ).first()
    if not meeting:
        abort(404)

    return jsonify(
        {
            "id": meeting.id,
            "status": meeting.status,
            "progress": meeting.progress,
            "error_message": meeting.error_message,
            "has_transcript": bool(meeting.transcript),
            "has_minutes": bool(meeting.minutes_of_meeting),
        }
    )


@api_bp.route("/meetings")
@login_required
def meetings_list():
    meetings = (
        Meeting.query.filter_by(user_id=current_user.id)
        .order_by(Meeting.created_at.desc())
        .limit(50)
        .all()
    )
    return jsonify(
        [
            {
                "id": m.id,
                "title": m.title,
                "status": m.status,
                "progress": m.progress,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in meetings
        ]
    )
