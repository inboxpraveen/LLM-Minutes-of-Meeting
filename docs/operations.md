# Operations

## What runs

| Service | Role |
| --- | --- |
| `web` | Flask behind gunicorn. Serves the UI and the API. |
| `worker` | Celery. Converts audio, transcribes, summarises. |
| `beat` | Celery beat. Triggers maintenance every 15 minutes. |
| `redis` | Job queue and result backend. |
| `flower` | Optional Celery dashboard, `--profile monitoring`. |

`worker` and `beat` wait for `web` to report healthy before starting, so one process creates the
database and the encryption key rather than three racing to.

The web process runs one worker with eight threads. It only accepts uploads and serves pages; the
real work happens in `worker`. One process also keeps SQLite writes serialised and keeps the metrics
registry simple.

---

## Health and metrics

| Endpoint | Meaning |
| --- | --- |
| `GET /healthz` | Liveness. 200 whenever the process is up. This is what Docker's health check uses. |
| `GET /readyz` | Readiness. 200 only when the database, the job queue and ffmpeg are all usable. 503 otherwise, with a per-check breakdown. |
| `GET /metrics` | Prometheus exposition format. |

Metrics exposed:

| Metric | Type | Notes |
| --- | --- | --- |
| `mom_http_requests_total` | counter | By method, endpoint and status |
| `mom_http_request_seconds` | histogram | By endpoint |
| `mom_meetings_uploaded_total` | counter | Recordings accepted |
| `mom_meetings` | gauge | Meetings by status, refreshed on scrape |

A minimal scrape config:

```yaml
scrape_configs:
  - job_name: mom-ai
    static_configs:
      - targets: ['localhost:5000']
```

`/metrics` and `/readyz` are unauthenticated so a monitoring agent can reach them. They expose
counts and check results, never transcripts or keys. Keep them on an internal network, or block them
at your reverse proxy if the app is public.

**Admin → System** shows the same checks in the browser, along with disk usage, job counts, recent
failures and the last 300 log lines — enough to diagnose most problems without a shell.

---

## Logs

Logs go to stdout and to `logs/app.log` in the data directory, rotating at 10 MB with five files
kept. Every line carries a request id, also returned as the `X-Request-ID` response header, so a
browser error can be traced to its log lines.

```bash
docker compose logs -f web worker      # follow
LOG_FORMAT=json docker compose up      # structured output for a log shipper
LOG_LEVEL=DEBUG docker compose up      # more detail
```

---

## Background jobs

Jobs are acknowledged late and prefetch is set to one, so a worker killed mid-job leaves the meeting
queued for another worker rather than losing it. Three things protect against stuck work:

- A soft time limit equal to **Job time limit** in Settings, which fails the meeting with a clear
  message.
- A hard limit five minutes later, which kills the process.
- The maintenance job, which fails any meeting that has been running longer than the limit plus ten
  minutes — this is what recovers meetings whose worker died without warning.

Redis redelivers a job only after the hard limit has passed, so a long meeting is never picked up a
second time while the first attempt is still transcribing. Recovery from a dead worker therefore goes
through the maintenance job, and re-running is always an explicit choice you make.

Users can cancel a running job from the meeting page. The job stops at the end of the current step.
Failed and cancelled meetings can be run again as long as the recording is still on disk.

To process more meetings at once:

```bash
WORKER_CONCURRENCY=4 docker compose up -d
docker compose up -d --scale worker=3     # or add workers
```

Transcription is mostly waiting on an API, so concurrency well above core count is fine. Local
Whisper is CPU-bound: keep concurrency at 1 or 2.

---

## Backups

Everything lives in one directory.

```bash
# Docker
docker run --rm -v mom-ai_app_data:/data -v "$PWD":/backup alpine \
  tar czf /backup/mom-ai-backup.tar.gz -C /data .

# Without Docker, on Linux or macOS
tar czf mom-ai-backup.tar.gz -C ~/.local/share/MoM-AI .
```

Stop the app first, or accept that a meeting in flight may be inconsistent. `instance.key` must be in
the backup: without it the stored API keys cannot be decrypted.

Restore by extracting the archive back into the same location.

---

## Upgrades

```bash
git pull
docker compose up --build -d
```

Missing tables and columns are created at startup, so no migration command is needed. Take a backup
before upgrading anyway.

Upgrading from a version before 3.0, **without Docker**: if a database exists at `instance/app.db`, it
is copied into the new data directory on first start. Your meetings and users come with it, and old
minutes stored as HTML still render correctly.

Under Docker the old database lived in a different volume, so copy it across once before starting:

```bash
docker compose up -d web
docker compose cp ./instance/app.db web:/data/mom.db   # only if /data/mom.db does not exist yet
docker compose restart web worker beat
```

---

## Behind a reverse proxy

```bash
BEHIND_PROXY=true
SESSION_COOKIE_SECURE=true
```

The first makes the app trust `X-Forwarded-For` and `X-Forwarded-Proto` from exactly one proxy; the
second stops the session cookie being sent over plain HTTP.

nginx needs a raised body limit and a long timeout, or large uploads and long jobs will fail:

```nginx
location / {
    proxy_pass http://127.0.0.1:5000;
    proxy_set_header Host              $host;
    proxy_set_header X-Real-IP         $remote_addr;
    proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;

    client_max_body_size 2048m;
    proxy_read_timeout   3600s;
    proxy_send_timeout   3600s;
}
```

Keep `client_max_body_size` at or above the **Maximum upload size** setting.

---

## PostgreSQL

SQLite is the default and handles a team comfortably. For heavier use:

```yaml
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: mom
      POSTGRES_PASSWORD: change-me
      POSTGRES_DB: momai
    volumes:
      - pg_data:/var/lib/postgresql/data
```

Then set `DATABASE_URL=postgresql+psycopg://mom:change-me@postgres:5432/momai`. The driver is already
in the image. Tables are created on first start; existing SQLite data is not migrated automatically.

---

## Security notes

- The first screen creates the administrator account. There is no default password to forget to change.
- Sign-ins are throttled: five failures locks the account for 15 minutes.
- All forms are CSRF protected.
- API keys are encrypted at rest with a key held only on this machine.
- Model output is sanitised before it is rendered, so a prompt-injected transcript cannot inject
  script into the page.
- Regular users only ever see their own meetings. Administrators see all of them.
- The app makes no outbound calls other than to the providers you configure. No CDN, no fonts, no
  telemetry.
