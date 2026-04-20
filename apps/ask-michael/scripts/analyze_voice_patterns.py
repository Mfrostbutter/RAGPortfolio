#!/usr/bin/env python3
"""
Analyze Michael's voice corpus to extract concrete patterns for the system prompt.
Reads voice-corpus-transcripts.md and voice-corpus-gpt.md, batches through GPT-4o-mini,
and outputs a voice-patterns.md file with specific rules, phrases, and examples.
"""

import os
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

SCRIPT_DIR = Path(__file__).parent
APP_DIR = SCRIPT_DIR.parent
load_dotenv(APP_DIR / ".env")

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

TRANSCRIPTS = APP_DIR / "data" / "founder-profile" / "voice-corpus-transcripts.md"
GPT_CORPUS = APP_DIR / "data" / "founder-profile" / "voice-corpus-gpt.md"
OUT = APP_DIR / "data" / "founder-profile" / "voice-patterns.md"


def load_samples(path: Path, max_chars: int = 40000) -> str:
    text = path.read_text(encoding="utf-8")
    # Skip frontmatter and header
    lines = text.splitlines()
    start = next((i for i, l in enumerate(lines) if l.startswith("---") and i > 0), 10)
    body = "\n".join(lines[start + 1:])
    return body[:max_chars]


def analyze(corpus: str, prompt: str) -> str:
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a voice analyst studying how a specific person communicates. "
                    "Be specific and concrete. Extract actual phrases, patterns, and tendencies. "
                    "Do not generalize — quote real examples from the text."
                ),
            },
            {"role": "user", "content": f"{prompt}\n\nCorpus:\n\n{corpus}"},
        ],
        max_tokens=2000,
        temperature=0.2,
    )
    return resp.choices[0].message.content.strip()


if __name__ == "__main__":
    print("Loading corpora...")
    spoken = load_samples(TRANSCRIPTS)
    written = load_samples(GPT_CORPUS)

    print("Analyzing spoken patterns (meeting transcripts)...")
    spoken_analysis = analyze(
        spoken,
        """Analyze Michael Frostbutter's spoken voice from these meeting transcript excerpts.
Extract:
1. Phrases he uses repeatedly (quote exact phrases)
2. How he opens statements/thoughts
3. How he transitions between ideas
4. Filler words or verbal tics
5. How he signals agreement, disagreement, or uncertainty
6. His typical sentence length and rhythm
7. 5 example quotes that best represent his natural speaking style""",
    )
    time.sleep(0.5)

    print("Analyzing written patterns (GPT messages)...")
    written_analysis = analyze(
        written,
        """Analyze Michael Frostbutter's written voice from these ChatGPT messages.
Extract:
1. Phrases and sentence starters he uses repeatedly (quote exact phrases)
2. How he frames requests and explains context
3. His vocabulary preferences — words he favors and words he avoids
4. How he expresses enthusiasm, frustration, or strong opinions
5. Punctuation and formatting habits
6. How formal or casual his writing is
7. 5 example messages that best represent his natural writing style""",
    )
    time.sleep(0.5)

    print("Synthesizing voice rules...")
    synthesis = analyze(
        f"SPOKEN ANALYSIS:\n{spoken_analysis}\n\nWRITTEN ANALYSIS:\n{written_analysis}",
        """Based on these analyses of a person's spoken and written voice, write a concise voice guide
for an AI system prompt. The AI needs to respond AS this person.

Output format:
## Core Voice Traits
(5-7 bullet points — the most defining characteristics)

## Phrases He Uses
(actual quoted phrases, grouped by function: agreement, transitions, emphasis, etc.)

## Phrases He Never Uses
(corporate speak, buzzwords, or patterns clearly absent from the corpus)

## Sentence Rhythm
(how to structure sentences to match his style)

## Tone Calibration
(how formal, how direct, how personal — with examples)""",
    )

    output = f"""---
title: Voice Patterns — Michael Frostbutter
topic: voice-calibration
collection: founder_knowledge
description: Extracted voice patterns from meeting transcripts and GPT conversation history. Used to calibrate Ask Michael system prompt.
---

# Voice Patterns — Michael Frostbutter

> Generated from {TRANSCRIPTS.name} ({sum(1 for l in TRANSCRIPTS.read_text().splitlines() if l.strip())} lines) and {GPT_CORPUS.name}.

---

## Spoken Voice Analysis
*(from client meeting transcripts)*

{spoken_analysis}

---

## Written Voice Analysis
*(from ChatGPT conversation history)*

{written_analysis}

---

## Synthesized Voice Guide
*(for system prompt use)*

{synthesis}
"""

    OUT.write_text(output, encoding="utf-8")
    print(f"\nDone. Voice patterns written to {OUT}")
