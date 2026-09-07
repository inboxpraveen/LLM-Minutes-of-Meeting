import os
from datetime import timedelta

import pytest

from app import settings
from app.extensions import db
from app.models import Meeting, utcnow
from app.providers.llm import generate_minutes
from app.tasks import maintenance, process


class FakeSpeech:
    name = "fake"
    label = "Fake provider"

    def __init__(self, transcript="Ana: revenue is up. Ben: I will send the deck."):
        self.transcript = transcript

    def transcribe(self, audio_path):
        return self.transcript


class FakeLLM:
    def __init__(self, model="fake-model"):
        self.model = model
        self.calls = []

    def complete(self, system, user):
        self.calls.append((system, user))
        return "## Summary\n\nRevenue is up."


@pytest.fixture()
def meeting(app, admin):
    path = os.path.join(app.config["UPLOAD_FOLDER"], "recording.wav")
    with open(path, "wb") as handle:
        handle.write(b"audio")

    record = Meeting(
        user_id=admin.id, title="Weekly", original_filename="recording.wav",
        stored_filename="recording.wav", file_size=5, status="queued",
    )
    db.session.add(record)
    db.session.commit()
    return record


@pytest.fixture(autouse=True)
def stub_audio(monkeypatch, app):
    monkeypatch.setattr(
        process, "convert_to_wav",
        lambda source, workdir: os.path.join(app.config["UPLOAD_FOLDER"], "recording.wav"),
    )
    monkeypatch.setattr(process, "probe_duration", lambda path: 1830.0)


def _run(monkeypatch, speech=None, llm=None):
    """The task commits in its own app context, so expire the test session afterwards."""
    monkeypatch.setattr(process, "get_speech_provider", lambda config: speech or FakeSpeech())
    monkeypatch.setattr(process, "get_llm_client", lambda config: llm or FakeLLM())

    def run(meeting_id):
        result = process.process_meeting.apply(args=[meeting_id]).result
        db.session.expire_all()
        return result

    return run


def test_a_meeting_runs_end_to_end(monkeypatch, meeting):
    task = _run(monkeypatch)
    assert task(meeting.id)["status"] == "completed"

    done = db.session.get(Meeting, meeting.id)
    assert done.status == "completed"
    assert done.progress == 100
    assert done.transcript.startswith("Ana: revenue is up")
    assert done.minutes_of_meeting.startswith("## Summary")
    assert done.duration_seconds == 1830.0
    assert done.speech_provider == "fake"
    assert done.llm_model == "fake-model"
    assert done.finished_at is not None

    messages = [event.message for event in done.events]
    assert any("Transcribing" in m for m in messages)
    assert "Minutes ready" in messages


def test_an_empty_transcript_fails_with_a_clear_message(monkeypatch, meeting):
    task = _run(monkeypatch, speech=FakeSpeech(transcript="   "))
    task(meeting.id)

    failed = db.session.get(Meeting, meeting.id)
    assert failed.status == "failed"
    assert "empty transcript" in failed.error_message


def test_provider_errors_are_recorded_not_raised(monkeypatch, meeting):
    class Broken(FakeSpeech):
        def transcribe(self, audio_path):
            raise RuntimeError("401 Unauthorized")

    task = _run(monkeypatch, speech=Broken())
    assert task(meeting.id)["status"] == "failed"

    failed = db.session.get(Meeting, meeting.id)
    assert failed.error_message == "401 Unauthorized"
    assert any(event.level == "error" for event in failed.events)


def test_a_cancelled_meeting_stops_between_steps(monkeypatch, meeting):
    meeting.cancel_requested = True
    db.session.commit()

    task = _run(monkeypatch)
    assert task(meeting.id)["status"] == "cancelled"
    assert db.session.get(Meeting, meeting.id).status == "cancelled"


def test_the_recording_is_deleted_when_that_setting_is_off(monkeypatch, meeting, app):
    settings.save({"keep_source_after_processing": "false"})
    task = _run(monkeypatch)
    task(meeting.id)

    done = db.session.get(Meeting, meeting.id)
    assert done.source_deleted_at is not None
    assert not os.path.exists(os.path.join(app.config["UPLOAD_FOLDER"], "recording.wav"))


def test_long_transcripts_are_summarised_in_parts():
    llm = FakeLLM()
    transcript = "\n\n".join(f"Speaker {i}: " + "word " * 200 for i in range(30))
    result = generate_minutes(llm, transcript, "PROMPT", chunk_chars=2000)

    assert len(llm.calls) > 2
    assert llm.calls[-1][0] == "PROMPT"
    assert "Part 1 of" in llm.calls[-1][1]
    assert result.startswith("## Summary")


def test_short_transcripts_use_a_single_call():
    llm = FakeLLM()
    generate_minutes(llm, "a short transcript", "PROMPT", chunk_chars=48000)
    assert len(llm.calls) == 1


def test_retention_deletes_recordings_but_keeps_the_minutes(app, meeting):
    meeting.status = "completed"
    meeting.minutes_of_meeting = "## Summary"
    meeting.expires_at = utcnow() - timedelta(days=1)
    db.session.commit()

    assert maintenance._expire_recordings() == 1

    kept = db.session.get(Meeting, meeting.id)
    assert kept.minutes_of_meeting == "## Summary"
    assert kept.source_deleted_at is not None
    assert not os.path.exists(os.path.join(app.config["UPLOAD_FOLDER"], "recording.wav"))


def test_abandoned_jobs_are_timed_out(app, meeting):
    meeting.status = "transcribing"
    meeting.started_at = utcnow() - timedelta(days=2)
    db.session.commit()

    assert maintenance._fail_stale_jobs() == 1
    assert db.session.get(Meeting, meeting.id).status == "failed"
