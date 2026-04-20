# RAG Portfolio: Technical Build Document

A production RAG chatbot that doubles as an interactive portfolio. Originally built by Michael Frost as his own portfolio site, then generalized into a reusable template.

## 1. What it is

An interactive AI portfolio. Instead of a static resume, visitors land on a page and have a real conversation with an AI grounded on the owner's background, projects, and writing. It can optionally speak replies back through ElevenLabs. It is the portfolio, the demo, and the proof of work in one artifact.

## 2. Architecture overview

### Stack

| Layer | Technology | Notes |
|---|---|---|
| Portfolio site | Astro 5 (static) | `apps/site`, served separately, frames the chat via iframe |
| Chat widget | Single-file HTML + vanilla JS + CSS | `chat.html`, zero build step, embeddable anywhere |
| Backend | FastAPI (Python 3.10+) | `web.py`, uvicorn, port 8510 |
| LLM | Claude Sonnet 4.6 via Anthropic API | `claude-sonnet-4-6`, 1024 max tokens, temperature 0.7 |
| Embeddings | OpenAI `text-embedding-3-large` | 3072 dims, used at ingest and query time |
| Vector DB | Qdrant | Self-hosted, collection `public_kb` by default |
| Voice (TTS) | ElevenLabs `eleven_turbo_v2_5` | Optional, configurable voice ID, base64 MP3 inline |
| Speech input | Web Speech API | Browser-native, no server dependency |
| Session store | SQLite | Per-session message history, token + cost logging |

### Request flow

```
Visitor browser
   |
   v
Astro portfolio (apps/site) --iframe--> chat.html (served by FastAPI)
                                             |
                                             | POST /chat or /chat/voice
                                             v
                                      FastAPI (web.py, 8510)
                                             |
                     +-----------------------+-----------------------+
                     |                       |                       |
                     v                       v                       v
            OpenAI embeddings        Qdrant top_k=10          SQLite history
            (3072-dim query)                                  (session + usage)
                     |                       |
                     +-----------+-----------+
                                 v
                      Claude Sonnet 4.6
                (system prompt + context + history)
                                 |
                                 v
                     (optional) ElevenLabs TTS
                                 |
                                 v
                       JSON {reply, audio?}
```

## 3. Key design decisions

### Single-file chat widget
`chat.html` contains all markup, styles, and scripts inline with no CDN references. It can be served from any FastAPI route, embedded via `iframe src="host?embed=1"`, or dropped into any hosting target. The `?embed=1` flag skips the landing overlay so the parent page controls first impression.

### Persona as data, not code
System prompt, welcome text, and voice-mode preamble live in [`prompts/`](prompts/) as plain text files with `{{OWNER_NAME}}`, `{{OWNER_ROLE}}`, `{{OWNER_BIO}}` placeholders. These get substituted at server start from env vars. Customizing the bot is editing three env values + optionally editing the prompt files. No code changes required.

### ElevenLabs opt-in, not default
Voice mode is off by default. The visitor flips the speaker icon to enable it. This bounds ElevenLabs character cost to users who actually want voice and prevents "why is this site talking to me" reactions. When on, replies come back as text plus base64 MP3 in one JSON response — no second round trip.

### System prompt guardrails
The default prompt enforces: first-person voice, no asking the visitor questions, no hallucinating content not in the knowledge base, a hard response-length cap, and a jailbreak clause that responds with a fixed sentence to adversarial input. Bring your own domain-specific rules (e.g. "never discuss client X" or "never cite figure Y") by editing `prompts/system.md`.

### Markdown stripping
Claude occasionally returns bold, italics, or headers. The backend strips these with regex before returning to the client. Prose reads cleanly in the chat UI and sounds clean when spoken by TTS (no asterisks in the audio).

### Em dash post-processing
After every LLM response, `strip_markdown()` replaces em dashes (U+2014) and en dashes with commas and periods. Enforced at the output layer so no model drift, fine-tuning change, or future model swap can violate it.

