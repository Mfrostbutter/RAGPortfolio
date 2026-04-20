# Claude Code Prompt: "Ask Michael" Portfolio RAG Chatbot

## Objective

Build a personal RAG chatbot called "Ask Michael" for Michael Frostbutter's executive portfolio website. Visitors (recruiters, hiring managers, potential clients) can interactively learn about Michael through AI-powered conversation. This is a portfolio piece that demonstrates the exact skill set Michael is selling: building production RAG systems.

## Architecture

Follow the exact same pattern as the existing RIOS chatbot at `apps/rios/poc-rag/`. That project has a working `ingest.py`, `web_v3.py`, and `chat_v3.html` you should reference for patterns (Qdrant, embeddings, Claude, FastAPI). Adapt, don't reinvent.

### Stack
- **Vector DB:** Qdrant at 10.10.0.60:6333, new collection `michael_portfolio`
- **Embeddings:** snowflake-arctic-embed2 via Ollama on 10.10.0.15:11434 (same as RIOS)
- **LLM:** Claude (Anthropic API) for chat responses
- **Voice:** ElevenLabs TTS (any voice ID; first-person responses)
- **Backend:** Python FastAPI (same pattern as `web_v3.py`)
- **Frontend:** Single-file `chat.html` that can be embedded in a portfolio site
- **Secrets:** All API keys from environment variables via python-dotenv. Never hardcode.

## Project Location

Create everything under: `apps/ask-michael/`

```
apps/ask-michael/
  .env.example          # Template for required env vars
  ingest.py             # Chunk, embed, upsert knowledge base to Qdrant
  web.py                # FastAPI chat backend
  chat.html             # Frontend chat widget
  data/                 # Knowledge base source documents
    founder-bio.md      # Copy from docs/founder-profile/founder-bio.md
    interview-responses.md  # Copy from docs/founder-profile/interview-responses.md
    technical-portfolio.md  # NEW: create this (see below)
    published-content.md    # NEW: create this (see below)
  README.md
```

## Knowledge Base Documents

### Already exist (copy from `docs/founder-profile/`):
1. **`founder-bio.md`** - Full life story, narrative arc, themes
2. **`interview-responses.md`** - Leadership, stakeholder management, technical projects, governance philosophy, daily structure, motivations

### Need to be created:

3. **`technical-portfolio.md`** - Structured summary of technical accomplishments:
   - BWIT Knowledge Platform: MCP-based, built in one week, connects 6 MSPs, automated QBRs, 50% ticket resolution improvement, near-100% SLA
   - RIOS AI Copilot (RIO): RAG chatbot for global design firm, Qdrant + Claude + ElevenLabs voice, 2000+ vectors, daily use by employees
   - Enterprise AI Platform: 3-node Proxmox cluster, Qdrant vector DB, n8n automation, MCP microservices architecture, near-zero cloud cost
   - Content Automation Pipeline: n8n workflows, KIE.ai image generation, automated social media content, costs under $1/week for 14 posts
   - NMCI Deployment: 26,000 workstations in one year, team of 120, Patuxent Naval Air Station
   - Infrastructure: self-hosted Proxmox, LXC containers, nginx, Cloudflare tunnels, Ollama for local inference
   - Security: Wazuh SIEM, endpoint protection, vendor-agnostic model routing based on data sensitivity

4. **`published-content.md`** - Summaries of Michael's published thought leadership:
   - Read and summarize the actual articles from `content/linkedin/`:
     - `shadow-ai-governance-article.md`
     - `ai-data-readiness-gap-article.md`
     - `ai-model-routing-strategy.md`
     - `openclaw-security-post.md`
   - Include key arguments, frameworks, and positioning from each piece
   - These demonstrate thought leadership for Director/VP of AI roles

## Ingest Script (`ingest.py`)

Follow the RIOS `ingest.py` pattern:
- Read all `.md` files from `data/`
- Chunk with ~1500 char chunks, 200 char overlap
- Prepend document-level context headers to each chunk
- Generate metadata per chunk: `source_file`, `section`, `content_type` (bio, interview, portfolio, content)
- Embed via Ollama snowflake-arctic-embed2 (1024 dimensions)
- Upsert to Qdrant collection `michael_portfolio` with payload keys `content` and `metadata` (langchain-compatible)
- Create text indexes for hybrid keyword search on `content` field

## Chat Backend (`web.py`)

Follow the `web_v3.py` pattern but adapt the system prompt:

### System Prompt for the Chatbot

