#!/usr/bin/env python3
"""
Distill ChatGPT export into structured knowledge files for the ask-michael portfolio.

Pipeline:
  1. Load all conversations-*.json from GPT export
  2. Filter — keep only conversations relevant to personal/professional knowledge
  3. Batch filtered conversations through GPT-4o-mini
  4. Distill into 5 topic markdown files
  5. Write to data/knowledge/ for manual review before ingest

Output files (data/knowledge/):
  - ai-philosophy-and-strategy.md
  - workflows-and-systems.md
  - hobbies-and-interests.md
  - business-and-career.md
  - technical-opinions.md
"""

import json
import os
import re
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

SCRIPT_DIR = Path(__file__).parent
APP_DIR = SCRIPT_DIR.parent
load_dotenv(APP_DIR / ".env")

GPT_DIR = Path(
    "/Users/frosty/Desktop/Claude-Code-Projects/BWIT-DEV/GPT-Conversations/"
    "b54434772aa95c388873b411ba0a1600c821185eac8c58dec1a9355ae8d88e51-2026-03-09-01-46-14-2e5c79a2af744b0bb0a17ec0442355e4"
)
OUT_DIR = APP_DIR / "data" / "knowledge"
OUT_DIR.mkdir(parents=True, exist_ok=True)

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

# ---------------------------------------------------------------------------
# Filter keywords — conversations containing these are likely BWIT ops noise
# ---------------------------------------------------------------------------
NOISE_PATTERNS = re.compile(
    r"connectwise|ticket\s*#?\d{5,}|offboard|cancellation|halo\s*psa|"
    r"cantique\s+order|etsy\s+order|square\s+order|invoice\s*#\d+|"
    r"pve\d|proxmox|netbird|lxc\s+\d{3}|bwit-ingest|systemd\s+unit",
    re.IGNORECASE,
)

KEEP_PATTERNS = re.compile(
    r"ai|machine learning|automation|workflow|n8n|agent|vector|rag|"
    r"mountain\s*bik|mtb|baseball|pilot|navy|cantique|agenius|"
    r"business\s+development|strategy|leadership|hire|career|"
    r"philosophy|opinion|believe|think\s+about|approach|framework",
    re.IGNORECASE,
)

BATCH_SIZE = 30  # conversations per GPT call

# ---------------------------------------------------------------------------
# Topic extraction prompts
# ---------------------------------------------------------------------------

