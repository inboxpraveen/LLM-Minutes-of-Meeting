import logging
from datetime import timedelta

from app import settings
from app.extensions import celery, db
from app.models import ACTIVE_STATUSES, Meeting, as_utc, utcnow
from app.utils.storage import remove_recording

log = logging.getLogger("mom.maintenance")


@celery.task(name="app.tasks.maintenance.run_maintenance")
def run_maintenance() -> dict:
    """Runs every 15 minutes: apply retention, then fail jobs nobody is working on."""
    result = {"recordings_removed": _expire_recordings(), "jobs_timed_out": _fail_stale_jobs()}
    if any(result.values()):
        log.info("Maintenance: %s", result)
    return result


def _expire_recordings() -> int:
    """Delete recordings past their retention date. Transcripts and minutes stay."""
    expired = (
        db.session.query(Meeting)
        .filter(
            Meeting.expires_at.isnot(None),
            Meeting.expires_at < utcnow(),
            Meeting.source_deleted_at.is_(None),
        )
        .all()
    )

    removed = 0
    for meeting in expired:
        remove_recording(meeting)
        meeting.source_deleted_at = utcnow()
        meeting.log("Recording deleted after the retention period")
        removed += 1

    if removed:
        db.session.commit()
    return removed


def _fail_stale_jobs() -> int:
    """A worker that dies mid-job would otherwise leave a meeting processing forever."""
    limit = max(600, settings.get_int("job_time_limit_seconds"))
    cutoff = utcnow() - timedelta(seconds=limit + 600)

    stale = [
        meeting
        for meeting in db.session.query(Meeting).filter(Meeting.status.in_(ACTIVE_STATUSES)).all()
        if (as_utc(meeting.started_at) or as_utc(meeting.created_at) or utcnow()) < cutoff
    ]
    for meeting in stale:
        meeting.status = "failed"
        meeting.error_message = "The job stopped responding and was timed out by the maintenance check."
        meeting.finished_at = utcnow()
        meeting.log(meeting.error_message, level="error")

    if stale:
        db.session.commit()
    return len(stale)