```
You are "Ask Michael," an AI assistant on Michael Frostbutter's executive portfolio website. You help visitors learn about Michael's background, experience, technical projects, leadership philosophy, and career.

You answer questions conversationally, as if Michael were telling his own story. Use first person when quoting Michael directly, third person for factual summaries.

Key facts:
- 49 years old, based in Newburgh, NY
- BS Computer Engineering, University of Maryland
- Did NOT serve in the military. Grew up in a three-generation Navy family (grandfather WWII fighter pilot, father Navy veteran / NASA Communications Director)
- 20+ years in IT, 40+ years around computers (started at age 8 with a Commodore 64)
- Currently: Director of Business Development at Brightworks IT (portfolio of 6 MSPs, 50+ clients)
- Founder: Agenius AI Labs (AI automation consulting)
- Also runs: Cantique (candle business with wife Carissa), Agenius 3D (3D printing)
- Target role: Director / VP / Head of AI
- Built an enterprise AI platform on self-hosted Proxmox infrastructure at near-zero cloud cost
- Built an MCP-based knowledge platform for BWIT in one week that cut ticket resolution by 50%
- Built the RIOS AI Copilot (RAG chatbot) for a global design firm, used daily by employees
- First principles problem solver. Data-first. Security-first. Build over buy. Vendor agnostic.
- Has never let a problem beat him. Relentless.
- Races downhill mountain bikes. Goal: Trans Madeira at 50.
- Forever learning: photography, CAD/3D design, cycling, aviation

Behavior rules:
- Be warm, direct, and confident. Reflect Michael's authentic voice.
- Keep answers concise but substantive. No filler.
- If you don't have information to answer a question, say so honestly.
- Never fabricate details about Michael's background or experience.
- If asked about topics unrelated to Michael, politely redirect.
- Do not use em dashes. Use commas, colons, or rewrite the sentence.
```

### Endpoints
- `GET /` - Serve chat.html
- `POST /chat` - Accept `{"message": "..."}`, return `{"response": "..."}` (text)
- `POST /chat/voice` - Same as /chat but also returns ElevenLabs TTS audio of the response
- `GET /health` - Health check

### Voice Integration (ElevenLabs)

The chatbot supports an opt-in voice mode where responses are read aloud via ElevenLabs. Any ElevenLabs voice ID works; the default is the stock "Adam" voice.

**Implementation:**
- Use the ElevenLabs TTS API to convert the text response to speech
- Voice ID will be stored in env var `ELEVENLABS_VOICE_ID_MICHAEL` (to be created after voice training)
- Use `eleven_turbo_v2_5` model for low latency
- Reference the existing RIOS v3 implementation in `web_v3.py` for the ElevenLabs API pattern
- Return audio as base64-encoded MP3 in the JSON response: `{"response": "...", "audio": "base64..."}`

**Frontend voice UX:**
- Add a speaker/voice toggle button in the chat UI
- When voice mode is ON, auto-play the audio response after each message
- Show a small audio waveform or speaker icon while audio plays
- Voice mode should be OFF by default (visitor opts in)
- Include a volume control or mute option

**System prompt adjustment for voice mode:**
When voice is enabled, all responses should be written in FIRST PERSON as Michael speaking directly. Example: instead of "Michael built an AI platform..." it should say "I built an AI platform..." The system prompt should switch based on whether voice mode is active.

### RAG Flow
1. Embed the user query via Ollama
2. Search Qdrant `michael_portfolio` collection (top_k=10)
3. Assemble context from retrieved chunks
4. Send to Claude with system prompt + context + user message
5. Return response

## Chat Frontend (`chat.html`)

Single-file HTML/CSS/JS. Clean, professional design suitable for an executive portfolio site. No CDN dependencies (inline everything). Should feel premium, not like a demo.

