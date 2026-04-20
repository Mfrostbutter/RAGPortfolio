> Draft LinkedIn article, not yet published. Part 2 of a 2-part series on policy-as-infrastructure (policy at AI speed).

# Keeping AI Policy Alive at the Speed of AI

In the [previous article](#) I argued that AI policy has to be infrastructure. Versioned, declarative, enforceable, distributed, auditable. Code, not PDFs.

That argument is the easy half. The hard half is operational. Once you have decided your policy is going to live as code, what does the day-to-day actually look like? Who writes it? Who maintains it? How do you keep documentation alive when the systems it describes are changing faster than any human can document them?

The answer is the same shape as the answer to "how do you keep production code alive in a fast-moving codebase." You commit it to a system that supports change at speed, you wire automated agents into the maintenance loop, and you treat human review as the gate, not the bottleneck.

Two backbones make this work. Pick the one that fits your shape.

## The two viable backbones

**Git** is the formal answer. Branch protection, required reviews, signed commits, audit log baked in by design. CODEOWNERS files route changes to the right humans. Pre-commit hooks reject malformed policy. CI runs validation on every PR. If you are a regulated firm, a public company, or anyone whose auditor is going to ask "show me who approved this change on what date," git is the backbone. It was built for exactly this question and it has been answering it for twenty years.

**Obsidian vaults** are the lightweight answer. Markdown files, local-first, mobile-friendly, agent-friendly because every file is plain text with linkable headings. Sync via git or iCloud. The Obsidian-Git community plugin gives you automatic commit-and-sync inside the editor. Multi-vault separation lets you keep an "AI workspace" vault distinct from personal notes. One documented operator runs roughly 8,000 notes with 64,000 internal links over three years on this stack, single human, no infrastructure.

The right choice depends on who is going to touch the policy.

If the only people editing the policy are engineers and the audit trail has to satisfy a regulator, use git. If the people editing the policy are operators, founders, or hybrid technical-business owners who want to write a note on their phone during a meeting and have it merge into the source of truth automatically, use Obsidian backed by a git repo. You get most of the audit benefit and almost none of the friction.

I run both. Git is the canonical store for anything that gates a system at runtime: model classifications, tool allowlists, tier definitions, secret rotation policy. Obsidian is the substrate for the human-facing knowledge layer: SOPs, runbooks, incident postmortems, the prose that explains why the policy is what it is. The two repos cross-link. The agents can read both.

## The agent-maintained loop

Here is the pattern, in five steps.

**Discovery.** A scheduled job scans the actual state of the system. What models are deployed. What tools are registered on each MCP server. What collections exist in the vector DB. What secrets are referenced by which service. Whatever you have decided constitutes the surface area of your AI infrastructure.

**Diff.** The discovery output gets compared against the canonical state in the repo. If the live system has a tool the policy does not document, that is a diff. If the policy says a model is deprecated and a service is still calling it, that is a diff.

**PR.** The agent opens a pull request that proposes the documentation update. The PR title says exactly what changed. The body cites the source of the diff. The branch is named for the discovery run.

**Review.** A human reviews the PR. Most of the time the change is mechanical and the review is a thirty-second confirmation. Sometimes the diff surfaces something the human did not know was happening, and that triggers a real conversation about whether the system or the policy should change.

**Merge.** Approved PR merges. The policy now matches reality. The next discovery run starts from the new baseline.

The doc never goes stale because the loop closes itself. The agent does the boring 90% of the work. The human does the interesting 10% which is judgment.

This pattern is not exotic. Renovate and Dependabot have been doing the equivalent for software dependencies for years. The novelty is applying it to documentation and policy, which historically have been hand-edited because no one had a good way to automate them. Agents are that way.

## The working example: Git-Organized

I built [Git-Organized](https://github.com/Mfrostbutter/Git-Organized) as the open-source prototype of this pattern, applied to infrastructure documentation specifically. It is the substrate I run my own home lab and datacenter on, generalized so anyone can lift it.

The structure tells you the pattern.

**Templates/** holds the repo scaffold. README, CLAUDE.md, .gitignore, directory tree definition, change-management.md. When you bootstrap a new infrastructure repo, you copy the templates, fill the placeholders, and you have a documented baseline before you have written a single line of original prose.

**Discovery/** holds walkthroughs for the actual scans. Proxmox discovery walks you through `pct list`, `qm list`, resource summaries, network topology. Network discovery walks you through nmap and SNMP collection. Workstation discovery walks you through pulling specs from the local machine. Each walkthrough has an `output-templates/` directory that defines the format the inventory document should land in.

**Agents/** holds the prompts that drive the loop. setup-agent.md is the first-run agent that sits with you in Claude Desktop and walks you through scaffolding a new environment from scratch. discovery-agent.md is the ongoing agent that re-runs scans against an established environment. sync-agent.md compares state across multiple sites. audit-agent.md does the periodic compliance review.

**Scripts/** holds the automation that runs the scans without a human in the loop, for environments where you want the discovery to happen on a schedule.

**n8n/** holds the workflow definitions for scheduled discovery and drift alerting. This is where the loop becomes self-driving. n8n triggers the discovery on a cron schedule, the script runs, the output goes through the formatter, the agent opens a PR if the diff is non-zero, the human reviews, the merge happens. The repo stays current because the system maintaining it never sleeps.

The reason I built this in the open is that the pattern matters more than my specific implementation. Most operators do not need to invent it from scratch. They need a working template they can adapt.

The same structure works for AI policy specifically. Replace `Discovery/proxmox-discovery.md` with `Discovery/mcp-tool-registry-discovery.md`. Replace `Discovery/network-discovery.md` with `Discovery/model-routing-policy-discovery.md`. The skeleton is identical. Discover the live state, diff against the canonical doc, PR the delta, review, merge.

## Giving an agent commit rights without losing your mind

The objection I hear most often is "I am not letting an AI commit to my repo." Fair instinct. Wrong conclusion.

You are not giving the agent unconstrained access. You are giving it the same access pattern you would give a junior engineer on day one, which is "you can propose changes, you cannot ship them." The controls that make that safe for a human work for an agent too, with one tightening.

**Scoped tokens.** Short-lived, single-repo. The GitHub guidance is 60-minute tokens bound to one repo, period. Use the built-in `GITHUB_TOKEN` from Actions wherever you can; it is automatically scoped and rotates per workflow run. Reach for a PAT only when you need cross-repo access, and scope it ruthlessly when you do.

**Branch protection on main.** Required reviews, required status checks, no force pushes, no admin overrides. The agent gets to push branches and open PRs. The agent does not get to merge.

**Required PR review by a human.** Every PR. No exceptions for "trivial" doc changes. The five seconds it takes to confirm a one-line diff is the cost of the audit trail you are buying.

**Signed commits.** GPG or sigstore. Every agent commit signed with an identifiable agent identity, tied to a real human accountable for that agent. The principle from GitHub's agentic security guidance is "agents propose, never own." Every change is attributable to a real person, even when an agent did the keystrokes.

**Reference a work item.** Every agent PR cites an issue, a ticket, or a discovery run ID. No drive-by edits. If there is no work item, the PR template fails and the agent has to either open one or back off.

**Dry-run mode.** New agent prompts run in a sandbox repo first, against a copy of the real state, before they get pointed at production. This is the equivalent of staging for code. If your agent is opening PRs against your live policy repo on day one without ever having been exercised against a copy, that is the actual unsafe pattern, and it has nothing to do with whether the actor is human or AI.

I run all of this for the agents that maintain my own infrastructure docs. Setup took an afternoon. The blast radius is bounded by design. The agent has not yet shipped a bad merge because the agent has never shipped a merge at all. Humans ship merges. Agents ship pull requests. That distinction is the whole game.

## The drift-detection pattern, generalized

Once the loop exists for documentation, the same loop generalizes to anything you want to keep current.

**Model deprecation tracking.** Frontier providers retire models on a schedule. Your routing config references model names. A scheduled job pulls the current deprecation calendar from each provider, diffs against your config, opens a PR proposing the swap. Human reviews the proposed replacement, merges, deploys.

**Tool registry drift.** Your MCP servers register tools at startup based on config. A scheduled job compares the registered tools against the documented tool catalog in the repo. Any delta opens a PR. The catalog stays current automatically.

**Vendor doc freshness.** Your knowledge base ingests vendor documentation. A scheduled job re-crawls each vendor, diffs against the last crawl, surfaces meaningful content changes as a PR against your internal SOP that references that vendor. Your SOPs do not silently go out of date when a vendor changes a critical default.

**Policy expiration.** Every policy has a review date. A scheduled job opens a PR thirty days before the review date with the relevant context attached. The policy gets re-affirmed or updated. Nothing expires silently.

The common shape is "the system that does the work also reports on the work." That is what closes the loop. Without that, every documentation effort eventually loses to entropy.

## What this gets you

A few specific outcomes worth naming.

**Audit reconstruction in minutes, not weeks.** When a regulator or a client asks "what was your policy on this date and how was it enforced," `git log` answers the first half and `journalctl` answers the second. You stop dreading audits because the audit substrate is already there.

**Onboarding that scales.** A new engineer reads the repo and knows the actual state of the system, because the repo is the state of the system. They are not relying on tribal knowledge that lives in someone's head.

**Real velocity.** The reason policy slows organizations down is that nobody trusts the policy is current, so every decision becomes a meeting to re-confirm. When the policy is verifiably current because the agents that maintain it are running every night, the meetings go away. People act on the doc.

**A genuine asset that compounds.** The repo is worth more every quarter, not less. Every drift PR adds context. Every audit reaffirms or updates a policy. Every incident produces a postmortem that gets linked from the relevant SOP. After two years of this, you have the most accurate picture of your AI infrastructure of any organization in your peer group, by a wide margin. That is competitive infrastructure.

## Closing

Documentation moves at the speed of the system it describes, or it is fiction.

For most of the last decade, that meant infrastructure documentation was fiction at most companies. The systems moved faster than humans could write. AI agents change that constraint. They can do the writing at the same cadence as the systems do the changing.

The companies that figure this out in the next twelve months are going to operate from a baseline of accurate, current, queryable knowledge about their own infrastructure and their own AI policy. The companies that do not are going to spend the next twelve months in audit prep, retroactively reconstructing what they should have been documenting in real time.

If you have not started, the smallest version of this is a single git repo with a single markdown file describing your current AI policy, a single discovery script that scans your current state, and a single scheduled job that diffs them and opens a PR when they disagree. That is a Saturday afternoon of work. It is also the entire pattern, in miniature.

Build it small, run it for a month, and watch what surfaces. The first three drift PRs will tell you more about your AI infrastructure than the last three quarters of governance reviews did.

Policy at the speed of AI is not a slogan. It is an operational pattern. It is shipping. Use it.

---

*Michael Frostbutter is the founder of Agenius AI Labs and Director of Business Development at Brightworks IT. He builds production AI systems and AI-maintained documentation pipelines on self-hosted infrastructure. [Git-Organized](https://github.com/Mfrostbutter/Git-Organized) is his open-source prototype for AI-assisted infrastructure documentation. DM if you are wiring this pattern into your own org and want to compare notes.*

---

*Sources: github.blog AI agentic security principles, Open Policy Agent (openpolicyagent.org) and CNCF best practices, Vinzent03/obsidian-git, dev.to/padiazg Obsidian + GitHub guide, GitHub Copilot Coding Agent docs, NACD Director Essentials on AI Governance cadence.*
