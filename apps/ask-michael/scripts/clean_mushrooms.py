#!/usr/bin/env python3
"""Remove all mushroom/mycology-related bullet points from distilled knowledge files."""

import re
from pathlib import Path

KNOWLEDGE_DIR = Path(__file__).parent.parent / "data" / "knowledge"

PATTERN = re.compile(
    r"mushroom|mycolog|psilocyb|psilocybe|fungi|fungal|spore|microdose|"
    r"lion.s mane|reishi|cordycep|chaga|turkey tail|shiitake|maitake|"
    r"hudson mushroom|mood mushroom|real simple mushroom|cultivat.*mushroom|"
    r"laminar flow hood|autoclave.*mushroom|grain spawn|fruiting block",
    re.IGNORECASE,
)

def clean_file(path: Path) -> int:
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    cleaned = []
    removed = 0
    i = 0
    while i < len(lines):
        line = lines[i]
        if PATTERN.search(line):
            removed += 1
            i += 1
            # If the next lines are a continuation of this bullet (indented), skip them too
            while i < len(lines) and lines[i].startswith("  ") and not lines[i].strip().startswith("-"):
                i += 1
        else:
            cleaned.append(line)
            i += 1
    path.write_text("".join(cleaned), encoding="utf-8")
    return removed

for md_file in sorted(KNOWLEDGE_DIR.glob("*.md")):
    n = clean_file(md_file)
    print(f"{md_file.name}: removed {n} lines")
