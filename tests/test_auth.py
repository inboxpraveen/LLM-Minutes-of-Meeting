from app.extensions import db
from app.models import User

from .conftest import ADMIN


def test_first_run_redirects_to_setup(client):
    assert client.get("/").headers["Location"].endswith("/auth/setup")


def test_setup_creates_the_administrator(client, app):
    response = client.post(
        "/auth/setup",
        data={"username": "owner", "email": "owner@example.com",
              "password": "longenough", "confirm_password": "longenough"},
        follow_redirects=False,
    )
    assert response.status_code == 302
    with app.app_context():
        user = db.session.query(User).filter_by(username="owner").first()
        assert user.is_admin and user.check_password("longenough")


def test_setup_rejects_mismatched_passwords(client, app):
    client.post(
        "/auth/setup",
        data={"username": "owner", "email": "owner@example.com",
              "password": "longenough", "confirm_password": "different"},
    )
    with app.app_context():
        assert db.session.query(User).count() == 0


def test_setup_closes_once_an_admin_exists(client, admin):
    assert client.get("/auth/setup").headers["Location"].endswith("/auth/login")


def test_sign_in_and_out(client, admin):
    response = client.post(
        "/auth/login", data={"username": ADMIN["username"], "password": ADMIN["password"]}
    )
    assert response.status_code == 302
    assert client.get("/").status_code == 200
    client.get("/auth/logout")
    assert client.get("/").status_code == 302


def test_account_locks_after_repeated_failures(client, admin, app):
    for _ in range(5):
        client.post("/auth/login", data={"username": ADMIN["username"], "password": "wrong"})

    with app.app_context():
        assert db.session.get(User, admin.id).is_locked

    response = client.post(
        "/auth/login", data={"username": ADMIN["username"], "password": ADMIN["password"]}
    )
    assert response.status_code == 200  # rejected while locked, no redirect


def test_users_page_requires_an_admin(client, admin, app):
    user = User(username="member", email="member@example.com", role="user", is_active=True)
    user.set_password("longenough")
    db.session.add(user)
    db.session.commit()
    app.config["SETUP_COMPLETE"] = True

    client.post("/auth/login", data={"username": "member", "password": "longenough"})
    assert client.get("/admin/users").status_code == 403


def test_deleting_a_user_who_saved_settings_succeeds(signed_in, app):
    """system_config.updated_by references users; the rows must outlive the user."""
    from app import settings
    from app.models import Meeting

    other = User(username="colleague", email="colleague@example.com", role="admin", is_active=True)
    other.set_password("longenough")
    db.session.add(other)
    db.session.commit()

    settings.save({"llm_model": "gpt-4o-mini"}, user_id=other.id)
    db.session.add(Meeting(user_id=other.id, title="Theirs", original_filename="a.mp3",
                           stored_filename="a.mp3", status="completed"))
    db.session.commit()

    response = signed_in.post(f"/admin/users/{other.id}/delete")
    assert response.status_code == 302
    assert db.session.get(User, other.id) is None
    assert db.session.query(Meeting).count() == 0
    assert settings.get("llm_model") == "gpt-4o-mini"
