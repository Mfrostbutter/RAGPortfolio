# Processing prompts

Ready-to-paste prompts and agent instructions for turning raw sources (chat exports, meeting transcripts, voice memos, draft essays) into ingest-ready markdown. Pair with [`SOURCE-IDEAS.md`](SOURCE-IDEAS.md).

Pick a target — Claude Code, Claude.ai, ChatGPT, or an API script — and paste the relevant prompt. Swap placeholders (`{OWNER_NAME}`, `{SOURCE_FILE}`) before running.

---

## How to use this file

Each prompt below is wrapped in a markdown code block so you can copy it cleanly. All prompts share three guarantees:

1. **Reviewable output.** Every prompt produces markdown, not JSON or prose — so you can skim, edit, and approve before ingesting.
2. **Voice-preserving.** They extract your voice, not summarize it away. Verbatim quotes are preserved.
3. **Low-cost batched.** Large inputs are chunked so you can run them against Haiku or GPT-4o-mini instead of Opus.

Recommended model per job:
- Distillation / categorization: **Haiku 4.5** or **GPT-4o-mini** (cheap, good enough)
- Voice-pattern extraction: **Sonnet 4.6** (pattern recognition matters)
- Redaction / secret-scrubbing: **Haiku 4.5** + a regex pre-pass (belt and suspenders)

---

## 1. ChatGPT / Claude conversation export → distilled knowledge

Your AI chat export is probably the richest voice-authentic source you have. But it's also 100K–5M tokens of raw dialogue. You can't ingest it raw. Distill it by topic.

### Prompt (paste into Claude Code, Claude.ai, or ChatGPT)

```
You are helping me extract signal from my AI chat export to build a portfolio knowledge base that speaks in my voice.

INPUT: A batch of my conversations with {ChatGPT / Claude}. Each conversation has a title, date, and message log. I am the "user"; the AI is the "assistant."

GOAL: Produce a distilled markdown file that captures what I think, how I phrase things, and what I care about — in my voice, not the AI's.

PROCESS:
1. Read all conversations. Identify the 8-15 distinct topics I discuss most often (e.g. "AI strategy," "team leadership," "self-hosted infrastructure").
2. For each topic, write a 150-300 word synthesis in FIRST PERSON, using my verbatim phrases wherever possible. Not "the user discusses X" — "I approach X by..."
3. Under each topic, include 3-8 verbatim quotes from me with minimal editing. Preserve hesitations, filler, and natural cadence ("I mean," "honestly," "yeah but"). Strip only typos and PII.
4. Mark anything uncertain or potentially private with `[REVIEW]` so I can triage.

OUTPUT FORMAT:
---
title: Distilled knowledge from {ChatGPT / Claude} export
source: ai-chat-distillation
date: {today}
---

# {Topic 1}

{150-300 word first-person synthesis.}

**Verbatim:**
- "Quote one."
- "Quote two."

---

# {Topic 2}
...

HARD RULES:
- Never paraphrase my voice into corporate neutral. If I said "that's bullshit," keep it.
- Never invent beliefs or positions I didn't express.
- Flag API keys, passwords, real client names, email addresses, phone numbers with `[REDACT]`.
- Only emit markdown. No preamble, no "here is your distillation."

INPUT:
{PASTE YOUR EXPORT HERE, OR REFERENCE A FILE PATH IF USING CLAUDE CODE}
```

### Notes
- If your export is over ~300K tokens, batch it: feed 20-30 conversations at a time, produce partial files, then run a merge pass.
- OpenAI export: unzip `conversations.json`, convert to markdown with a tiny script, feed in batches.
- Anthropic export: comes as JSON with clear message structure, easier to batch.

---

## 2. Meeting transcripts → voice patterns + topic notes

Meeting transcripts (Otter, Fathom, Granola, Fireflies) are where your actual spoken voice lives. Two outputs per transcript: one is a voice-patterns analysis, the other is topical content.

### Prompt A: Voice-patterns extraction

