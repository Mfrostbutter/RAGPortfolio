> Draft LinkedIn article, not yet published. Part 1 of a 2-part series on policy-as-infrastructure.

# AI Policy Has to Be Infrastructure

AI ships weekly. Policy moves quarterly. Shadow AI lives in the gap.

That's the entire problem in one sentence. Every other governance failure I've watched at the mid-market level is a downstream effect of that cadence mismatch. The model providers push a new capability on Tuesday, your employees adopt it by Friday, and your governance committee reviews it next quarter. By then it has touched payroll, contracts, client data, and source code, and nobody on the policy side has any idea.

I run AI operations across a portfolio of 7 MSPs and build production AI systems on self-hosted infrastructure. I see this play out in every environment I touch. The companies that have a working AI policy are not the ones with the thickest binder. They are the ones whose policy operates at the same cadence as the systems it governs.

That requires a different format for the policy itself.

## The failure mode of conventional policy

Walk into a typical mid-market company today and ask to see their AI policy. You will get one of three things. A PDF in a SharePoint folder, last updated nine months ago. A wiki page that references tools the company stopped using two years ago. Or, most often, an email from legal saying "we're working on it."

None of those are policy. They are policy-shaped objects. Here is the test.

Can an AI agent query the policy at runtime and refuse a non-compliant action? No. Does the policy version-bump when a new model gets approved? No. Is there a diff log of what changed and who approved it? No. Can you run a compliance check across the entire org against the current policy, automated, in under a minute? No.

If the answer to all four is no, what you have is documentation. Documentation does not enforce anything. Documentation does not survive contact with employees who are trying to get work done before lunch.

EY's 2026 Technology Pulse Poll surveyed 500 US technology executives. 69% of organizations report having AI risk and compliance policies. Only 38% maintain an actual inventory of the AI applications in use. The policy exists. The reality the policy is supposed to govern is invisible to the people who wrote the policy. That is the gap shadow AI lives in.

73% of organizations have detected unauthorized AI tool usage on their networks. Only 28% have implemented any monitoring or blocking. The detection happened by accident. The enforcement does not exist.

## The thesis, stated plainly

**Policy must be code. Versioned, declarative, enforceable, distributed, auditable.**

That is not a metaphor. I mean it literally. The same way infrastructure-as-code replaced ClickOps for cloud provisioning, policy-as-code has to replace PDF-as-policy for AI governance. Anything less than that cannot keep pace with the systems it is supposed to govern.

The five properties that matter:

**Versioned.** Every change has an author, a timestamp, a diff, and a rollback path. You can answer the question "what was our policy on June 14?" in three seconds, not three weeks.

**Declarative.** The policy says what is true, not what someone hopes is true. A model is approved or not approved. A data class is allowed at a tier or not. There is no ambiguous prose for an employee to interpret at 4:55pm on a Friday.

**Enforceable.** The runtime systems read the policy and act on it. An MCP server checks the tier of the requesting user against the tier of the requested tool before responding. An agent refuses to call a frontier model with a payload tagged PHI. The policy is not advice. It is a control.

**Distributed.** The policy lives where the systems live. In the repo, in the secret manager, in the agent's tool registry. Not in a binder on someone's desk and not in a SharePoint folder three departments away.

**Auditable.** Every decision the system made, against which version of the policy, with what input, is logged. When a regulator or a client asks "show me how this answer was produced," you can produce the answer in minutes.

That is what policy-as-infrastructure looks like. The PDF stays. It is the human-readable rendering of the source of truth. But the source of truth is the code.

## What it looks like in production

I am going to use my own stack as the proof, because I built it this way deliberately and I can show you every layer.

**Model routing is policy enforced at the request layer.** Sensitive data (anything tagged HIPAA, CMMC, MNPI, contract-restricted) routes to a self-hosted model on my own GPU. Non-sensitive operational queries route to a frontier API. That decision is not made by the employee at the keyboard. It is made by the routing layer, against a classification policy that is versioned in git. If someone tries to send a regulated payload to a public API, the request fails. The policy is not advice. It is a wall.

**Tool allowlists are tier-gated at the MCP layer.** I run six MCP servers. Each one registers a different set of tools depending on the tier of the bearer token presented. A technician token gets read-only ConnectWise data. A leadership token gets the same plus the financial tools. The same Python file, two different tool registries, decided at startup based on a single environment variable. When the policy changes (say, a new role gets read access to a new collection), the change is a one-line config bump in the repo, deploy script runs, the MCP server picks up the new policy on restart. No SharePoint update required. The policy and the enforcement are the same artifact.

**Secrets governance lives in Infisical.** No `.env` files committed to git, ever. Machine identities pull secrets at container start, scoped per service. Rotating a key is a single action in Infisical and every consuming service picks it up. The "policy" that says "secrets do not live in repos" is enforced by the fact that they literally cannot, because the only place they exist is the secret manager.

