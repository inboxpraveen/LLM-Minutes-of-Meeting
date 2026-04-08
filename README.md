# MoM AI — AI-Powered Minutes of Meeting

---

## Recall.ai - API for meeting recording

If you’re looking for a meeting recording API, consider checking out [Recall.ai](https://www.recall.ai), an API that records Zoom, Google Meet, Microsoft Teams, in-person meetings, and more.

> Sponsored by [Recall.ai](https://www.recall.ai) — The unified API for meeting bots.

---

A clean, modern web application that transcribes meeting recordings and generates structured **Minutes of Meeting** using your preferred AI providers. Upload once, get professional meeting minutes automatically.

---

## Features

- **AI Transcription** — Deepgram, AssemblyAI, Sarvam AI, or ElevenLabs
- **Smart Summarization** — Any OpenAI-compatible LLM (OpenAI, OpenRouter, Groq, Together, Azure, Ollama, etc.)
- **Background Processing** — Celery + Redis; upload and come back when it's done
- **Auto Cleanup** — Files auto-deleted after a configurable number of days
- **Two Roles** — Admin (full config access) + User (upload & view only)
- **Modern UI** — Light-themed, fully responsive, smooth animations
- **Docker-ready** — One command to spin up everything

---

## Quick Start

### 1. Configure environment

```bash
cp .env.example .env
# Edit .env — set your API keys
```

### 2a. Docker (recommended)

```bash
docker compose up --build
```

App is available at `http://localhost:5000`

### 2b. Local development

**Prerequisites:** Python 3.12+, Redis, ffmpeg

```bash
# Install dependencies
pip install -r requirements.txt

# Start Redis (one terminal)
redis-server

# Start Celery worker (another terminal)
celery -A celery_worker:celery worker -l info

# Start Celery beat for periodic cleanup (another terminal)
celery -A celery_worker:celery beat -l info

# Start Flask app
python run.py
```

---

## Default Login


| Field    | Value       |
| -------- | ----------- |
| Username | `admin`     |
| Password | `admin@123` |


> Change these in `.env` before deploying.

---

## Admin Panel

Log in as admin and navigate to **Settings** to configure:


| Tab                 | What you can set                              |
| ------------------- | --------------------------------------------- |
| **LLM Provider**    | Base URL, API key, model name                 |
| **Speech Provider** | Active provider, API keys for all 4 providers |
| **Storage**         | Retention days (how long files are kept)      |


Navigate to **Users** to create/manage user accounts.

---

## LLM Provider Examples

The app uses the OpenAI client format — works with any compatible endpoint:


| Provider       | `LLM_BASE_URL`                   | Example model                    |
| -------------- | -------------------------------- | -------------------------------- |
| OpenAI         | `https://api.openai.com/v1`      | `gpt-4o`                         |
| OpenRouter     | `https://openrouter.ai/api/v1`   | `anthropic/claude-opus-4`        |
| Groq           | `https://api.groq.com/openai/v1` | `llama-3.3-70b-versatile`        |
| Together AI    | `https://api.together.xyz/v1`    | `meta-llama/Llama-3-70b-chat-hf` |
| Ollama (local) | `http://localhost:11434/v1`      | `llama3.2`                       |


---

## Speech Providers


| Provider       | Notes                                 |
| -------------- | ------------------------------------- |
| **Deepgram**   | Nova-3 model, fastest & most accurate |
| **AssemblyAI** | High accuracy, speaker diarisation    |
| **Sarvam AI**  | Best for Indian languages + English   |
| **ElevenLabs** | Scribe v1 model                       |


---

## Project Structure

```
├── app/
│   ├── __init__.py          # App factory + seeding
│   ├── config.py            # All configuration
│   ├── extensions.py        # db, login_manager, celery
│   ├── models.py            # User, Meeting, SystemConfig
│   ├── auth/                # Login / logout
│   ├── dashboard/           # Dashboard home
│   ├── meetings/            # Upload, list, detail, delete
│   ├── admin/               # Settings + user management
│   ├── api/                 # REST endpoints (status polling)
│   ├── tasks/               # Celery tasks (process + cleanup)
│   ├── providers/
│   │   ├── llm/             # OpenAI-compatible LLM client
│   │   └── speech/          # Deepgram, AssemblyAI, Sarvam, ElevenLabs
│   ├── utils/               # ffmpeg audio conversion
│   ├── static/              # CSS + JS
│   └── templates/           # Jinja2 HTML templates
├── celery_worker.py         # Celery entry point
├── run.py                   # Flask entry point
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