```
I am building a RAG chatbot that speaks in my voice. I am {OWNER_NAME}, a {OWNER_ROLE}. I will paste a meeting transcript where I am one of the speakers (identified as {MY_NAME_IN_TRANSCRIPT}).

GOAL: Extract concrete, reusable voice patterns that I can feed into a system prompt so an LLM can imitate how I actually talk.

For each category, output 5-10 verbatim examples from this transcript, exactly as I said them. No paraphrasing.

OUTPUT (markdown):

# Voice patterns — {meeting name / date}

## Opens thoughts with
- "..."

## Transitions with
- "..."

## Agrees with
- "..."

## Disagrees with
- "..."

## Signals uncertainty with
- "..."

## Repeat-phrases that land naturally
- "..."

## Filler when it fits spoken rhythm
- "..."

## Words or framings I never use (infer from absence)
- ...

## Characteristic sentence shape
{1-2 sentence description of my typical sentence length, structure, and rhythm}

## Do-not-use list (corporate jargon I avoided)
- synergy, leverage, paradigm shift, game-changer... {any you notice}

HARD RULES:
- Verbatim quotes only. If I didn't say it exactly, don't put it in.
- If I was terse in this meeting, the output is terse. Don't pad.
- Flag any confidential / client-specific content with `[REVIEW]`.

INPUT TRANSCRIPT:
{PASTE}
```

Run this against 10-20 transcripts, then merge the outputs into one `voice-patterns.md` file. That file goes into your system prompt as the Voice section.

### Prompt B: Topical content extraction from transcripts

```
I am building a RAG knowledge base from meeting transcripts I participated in. I am {OWNER_NAME}, speaker {MY_NAME_IN_TRANSCRIPT} in this transcript.

GOAL: Extract the substantive things I said — decisions, explanations, positions, examples — as first-person markdown that can be ingested into a vector DB.

PROCESS:
1. Identify 3-8 distinct substantive topics I spoke to in this transcript (not small talk, not logistics).
2. For each, write a 100-200 word first-person note in my voice.
3. Include 2-4 verbatim quotes per topic.
4. Preserve my actual cadence. Do not smooth.

OUTPUT:
---
title: Notes from {meeting name / date}
source: meeting-transcript
date: {meeting date}
topics: [topic1, topic2, ...]
---

# {Topic 1}

{100-200 word first-person synthesis.}

**Said verbatim:**
- "..."
- "..."

# {Topic 2}
...

HARD RULES:
- Drop anything confidential: client names, deal specifics, personal details about others. Replace with `[CLIENT]`, `[PERSON]`.
- If I didn't actually say something substantive about a topic, skip it. No filler.
- First person, always.

INPUT:
{PASTE TRANSCRIPT}
```

---

## 3. Voice memos / podcast appearances → transcript + processing

### Step 1: Transcribe

Use Whisper locally for privacy + cost:

```bash
# Install once
pip install -U openai-whisper

# Transcribe (large-v3 is best quality; medium is fast enough and good)
whisper my-voice-memo.m4a --model medium --language en --output_format txt
```

Or use the OpenAI API (`whisper-1`) if you don't mind uploading, or a hosted tool (Descript, Riverside) if you want speaker diarization.

### Step 2: Process the transcript

Feed the output into **Prompt A** (voice patterns) or **Prompt B** (topical content) from section 2 above. Voice memos lean toward Prompt A (raw voice); podcast appearances lean toward Prompt B (substantive topics).

### Podcast-specific refinement prompt

```
I was a guest on a podcast called {PODCAST_NAME}. The host is {HOST_NAME}. I am {OWNER_NAME}.

GOAL: Extract my substantive contributions as a first-person markdown note, as if I had written it down as a blog post.

Keep MY answers verbatim wherever possible. Summarize the host's setup questions in one line each, so context is preserved but the output is my voice, not theirs.

OUTPUT:
---
title: Guest appearance on {PODCAST_NAME}
source: podcast-appearance
date: {airdate}
topics: [...]
---

## What we talked about
{One paragraph, first person, what the conversation covered}

## {Topic 1}
{Host set up: one-line summary of the question}

{My full answer, preserved verbatim, lightly edited for readability}

## {Topic 2}
...

INPUT:
{PASTE TRANSCRIPT}
```

---

## 4. Unpublished drafts, notes, scrap files → ingest-ready markdown

