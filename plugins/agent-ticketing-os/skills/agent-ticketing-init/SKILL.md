---
name: agent-ticketing-init
description: Initialize a repository for Agent Ticketing OS ticketing. Use when the user says "$agent-ticketing-init", "set up ticketing", "initialize ticketing", "install the ticket system in this repo", "start a backlog for this repo", or wants the repo prepared for agent-readable tickets, backlog, board, decisions, and handoffs.
---

# Agent Ticketing Init

Set up the current repository for Agent Ticketing OS ticketing.

When the user wants the stricter split-board workflow, initialize with the strict profile:

```bash
python3 <package-root>/scripts/ticketctl.py init --root . --profile strict --interactive
```

## Workflow

1. Check whether `.tickets/config.json` exists.
2. If it exists, do not overwrite it unless the user explicitly asks to reinitialize or reset ticketing.
3. If it does not exist, run:

```bash
python3 <package-root>/scripts/ticketctl.py init --root . --interactive
```

Use non-interactive defaults when the user asks for a fast setup:

```bash
python3 <package-root>/scripts/ticketctl.py init --root .
```

4. After initialization, run:

```bash
python3 <package-root>/scripts/ticketctl.py doctor --root .
```

5. Report the created `.tickets/` files and the seed ticket id.

## Setup Questions

When interactive setup is appropriate, collect:

- Project name.
- Product mission.
- Ticket prefix.
- Default priority.
- Validation commands.
- Main repo areas.

Keep setup moving. If the user gives partial answers, use sensible defaults and record assumptions in `.tickets/config.json`.
