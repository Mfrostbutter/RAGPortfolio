# Knowledge source ideas

A curated list of content sources for your RAG knowledge base, organized by how authentically they capture your voice. The bot is only as interesting as the corpus behind it. Polished content alone produces a polished-but-hollow bot. Raw, unfiltered signal produces a bot that actually sounds like you.

The principle: **the places where you were talking without a filter are higher-value than the places you were performing.** Write drafts of this speak in your voice. Recorded calls where you were thinking out loud capture your actual cadence. An email to a trusted peer reveals how you explain things when no one is watching.

---

## Tier 1: High-authenticity voice corpus

These are the gold. They capture how you actually think and talk when you aren't performing.

### AI chat exports
- **ChatGPT conversation export** (Settings → Data Controls → Export data). Months or years of you explaining problems, pushing back, working through ideas in your real voice.
- **Claude conversation export** (Settings → Privacy → Export data).
- **Gemini / Copilot / Grok** exports if you use them.

**Why it's gold:** you're not writing for an audience. You're just thinking. The vocabulary, the impatience, the specific phrases you repeat — all there.

**What to extract:** topical summaries and representative quotes. Don't dump 500K tokens raw. Run them through a distillation pass (there's a pattern in the original project if you want inspiration: summarize by topic, extract 5-10 verbatim quotes per topic, review and approve before ingest).

### Meeting transcriptions
- **Otter.ai / Fathom / Granola / Zoom AI / Tactiq / Fireflies** exports of internal and external meetings.
- Calls where you were pitching, debating, explaining technical decisions, interviewing candidates, or giving feedback.

**Why it's gold:** this is literally how you sound out loud. Hesitations, common phrases, how you open and close thoughts.

**What to extract:** a voice-patterns analysis. What phrases do you repeat? How do you open vs. close? How do you agree, disagree, signal uncertainty? Build these into your system prompt as calibration.

### Voice recordings
- **Voice memos** on your phone (Apple, Google, Samsung). Often where you capture ideas mid-commute in your most natural voice.
- **Loom recordings** where you narrated a walkthrough, demo, or decision rationale.
- **Podcast / panel / conference appearances.** Transcribe via Whisper or YouTube auto-captions.
- **Voice clone training script** if you recorded one for ElevenLabs or similar — by design it's you reading your own words.

### Written drafts that never shipped
- **Half-finished blog posts** in Notion, Obsidian, Drafts, or scrap files.
- **Abandoned tweets** in your drafts folder.
- **Notes to self** in any note-taking app.

**Why it's gold:** unpolished = unfiltered. What you almost published is often more honest than what you actually published.

---

## Tier 2: Deliberate writing, still in your voice

Polished but authored by you. Good for topical coverage and position statements.

### Long-form published work
- **Blog posts and essays** (personal site, Substack, Medium).
- **LinkedIn articles** (the long-form ones, not the posts).
- **Guest articles** on industry sites.
- **Newsletter archives** you've written.

