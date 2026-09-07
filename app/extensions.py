from celery import Celery
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import event, inspect, text
from sqlalchemy.engine import Engine

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
celery = Celery("mom")

login_manager.login_view = "auth.login"
login_manager.login_message = "Please sign in to continue."
login_manager.login_message_category = "info"


@event.listens_for(Engine, "connect")
def _sqlite_pragmas(dbapi_connection, connection_record):
    """WAL keeps the web process readable while a worker is writing."""
    if type(dbapi_connection).__module__.startswith("sqlite3"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=10000")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def sync_schema() -> None:
    """Create missing tables and add columns introduced by a newer version.

    Keeps upgrades working without a migration tool, which is enough for a
    schema that only ever grows.
    """
    db.create_all()
    engine = db.engine
    inspector = inspect(engine)
    with engine.begin() as conn:
        for table in db.metadata.sorted_tables:
            if not inspector.has_table(table.name):
                continue
            present = {c["name"] for c in inspector.get_columns(table.name)}
            for column in table.columns:
                if column.name in present:
                    continue
                ddl = f'ALTER TABLE "{table.name}" ADD COLUMN "{column.name}" ' \
                      f"{column.type.compile(engine.dialect)}"
                conn.execute(text(ddl))