Your Notion / Obsidian / Apple Notes / Drafts graveyard is signal-rich. Most of it isn't publishable as-is. This prompt cleans it up without losing voice.

```
I have a collection of unpublished drafts and scrap notes. Some are 80% done, some are 20% done, some are just bullet lists. I want to extract the ones that are coherent enough to ingest into a RAG knowledge base.

GOAL: For each draft, decide: polish, flag, or drop.

DECISION RULES:
- POLISH: if the draft has a clear point and is 70%+ coherent. Finish it in my voice. Target 200-500 words. Do not rewrite my phrasing unless it's broken.
- FLAG: if the draft has a strong idea but needs my input to complete. Output a 2-3 sentence summary + "[REVIEW: {what's missing}]"
- DROP: if the draft is a stub, duplicate, or unclear. Do not output anything for these.

OUTPUT FORMAT:
For each POLISHED draft:
---
title: {original or inferred title}
source: unpublished-draft
date: {today}
status: polished
---

# {Title}

{finished piece in my voice}

---

For each FLAGGED draft:
---
title: {inferred title}
source: unpublished-draft
status: needs-review
---

# {Title}

[REVIEW: {what's missing}]

{1-3 sentence summary of what the draft was going for}

HARD RULES:
- My voice above all. Don't smooth into generic blog prose.
- No hallucinated facts or numbers. If I wrote "~50K vectors," don't make it "50,000 vectors" — match my style.
- Drop anything that mentions clients by name, internal company details, or secrets.

INPUT:
{PASTE DRAFTS, ONE PER BATCH}
```

---

## 5. Email / Slack / sent-folder content → redacted ingest

Only use this if you have rights to the content (personal email, your own public GitHub comments, messages you sent). Never ingest messages from others without consent.

```
I have a batch of emails/messages I sent. I want to extract the parts where I was explaining a technical decision, pitching an idea, or teaching something — the parts where my voice is clearest.

REDACTION FIRST:
1. Replace all recipient names with `[RECIPIENT]`.
2. Replace all company / client names with `[COMPANY]` or `[CLIENT]`.
3. Replace all email addresses, phone numbers, and personal identifiers with `[PII]`.
4. Drop any message that contains: API keys, passwords, credentials, financial figures tied to a deal, legal strategy, personnel decisions about specific people.

EXTRACTION:
For each KEPT message, output:
---
title: {inferred one-line topic}
source: sent-email
date: {date}
topics: [...]
---

# {Topic}

{The substantive part of what I wrote, with redactions applied.}

HARD RULES:
- If in doubt, drop. You are processing private correspondence. Defaulting to drop is correct.
- Do not synthesize across messages. One output per input.
- Preserve my actual phrasing. No "cleaning up" tone.

INPUT:
{PASTE MESSAGES}
```

---

## 6. Resume variants / bio pages → structured facts

Resumes, CVs, LinkedIn profiles, speaker bios — these become the factual substrate of the bot. Different from voice work. Goal is precision.

```
I have {N} resume / CV / bio variants. I want to extract a single canonical set of structured facts for a RAG knowledge base.

GOAL: Produce one canonical `professional-profile.md` that reconciles all variants. Where versions disagree, note the disagreement and flag for my review.

OUTPUT:
---
title: Professional profile (canonical)
source: resume-synthesis
date: {today}
---

## Current role
{Latest role. Flag if variants disagree.}

## Role history
{Reverse chronological, one paragraph per role. Include dates, title, employer type (redacted if needed), and 2-4 concrete things shipped.}

## Education
{Schools, degrees, years.}

## Signature projects
{3-7 projects. One paragraph each: problem, approach, result, stack.}

## Recognition
{Awards, certifications, talks, publications.}

## Skills (narrative, not list)
{2-3 sentences in my voice about what I actually do day-to-day. Skip generic skill lists.}

## [REVIEW] Disagreements across variants
- {Variant A said X about Role Y; Variant B said Z. Confirm which is current.}
- ...

HARD RULES:
- Factual accuracy > comprehensiveness. If dates disagree, flag — don't guess.
- No embellishment. If a variant said "led team of 5," another said "managed 3," flag it.
- Narrative skills only. No "Skills: Python, Docker, AWS..." lists.

INPUT:
{PASTE RESUMES / CVS / BIOS}
```

