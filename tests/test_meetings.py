import io
import os

from app.extensions import db
from app.models import Meeting, User

from .conftest import ADMIN


def _upload(client, filename="standup.mp3", body=b"fake audio bytes", title=""):
    return client.post(
        "/meetings/upload",
        data={"file": (io.BytesIO(body), filename), "title": title},
        content_type="multipart/form-data",
        follow_redirects=False,
    )


def test_upload_stores_the_file_and_queues_a_job(signed_in, app):
    assert _upload(signed_in, title="Weekly standup").status_code == 302

    meeting = db.session.query(Meeting).one()
    assert meeting.title == "Weekly standup"
    assert meeting.status == "queued"
    assert meeting.task_id
    assert meeting.expires_at is not None
    assert os.path.exists(os.path.join(app.config["UPLOAD_FOLDER"], meeting.stored_filename))
    assert [event.message for event in meeting.events] == ["Uploaded"]


def test_title_falls_back_to_the_filename(signed_in):
    _upload(signed_in, filename="board-review.m4a")
    assert db.session.query(Meeting).one().title == "board-review"


def test_unsupported_file_types_are_rejected(signed_in):
    assert _upload(signed_in, filename="notes.pdf").status_code == 302
    assert db.session.query(Meeting).count() == 0


def test_uploads_above_the_configured_limit_are_refused(signed_in, app):
    from app import settings

    settings.save({"max_upload_size_mb": "1"})
    response = _upload(signed_in, body=b"x" * (2 * 1024 * 1024))
    assert response.status_code == 413
    assert db.session.query(Meeting).count() == 0


def test_downloads_return_the_stored_text(signed_in):
    _upload(signed_in)
    meeting = db.session.query(Meeting).one()
    meeting.transcript = "Ana: hello"
    meeting.minutes_of_meeting = "## Summary\n\nAll good."
    db.session.commit()

    minutes = signed_in.get(f"/meetings/{meeting.id}/download/minutes")
    assert minutes.status_code == 200
    assert b"## Summary" in minutes.data
    assert "attachment" in minutes.headers["Content-Disposition"]

    transcript = signed_in.get(f"/meetings/{meeting.id}/download/transcript")
    assert transcript.data == b"Ana: hello"


def test_cancel_marks_the_job_for_cancellation(signed_in):
    _upload(signed_in)
    meeting = db.session.query(Meeting).one()
    meeting.status = "transcribing"
    db.session.commit()

    signed_in.post(f"/meetings/{meeting.id}/cancel")
    assert db.session.get(Meeting, meeting.id).cancel_requested is True


def test_retry_requeues_a_failed_meeting(signed_in):
    _upload(signed_in)
    meeting = db.session.query(Meeting).one()
    meeting.status = "failed"
    meeting.error_message = "provider down"
    db.session.commit()

    signed_in.post(f"/meetings/{meeting.id}/retry")
    refreshed = db.session.get(Meeting, meeting.id)
    assert refreshed.status == "queued" and refreshed.error_message is None


def test_delete_removes_the_row_and_the_file(signed_in, app):
    _upload(signed_in)
    meeting = db.session.query(Meeting).one()
    path = os.path.join(app.config["UPLOAD_FOLDER"], meeting.stored_filename)

    signed_in.post(f"/meetings/{meeting.id}/delete")
    assert db.session.query(Meeting).count() == 0
    assert not os.path.exists(path)


def test_users_cannot_open_another_persons_meeting(client, admin, app):
    other = User(username="member", email="member@example.com", role="user", is_active=True)
    other.set_password("longenough")
    db.session.add(other)
    db.session.commit()
    app.config["SETUP_COMPLETE"] = True

    client.post("/auth/login", data={"username": ADMIN["username"], "password": ADMIN["password"]})
    _upload(client)
    meeting_id = db.session.query(Meeting).one().id
    client.get("/auth/logout")

    client.post("/auth/login", data={"username": "member", "password": "longenough"})
    assert client.get(f"/meetings/{meeting_id}").status_code == 404


def test_detail_page_renders_minutes_as_html(signed_in):
    _upload(signed_in)
    meeting = db.session.query(Meeting).one()
    meeting.status = "completed"
    meeting.minutes_of_meeting = "## Summary\n\n| Task | Owner |\n| --- | --- |\n| Ship | Ana |"
    db.session.commit()

    body = signed_in.get(f"/meetings/{meeting.id}").get_data(as_text=True)
    assert "<h2>Summary</h2>" in body
    assert "<td>Ship</td>" in body


def test_detail_page_does_not_execute_model_output(signed_in):
    _upload(signed_in)
    meeting = db.session.query(Meeting).one()
    meeting.status = "completed"
    meeting.minutes_of_meeting = "## Summary\n\n<script>alert(1)</script>"
    db.session.commit()

    body = signed_in.get(f"/meetings/{meeting.id}").get_data(as_text=True)
    assert "<script>alert(1)</script>" not in body


def test_upload_page_passes_config_without_breaking_the_alpine_attribute(signed_in):
    """A JSON list inside x-data="…" would end the attribute at its first quote."""
    body = signed_in.get("/meetings/upload").get_data(as_text=True)
    assert 'x-data="uploadForm()"' in body
    assert 'data-allowed="aac,avi,' in body
    assert 'data-max-mb="2048"' in body
