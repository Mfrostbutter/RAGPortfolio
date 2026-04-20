#!/usr/bin/env python3
"""
Ask Michael RAG Ingestion Pipeline

Reads data/_manifest.yml, chunks each file, embeds once with OpenAI
text-embedding-3-large (3072 dims), and upserts to one or more Qdrant
collections per the manifest routing (michael_portfolio, founder_knowledge).

Usage:
  python ingest.py --collection michael_portfolio
  python ingest.py --collection founder_knowledge
  python ingest.py --all
  python ingest.py --dry-run
"""

import argparse
import os
import re
import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    PointStruct,
    ScalarQuantization,
    ScalarQuantizationConfig,
    ScalarType,
    VectorParams,
)

load_dotenv()

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
QDRANT_HOST = os.getenv("QDRANT_HOST", "10.10.0.60")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-large")
EMBED_DIM = 3072
CHUNK_SIZE = 1500
CHUNK_OVERLAP = 200
EMBED_BATCH = 100

APP_DIR = Path(__file__).parent
MANIFEST_PATH = APP_DIR / "data" / "_manifest.yml"

VALID_COLLECTIONS = {"michael_portfolio", "founder_knowledge"}

TOPIC_TAXONOMY = {
    "ai-governance": ["governance", "compliance", "policy", "audit", "regulat", "hipaa", "cmmc", "soc 2", "iso"],
    "shadow-ai": ["shadow ai", "unapproved", "personal account", "unauthorized ai", "employees are using"],
    "rag": ["rag", "retrieval", "retrieval-augmented", "vector search", "semantic search", "embedding"],
    "model-routing": ["model routing", "routing", "model selection", "route", "fallback", "model picker"],
    "data-readiness": ["data readiness", "data quality", "data pipeline", "clean data", "data ready", "data infrastructure"],
    "mcp": ["mcp", "model context protocol"],
    "vector-db": ["qdrant", "pinecone", "weaviate", "vector db", "vector database", "chroma"],
    "self-hosting": ["self-host", "self host", "on-prem", "proxmox", "lxc", "homelab", "self-hosted"],
    "msp": ["msp", "managed service", "brightworks", "connectwise", "cw "],
    "leadership": ["leadership", "manager", "team", "mentor", "lead ", "leader", "director", "vp "],
    "career": ["career", "experience", "background", "job", "role", "position", "history", "nmci"],
    "security": ["security", "breach", "vulnerability", "cve", "exploit", "attack", "defensive", "zero trust"],
    "automation": ["automation", "automate", "n8n", "workflow", "orchestration"],
    "n8n": ["n8n"],
    "infrastructure": ["infrastructure", "proxmox", "docker", "kubernetes", "cluster", "lxc", "vm", "nginx"],
    "product": ["product", "ship", "launch", "beta", "release", "customer", "user"],
}

CONTENT_TYPE_BY_ORIGIN = {
    "founder-profile": "bio",
    "linkedin-article": "article",
    "technical-portfolio": "portfolio",
    "webflow-legacy": "article",
    "rios-thesis": "principle",
}


