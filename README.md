# RAGPortfolio

A reusable template for an **interactive AI portfolio**: a static site plus a RAG chatbot grounded on your own content. Visitors land on your page and have a real conversation with an AI trained on your background, projects, and writing. It's the portfolio, the demo, and the proof of work in one artifact.

## What's here

| Path | What it is |
|---|---|
| [`apps/site`](apps/site) | Astro 5 static site. All copy driven by [`site.config.ts`](apps/site/src/config/site.ts). |
| [`apps/rag-chat`](apps/rag-chat) | FastAPI + single-file HTML RAG chatbot. Claude + OpenAI embeddings + Qdrant + optional ElevenLabs TTS. |

## Stack

- **Frontend:** Astro 5 static output, single-file embeddable chat widget (no framework deps)
- **Backend:** FastAPI, uvicorn, Python 3.10+
- **LLM:** Anthropic `claude-sonnet-4-6` (GPT-4o fallback)
- **Embeddings:** OpenAI `text-embedding-3-large` (3072 dims)
- **Vector store:** Qdrant (self-hosted)
- **TTS:** ElevenLabs (opt-in; any voice ID)
- **Session store:** SQLite
- **Rate limiting:** slowapi
- **Deploy:** Cloudflare Pages (site), uvicorn behind Cloudflare Tunnel / reverse proxy (chat API)

## Quick start

**1. Stand up Qdrant.** Easiest: `docker run -p 6333:6333 qdrant/qdrant`.

**2. Configure the chat server.**

```sh
cd apps/rag-chat
cp .env.example .env
# Edit .env — at minimum fill in:
#   OWNER_NAME, OWNER_ROLE, OWNER_BIO
#   ANTHROPIC_API_KEY, OPENAI_API_KEY
#   QDRANT_HOST, QDRANT_PORT
pip install -r requirements.txt
```

**3. Add your content.** Replace the placeholders in `apps/rag-chat/data/example/` with your own markdown, and register them in `data/_manifest.yml`. See [`apps/rag-chat/data/README.md`](apps/rag-chat/data/README.md) for the format.

**4. Ingest.**

```sh
python ingest.py --all
```

**5. Run the chat server.**

```sh
uvicorn web:app --host 0.0.0.0 --port 8510
```

**6. Customize the site.** Edit [`apps/site/src/config/site.ts`](apps/site/src/config/site.ts). Owner name, hero pitch, about copy, work cards, chat iframe URL, social links.

**7. Run the site.**

```sh
cd ../site
npm install
npm run dev
```

Open `http://localhost:4321`.

## Per-app docs

- [`apps/rag-chat/README.md`](apps/rag-chat/README.md) — chat server, config, endpoints, embedding
- [`apps/rag-chat/TECHNICAL-BUILD-DOC.md`](apps/rag-chat/TECHNICAL-BUILD-DOC.md) — architecture, design decisions, runbook
- [`apps/rag-chat/data/README.md`](apps/rag-chat/data/README.md) — how to write content for a RAG chat
- [`apps/rag-chat/data/SOURCE-IDEAS.md`](apps/rag-chat/data/SOURCE-IDEAS.md) — curated list of knowledge sources (AI chat exports, meeting transcripts, voice memos, drafts) to capture how you actually communicate
- [`apps/site/README.md`](apps/site/README.md) — site config, build, deploy

## License

Sustainable Use License v1.0. Free for internal, personal, and non-commercial use. You may not provide the software to third parties as a hosted or managed service. See [`LICENSE.md`](LICENSE.md).

---

Originally built by [Michael Frost](https://github.com/Mfrostbutter) as his own portfolio, then generalized into a template.
