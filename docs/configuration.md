# Configuration

Almost everything is configured from **Settings** in the app, by an administrator, and stored in the
local database. Secrets are encrypted at rest. Changes take effect on the next job — there is nothing
to restart.

A handful of values have to be known before the database exists. Those are environment variables, and
all of them are optional.

---

## Settings screen

### LLM provider

| Setting | Default | What it does |
| --- | --- | --- |
| Base URL | empty | Any OpenAI-compatible endpoint. Presets fill this in. |
| API key | empty | Encrypted at rest. Leave blank to keep the saved key; tick **Remove the saved key** to erase it. |
| Model | empty | The exact model id your provider expects. |
| Temperature | `0.2` | Lower produces more consistent minutes. |
| Max output tokens | `4000` | Upper bound on the generated minutes. |
| Request timeout | `300` | Seconds to wait for a single completion. |

Press **Test** to send one tiny request. It uses whatever is currently in the form, so you can verify
a key before saving it.

### Speech provider

| Setting | Default | What it does |
| --- | --- | --- |
| Active provider | `deepgram` | Only this provider is used. The fields below it change to match. |
| Language | empty | ISO code such as `en` or `hi`. Blank means auto-detect. |
| Speaker diarization | on | Labels who said what. Not available on OpenAI-compatible or local Whisper. |

Each provider then has its own key and model field. See [providers.md](providers.md).

### Processing

| Setting | Default | What it does |
| --- | --- | --- |
| Minutes prompt | see below | The instructions sent to the LLM. Edit it to match how your team writes minutes. |
| Transcript chunk size | `48000` characters | Transcripts longer than this are summarised in parts and merged. Roughly 12,000 tokens. |
| Audio chunk length | `600` seconds | Used when a transcription endpoint has an upload size limit. |
| Job time limit | `10800` seconds | A job running longer than this is marked failed and released. |

The default prompt asks for Summary, Attendees, Key Discussion Points, Decisions Made, Action Items
(as a table) and Next Steps. Rewrite the section headings and the output changes to match — the app
does not depend on any particular structure.

### Storage

| Setting | Default | What it does |
| --- | --- | --- |
| Retention period | `30` days | Recordings are deleted this many days after upload. **Transcripts and minutes are always kept.** |
| Maximum upload size | `2048` MB | Enforced in the browser and again on the server. |
| Keep recording after processing | on | Turn off to delete the recording as soon as the minutes are written. |

Retention is applied by a maintenance job that runs every 15 minutes. Changing the setting affects
recordings uploaded from that point on; existing ones keep the expiry date they were given.

---

## Environment variables

All optional. Copy `.env.example` to `.env` if you want to set any of them.

| Variable | Default | Purpose |
| --- | --- | --- |
| `APP_PORT` | `5000` | Host port published by Docker Compose. |
| `MOM_DATA_DIR` | OS data directory | Where the database, uploads, logs and encryption key live. |
| `UPLOAD_FOLDER` | `<data dir>/uploads` | Put recordings on a different disk from the database. |
| `WITH_LOCAL_WHISPER` | `false` | Build the image with local Whisper included. |
| `WORKER_CONCURRENCY` | `2` | Meetings processed in parallel by one worker. |
| `FLOWER_PORT` | `5555` | Host port for the optional Celery dashboard. |
| `CELERY_BROKER_URL` | `redis://localhost:6379/0` | Set automatically by Compose. |
| `CELERY_RESULT_BACKEND` | same as broker | Set automatically by Compose. |
| `DATABASE_URL` | SQLite in the data directory | Point at PostgreSQL for a larger deployment. |
| `LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR`. |
| `LOG_FORMAT` | `console` | `json` for log shippers. |
| `BEHIND_PROXY` | `false` | Trust `X-Forwarded-*` headers from one proxy. |
| `SESSION_COOKIE_SECURE` | `false` | Set to `true` when serving over HTTPS. |
| `SECRET_KEY` | derived from the local key file | Only needed if several web containers must share sessions. |
| `FLASK_DEBUG` | `false` | Development server with auto-reload. Never use in production. |
| `APP_VERSION` | `3.0.0` | Shown in the sidebar. Handy when you run a fork. |

---

## Data directory

| Platform | Location |
| --- | --- |
| Windows | `%LOCALAPPDATA%\MoM-AI` |
| macOS | `~/Library/Application Support/MoM-AI` |
| Linux | `~/.local/share/MoM-AI` |
| Docker | the `app_data` volume, at `/data` |

```
mom.db                 SQLite database: users, meetings, transcripts, minutes, settings
instance.key           Encrypts stored API keys and signs sessions
uploads/               Uploaded recordings, removed on the retention schedule
logs/app.log           Rotating application log, 10 MB × 5 files
models/                Whisper models, only when using local transcription
```

`instance.key` is the one file you cannot regenerate: without it the stored API keys cannot be
decrypted and you will have to enter them again. Include the whole directory in your backups.