# ---------------------------------------------------------------------------
# Frontmatter + chunking
# ---------------------------------------------------------------------------
def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Pull YAML frontmatter out of the top of a markdown file if present."""
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    try:
        fm = yaml.safe_load(text[3:end]) or {}
    except Exception:
        return {}, text
    body = text[end + 4:].lstrip("\n")
    return fm, body


def extract_title(fm: dict, body: str, fallback: str) -> str:
    if fm.get("title"):
        return str(fm["title"]).strip()
    for line in body.splitlines():
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()
        if line and not line.startswith(("#", ">", "-", "|")):
            break
    return fallback


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[dict]:
    """Paragraph-first chunker. Returns list of {text, section} dicts."""
    if not text or len(text.strip()) < 50:
        return []

    # Track nearest heading path while walking the doc
    heading_stack: list[tuple[int, str]] = []
    current_section = ""

    paragraphs = text.split("\n\n")
    annotated: list[tuple[str, str]] = []  # (section, para)

    for para in paragraphs:
        para_s = para.strip()
        if not para_s:
            continue
        heading_match = re.match(r"^(#{1,6})\s+(.*)", para_s)
        if heading_match:
            level = len(heading_match.group(1))
            heading_text = heading_match.group(2).strip()
            heading_stack = [(lv, tx) for lv, tx in heading_stack if lv < level]
            heading_stack.append((level, heading_text))
            current_section = " > ".join(tx for _, tx in heading_stack)
            continue
        annotated.append((current_section, para_s))

    # Pack paragraphs into chunks up to chunk_size
    chunks: list[dict] = []
    buf = ""
    buf_section = ""

    def flush():
        nonlocal buf, buf_section
        if buf.strip():
            chunks.append({"text": buf.strip(), "section": buf_section})
        buf = ""
        buf_section = ""

    for section, para in annotated:
        if not buf:
            buf_section = section
        candidate = f"{buf}\n\n{para}" if buf else para
        if len(candidate) <= chunk_size:
            buf = candidate
        else:
            flush()
            if len(para) > chunk_size:
                # Sentence-split oversized paragraph
                sentences = re.split(r"(?<=[.!?])\s+", para)
                for sent in sentences:
                    cand = f"{buf} {sent}" if buf else sent
                    if len(cand) <= chunk_size:
                        buf = cand
                        buf_section = section
                    else:
                        flush()
                        buf = sent
                        buf_section = section
            else:
                buf = para
                buf_section = section
    flush()

    # Apply overlap by prepending tail of previous chunk
    if overlap > 0 and len(chunks) > 1:
        with_overlap = [chunks[0]]
        for i in range(1, len(chunks)):
            tail = chunks[i - 1]["text"][-overlap:]
            with_overlap.append({
                "text": f"...{tail}\n\n{chunks[i]['text']}",
                "section": chunks[i]["section"],
            })
        chunks = with_overlap

    return [c for c in chunks if len(c["text"].strip()) > 50]


def match_topics(text: str) -> list[str]:
    tl = text.lower()
    hits = []
    for topic, kws in TOPIC_TAXONOMY.items():
        if any(kw in tl for kw in kws):
            hits.append(topic)
    return hits


def infer_content_type(origin: str, source_file: str, text: str) -> str:
    if origin == "founder-profile":
        if "interview" in source_file.lower():
            return "interview"
        return "bio"
    if origin == "rios-thesis":
        if "use-case" in source_file.lower():
            return "use_case"
        return "principle"
    return CONTENT_TYPE_BY_ORIGIN.get(origin, "article")


# ---------------------------------------------------------------------------
# Manifest + file loading
# ---------------------------------------------------------------------------
def load_manifest() -> list[dict]:
    if not MANIFEST_PATH.exists():
        print(f"ERROR: manifest not found at {MANIFEST_PATH}", file=sys.stderr)
        sys.exit(1)
    with open(MANIFEST_PATH) as f:
        data = yaml.safe_load(f) or {}
    return data.get("files", [])


def is_stub(text: str) -> bool:
    return text.lstrip().startswith("# TO BE ADDED")


# ---------------------------------------------------------------------------
# Qdrant setup
# ---------------------------------------------------------------------------
def ensure_collection(client: QdrantClient, name: str, recreate: bool = True):
    existing = [c.name for c in client.get_collections().collections]
    if name in existing and recreate:
        print(f"  Dropping existing collection '{name}'...")
        client.delete_collection(name)
        existing = [c.name for c in client.get_collections().collections]

    if name not in existing:
        print(f"  Creating collection '{name}' ({EMBED_DIM} dims, COSINE, INT8 quantization)...")
        client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(size=EMBED_DIM, distance=Distance.COSINE),
            quantization_config=ScalarQuantization(
                scalar=ScalarQuantizationConfig(
                    type=ScalarType.INT8,
                    always_ram=True,
                ),
            ),
        )
        # Payload indexes for filtering
        for field in ["content_type", "origin"]:
            client.create_payload_index(
                collection_name=name,
                field_name=field,
                field_schema="keyword",
            )
        client.create_payload_index(
            collection_name=name,
            field_name="topics",
            field_schema="keyword",
        )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Ingest data/ into Qdrant via the manifest.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--collection", choices=sorted(VALID_COLLECTIONS))
    group.add_argument("--all", action="store_true", help="Ingest into both collections")
    group.add_argument("--dry-run", action="store_true", help="Plan only, no embeddings, no upsert")
    parser.add_argument("--no-recreate", action="store_true", help="Keep existing collection data")
    args = parser.parse_args()

    if args.all:
        target_collections = set(VALID_COLLECTIONS)
    elif args.collection:
        target_collections = {args.collection}
    else:
        target_collections = set(VALID_COLLECTIONS)  # dry-run plans for all

    print("=" * 60)
    print("Ask Michael RAG Ingestion")
    print("=" * 60)
    print(f"Targets: {sorted(target_collections)}")
    print(f"Dry run: {args.dry_run}")
    print(f"Embed model: {EMBED_MODEL} ({EMBED_DIM}d)")
    print()

    # Load manifest
    manifest = load_manifest()
    print(f"Manifest entries: {len(manifest)}")

    # Resolve files, skip stubs and out-of-scope
    resolved: list[dict] = []
    for entry in manifest:
        rel_path = entry["path"]
        abs_path = APP_DIR / rel_path
        collections = set(entry.get("collections", []))
        in_scope = collections & target_collections
        if not in_scope:
            continue
        if not abs_path.exists():
            print(f"  WARN: file missing, skipping: {rel_path}")
            continue
        text = abs_path.read_text(encoding="utf-8", errors="ignore")
        if entry.get("skip_if_stub") and is_stub(text):
            print(f"  SKIP (stub): {rel_path}")
            continue
        resolved.append({
            "path": rel_path,
            "abs": abs_path,
            "origin": entry.get("origin", "unknown"),
            "collections": sorted(in_scope),
            "text": text,
        })

    print(f"Files to ingest: {len(resolved)}")
    print()

    # Chunk everything first (deterministic, LLM-free)
    all_points: list[dict] = []
    for r in resolved:
        fm, body = parse_frontmatter(r["text"])
        source_file = Path(r["path"]).name
        title = extract_title(fm, body, fallback=source_file)
        date = fm.get("date")
        origin = fm.get("origin") or r["origin"]
        content_type = infer_content_type(origin, source_file, body)

        chunks = chunk_text(body)
        total = len(chunks)
        for i, c in enumerate(chunks):
            topics = match_topics(c["text"])
            word_count = len(c["text"].split())
            payload = {
                "content": c["text"],
                "text": c["text"],
                "source_file": source_file,
                "title": title,
                "section": c["section"],
                "content_type": content_type,
                "origin": origin,
                "topics": topics,
                "date": str(date) if date else None,
                "word_count": word_count,
                "chunk_index": i,
                "chunk_total": total,
            }
            all_points.append({
                "text": c["text"],
                "payload": payload,
                "collections": r["collections"],
            })

    print(f"Total chunks: {len(all_points)}")
    by_origin: dict[str, int] = {}
    for p in all_points:
        by_origin[p["payload"]["origin"]] = by_origin.get(p["payload"]["origin"], 0) + 1
    for origin, n in sorted(by_origin.items(), key=lambda x: -x[1]):
        print(f"  {origin}: {n} chunks")
    print()

    if args.dry_run:
        print("Dry run complete. No embeddings computed, no upserts performed.")
        return

    # Connect to Qdrant
    print(f"Connecting to Qdrant at {QDRANT_HOST}:{QDRANT_PORT}...")
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    for coll in sorted(target_collections):
        ensure_collection(client, coll, recreate=not args.no_recreate)
    print()

    # OpenAI client
    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY not set", file=sys.stderr)
        sys.exit(1)
    oai = OpenAI()

    # Embed once per chunk
    print(f"Embedding {len(all_points)} chunks in batches of {EMBED_BATCH}...")
    vectors: list[list[float]] = [None] * len(all_points)  # type: ignore
    for i in range(0, len(all_points), EMBED_BATCH):
        batch = all_points[i:i + EMBED_BATCH]
        inputs = [p["text"][:8000] for p in batch]
        resp = oai.embeddings.create(model=EMBED_MODEL, input=inputs)
        for j, item in enumerate(resp.data):
            vectors[i + j] = item.embedding
        print(f"  [{min(i + EMBED_BATCH, len(all_points))}/{len(all_points)}]", end="\r")
    print()

    # Group points by destination collection, upsert without re-embedding
    for coll in sorted(target_collections):
        points_for_coll = []
        point_id = 0
        for idx, p in enumerate(all_points):
            if coll not in p["collections"]:
                continue
            points_for_coll.append(PointStruct(
                id=point_id,
                vector=vectors[idx],
                payload=p["payload"],
            ))
            point_id += 1
        if not points_for_coll:
            continue
        print(f"Upserting {len(points_for_coll)} points into '{coll}'...")
        BATCH = 100
        for i in range(0, len(points_for_coll), BATCH):
            client.upsert(collection_name=coll, points=points_for_coll[i:i + BATCH])
        info = client.get_collection(coll)
        print(f"  '{coll}' now has {info.points_count} vectors (status: {info.status})")

    print()
    print("Done.")


if __name__ == "__main__":
    main()
