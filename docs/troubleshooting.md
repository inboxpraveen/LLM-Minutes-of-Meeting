# Troubleshooting

Start at **Admin → System**. It checks the database, the job queue, the workers, ffmpeg, disk space
and whether your providers are configured, and it shows the tail of the log. Most answers are there.

---

## Meetings stay "Queued" forever

No worker is running, or it cannot reach Redis. **Admin → System → Workers** will say so.

```bash
docker compose ps
docker compose logs worker
docker compose up -d worker
```

Without Docker, the worker is a separate process and has to be started:

```bash
celery -A celery_worker:celery worker -l info
```

## "The job queue is unreachable"

Redis is down or the broker URL is wrong. Under Compose it is set for you. Running without Docker,
start Redis and check `CELERY_BROKER_URL` points at `localhost`, not `redis`.

## "ffmpeg was not found"

ffmpeg converts every recording to a common format before transcription.

- Docker: already included. If you see this, the image is stale — rebuild with `--build`.
- macOS: `brew install ffmpeg`
- Debian or Ubuntu: `sudo apt install ffmpeg`
- Windows: `winget install ffmpeg`, then open a new terminal

## 401 or "Incorrect API key"

Almost always a key used against the wrong base URL. An OpenRouter key starts with `sk-or-v1-` and
only works with `https://openrouter.ai/api/v1`. Press **Test** in Settings — it reports the
provider's own error message.

## "The LLM returned an empty response"

The model produced nothing. Usually one of:

- The model id is wrong or not available on your account
- **Max output tokens** is too low for a full set of minutes
- The provider refused the content

Try a different model, or raise the limit in **Settings → Processing**.

## "returned an empty transcript"

The provider transcribed the audio and found no speech. Check the recording plays and has audio, and
set the language explicitly in **Settings → Speech provider** if it is not English.

## Uploads fail at a certain size

Two limits apply. **Settings → Storage → Maximum upload size** is the app's. If you are behind nginx,
`client_max_body_size` is the other, and it must be at least as large.

## Transcription is slow

Hosted APIs usually run several times faster than real time. Local Whisper on a CPU does not — that
is expected. Use `base` or `distil-large-v3`, set compute type to `int8`, or switch to a hosted
provider for long recordings.

## Local Whisper says it is not installed

The image was built without it:

```bash
WITH_LOCAL_WHISPER=true docker compose up --build
```

Without Docker: `pip install -r requirements-local.txt`.

## A job is stuck "Transcribing"

Cancel it from the meeting page. If the worker died, the maintenance job fails the meeting
automatically once the job time limit plus ten minutes has passed. Then press **Run again**.

## I forgot the administrator password

Reset it from the shell on the machine running the app:

```bash
docker compose exec web python -c "
from app import create_app
from app.extensions import db
from app.models import User
app = create_app()
with app.app_context():
    user = db.session.query(User).filter_by(role='admin').first()
    user.set_password('a-new-password')
    user.locked_until = None
    db.session.commit()
    print('Password reset for', user.username)
"
```

Drop `docker compose exec web` when running without Docker.

## "Too many failed attempts"

Five wrong passwords locks an account for 15 minutes. Another administrator can reset it from
**Admin → Users**, or wait it out.

## The page looks unstyled

`app/static/css/tailwind.css` is missing. It is committed to the repository, so this means an
incomplete checkout. Rebuild it:

```bash
npm install && npm run build:css
```

## Starting over

This deletes every meeting, user and setting:

```bash
docker compose down -v && docker compose up --build
```

Without Docker, delete the data directory shown in **Admin → System**.
