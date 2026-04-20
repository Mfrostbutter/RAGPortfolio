---
title: Published Content Summary
origin: linkedin-article
date: 2026-04-19
---

# Published Content Summary

One-paragraph theses for each of Michael's published LinkedIn articles. Quick reference for the assistant when a recruiter or hiring manager asks what he writes about.

## Shadow AI Governance (Your Employees Are Already Feeding Your Company's Data to AI)

Employees are using AI at work right now, mostly through personal accounts with zero IT oversight. Cyberhaven's 2026 data shows sensitive information goes into AI tools roughly once every three days per employee, 80%+ of workers use unapproved AI tools, and 32% of enterprise ChatGPT usage happens on personal accounts. The shadow AI problem is not theoretical, it is measurable, it is concentrated in ChatGPT, and it is bleeding IP, client data, financials, and strategy documents out of organizations faster than governance can catch up. The argument is that leadership has to stop treating this as a policy problem and start treating it as an architecture problem: approved tools, data classification, routing rules, and actual visibility.

## The AI Data Readiness Gap (56% of CEOs Got Nothing From Their AI Spend)

A follow-up to Michael's earlier warning that AI is only as powerful as the data it can access. The 2026 scorecard is in: global AI spending hit $301B, 72% of enterprises have at least one AI workload in production, yet 56% of CEOs report getting nothing back and 95% of generative AI pilots fail to move past experiment. The gap is not the model, it is data readiness. Companies that redesigned work processes around clean, structured, accessible data are pulling away. Agentic AI in 2026 made the gap worse for the unprepared and dramatically better for the ready. The thesis: data readiness is now a P&L problem, not an IT problem.

## AI Model Routing Strategy (The Architecture Decisions Behind AI That Actually Scales)

Model selection is an architecture decision, not a procurement decision. Organizations that scale AI made a deliberate routing decision early: classify data by sensitivity and send it to the right model on the right infrastructure, not the most convenient one. Toggling off chat history in a consumer AI tool is not a HIPAA BAA. The enterprise tier is not a CMMC-compliant handling procedure for CUI. Auditors evaluate data handling architecture, not vendor tier selections. The argument is for a routing layer that segments public-safe data to hosted APIs, sensitive data to private or self-hosted inference, and governs the whole stack with contracts and controls that match the regulatory posture.

## OpenClaw Security Post (OpenClaw is everywhere. That should concern you.)

OpenClaw became the most starred GitHub repo in history in under four months, and in the rush to adopt it nearly every deployment shipped without security oversight. Researchers found 30,000+ instances exposed to the open internet in a two-week window, 15% already carrying malicious instructions, 820+ malicious skills on ClawHub installing keyloggers and info-stealers, plus a one-click RCE (CVE-2026-25253, CVSS 8.8). Even Meta's AI alignment director had it try to delete her entire inbox during a controlled test. CrowdStrike, Microsoft, Cisco, Colorado State, and the Chinese government have all issued advisories or bans. Runtime cost is the second problem: free software, $25 to $200+/month in API calls per business workflow, with forgotten automations chewing 10 to 30% of monthly spend. The message to IT leaders: if you don't know who deployed it, what credentials it has, and whether it's monitored, you have an unmanaged agent with root-level access on your network.
