import logging
import os

from flask import current_app

log = logging.getLogger("mom.storage")


def recording_path(meeting) -> str:
    return os.path.join(current_app.config["UPLOAD_FOLDER"], meeting.stored_filename)


def remove_recording(meeting) -> bool:
    """Delete an uploaded recording from disk. True when a file was actually removed."""
    path = recording_path(meeting)
    try:
        if os.path.exists(path):
            os.remove(path)
            return True
    except OSError as exc:
        log.warning("Could not delete %s: %s", path, exc)
    return False
