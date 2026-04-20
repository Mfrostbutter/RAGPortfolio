#!/usr/bin/env python3
"""
RAG portfolio chatbot.
FastAPI backend, Claude Sonnet 4, OpenAI embeddings, Qdrant retrieval.

Persona is driven by prompts/*.md + env vars (OWNER_NAME, OWNER_ROLE, OWNER_BIO).
"""

import base64
import os
import re
import sqlite3
import threading
from pathlib import Path

import httpx
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

import anthropic
from openai import OpenAI
from qdrant_client import QdrantClient

load_dotenv(override=True)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
COLLECTION = os.getenv("QDRANT_COLLECTION", "public_kb")

# Persona config — fill these in .env to customize the bot
OWNER_NAME = os.getenv("OWNER_NAME", "the site owner")
OWNER_ROLE = os.getenv("OWNER_ROLE", "Builder and problem solver")
OWNER_BIO = os.getenv("OWNER_BIO", "I build things with software. Ask me about my work.")

EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-large")
ALLOWED_ORIGIN = os.getenv("ALLOWED_ORIGIN", "*")
MAX_MESSAGE_LEN = 1000

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "").strip()
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "pNInz6obpgDQGcFmaJgB").strip()  # default: ElevenLabs stock "Adam" voice
CALENDAR_BOOKING_URL = os.getenv("CALENDAR_BOOKING_URL", "").strip()
LLM_MODEL = "claude-sonnet-4-6"
FALLBACK_MODEL = "gpt-4o"  # OpenAI fallback if Anthropic API fails (network, rate limit, outage)
MAX_TOKENS = 1024
TOP_K = 7
CONTEXT_CHAR_CAP = 8000
HISTORY_TURNS = 16

# Claude Sonnet 4 pricing (per million tokens)
PRICE_INPUT = 3.0
PRICE_OUTPUT = 15.0

_PROMPTS_DIR = Path(__file__).parent / "prompts"


def _load_prompt(filename: str) -> str:
    """Load a prompt file and substitute {{OWNER_*}} placeholders from env."""
    path = _PROMPTS_DIR / filename
    text = path.read_text(encoding="utf-8")
    return (
        text
        .replace("{{OWNER_NAME}}", OWNER_NAME)
        .replace("{{OWNER_ROLE}}", OWNER_ROLE)
        .replace("{{OWNER_BIO}}", OWNER_BIO)
    )


SYSTEM_PROMPT = _load_prompt("system.md")
VOICE_MODE_PREAMBLE = _load_prompt("voice_mode_preamble.txt")
WELCOME_TEXT = _load_prompt("welcome.txt").strip()

# ---------------------------------------------------------------------------
# Clients
# ---------------------------------------------------------------------------
limiter = Limiter(key_func=get_remote_address, default_limits=["30/minute"])
app = FastAPI(title=f"Ask {OWNER_NAME}")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[ALLOWED_ORIGIN] if ALLOWED_ORIGIN != "*" else ["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

_STATIC_DIR = Path(__file__).parent / "static"
_STATIC_DIR.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=_STATIC_DIR), name="static")

claude_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
oai = OpenAI()
qdrant = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

# ---------------------------------------------------------------------------
# SQLite
# ---------------------------------------------------------------------------
DB_PATH = Path(__file__).parent / "rag_chat.db"
_db_lock = threading.Lock()


def _get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_session ON messages(session_id)")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS api_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            input_tokens INTEGER NOT NULL,
            output_tokens INTEGER NOT NULL,
            cost_usd REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn


def log_api_usage(session_id: str, input_tokens: int, output_tokens: int):
    cost = (input_tokens * PRICE_INPUT + output_tokens * PRICE_OUTPUT) / 1_000_000
    with _db_lock:
        conn = _get_db()
        conn.execute(
            "INSERT INTO api_usage (session_id, input_tokens, output_tokens, cost_usd) VALUES (?, ?, ?, ?)",
            (session_id, input_tokens, output_tokens, cost),
        )
        conn.commit()
        conn.close()


