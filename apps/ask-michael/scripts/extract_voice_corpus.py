#!/usr/bin/env python3
"""
Extract Michael's voice from two sources:
  1. Meeting transcripts (.docx) — lines labeled "Michael Frostbutter"
  2. ChatGPT export (conversations-*.json) — all user messages

Outputs:
  data/founder-profile/voice-corpus-transcripts.md
  data/founder-profile/voice-corpus-gpt.md
"""

import json
import re
import sys
from pathlib import Path

from docx import Document

SCRIPT_DIR = Path(__file__).parent
APP_DIR = SCRIPT_DIR.parent
DATA_OUT = APP_DIR / "data" / "founder-profile"
DATA_OUT.mkdir(parents=True, exist_ok=True)

TRANSCRIPTS_DIR = Path(
    "/Users/frosty/Desktop/Claude-Code-Projects/BWIT-DEV/Knowledge/Meeting Transcripts"
)
GPT_DIR = Path(
    "/Users/frosty/Desktop/Claude-Code-Projects/BWIT-DEV/GPT-Conversations/"
    "b54434772aa95c388873b411ba0a1600c821185eac8c58dec1a9355ae8d88e51-2026-03-09-01-46-14-2e5c79a2af744b0bb0a17ec0442355e4"
)

MIN_WORDS = 8  # skip one-liners shorter than this

# ---------------------------------------------------------------------------
# Transcript extraction
# ---------------------------------------------------------------------------

MICHAEL_RE = re.compile(r"^Michael\s+Frostbutter\s+\d+:\d+\s*\n?", re.IGNORECASE)
ANY_SPEAKER_RE = re.compile(r"^[A-Za-z][\w\s]+\s+\d+:\d+\s*\n", re.MULTILINE)


def extract_transcripts() -> list[str]:
    lines: list[str] = []
    docx_files = sorted(TRANSCRIPTS_DIR.glob("*.docx"))
    print(f"Found {len(docx_files)} transcript files")

    for path in docx_files:
        try:
            doc = Document(path)
        except Exception as e:
            print(f"  SKIP {path.name}: {e}", file=sys.stderr)
            continue

        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue

            # Each paragraph is "Speaker Name  H:MM\nSpoken text..."
            if MICHAEL_RE.match(text):
                # Strip the speaker header line, keep everything after
                speech = MICHAEL_RE.sub("", text).strip()
                if len(speech.split()) >= MIN_WORDS:
                    lines.append(speech)

    return lines


# ---------------------------------------------------------------------------
# GPT export extraction
# ---------------------------------------------------------------------------

def extract_gpt() -> list[str]:
    lines: list[str] = []
    seen: set[str] = set()

    json_files = sorted(GPT_DIR.glob("conversations-*.json"))
    print(f"Found {len(json_files)} GPT conversation files")

    for path in json_files:
        with open(path, encoding="utf-8") as f:
            convos = json.load(f)

        for convo in convos:
            mapping = convo.get("mapping", {})
            for node in mapping.values():
                msg = node.get("message")
                if not msg:
                    continue
                if msg.get("author", {}).get("role") != "user":
                    continue

                content = msg.get("content", {})
                parts = content.get("parts", [])
                for part in parts:
                    if not isinstance(part, str):
                        continue
                    clean = part.strip()
                    # skip short messages, code blocks, image refs
                    if len(clean.split()) < MIN_WORDS:
                        continue
                    if clean.startswith("```") or clean.startswith("data:"):
                        continue
                    # deduplicate
                    key = clean[:120]
                    if key in seen:
                        continue
                    seen.add(key)
                    lines.append(clean)

    return lines


# ---------------------------------------------------------------------------
# Write outputs
# ---------------------------------------------------------------------------

def write_md(path: Path, title: str, source_desc: str, lines: list[str]) -> None:
    header = f"""---
title: {title}
topic: voice-corpus
collection: founder_knowledge
description: {source_desc}
---

# {title}

{source_desc}

Total entries: {len(lines)}

---

"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(header)
        for line in lines:
            f.write(line.replace("\n", " ").strip())
            f.write("\n\n")
    print(f"Wrote {len(lines)} entries → {path}")


if __name__ == "__main__":
    print("=== Extracting meeting transcript lines ===")
    transcript_lines = extract_transcripts()
    write_md(
        DATA_OUT / "voice-corpus-transcripts.md",
        "Voice Corpus — Meeting Transcripts",
        "Michael Frostbutter's spoken lines extracted from client and internal meeting transcripts. Used to calibrate voice authenticity.",
        transcript_lines,
    )

    print("\n=== Extracting ChatGPT conversation messages ===")
    gpt_lines = extract_gpt()
    write_md(
        DATA_OUT / "voice-corpus-gpt.md",
        "Voice Corpus — Written Messages",
        "Michael Frostbutter's written messages extracted from ChatGPT conversation history. Captures natural written voice, thought patterns, and communication style.",
        gpt_lines,
    )

    print("\nDone.")
