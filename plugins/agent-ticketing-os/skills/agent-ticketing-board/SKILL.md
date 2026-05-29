---
name: agent-ticketing-board
description: Show, summarize, or refresh the Agent Ticketing OS board and backlog. Use when the user says "$agent-ticketing-board", "show ticket board", "show backlog", "list open tickets", "what tickets are active", or asks for ticket status.
---

# Agent Ticketing Board

Refresh and summarize the repo-local board.

If `.tickets/config.json` is missing, run or offer `$agent-ticketing-init` first.

Run:

```bash
python3 <package-root>/scripts/ticketctl.py sync --root .
```

Then read `.tickets/BOARD.md` for active work or `.tickets/BACKLOG.md` for the full backlog. Summarize blocked and review tickets first, then in-progress and ready tickets.
