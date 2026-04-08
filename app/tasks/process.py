import os
import tempfile
import logging
from app.extensions import celery, db
from app.models import Meeting

logger = logging.getLogger(__name__)


@celery.task(bind=True, name="app.tasks.process.process_meeting", max_retries=2)
def process_meeting(self, meeting_id: int) -> dict:
    """
    Full meeting processing pipeline:
      1. Convert audio to WAV
      2. Transcribe via configured speech provider
      3. Generate minutes of meeting via configured LLM
      4. Persist results and clean up temp files
    """
    meeting = db.session.get(Meeting, meeting_id)
    if not meeting:
        raise ValueError(f"Meeting {meeting_id} not found")

    wav_path = None

    def _update(status: str, progress: int, **kwargs):
        meeting.status = status
        meeting.progress = progress
        for k, v in kwargs.items():
            setattr(meeting, k, v)
        db.session.commit()

    try:
        from flask import current_app
        upload_folder = current_app.config["UPLOAD_FOLDER"]
        audio_path = os.path.join(upload_folder, meeting.stored_filename)

        # ── Step 1: Convert audio ───────────────────────────────────────────
        _update("processing", 10)
        from app.utils.audio import convert_to_wav
        tmp_dir = tempfile.mkdtemp()
        wav_path = convert_to_wav(audio_path, output_dir=tmp_dir)
        _update("processing", 30)

        # ── Step 2: Transcribe ──────────────────────────────────────────────
        _update("transcribing", 35)
        from app.providers.speech import get_speech_provider
        speech_provider = get_speech_provider()
        transcript = speech_provider.transcribe_file(wav_path)
        _update("transcribing", 65, transcript=transcript)

        # ── Step 3: Generate Minutes of Meeting ─────────────────────────────
        _update("summarizing", 70)
        from app.providers.llm import get_llm_client
        import markdown as md_lib
        llm = get_llm_client()
        minutes_md = llm.generate_minutes(transcript)
        minutes_html = md_lib.markdown(minutes_md, extensions=["tables", "nl2br"])
        _update("summarizing", 90, minutes_of_meeting=minutes_html)

        # ── Step 4: Complete ─────────────────────────────────────────────────
        _update("completed", 100, transcript=transcript, minutes_of_meeting=minutes_html)
        return {"meeting_id": meeting_id, "status": "completed"}

    except Exception as exc:
        logger.exception("process_meeting failed for meeting %d", meeting_id)
        _update("failed", 0, error_message=str(exc))
        raise

    finally:
        if wav_path and os.path.exists(wav_path):
            try:
                os.remove(wav_path)
                os.rmdir(os.path.dirname(wav_path))
            except OSError:
                pass
