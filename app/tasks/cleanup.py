import os
import logging
from datetime import datetime, timezone
from app.extensions import celery, db
from app.models import Meeting

logger = logging.getLogger(__name__)


@celery.task(name="app.tasks.cleanup.cleanup_expired_meetings")
def cleanup_expired_meetings() -> dict:
    """
    Periodic task (runs hourly via Celery beat).
    Deletes meeting records whose expires_at is in the past,
    and removes the associated uploaded files from disk.
    """
    from flask import current_app

    now = datetime.now(timezone.utc)
    expired = Meeting.query.filter(
        Meeting.expires_at != None,  # noqa: E711
        Meeting.expires_at < now,
        Meeting.deleted_at == None,  # noqa: E711
    ).all()

    deleted_count = 0
    upload_folder = current_app.config["UPLOAD_FOLDER"]

    for meeting in expired:
        file_path = os.path.join(upload_folder, meeting.stored_filename)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError as exc:
                logger.warning("Could not remove file %s: %s", file_path, exc)

        meeting.deleted_at = now
        db.session.delete(meeting)
        deleted_count += 1

    db.session.commit()
    logger.info("Cleanup: removed %d expired meeting(s)", deleted_count)
    return {"deleted": deleted_count}