def get_session_cost(session_id: str) -> float:
    with _db_lock:
        conn = _get_db()
        row = conn.execute(
            "SELECT COALESCE(SUM(cost_usd), 0) FROM api_usage WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        conn.close()
    return float(row[0] or 0.0)


def get_history(session_id: str, limit: int = HISTORY_TURNS) -> list[dict]:
    with _db_lock:
        conn = _get_db()
        rows = conn.execute(
            "SELECT role, content FROM messages WHERE session_id = ? ORDER BY id DESC LIMIT ?",
            (session_id, limit),
        ).fetchall()
        conn.close()
    return [{"role": r, "content": c} for r, c in reversed(rows)]


def save_message(session_id: str, role: str, content: str):
    with _db_lock:
        conn = _get_db()
        conn.execute(
            "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
            (session_id, role, content),
        )
        conn.commit()
        conn.close()


def clear_history(session_id: str):
    with _db_lock:
        conn = _get_db()
        conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
        conn.commit()
        conn.close()


_get_db().close()


# ---------------------------------------------------------------------------
# RAG
# ---------------------------------------------------------------------------
def embed_query(text: str) -> list[float]:
    resp = oai.embeddings.create(model=EMBED_MODEL, input=[text[:8000]])
    return resp.data[0].embedding


def search_knowledge(query: str, top_k: int = TOP_K) -> list[dict]:
    vector = embed_query(query)
    results = qdrant.query_points(
        collection_name=COLLECTION,
        query=vector,
        limit=top_k,
        with_payload=True,
    )
    docs = []
    for r in results.points:
        p = r.payload or {}
        docs.append({
            "text": p.get("text") or p.get("content", ""),
            "title": p.get("title", ""),
            "section": p.get("section", ""),
            "origin": p.get("origin", ""),
            "content_type": p.get("content_type", ""),
            "score": r.score,
        })
    return docs


def build_context(docs: list[dict], max_chars: int = CONTEXT_CHAR_CAP) -> str:
    parts = []
    total = 0
    for d in docs:
        text = d["text"]
        remaining = max_chars - total
        if remaining <= 0:
            break
        if len(text) > remaining:
            text = text[:remaining]
        label = f"[{d['origin']}]"
        if d.get("title"):
            label += f" {d['title']}"
        if d.get("section"):
            label += f" > {d['section']}"
        parts.append(f"--- {label} (score {d['score']:.2f}) ---\n{text}")
        total += len(text)
    return "\n\n".join(parts)


def strip_markdown(text: str) -> str:
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    text = text.replace("\u2014", ",").replace(" \u2013 ", ", ")
    return text


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def index():
    html = (Path(__file__).parent / "chat.html").read_text()
    return HTMLResponse(content=html)


@app.get("/health")
async def health():
    base = {"calendar_url": CALENDAR_BOOKING_URL or None}
    try:
        info = qdrant.get_collection(COLLECTION)
        return {"status": "ok", "collection": COLLECTION, "points": info.points_count, **base}
    except Exception as e:
        return {"status": "degraded", "error": str(e), **base}


@app.get("/config")
async def config():
    return {
        "calendar_url": CALENDAR_BOOKING_URL or None,
        "voice_enabled": bool(ELEVENLABS_API_KEY),
        "owner_name": OWNER_NAME,
        "owner_role": OWNER_ROLE,
        "welcome_text": WELCOME_TEXT,
    }


ABOUT_PAGE_TRIGGERS = {
    "ask me about this page",
    "tell me about this page",
    "what is this page",
    "how does this work",
    "how does this page work",
    "why does this exist",
    "why did you build this",
    "what is this",
}

def _run_rag(message: str, session_id: str, voice_mode: bool = False) -> str:
    history = get_history(session_id)
    docs = search_knowledge(message)
    context = build_context(docs)

    messages = list(history)
    user_msg = f"Context from {OWNER_NAME}'s portfolio knowledge base:\n\n{context}\n\nQuestion: {message}"
    messages.append({"role": "user", "content": user_msg})

    system_text = SYSTEM_PROMPT
    if voice_mode:
        system_text = VOICE_MODE_PREAMBLE + "\n\n" + SYSTEM_PROMPT
    max_tok = 220 if voice_mode else MAX_TOKENS

    # Use Anthropic prompt caching on the (stable) system prompt. The system text
    # is identical every call within a session, so we mark it ephemeral-cached.
    system_blocks = [{"type": "text", "text": system_text, "cache_control": {"type": "ephemeral"}}]

    try:
        response = claude_client.messages.create(
            model=LLM_MODEL,
            system=system_blocks,
            messages=messages,
            max_tokens=max_tok,
            temperature=0.7,
        )
        reply = strip_markdown(response.content[0].text)
        usage = response.usage
        cache_read = getattr(usage, "cache_read_input_tokens", 0) or 0
        cache_write = getattr(usage, "cache_creation_input_tokens", 0) or 0
        if cache_read or cache_write:
            print(f"[cache] read={cache_read} write={cache_write} input={usage.input_tokens}")
        log_api_usage(session_id, usage.input_tokens + cache_read + cache_write, usage.output_tokens)
    except Exception as anthropic_err:
        # Anthropic failed (rate limit, outage, network). Fall back to OpenAI.
        print(f"[fallback] Anthropic failed ({type(anthropic_err).__name__}): {anthropic_err}; using {FALLBACK_MODEL}")
        oai_messages = [{"role": "system", "content": system_text}] + messages
        oai_response = oai.chat.completions.create(
            model=FALLBACK_MODEL,
            messages=oai_messages,
            max_tokens=max_tok,
            temperature=0.7,
        )
        reply = strip_markdown(oai_response.choices[0].message.content)
        log_api_usage(session_id, oai_response.usage.prompt_tokens, oai_response.usage.completion_tokens)

    save_message(session_id, "user", message)
    save_message(session_id, "assistant", reply)
    return reply


def _elevenlabs_tts(text: str) -> str | None:
    """Return base64-encoded MP3 or None on any failure."""
    if not ELEVENLABS_API_KEY:
        return None
    try:
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
        headers = {
            "xi-api-key": ELEVENLABS_API_KEY,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        }
        payload = {
            "text": text,
            "model_id": "eleven_turbo_v2_5",
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
        }
        with httpx.Client(timeout=60.0) as client:
            r = client.post(url, headers=headers, json=payload)
            if r.status_code != 200:
                return None
            return base64.b64encode(r.content).decode("ascii")
    except Exception:
        return None


@app.post("/chat")
@limiter.limit("30/minute")
async def chat(request: Request):
    body = await request.json()
    message = (body.get("message") or "").strip()
    session_id = body.get("session_id") or "default"

    if not message:
        return {"error": "Empty message"}
    if len(message) > MAX_MESSAGE_LEN:
        return {"error": "Message too long."}

    if message.lower() == "__clear__":
        clear_history(session_id)
        return {"status": "cleared"}

    try:
        reply = _run_rag(message, session_id, voice_mode=False)
        return {"reply": reply, "session_cost_usd": get_session_cost(session_id)}
    except Exception as exc:
        import traceback; traceback.print_exc()
        return {"error": f"Something went wrong on my end. Try again in a moment. ({type(exc).__name__})"}


@app.post("/chat/voice")
@limiter.limit("30/minute")
async def chat_voice(request: Request):
    body = await request.json()
    message = (body.get("message") or "").strip()
    session_id = body.get("session_id") or "default"
    voice_mode = bool(body.get("voice_mode", True))

    if not message:
        return {"error": "Empty message"}
    if len(message) > MAX_MESSAGE_LEN:
        return {"error": "Message too long."}

    if message.lower() == "__clear__":
        clear_history(session_id)
        return {"status": "cleared"}

    if message.lower() == "__welcome__":
        audio_b64 = _elevenlabs_tts(WELCOME_TEXT)
        resp = {"reply": WELCOME_TEXT}
        if audio_b64:
            resp["audio"] = audio_b64
            resp["audio_format"] = "mp3"
        return resp

    try:
        reply = _run_rag(message, session_id, voice_mode=voice_mode)
    except Exception as exc:
        import traceback; traceback.print_exc()
        return {"error": f"Something went wrong on my end. Try again in a moment. ({type(exc).__name__})"}
    audio_b64 = _elevenlabs_tts(reply)
    resp = {"reply": reply, "session_cost_usd": get_session_cost(session_id)}
    if audio_b64:
        resp["audio"] = audio_b64
        resp["audio_format"] = "mp3"
    return resp


@app.post("/clear")
async def clear_endpoint(request: Request):
    body = await request.json()
    session_id = body.get("session_id") or "default"
    clear_history(session_id)
    return {"status": "cleared"}


@app.get("/api/stats")
async def stats():
    with _db_lock:
        conn = _get_db()
        total_sessions = conn.execute("SELECT COUNT(DISTINCT session_id) FROM messages").fetchone()[0]
        total_messages = conn.execute("SELECT COUNT(*) FROM messages WHERE role = 'user'").fetchone()[0]
        today_messages = conn.execute(
            "SELECT COUNT(*) FROM messages WHERE role = 'user' AND date(created_at) = date('now')"
        ).fetchone()[0]
        cost_today = conn.execute(
            "SELECT COALESCE(SUM(cost_usd), 0), COALESCE(SUM(input_tokens), 0), COALESCE(SUM(output_tokens), 0) "
            "FROM api_usage WHERE date(created_at) = date('now')"
        ).fetchone()
        cost_total = conn.execute(
            "SELECT COALESCE(SUM(cost_usd), 0), COALESCE(SUM(input_tokens), 0), COALESCE(SUM(output_tokens), 0) "
            "FROM api_usage"
        ).fetchone()
        daily = conn.execute(
            "SELECT date(created_at) as day, SUM(cost_usd), SUM(input_tokens), SUM(output_tokens), COUNT(*) "
            "FROM api_usage WHERE created_at >= datetime('now', '-7 days') GROUP BY day ORDER BY day"
        ).fetchall()
        conn.close()

    return {
        "model": LLM_MODEL,
        "collection": COLLECTION,
        "total_sessions": total_sessions,
        "total_messages": total_messages,
        "today_messages": today_messages,
        "cost": {
            "today_usd": round(cost_today[0], 4),
            "total_usd": round(cost_total[0], 4),
            "today_input_tokens": cost_today[1],
            "today_output_tokens": cost_today[2],
            "total_input_tokens": cost_total[1],
            "total_output_tokens": cost_total[2],
        },
        "daily": [
            {
                "date": r[0],
                "cost_usd": round(r[1] or 0, 4),
                "input_tokens": r[2] or 0,
                "output_tokens": r[3] or 0,
                "requests": r[4],
            }
            for r in daily
        ],
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8510)