### SQLite for sessions and usage
Per-session chat history, per-call Anthropic usage (input tokens, output tokens, cost in USD), optional ElevenLabs character usage. Small footprint, zero ops. A single file next to `web.py`.

### Rate limiting + input cap
`slowapi` at 30 req/min per IP on `/chat` endpoints, hardcoded 1000-char message cap. Stops runaway costs from a single noisy actor. CORS locked to a single origin (`ALLOWED_ORIGIN` env var) in production.

### Prompt caching
The (stable) system prompt is marked `cache_control: ephemeral` on the Anthropic API. For a typical session of 5+ turns, this cuts input-token cost on the system prompt by ~90%.

## 4. Data ingestion

### Content flow
1. You drop markdown files under `data/` and register them in `_manifest.yml`.
2. `ingest.py --all` parses each file, splits on headings and paragraphs, chunks with overlap, embeds via OpenAI, and upserts to Qdrant with metadata (origin, topics, source file).
3. On query, `web.py` embeds the question, pulls top-K chunks from Qdrant, builds a context window under a char cap, and hands off to Claude.

### Embedding model
OpenAI `text-embedding-3-large`, 3072 dimensions. The query path uses the same model (`embed_query` in `web.py`), so ingest and retrieval vectors are always compatible.

### Qdrant config
- Distance: `Cosine`
- Payload indexes: `origin`, `topics`
- Default collection: `public_kb`
- Optional second collection: `private_kb` for richer content served to authenticated tools

## 5. System prompt structure

The prompt has three layers, concatenated at runtime:

1. **Persona header** — `{{OWNER_NAME}}`, `{{OWNER_ROLE}}`, `{{OWNER_BIO}}` substituted from env
2. **Response rules** — length caps, voice and style rules, hard constraints
3. **Guardrails** — adversarial input handling

When voice mode is on, a short preamble from `prompts/voice_mode_preamble.txt` is prepended, shifting the model from narrator to speaker.

## 6. UX flow

1. **Landing.** Visitor hits the portfolio site. Chat mounts in an iframe.
2. **First prompt.** A row of suggestion chips seeds typical questions so the visitor doesn't face a blank box.
3. **Conversation.** Visitor types or clicks a chip. Backend runs RAG (embed, Qdrant search, Claude call) and returns a reply in roughly 2 to 4 seconds. Voice mode (if on) returns base64 MP3 inline.
4. **Speech input.** Browsers with Web Speech API support show a mic button.
5. **Session persistence.** Session ID in `localStorage`. History persists across refreshes. A Clear button starts a new session.
6. **Booking exit.** `CALENDAR_BOOKING_URL` shows up as a Schedule a Call button when set.

## 7. Deployment topology

Recommended:

1. Chat server on a small VM, LXC, or container. uvicorn bound to 127.0.0.1:8510.
2. Cloudflare Tunnel (or nginx + TLS) proxies a public hostname to localhost:8510.
3. `ALLOWED_ORIGIN` set to the portfolio site's origin.
4. Portfolio site (`apps/site`) deployed to Cloudflare Pages, Netlify, or any static host.
5. Qdrant running as a sibling service (Docker container on the same VM, or a separate managed instance).

## 8. File map

- `apps/rag-chat/web.py` — FastAPI backend, RAG loop, TTS, SQLite persistence, stats endpoint
- `apps/rag-chat/ingest.py` — manifest-driven chunk + embed + upsert
- `apps/rag-chat/chat.html` — frontend widget
- `apps/rag-chat/prompts/` — system prompt + welcome + voice preamble, with `{{OWNER_*}}` placeholders
- `apps/rag-chat/data/` — your knowledge base (markdown files + `_manifest.yml`)
- `apps/rag-chat/.env.example` — full env var reference
- `apps/site/src/config/site.ts` — single source of truth for all portfolio site copy
