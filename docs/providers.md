# Providers

Two choices, both made in **Settings**: who turns audio into text, and who turns text into minutes.
Neither is locked in.

---

## Transcription

### Deepgram

Speaker labels, fast, accurate. Get a key at [console.deepgram.com](https://console.deepgram.com/).

- Model: `nova-3` (default)
- Handles long recordings directly, no splitting needed

### AssemblyAI

Speaker labels and strong accuracy. Get a key at
[assemblyai.com/dashboard](https://www.assemblyai.com/dashboard/).

- Models: `universal` (default), `slam_1`, `best`, `nano`
- Language is auto-detected unless you set one

### ElevenLabs Scribe

Very good on multilingual audio. Get a key at [elevenlabs.io](https://elevenlabs.io/).

- Model: `scribe_v2` (default)
- Stereo recordings are treated as one speaker per channel, which gives clean attribution for
  two-party calls

### Sarvam AI

The best option for Indian languages and code-mixed English. Get a key at
[dashboard.sarvam.ai](https://dashboard.sarvam.ai/).

- Model: `saaras:v3` (default). `saarika:v2.5` is the older model and is being retired
- Uses the batch job API, so recording length is not capped
- The job is polled every 10 seconds for up to two hours

### OpenAI-compatible endpoint

Anything exposing `/v1/audio/transcriptions`. No speaker labels — the API has no notion of them.
Recordings over 24 MB are split with ffmpeg and stitched back together, so the 25 MB limit that
OpenAI and Groq impose never applies.

| Service | Base URL | Model |
| --- | --- | --- |
| OpenAI | `https://api.openai.com/v1` | `gpt-4o-transcribe` or `whisper-1` |
| Groq | `https://api.groq.com/openai/v1` | `whisper-large-v3-turbo` |
| [Speaches](https://github.com/speaches-ai/speaches) | `http://localhost:8000/v1` | `Systran/faster-whisper-large-v3` |
| [LocalAI](https://localai.io/) | `http://localhost:8080/v1` | whichever model you loaded |

### Local Whisper

Transcription on your own machine. No API key, no per-minute cost, and no audio leaves the computer.
Speaker labels are not available.

Include it in the image:

```bash
WITH_LOCAL_WHISPER=true docker compose up --build
```

Without Docker: `pip install -r requirements-local.txt`.

| Model | Size | Roughly |
| --- | --- | --- |
| `tiny` | 75 MB | Fastest, least accurate |
| `base` | 145 MB | Default. Fine for clear audio |
| `small` | 480 MB | A good balance |
| `medium` | 1.5 GB | Noticeably better |
| `large-v3` | 3 GB | Best accuracy, slow on CPU |
| `distil-large-v3` | 1.5 GB | Close to `large-v3`, considerably faster |

The model downloads once on first use and is cached in the data directory. Leave **Device** on `auto`
unless you want to force `cpu` or `cuda`, and set **Compute type** to
`int8` on a CPU and `float16` on a GPU. On CPU, expect roughly real-time with `base` and several
times slower with `large-v3` — start with `base` or `distil-large-v3`.

---

## Summarisation

One code path: the OpenAI chat completions API. Everything below speaks it.

| Provider | Base URL | Example model |
| --- | --- | --- |
| OpenAI | `https://api.openai.com/v1` | `gpt-4o-mini` |
| OpenRouter | `https://openrouter.ai/api/v1` | `openai/gpt-4o-mini` |
| Groq | `https://api.groq.com/openai/v1` | `llama-3.3-70b-versatile` |
| Together AI | `https://api.together.xyz/v1` | `meta-llama/Llama-3.3-70B-Instruct-Turbo` |
| Fireworks AI | `https://api.fireworks.ai/inference/v1` | `accounts/fireworks/models/llama-v3p3-70b-instruct` |
| DeepInfra | `https://api.deepinfra.com/v1/openai` | `meta-llama/Llama-3.3-70B-Instruct` |
| Mistral | `https://api.mistral.ai/v1` | `mistral-large-latest` |
| Cerebras | `https://api.cerebras.ai/v1` | `llama-3.3-70b` |
| Anthropic | `https://api.anthropic.com/v1/` | `claude-sonnet-4-5` |
| Google Gemini | `https://generativelanguage.googleapis.com/v1beta/openai/` | `gemini-2.5-flash` |
| Ollama | `http://localhost:11434/v1` | `llama3.2` |
| LM Studio | `http://localhost:1234/v1` | whichever model you loaded |
| vLLM / llama.cpp | `http://localhost:8000/v1` | whichever model you serve |

**OpenRouter** is the easiest starting point: one key, hundreds of models, and you can change model
without changing anything else.

**Use the key with its own base URL.** An OpenRouter key (`sk-or-v1-…`) against
`https://api.openai.com/v1` returns a 401.

### Local models

Ollama is the simplest route:

```bash
ollama pull llama3.2
ollama serve
```

Then set the base URL to `http://localhost:11434/v1`, model `llama3.2`, and leave the API key blank.

If the app runs in Docker and Ollama runs on the host, use `http://host.docker.internal:11434/v1`.
Compose already maps that name on Linux as well as Windows and macOS.

Summarising a meeting is a long-context task. A 7B model produces usable minutes for short meetings;
for hour-long recordings, prefer a larger model or leave the transcript chunk size at its default so
the meeting is summarised in parts.

---

## Long meetings

Two independent limits could bite, and both are handled:

- **Upload size at the transcription API.** Only the OpenAI-compatible provider has one. Files over
  24 MB are split into chunks (10 minutes by default) and the parts are joined.
- **The model's context window.** Transcripts longer than the configured chunk size are summarised
  part by part, and those notes are merged into the final minutes. A three-hour meeting works with a
  small context window.

Both thresholds are in **Settings → Processing**.