**Audit logging on every tool call.** Every MCP tool invocation writes to journald with the bearer token identity, the tool name, the arguments, and the result. When I want to know what an agent did last Tuesday, I run one command. There is no "let me check with the team and get back to you next week." The audit is automatic.

**Evaluation gates before any agent reaches production.** New tools, new prompts, and new models go to a dev MCP first. They get exercised against a fixed eval set. They do not promote to prod until the evals pass. This is the same pattern engineering orgs have used for code for twenty years, applied to AI behavior.

None of this is exotic. None of it requires a six-figure GRC platform. The whole stack runs on a four-node Proxmox cluster on hardware I own. The reason it works is that policy is not a separate artifact from the system. It is part of the system.

## "This sounds like bureaucracy"

It is the opposite of bureaucracy. It is the only way to move fast safely.

Bureaucracy is the state where every new tool requires a six-week approval cycle, three meetings, and a memo. Bureaucracy is what happens when policy is human-readable prose and every edge case has to be re-litigated by a committee that meets monthly.

Policy-as-infrastructure is the opposite. The decisions about what is safe, what data goes where, and what tools are approved have already been made and encoded. New tools that fit inside the existing classification slot in immediately. Edge cases trigger an explicit policy update, which is a PR, which gets reviewed, which merges, which deploys. The whole loop is hours, not weeks.

The companies that are scaring everyone with their AI velocity right now are not skipping governance. They are running governance at the same cadence as their deployments. Anthropic publishes a new version of its Responsible Scaling Policy and it is dated, versioned, and live at a public URL within hours. The policy is part of the product surface. That is what infrastructure-grade governance looks like.

The contrast with most enterprises is brutal. Anthropic's RSP has a version number. Yours probably does not.

## The regulatory clock is real

This is not optional much longer.

The EU AI Act enforcement for high-risk systems lands August 2, 2026. Conformity assessments, technical documentation, CE marking, EU database registration. Three and a half months from today. ISO/IEC 42001, the world's first AI management system standard, is becoming the de facto operating system for AI compliance the way ISO 27001 became the standard for information security. NIST AI 600-1, the Generative AI Profile, defines twelve risk categories that map directly to the kind of controls your AI policy needs to enforce.

Every one of those frameworks expects you to demonstrate your controls, not describe them. "We have a policy" is not a control. "Our routing layer rejects regulated data on public APIs and here is the audit log" is a control.

The shadow AI premium on a breach is $670,000 above a standard breach (IBM). The orgs with high shadow-AI density are running average breach costs of $4.63 million. That number is the price of running quarterly governance against a weekly-deployment problem.

## What to do this quarter

If you are an executive reading this and you do not have policy-as-infrastructure today, here is the order of operations.

**One**, get an inventory. You cannot govern what you cannot see. The 38% of organizations who have an AI inventory are the ones positioned to do anything else on this list. The rest are pretending.

**Two**, classify your data. Public, internal, sensitive, regulated. Four buckets minimum. Until that classification exists, no routing logic can be enforced because there is nothing to route against.

**Three**, build a routing layer. It does not have to be sophisticated on day one. A reverse proxy with header-based rules in front of your AI calls is enough to start. The point is that the policy lives in the layer, not in employee judgment.

**Four**, version your policy in git. Move the PDF to a markdown file in a repo. Add a CODEOWNERS entry. Require PR review for changes. The act of putting it under version control will surface every ambiguity that has been hiding inside the prose for the last two years.

**Five**, log everything. Every model call, every tool invocation, every agent action. Cheap, structured, queryable. You cannot pass an audit you cannot reconstruct.

The firms that win the next two years on AI are the ones whose policy operates at the same cadence as their models. Everyone else is going to spend the next two years explaining to regulators, clients, and boards why the policy in the binder did not match what the systems were actually doing.

Policy is infrastructure now. Build it that way.

---

*Part 2 of this series walks the operational pattern: how to actually run policy-as-infrastructure with git, Obsidian, and AI agents that maintain the documentation themselves. Coming next.*

*Michael Frostbutter is the founder of Agenius AI Labs and Director of Business Development at Brightworks IT. He builds production AI systems on self-hosted infrastructure for SMBs and enterprises, including RAG knowledge bases, MCP servers, and tier-routed agent platforms at near-zero cloud cost.*

---

*Sources: EY 2026 Technology Pulse Poll, IBM 2025 Cost of a Data Breach Report, NIST AI Risk Management Framework (AI RMF 1.0 + 600-1), EU AI Act implementation timeline (artificialintelligenceact.eu), ISO/IEC 42001:2023, Anthropic Responsible Scaling Policy v3.0, NACD Director Essentials on AI Governance.*
