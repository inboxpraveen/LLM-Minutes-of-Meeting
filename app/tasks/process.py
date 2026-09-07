import logging
import os
import shutil
import tempfile

from celery.exceptions import SoftTimeLimitExceeded

from app import settings
from app.extensions import celery, db
from app.models import Meeting, utcnow
from app.providers.llm import generate_minutes, get_llm_client
from app.providers.speech import get_speech_provider
from app.utils.audio import convert_to_wav, probe_duration
from app.utils.storage import recording_path, remove_recording

log = logging.getLogger("mom.task")


class Cancelled(Exception):
    pass


@celery.task(bind=True, name="app.tasks.process.process_meeting")
def process_meeting(self, meeting_id: int) -> dict:
    """Convert the recording, transcribe it, then write the minutes."""
    meeting = db.session.get(Meeting, meeting_id)
    if meeting is None:
        log.warning("Meeting %s no longer exists", meeting_id)
        return {"meeting_id": meeting_id, "status": "missing"}
    if meeting.status == "completed":
        return {"meeting_id": meeting_id, "status": "completed"}

    config = settings.snapshot()
    workdir = tempfile.mkdtemp(prefix="mom-")
    meeting.started_at = utcnow()
    meeting.error_message = None
    meeting.task_id = self.request.id or meeting.task_id

    def step(status: str, progress: int, message: str | None = None) -> None:
        meeting.status = status
        meeting.progress = progress
        if message:
            meeting.log(message)
        db.session.commit()

    def guard() -> None:
        db.session.commit()  # persists pending changes and expires the row, so this re-reads it
        if meeting.cancel_requested:
            raise Cancelled()

    try:
        source = recording_path(meeting)
        if not os.path.exists(source):
            raise RuntimeError("The uploaded recording is no longer on disk.")

        guard()
        step("converting", 5, "Preparing audio")
        audio = convert_to_wav(source, workdir)
        meeting.duration_seconds = probe_duration(audio)
        step("converting", 15, f"Audio ready ({meeting.duration_label})")

        guard()
        provider = get_speech_provider(config)
        meeting.speech_provider = provider.name
        step("transcribing", 20, f"Transcribing with {provider.label}")
        transcript = (provider.transcribe(audio) or "").strip()
        if not transcript:
            raise RuntimeError(
                f"{provider.label} returned an empty transcript. "
                "The recording may be silent or in an unsupported language."
            )
        meeting.transcript = transcript
        step("transcribing", 65, f"Transcript ready ({len(transcript.split()):,} words)")

        guard()
        client = get_llm_client(config)
        meeting.llm_model = client.model
        step("summarizing", 70, f"Writing minutes with {client.model}")

        def on_progress(done: int, total: int) -> None:
            step("summarizing", 70 + int(25 * done / total), f"Summarised part {done} of {total}")

        meeting.minutes_of_meeting = generate_minutes(
            client,
            transcript,
            config.get("minutes_prompt") or settings.DEFAULT_MINUTES_PROMPT,
            _positive(config.get("transcript_chunk_chars"), 48000),
            on_progress,
        )

        meeting.finished_at = utcnow()
        step("completed", 100, "Minutes ready")
        _discard_source_if_requested(meeting, config)
        return {"meeting_id": meeting_id, "status": "completed"}

    except Cancelled:
        meeting.finished_at = utcnow()
        step("cancelled", meeting.progress or 0, "Cancelled")
        return {"meeting_id": meeting_id, "status": "cancelled"}

    except SoftTimeLimitExceeded:
        _fail(meeting, "The job exceeded the configured time limit. Raise it in Settings → Processing.")
        raise

    except Exception as exc:
        log.exception("Processing failed for meeting %s", meeting_id)
        _fail(meeting, str(exc) or exc.__class__.__name__)
        return {"meeting_id": meeting_id, "status": "failed"}

    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def _fail(meeting: Meeting, message: str) -> None:
    meeting.status = "failed"
    meeting.error_message = message[:2000]
    meeting.finished_at = utcnow()
    meeting.log(message, level="error")
    db.session.commit()


def _discard_source_if_requested(meeting: Meeting, config: dict) -> None:
    if str(config.get("keep_source_after_processing", "true")).lower() in {"1", "true", "yes", "on"}:
        return
    if remove_recording(meeting):
        meeting.source_deleted_at = utcnow()
        meeting.log("Recording deleted after processing")
        db.session.commit()


def _positive(value, fallback: int) -> int:
    try:
        return max(2000, int(float(value)))
    except (TypeError, ValueError):
        return fallback
