---
name: agent-ticketing-os
description: Install or initialize the complete Agent Ticketing OS, including both the ticketing system and optional agent operating mode. Use when the user says "$agent-ticketing-os", "install the whole ticketing system", "set up the full agent ticketing OS", "install both ticketing and operating mode", or wants the complete package instead of only ticketing or only operating guardrails.
---

# Agent Ticketing OS

Set up the complete Agent Ticketing OS: ticketing plus agent operating mode.

Use this when the user wants the whole system. If the user only wants local tickets, backlog, board, sprints, and sync, use `$agent-ticketing-init`. If the user already has ticketing and only wants stricter branch, commit, PR, QA, review, release, security, and handoff rules, use `$agent-operating-init`.

## Setup Options

Offer these choices:

- **Full OS**: ticketing plus operating mode.
- **Ticketing only**: tickets, backlog, board, sprints, sync.
- **Operating only**: branch, commit, PR, QA, review, release, security, and handoff guardrails on top of an existing ticketing workflow.

## Workflow

1. Ask whether the user wants Fast or Deep setup unless they already specified.
2. Initialize ticketing first:

```bash
python3 <package-root>/scripts/ticketctl.py init --root . --profile strict
```

Use `--interactive` for Deep setup.

3. Run `$agent-operating-init` for the operating layer.
4. Run:

```bash
python3 <package-root>/scripts/ticketctl.py doctor --root .
```

5. Report what was installed:
   - ticket files
   - operating docs
   - sprint/sync readiness
   - next recommended command

## Rules

- Do not overwrite mature existing repo instructions without permission.
- If `.tickets/config.json` already exists, do not reinitialize ticketing unless the user explicitly asks.
- If operating docs already exist, merge missing sections or report what would change.
- Keep the setup public-safe and generic. Do not bake private repo names into generated files.
