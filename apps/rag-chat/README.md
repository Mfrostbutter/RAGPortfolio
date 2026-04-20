# RAG chat server

Portfolio RAG chatbot. FastAPI backend, single-file HTML frontend, Claude `claude-sonnet-4-6` + OpenAI `text-embedding-3-large` + Qdrant, with optional ElevenLabs TTS.

Designed to be embedded via iframe in a portfolio site (see `apps/site`). Runs on port 8510 by default.

## Persona

The bot speaks in first person as the site owner. Persona is driven by three env vars:

| Variable | Purpose |
|---|---|
| `OWNER_NAME` | Your name. Appears in the system prompt, welcome message, and iframe title. |
| `OWNER_ROLE` | Your current title / role. |
| `OWNER_BIO` | One-paragraph bio. Shapes every reply. |

System prompt, welcome text, and voice-mode preamble all live in [`prompts/`](prompts/). Customize those files directly if you need deeper changes.

## Collections

| Collection | Use |
|---|---|
| `public_kb` | Default. What the public chat queries. |
| `private_kb` | Optional. Fuller corpus for authenticated use. |

Configured via `QDRANT_COLLECTION` env var (default: `public_kb`).

## Environment

See [`.env.example`](.env.example) for the full list. Required:

| Key | Purpose |
|---|---|
| `OWNER_NAME`, `OWNER_ROLE`, `OWNER_BIO` | Persona |
| `ANTHROPIC_API_KEY` | Claude |
| `OPENAI_API_KEY` | Embeddings |
| `QDRANT_HOST`, `QDRANT_PORT` | Qdrant |
| `ALLOWED_ORIGIN` | CORS (lock to your portfolio origin in prod) |

Optional:

| Key | Purpose |
|---|---|
| `QDRANT_COLLECTION` | Defaults to `public_kb` |
| `ELEVENLABS_API_KEY` | TTS replies |
| `ELEVENLABS_VOICE_ID` | Voice ID (default: stock "Adam" voice) |
| `CALENDAR_BOOKING_URL` | Calendly link surfaced in the UI |
| `EMBED_MODEL` | Defaults to `text-embedding-3-large` |

## Layout

```
rag-chat/
  web.py                  # FastAPI app: Claude + TTS + Qdrant retrieval + SQLite logs
  ingest.py               # Manifest-driven chunk + embed + upsert
  chat.html               # Single-file frontend, inline CSS/JS, no CDN
  requirements.txt
  .env.example
  prompts/
    system.md                # System prompt with {{OWNER_*}} placeholders
    welcome.txt              # Welcome message shown on first load
    voice_mode_preamble.txt  # Prepended when voice mode is on
  data/
    README.md             # How to add your content
    _manifest.yml         # File to collection routing
    example/              # Starter templates (replace with your own)
```

## Ingest

```bash
python ingest.py --all
python ingest.py --collection public_kb
python ingest.py --dry-run
```

## Run the server

```bash
uvicorn web:app --host 0.0.0.0 --port 8510
```

Then open `http://localhost:8510/` directly, or embed via iframe at `http://localhost:8510/?embed=1`.

## Endpoints

- `GET /` — serves `chat.html`
- `GET /health` — Qdrant reachability + point count
- `GET /config` — calendar URL, voice-enabled flag, owner info, welcome text
- `POST /chat` — `{message, session_id}` returns `{reply}`
- `POST /chat/voice` — adds base64 MP3 from ElevenLabs
- `POST /clear` — wipe session history
- `GET /api/stats` — daily + lifetime token / message totals

## Embedding in your site

In [`apps/site/src/config/site.ts`](../site/src/config/site.ts), set `chat.iframeUrl` to this server's public URL with `?embed=1`. The embed flag strips chrome so the parent page owns layout.

## Deployment

Recommended topology:

1. Chat server runs on a small VM / container, uvicorn bound to 127.0.0.1:8510
2. Cloudflare Tunnel (or nginx + TLS) proxies a public hostname to localhost:8510
3. `ALLOWED_ORIGIN` set to your portfolio origin