TOPICS = {
    "ai-philosophy-and-strategy": {
        "filename": "ai-philosophy-and-strategy.md",
        "prompt": (
            "Extract every distinct insight, opinion, or belief Michael holds about AI, "
            "machine learning, automation, and AI strategy. Focus on his philosophy: "
            "how he thinks AI should be deployed, what he believes about human-AI collaboration, "
            "governance concerns, practical vs hype distinctions, and how he approaches AI projects. "
            "Format as bullet points grouped by sub-theme. Be specific — capture his actual views, "
            "not generic AI talking points."
        ),
    },
    "workflows-and-systems": {
        "filename": "workflows-and-systems.md",
        "prompt": (
            "Extract every workflow, system, process, or tool Michael has built or designed. "
            "Include: n8n workflows, automation pipelines, data systems, infrastructure decisions, "
            "how he structures projects, his approach to tooling. "
            "Format as bullet points. Include specific tools, platforms, and architectural choices."
        ),
    },
    "hobbies-and-interests": {
        "filename": "hobbies-and-interests.md",
        "prompt": (
            "Extract everything about Michael's personal interests, hobbies, and non-work passions. "
            "Include: mountain biking, baseball, flying/aviation, family, travel, physical pursuits, "
            "anything he does for fun or considers part of his identity outside of work. "
            "Format as bullet points. Capture specific details — trails, gear, experiences, goals."
        ),
    },
    "business-and-career": {
        "filename": "business-and-career.md",
        "prompt": (
            "Extract insights about Michael's business philosophy, career decisions, and professional identity. "
            "Include: how he thinks about running an MSP, building Agenius AI Labs, client relationships, "
            "what he looks for in work, career pivots, lessons learned, how he describes his value. "
            "Format as bullet points. Focus on things that reveal who he is as a professional."
        ),
    },
    "technical-opinions": {
        "filename": "technical-opinions.md",
        "prompt": (
            "Extract Michael's technical opinions, preferences, and strong views on technology. "
            "Include: preferred languages/frameworks, architectural opinions, tools he advocates or avoids, "
            "security posture, opinions on vendors and platforms, technical decisions he's made and why. "
            "Format as bullet points. Capture his actual stances, not neutral descriptions."
        ),
    },
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_conversations() -> list[dict]:
    convos = []
    for path in sorted(GPT_DIR.glob("conversations-*.json")):
        with open(path, encoding="utf-8") as f:
            convos.extend(json.load(f))
    return convos


def extract_text(convo: dict) -> str:
    """Return a cleaned text representation of a conversation."""
    title = convo.get("title", "Untitled")
    lines = [f"[{title}]"]
    mapping = convo.get("mapping", {})
    for node in mapping.values():
        msg = node.get("message")
        if not msg:
            continue
        role = msg.get("author", {}).get("role", "")
        if role not in ("user", "assistant"):
            continue
        parts = msg.get("content", {}).get("parts", [])
        for part in parts:
            if not isinstance(part, str) or not part.strip():
                continue
            prefix = "Michael" if role == "user" else "GPT"
            lines.append(f"{prefix}: {part.strip()[:800]}")
    return "\n".join(lines)


def is_relevant(text: str) -> bool:
    noise_score = len(NOISE_PATTERNS.findall(text))
    keep_score = len(KEEP_PATTERNS.findall(text))
    # Keep if strong keep signal and not dominated by noise
    return keep_score >= 2 and noise_score < keep_score


def distill_batch(texts: list[str], topic_prompt: str) -> str:
    combined = "\n\n---\n\n".join(texts)
    system = (
        "You are extracting knowledge about a specific person — Michael Frostbutter — "
        "from his personal ChatGPT conversation history. "
        "Extract only facts, opinions, and details that are clearly about Michael himself. "
        "Be specific and concrete. Do not invent or embellish. "
        "If a conversation does not contain relevant information for the requested topic, skip it."
    )
    user = (
        f"{topic_prompt}\n\n"
        f"Here are {len(texts)} conversations to analyze:\n\n{combined[:60000]}"
    )
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        max_tokens=2000,
        temperature=0.2,
    )
    return resp.choices[0].message.content.strip()


def write_topic_file(topic_key: str, config: dict, sections: list[str]) -> None:
    path = OUT_DIR / config["filename"]
    header = f"""---
title: {topic_key.replace("-", " ").title()}
topic: founder-knowledge
collection: michael_portfolio
description: Distilled from Michael Frostbutter's ChatGPT conversation history. Review before publishing.
---

# {topic_key.replace("-", " ").title()}

> **Review required before ingest.** Distilled from GPT conversation history via GPT-4o-mini.

"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(header)
        for i, section in enumerate(sections, 1):
            f.write(f"## Batch {i}\n\n{section}\n\n")
    print(f"  Wrote → {path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Loading conversations...")
    all_convos = load_conversations()
    print(f"  Total: {len(all_convos)} conversations")

    print("Filtering relevant conversations...")
    relevant_texts = []
    for convo in all_convos:
        text = extract_text(convo)
        if is_relevant(text):
            relevant_texts.append(text)
    print(f"  Kept: {len(relevant_texts)} conversations after filtering")

    if not relevant_texts:
        print("No relevant conversations found. Exiting.")
        sys.exit(1)

    # Batch into groups
    batches = [relevant_texts[i:i + BATCH_SIZE] for i in range(0, len(relevant_texts), BATCH_SIZE)]
    print(f"  Batches: {len(batches)} x ~{BATCH_SIZE} conversations\n")

    for topic_key, config in TOPICS.items():
        print(f"Distilling: {topic_key}")
        sections = []
        for i, batch in enumerate(batches, 1):
            print(f"  Batch {i}/{len(batches)}...", end=" ", flush=True)
            try:
                result = distill_batch(batch, config["prompt"])
                sections.append(result)
                print("done")
            except Exception as e:
                print(f"ERROR: {e}")
                sections.append(f"[Batch {i} failed: {e}]")
            time.sleep(0.5)  # gentle rate limiting
        write_topic_file(topic_key, config, sections)
        print()

    print(f"Done. Review files in {OUT_DIR} before running ingest.")
