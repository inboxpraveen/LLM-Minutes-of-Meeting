import os
import tempfile

# The data directory is read when app.paths and app.security are first imported.
os.environ["MOM_DATA_DIR"] = tempfile.mkdtemp(prefix="mom-tests-")
os.environ["CELERY_BROKER_URL"] = "memory://"
os.environ["CELERY_RESULT_BACKEND"] = "cache+memory://"

import pytest  # noqa: E402

from app import create_app, settings  # noqa: E402
from app.extensions import db, sync_schema  # noqa: E402
from app.models import User  # noqa: E402

ADMIN = {"username": "admin", "email": "admin@example.com", "password": "supersecret"}


@pytest.fixture()
def app():
    application = create_app()
    application.config.update(TESTING=True, WTF_CSRF_ENABLED=False, SETUP_COMPLETE=False)
    with application.app_context():
        db.drop_all()
        sync_schema()
        settings.seed_from_env()
        yield application
        db.session.remove()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def admin(app):
    user = User(username=ADMIN["username"], email=ADMIN["email"], role="admin", is_active=True)
    user.set_password(ADMIN["password"])
    db.session.add(user)
    db.session.commit()
    app.config["SETUP_COMPLETE"] = True
    return user


@pytest.fixture()
def signed_in(client, admin):
    client.post("/auth/login", data={"username": ADMIN["username"], "password": ADMIN["password"]})
    return client