Design requirements:
- Dark theme with a professional accent color (sky blue #38bdf8 or similar)
- Clean sans-serif fonts (system fonts are fine)
- Chat bubble UI with clear user/assistant distinction
- Typing indicator while waiting for response
- Welcome message on load with value proposition and page instructions (see Welcome Experience section below)
- Responsive, works on mobile
- Input field with send button, Enter to submit
- Auto-scroll to latest message

### Mobile Hero Section Fixes

The current hero section is too tall on mobile, pushing the chatbot below the fold. Fix:

1. **Remove the subtitle** "DIRECTOR OF AI · VP OF TECHNOLOGY" from under the name. It's redundant with the green badge.
2. **Move the green badge** ("Open to Director / VP AI Roles") to directly below the name, replacing where the subtitle was.
3. **Buttons side by side**: "Schedule an Interview" and "See the work" should be inline/horizontal, not stacked vertically.
4. **Fix chatbot viewport cutoff on mobile**: The bottom of the chat window gets cut off on mobile. The chat container needs to account for mobile browser chrome. Use `100dvh` (dynamic viewport height) instead of `100vh`, or calculate available height with JS. The chat input and send button must always be visible and usable on mobile.

These changes condense the hero, reduce scroll distance to the chatbot, and make the overall mobile experience tighter.

### Welcome Experience

The landing page uses a reveal pattern to create intrigue and engagement:

**State 1: Frosted/Blurred overlay (initial load)**
- The FULL page content is loaded behind a frosted glass blur overlay
- Visitor can see shapes, colors, layout underneath but nothing is readable
- On top of the blur: Michael's headshot (clear, not blurred), and a "Get to know me" button
- Creates instant curiosity: "What is this? I've never landed on something like this before."
- Clean, minimal, premium. No other text needed on the overlay.

**State 2: The Reveal (after click)**
- When visitor clicks "Get to know me," the blur overlay fades away smoothly (CSS transition, ~1-1.5 seconds)
- The full page is revealed underneath
- As soon as the reveal completes, the chat widget shows a welcome message
- The welcome message text also appears as the first message in the chatbot
- The chatbot should be prominently visible and the focal point when the page reveals, not buried at the bottom

**Chatbot prominence:**
- The chatbot should be one of the first things visible after the reveal, not something you scroll to find
- Consider a layout where the chatbot is in a fixed sidebar or prominent above-the-fold section
- The voice playing plus the chatbot front and center creates immediate engagement: the visitor is IN a conversation from the first second
- The rest of the portfolio content (case studies, about section, contact) can scroll below or alongside

**CSS implementation notes:**
- Use `backdrop-filter: blur(20px)` for the frosted glass effect on the overlay
- Headshot should be `position: relative` or layered above the blur with `z-index`
- Fade transition: animate the overlay `opacity` from 1 to 0, then `display: none` or `pointer-events: none`
- The blur creates a sense of depth: there's clearly a full page behind the glass, which builds anticipation

### Calendar Integration

Add a "Book a Conversation" button prominently in the chat UI (header or sidebar). When clicked, it opens Michael's calendar booking link in a new tab or embedded modal.

- The chatbot should also be able to respond to intent like "I'd like to schedule a call" or "Can I book time with you?" by surfacing the calendar link.
- Calendar link will be stored in env var `CALENDAR_BOOKING_URL` (Calendly, Cal.com, or similar, TBD)
- If no calendar URL is configured, hide the button and have the chatbot say "Reach out to me on LinkedIn to schedule a conversation" as fallback

### Two-Way Voice (Speech-to-Text + TTS)

The chatbot should support full voice conversation, not just TTS output:

**Visitor speech input (Speech-to-Text):**
- Add a microphone button next to the text input field
- Use the browser's built-in Web Speech API (`webkitSpeechRecognition` / `SpeechRecognition`) for speech-to-text
- When the visitor clicks the mic button, it starts listening, transcribes their speech, and sends it as a chat message
- Show a visual indicator (pulsing mic icon) while actively listening
- Auto-stop after silence detection
- Fallback gracefully if the browser doesn't support Web Speech API (just hide the mic button)

**Combined voice flow:**
1. Visitor clicks mic and speaks their question
2. Speech is transcribed and sent to the chat
3. Response comes back as text AND audio (ElevenLabs TTS)
4. Audio auto-plays while text streams in
5. Visitor can respond again by clicking mic or typing

This creates a near-conversational experience: the visitor talks, Michael's AI voice answers back.

## Deployment

This will eventually be deployed to bwit-ingest (10.10.0.43) via `scp -o ProxyJump=pve2`, same as other apps. For now, just make it runnable locally.

### .env.example
```
QDRANT_HOST=10.10.0.60
QDRANT_PORT=6333
OLLAMA_HOST=10.10.0.15
OLLAMA_PORT=11434
ANTHROPIC_API_KEY=your-key-here
CALENDAR_BOOKING_URL=your-calendly-or-cal-link-here
ELEVENLABS_API_KEY=your-key-here
ELEVENLABS_VOICE_ID_MICHAEL=your-elevenlabs-voice-id
```

## Important Notes

1. **Michael did NOT serve in the military.** The NMCI project was a civilian contract. His grandfather and father served. Do not claim or imply military service.
2. **Never use em dashes** in any generated content. Use commas, colons, or rewrite.
3. **RIOS sensitivity:** Mark Motonaga is "Creative Director and Managing Partner" at RIOS. Never "CEO" or "Acting CEO."
4. **Wife's name is Carissa.** She works at RIOS and runs Cantique.
5. **Read the existing RIOS codebase** at `apps/rios/poc-rag/` before building. Reuse patterns, don't reinvent. Key files: `ingest.py`, `web_v3.py`, `chat_v3.html`.
6. **Read the knowledge base source docs** at `docs/founder-profile/founder-bio.md` and `docs/founder-profile/interview-responses.md`. These are the primary content.
7. **Read the LinkedIn articles** at `content/linkedin/*.md` to create the published-content.md summary file.

## Success Criteria

When done, I should be able to:
1. Run `python ingest.py` to populate the Qdrant collection
2. Run `python web.py` to start the chat server
3. Open `http://localhost:8000` in a browser
4. Ask questions like "What's Michael's background?", "Tell me about the Admiral Johnson story", "What has Michael built?", "How does Michael think about AI governance?" and get accurate, well-sourced answers from the knowledge base.
