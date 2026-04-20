# Ask Me

Interactive portfolio RAG chatbot. FastAPI backend, single-file HTML frontend, Claude `claude-sonnet-4-6` + OpenAI `text-embedding-3-large` + Qdrant, with optional ElevenLabs TTS for spoken replies.

Embedded via iframe in `apps/michael-site` (Astro portfolio, deployed to Cloudflare Pages). Runs on port 8510 locally.

## Collections

| Collection | Use |
|---|---|
| `michael_portfolio` | Public chatbot, safe-for-visitors content |
| `founder_knowledge` | Private second brain, full corpus |

Both use OpenAI `text-embedding-3-large` (3072 dims).

## Stack

- **LLM:** Anthropic `claude-sonnet-4-6`
- **Embeddings:** OpenAI `text-embedding-3-large`
- **Vector store:** Qdrant 1.17.0
- **TTS:** ElevenLabs (opt-in, uses any voice ID you configure; defaults to the stock "Adam" voice)
- **Session store:** SQLite (`ask_michael.db`), per-session history + per-call token/cost logging
- **Rate limiting:** `slowapi`, 30 req/min per IP on `/chat` endpoints
- **Input cap:** 1000 chars
- **CORS:** locked via `ALLOWED_ORIGIN`

## Layout

```
ask-michael/
  web.py                  # FastAPI app: Claude + TTS + Qdrant retrieval + SQLite logs + slowapi
  ingest.py               # Manifest-driven chunk + embed + upsert
  chat.html               # Single-file frontend, inline CSS/JS, no CDN
  requirements.txt
  .env.example
  data/
    _manifest.yml             # File to collection routing
    founder-profile/          # Bio, interview responses
    knowledge/                # Distilled topic docs (philosophy, workflows, etc.)
    linkedin/                 # Published articles
    webflow/                  # Legacy website content
    rios-thesis/              # Public-safe methodology concepts
    technical-portfolio.md
    published-content.md
  scripts/                  # Optional corpus processing utilities
  static/
    headshot.jpg
```

## Environment

See `.env.example` for the full list. Required:

| Key | Purpose |
|---|---|
| `ANTHROPIC_API_KEY` | Claude |
| `OPENAI_API_KEY` | Embeddings |
| `QDRANT_HOST`, `QDRANT_PORT` | Qdrant |
| `ALLOWED_ORIGIN` | CORS (lock to your portfolio origin in prod) |

Optional:

| Key | Purpose |
|---|---|
| `ELEVENLABS_API_KEY` | TTS replies |
| `ELEVENLABS_VOICE_ID_MICHAEL` | Voice ID (use any ElevenLabs voice you have access to) |
| `CALENDAR_BOOKING_URL` | Calendly link surfaced in the UI |

## Run ingest

```bash
python ingest.py --all
python ingest.py --collection michael_portfolio
python ingest.py --dry-run
```

## Run the server

```bash
uvicorn web:app --host 0.0.0.0 --port 8510
```

Then open `http://localhost:8510/`.

## Endpoints

- `GET /` serves `chat.html`
- `GET /health` Qdrant reachability + point count
- `GET /config` calendar URL + voice-enabled flag
- `POST /chat` `{message, session_id}` returns `{reply}`
- `POST /chat/voice` adds base64 MP3 from ElevenLabs
- `POST /clear` wipe session history
- `GET /api/stats` daily + lifetime token/message totals

## Embedding

The Astro site in `apps/michael-site` embeds this via iframe with `?embed=1`. That flag strips chrome so the parent page owns layout.