### Short-form published work
- **LinkedIn posts** — grab your post history from Sales Navigator or your LinkedIn data export.
- **Twitter / X threads** — export via their data download.
- **Hacker News comments** (if you're active).
- **Reddit comments** (if you have a professional presence there).

### Technical writing
- **White papers** you authored or co-authored.
- **RFCs, design docs, architecture decision records** you wrote.
- **Conference talk scripts and slide notes.**
- **GitHub READMEs and project docs** for things you built.
- **Stack Overflow answers** (high-karma answers are often cleanly reasoned explanations).

### Internal-to-public bridges
- **Slack / Discord threads where you were teaching or debating** (redact names first).
- **Product or engineering blog posts** you wrote for an employer (check that you have rights).

---

## Tier 3: Structured facts and evidence

Not voice signal — but the substrate that lets the bot answer factual questions about you.

### Career facts
- **Resume and CV variants** (different versions for different roles reveal framing choices).
- **LinkedIn profile export** (positions, descriptions, skills endorsements).
- **GitHub profile + pinned repos** (project summaries, stack, stars).
- **Portfolio site pages** if you have one.
- **Award / certification / speaking gig lists.**

### Project case studies
- **One writeup per shipped project** with: problem, approach, decision points, result, stack, what you would change.
- **Interview prep docs** where you've rehearsed your STAR stories.
- **Before-and-after metrics** (tickets reduced by X, latency cut by Y, cost down by Z).

### Published thought leadership summaries
- **Summaries of your own articles** with key arguments extracted. The bot can cite the article when asked.
- **A "positions" doc** — things you believe about your field, each with 1-2 sentence justification.

---

## Tier 4: Think-outside-the-box sources

The ones people don't think of, that often carry the most character.

### Unfiltered text-streams
- **Notes app** — the thousands of fragments that live in Apple Notes, Google Keep, Notion daily logs, Obsidian daily notes. Aggregate and dedupe.
- **Journal entries** (if you're comfortable publishing them — skip anything personal; keep the professional / philosophical ones).
- **Commit messages** from your own projects over the years. Shows how you think about change.
- **Code comments you wrote** — especially the ones that explain why, not what.

### Email and messaging (handle with care)
- **Sent-folder emails** where you were explaining a decision to a peer or pitching a client. Redact names and confidential info first.
- **GitHub issue comments** you wrote on your own public projects.
- **Engineering mailing list posts** or Google Group posts you authored.

### Recordings you didn't know were a corpus
- **Your own voicemails and voice-notes** to others (ask for copies if you need).
- **Interview recordings** where you answered questions about your work (podcast guest spots, customer interviews, panel appearances).
- **Workshop or class recordings** where you were teaching.
- **All-hands or team-meeting recordings** where you presented.

### Artifacts from how you work
- **Whiteboard photos** from meetings where you sketched architecture. OCR them or just describe each photo in markdown.
- **Screenshots from a live coding or pair-programming session** with your narration.
- **Decision logs or changelogs** you maintained for a project.

### Social / community presence
- **GitHub Discussions / Issue comments** where you were helping others.
- **Discord community answers** (in communities you're a known voice in).
- **Meetup notes or Q&A session transcripts** where you spoke.

### The "if no one was watching" layer
- **Your own bookmark folder names and tags** (reveals mental taxonomy).
- **Your personal TODO list items from the past year** (shows what you actually care about).
- **Your browser tab groups** (same).
- **The problem statements at the top of your side projects** (these are you explaining a problem to yourself).

---

## How to process raw sources

Don't dump raw into Qdrant. Most of these need a curation pass:

1. **Export raw** — get the full dump out (JSON, HTML, markdown, text).
2. **Filter and redact** — strip anything confidential, personal, secret. **Run a regex sweep for API keys, passwords, real client names, private phone numbers.** Low effort, high risk if you skip it.
3. **Distill by topic** — for long corpora (chat exports, meeting transcripts), use a cheap LLM to summarize by topic and extract representative quotes. Cost is small, quality lift is huge.
4. **Review before ingest** — a human pass over the distilled output catches things the LLM missed. This is the step most people skip.
5. **Structure as markdown** — one file per topic or per source type. Frontmatter with `topics:` tags.
6. **Register in `_manifest.yml`** — route to `public_kb` (visitor-facing) or `private_kb` (authenticated-only).
7. **Re-ingest** — `python ingest.py --all`.

---

## Voice patterns: the meta-artifact

Once you have Tier 1 content (chat exports, transcripts, voice memos), run a voice-patterns extraction. Output a single markdown file that captures:

- **Opens thoughts with:** (the phrases you actually use, e.g. "So," "Honestly," "Right")
- **Transitions with:** (e.g. "I mean," "But I do know")
- **Agrees with / disagrees with:** (distinctive phrasings)
- **Signals uncertainty with:** (how you actually say "I don't know")
- **Repeat-phrases that feel natural:** (verbatim phrases that recur)
- **Words you never use:** (corporate jargon you avoid — lets you blacklist them in the system prompt)

Inject this into your `prompts/system.md` as a Voice section. This is what tips the bot from "generic helpful assistant" to "sounds like you."

---

## What not to include

- Anything containing secrets (API keys, passwords, tokens, private IPs, emails). **Even once is once too many** on a public-facing bot.
- Anything bound by NDA or a confidentiality clause.
- Client-specific strategy or deliverables.
- Personal details about family, health, relationships beyond what you'd share with a stranger.
- Anything you'd be uncomfortable reading out loud at a hiring interview. The bot will read it out loud, essentially.

---

## Summary

The cheapest way to build a boring portfolio bot is to ingest your resume and your published blog posts and call it done. The cheapest way to build a portfolio bot that actually sounds like you is to ingest the places where you were talking without a filter, then layer polished content on top.

Start with one Tier 1 source (your ChatGPT export is the easiest). Run the distillation pass. Ingest. Test. Iterate. Add sources as you find them.
