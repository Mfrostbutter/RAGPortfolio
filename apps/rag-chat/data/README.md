# Your knowledge base

This directory is where your content lives. The ingester reads [`_manifest.yml`](_manifest.yml), chunks each file, embeds the chunks, and upserts them to Qdrant.

## Add your content

1. Drop markdown files anywhere under `data/`. Organize by topic (e.g. `data/projects/`, `data/writing/`, `data/bio/`).
2. Register each file in `_manifest.yml`.
3. Run `python ingest.py --all`.

## Writing for a RAG chat

- **First person.** The system prompt tells the model to speak as you; your own voice is the highest-quality training signal.
- **Short paragraphs.** The chunker splits on blank lines and headings. 3–6 sentences per paragraph works well.
- **Use headings.** `##` level for sections inside a file. Each section becomes a retrievable chunk.
- **Be concrete.** "I cut ticket resolution time by 50%" beats "improved operational efficiency."
- **One topic per file.** One-project-per-file, one-writeup-per-file. Keeps retrieval precise.
- **Skip filler.** Omit anything you wouldn't say in an interview. The retrieval layer finds the specific, not the generic.

## Collections

The manifest supports multiple collections. A common pattern:

| Collection | Use |
|---|---|
| `public_kb` | Safe-for-visitors content. This is what the public chat queries. |
| `private_kb` | Fuller corpus including private notes, unpublished drafts. Query from authenticated tools only. |

Start with `public_kb` only. Add `private_kb` if you build tooling around it.

## Frontmatter (optional)

```yaml
---
title: Project X
topics: [engineering, automation]
date: 2025-10-01
---
```

Frontmatter is parsed and stored as chunk metadata. You can filter on it at retrieval time if you extend `ingest.py`.

## What's already here

[`example/bio.md`](example/bio.md) and [`example/project-example.md`](example/project-example.md) are starter templates. Replace them with your own content, or use them as scaffolding and delete the originals when you're done.

## Where to find content to ingest

See [`SOURCE-IDEAS.md`](SOURCE-IDEAS.md) for a curated list of knowledge sources — ChatGPT / Claude exports, meeting transcripts, voice memos, draft essays, and unfiltered text streams that capture how you actually communicate. The bot is only as good as the corpus behind it.