---

## 7. Secret-scrubbing pass (run on EVERY processed output)

Before ingesting anything processed by the prompts above, run one final secret-scrub. This is the last line of defense.

```
Scan the following markdown files for:

- API keys (patterns: sk-*, sk_live_*, sk_test_*, pk_live_*, xoxb-*, xoxp-*, ghp_*, gho_*, AKIA*, AIza*)
- Passwords in plain text (look for `password=`, `pwd:`, `Fr0*`, etc.)
- Bearer tokens, JWTs, OAuth secrets
- Private IPs (10.x.x.x, 192.168.x.x, 172.16-31.x.x)
- Personal email addresses
- Phone numbers
- Real client names you know I shouldn't publish ({LIST YOUR CLIENT NAMES HERE})
- SSH private keys or `-----BEGIN PRIVATE KEY-----` blocks

For each finding, output:
  FILE: {filename}
  LINE: {line number}
  TYPE: {category}
  SNIPPET: {matched text, redacted if actually sensitive}

If you find nothing, output: CLEAN.

INPUT FILES:
{PASTE OR REFERENCE}
```

Follow up with a manual `grep -rE "..."` pass in your terminal. Two checks beat one.

---

## 8. Voice-patterns consolidation (run last, on all processed outputs)

After running the prompts above on multiple sources, you'll have many partial `voice-patterns.md` files. Merge them into one canonical voice file that feeds your system prompt.

```
I have {N} partial voice-pattern files extracted from different sources (meetings, podcasts, chat exports). I want to merge them into one canonical voice pattern document.

GOAL: Consolidate duplicates, rank by frequency, and output a single voice reference that my system prompt can use to calibrate my voice.

PROCESS:
1. For each category (opens thoughts with, transitions with, agrees with, etc.), aggregate all examples across files.
2. Deduplicate. If "Honestly" appears 14 times across 6 transcripts, it's a real signal. If "Indeed" appears once, drop it.
3. For each kept pattern, include up to 5 representative verbatim examples.
4. At the end, produce a "Top 10 most characteristic patterns" section — the fingerprint phrases that most identify my voice.

OUTPUT:
---
title: Voice patterns (canonical)
source: voice-patterns-consolidation
date: {today}
---

# Voice patterns

## Opens thoughts with
- "..." (N occurrences)
- "..." (N occurrences)

...

# Top 10 fingerprint phrases
1. "..."
2. "..."
...

INPUT:
{PASTE OR REFERENCE PARTIAL FILES}
```

Drop the `# Voice patterns` section of the output into `apps/rag-chat/prompts/system.md` under a new "Voice" heading. That's your calibration layer.

---

## Putting it all together: a recommended workflow

For a ~4 hour session that will give you a strong first corpus:

1. **(30 min) Export everything.** ChatGPT, Claude, your most recent 10 meeting transcripts, resume, LinkedIn export, your blog posts.
2. **(60 min) Run Prompt 1** on your AI chat export. Review the output. Approve the topic files.
3. **(45 min) Run Prompt 2A** on 5 meeting transcripts. Produce partial voice-pattern files.
4. **(30 min) Run Prompt 2B** on the same transcripts. Produce topical content files.
5. **(20 min) Run Prompt 6** on your resume variants. Produce `professional-profile.md`.
6. **(15 min) Run Prompt 8** to merge voice-patterns. Paste the output into `prompts/system.md`.
7. **(20 min) Run Prompt 7** across everything. Fix any findings.
8. **(20 min) Commit, `python ingest.py --all`, test the bot.**

Iterate from there. Add new sources (Prompt 3 for podcasts, Prompt 4 for drafts) as you find time.

---

## One-liner for Claude Code users

If you're running Claude Code in a directory that contains your raw exports, you can invoke any of the prompts above directly by pasting the prompt and saying "apply this to the files in `./raw-exports/`". Claude Code will read, process, and write output files without you needing to manually paste content.

Example:

```
Apply the prompt in apps/rag-chat/data/PROCESSING-PROMPTS.md section 1 to my ChatGPT export at ./raw-exports/chatgpt/conversations.json. Output one markdown file per topic at data/ai-chat/.
```
