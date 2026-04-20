---
title: Technical Portfolio
origin: technical-portfolio
date: 2026-04-19
---

# Michael Frost, Technical Portfolio

A working inventory of the AI and infrastructure systems I have built and run in production. Stack, outcomes, and scale per bullet. Everything below is live and operating, not slideware.

---

## BWIT Knowledge Platform

The primary proof point. A production MCP-based knowledge platform that consolidates operations across a portfolio of MSPs under Brightworks IT. Built from zero to running in roughly one week, then hardened over months of daily use. I built this for internal use at Brightworks IT. It's not a product, it's not something I sell, it's proof that I build the things I talk about.

**Stack:**
- FastAPI MCP servers (six active endpoints, bearer-token auth) on a dedicated LXC
- Qdrant vector database, 30+ collections, roughly 75K vectors across client data, vendor documentation, and internal knowledge
- PostgreSQL 16 for ingest deduplication and structured records
- ConnectWise Manage API as the system-of-record (tickets, companies, agreements, configurations)
- n8n automation platform driving lifecycle workflows
- Claude and GPT-class LLMs routed per task, with OpenAI and Voyage embeddings
- Self-hosted on a four-node Proxmox cluster, zero public cloud dependency for core data

**Outcomes:**
- QBR preparation time dropped from multi-day to minutes
- Automated agreement review triggered on every offboarding request
- Cancellation workflow reads signed SOW and MSA documents, not just CW metadata, so nothing gets missed
- Full-text plus semantic search across every vendor doc and client record any technician can query
- Serves multiple Claude Code and Claude Desktop instances simultaneously

**Scale:** ~90K tickets classified with deBERTa NLI, 38 vendor platforms crawled via Crawl4AI, 50+ client companies, 17 employees interacting with the platform daily.

---

## AgeniusDesk

Productized version of the internal n8n command center. Beta launch 2026-05-06 with a small cohort of testers on frozen beta LXCs.

**Stack:**
- FastAPI backend with auto-discovered module system (manifest.json plugin pattern)
- Vanilla JS ES modules frontend, zero build step
- SQLite via aiosqlite, Fernet-encrypted config at rest
- WebSocket for real-time workflow status updates
- Docker compose deploy behind nginx, Cloudflare Tunnel, Cloudflare Access for auth
- GitHub tarball module installer so customers can pull in new modules without a redeploy

**Outcomes:**
- Single pane of glass for every n8n workflow a business runs (prod, ops, marketing, service desk)
- Recent Errors panel surfaces failures from both global error workflows in one view
- Modules UI lets operators install new capabilities without touching n8n or the host

**Scale:** Production at app.ageniusdesk.com, five frozen beta LXCs pinned for external testers, module system shipped as Phase 5.

---

## RIOS AI Copilot

Thesis work and workflow analysis for a global architecture and landscape design collective. Built as a retrieval-first copilot for internal teams.

**Stack:**
- FastAPI backend, Claude Sonnet for generation, OpenAI and Snowflake Arctic embeddings (migrated to Voyage + OpenAI)
- Qdrant collection seeded from Airtable project records, press coverage, meeting transcripts, OCR'd PDFs of project pages, LinkedIn leadership content, and reference facts
- Rich per-chunk metadata: disciplines, markets, materials, collaborators, RIOS people, awards, square footage, dollar figures
- Hybrid keyword plus vector search via Qdrant text indexes

**Outcomes (public-safe, concepts only):**
- Demonstrates a reusable pattern for studio-scale creative operations: ingest once, retrieve in context, generate in brand voice
- Content tier weighting so award submissions and project briefs outrank thin scraped press
- System prompt enforces brand voice and hard rules (no em dashes, plain text for TTS readout)

Specific client strategies and recommendations are not part of this portfolio and never leave the engagement.

---

## Self-hosted AI Infrastructure

The substrate under everything else. Built to run AI workloads at near-zero marginal cost.

**Stack:**
- Proxmox cluster across four nodes (pve1 through pve4), kernel 6.17+, e1000e NIC fix applied
- LXC fleet: Qdrant, PostgreSQL, Crawl4AI, MCP servers, Twenty CRM, Listmonk, Infisical, Wazuh SIEM, NetBird, Proxmox Backup Server
- n8n on a 4 vCPU / 12 GB VM running five instance roles (prod, dev, marketing, operations, service desk)
- McNasty GPU workstation (RTX 5060) for Ollama inference and ticket classification
- NetBird self-hosted for zero-trust access across the entire footprint
- Cloudflare Tunnel plus Access for every public surface, no exposed ports
- Pi-hole HA pair for internal DNS
- Infisical for machine-identity secret injection into containers

**Outcomes:**
- No AWS, no Azure, no GCP for core AI data planes
- Full encryption at rest and in transit, audited via Wazuh
- iDrive plus Proxmox Backup Server for off-site and local snapshots
- Fleet-wide NetBird ACLs replace per-host firewall management

**Scale:** 29 platforms in the dev knowledge base (~75K vectors), six active MCP servers, roughly 12 LXCs plus one VM running 24x7, weekly KB crawl plus ingest on a systemd timer.

---

## Content Automation Pipeline

n8n-driven content operations for Agenius 3D and related brands.

**Stack:**
- n8n workflows orchestrating social media generation, asset management, and scheduling
- Claude and GPT for draft generation with brand-specific system prompts
- Airtable as the editorial source of truth
- Image pipeline for product shots
- Weekly cadence automated end-to-end

**Outcomes:**
- Product-to-post time cut to minutes
- Consistent brand voice across channels
- Editorial workflow operated without a full-time content hire

---

## NMCI Deployment

The foundational enterprise reference. At NMCI (Patuxent Naval Air Station), I held several roles across the engagement: Staging Engineer, Deployment Engineer, and ultimately Deployment Lead with 15 direct reports. We deployed 26,000 workstations in one year. I also oversaw network operations for 16,000 users as Network Administrator. This was a government contract operating under national security standards. Uptime, security, and process discipline were not optional. It's where I learned what real scale looks like.

**What it taught:**
- How massive organizations actually run their technology at scale
- Scripting, networking, troubleshooting in an environment where every decision is audited
- Stakeholder management up to flag-officer level (the Admiral Johnson story: read the room, appeal to the right motivation, follow through with excellent service)
- The difference between theoretical architecture and what survives contact with real users
- Security-first mindset from day one, because the network was classified

Everything I've built since stands on this foundation.
