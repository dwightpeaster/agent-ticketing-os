---
name: agent-ticketing-os
description: Install, upgrade, or repair Agent Ticketing OS in a repository with one command. Use when the user asks to set up the full local ticketing and agent workflow system, initialize a repository for agent work, upgrade an existing Agent Ticketing OS installation, or verify that setup is healthy.
---

# Agent Ticketing OS

Install the complete default system without an interview unless the user asks to customize it:

```bash
python3 <package-root>/scripts/ticketctl.py install --root .
```

This command is idempotent. It initializes a new repository, migrates a supported older installation with a backup, or repairs generated views without overwriting customized workflow documents.

Use guarded policy only when the user explicitly wants enforced readiness and closure gates:

```bash
python3 <package-root>/scripts/ticketctl.py install --root . --profile guarded
```

Use the extended operating kit only when the user asks for QA, release, security, writing, and repository-map guidance:

```bash
python3 <package-root>/scripts/ticketctl.py install --root . --operating extended
```

After installation, run the non-mutating health check:

```bash
python3 <package-root>/scripts/ticketctl.py doctor --root .
python3 <package-root>/scripts/ticketctl.py context --root .
```

Report whether the repository was created, migrated, or already current; list preserved customized files and the next useful ticket action. Do not configure an external tracker unless the user asks.
