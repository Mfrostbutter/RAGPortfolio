# OpenClaw is everywhere. That should concern you.

If you manage IT for any organization, there's a good chance OpenClaw is already running somewhere in your environment. Whether you approved it or not.

In less than four months, OpenClaw became the most starred repository on GitHub. Over 250,000 stars. Faster than React. Faster than anything in GitHub's history.

The appeal is obvious. An AI agent that actually acts. It reads and writes files, executes shell commands, controls browsers, sends emails, manages calendars. All autonomously, all in the background.

The problem? Most deployments have zero security oversight.

Researchers found over 30,000 instances exposed to the open internet in a two-week window. Nearly 15% already contained malicious instructions. Harvard and MIT red-teamed it in a paper titled "Agents of Chaos."

In Q1 2026 alone:

- A one-click RCE vulnerability (CVE-2026-25253, CVSS 8.8). Victim just had to visit a webpage.
- 820+ malicious skills on ClawHub disguised as legitimate tools, installing keyloggers and info-stealers.
- Plaintext API keys leaked through unsecured endpoints.
- Meta's AI alignment director tested it with email tasks. It tried to delete her entire inbox. She had to run to her computer to stop it.

CrowdStrike, Microsoft, and Cisco have all published security advisories. Colorado State banned it from university devices. China issued government-level restrictions.

Then there's the cost problem.

The software is free. Running it is not. Every action triggers API calls to external AI providers. Business workflows run $25 to $50/month. Heavy automation exceeds $200. The heartbeat system pings AI models constantly, even idle. Forgotten automations account for 10 to 30% of monthly spend.

If your business deployed this, ask now: Who set it up? What credentials does it have? Is it exposed to the internet? Is anyone monitoring spend?

If you don't know the answers, that's the problem.

I'm not saying the tech isn't impressive. It is. But if your team deployed this without isolation, credential scoping, and monitoring, you have an unmanaged AI agent with root-level access on your network.

That's not innovation. That's a liability.
