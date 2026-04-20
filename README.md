# RAGPortfolio

An interactive AI portfolio. Instead of a static resume, visitors land on a page and have a real conversation with an AI grounded on the owner's background, projects, writing, and published thinking. It is the portfolio, the demo, and the proof of work in one artifact.

Built by Michael Frost.

## What's here

Two applications that compose into the live experience:

| Path | What it is |
|---|---|
| [`apps/michael-site`](apps/michael-site) | Astro 5 static portfolio site. Deployed to Cloudflare Pages. Frames the chat via iframe. |
| [`apps/ask-michael`](apps/ask-michael) | FastAPI + single-file HTML RAG chatbot. Claude `claude-sonnet-4-6` + OpenAI `text-embedding-3-large` + Qdrant, with optional ElevenLabs TTS. |

Full architecture, design decisions, and runbook: [`apps/ask-michael/TECHNICAL-BUILD-DOC.md`](apps/ask-michael/TECHNICAL-BUILD-DOC.md).

## Stack

- **Frontend:** Astro 5 static output, single-file embeddable chat widget
- **Backend:** FastAPI, uvicorn, Python 3.10+
- **LLM:** Anthropic `claude-sonnet-4-6` (GPT-4o fallback)
- **Embeddings:** OpenAI `text-embedding-3-large` (3072 dims)
- **Vector store:** Qdrant (self-hosted)
- **TTS:** ElevenLabs (opt-in; any voice ID)
- **Session store:** SQLite
- **Rate limiting:** slowapi
- **Deploy:** Cloudflare Pages (site), uvicorn behind Cloudflare Tunnel (chat API)

## Quick start

```bash
# Chat API
cd apps/ask-michael
cp .env.example .env       # fill in API keys
pip install -r requirements.txt
python ingest.py --all     # chunk + embed + upsert knowledge base
uvicorn web:app --host 0.0.0.0 --port 8510

# Portfolio site
cd apps/michael-site
npm install
npm run dev
```

Per-app READMEs have more detail:
- [`apps/ask-michael/README.md`](apps/ask-michael/README.md)
- [`apps/michael-site/README.md`](apps/michael-site/README.md)

## License

Sustainable Use License v1.0. Free for internal, personal, and non-commercial use. You may not provide the software to third parties as a hosted or managed service. See [`LICENSE.md`](LICENSE.md).
