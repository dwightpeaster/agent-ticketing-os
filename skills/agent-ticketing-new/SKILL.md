---
name: agent-ticketing-new
description: Create a new Agent Ticketing OS ticket. Use when the user says "$agent-ticketing-new", "new ticket", "create a ticket", "file a bug", "add this to the backlog", "track this issue", or "we need a ticket for x".
---

# Agent Ticketing New

Create one focused repo-local ticket using the shared ticket engine.

If `.tickets/config.json` is missing, run or offer `$agent-ticketing-init` first.

## Workflow

1. Infer ticket fields from the user's request:
   - `type`: bug, feature, change, repo, research, design, or security.
   - `priority`: default `P2`.
   - `status`: `ready` for actionable work, `backlog` when the user says backlog, `inbox` for rough ideas.
   - `area`: infer from repo modules or use `repo`.
2. Ask at most one clarifying question only if the ticket would be misleading without it.
3. Run:

```bash
python3 <package-root>/scripts/ticketctl.py new --root . --type <type> --priority <priority> --area <area> --title "<title>"
```

Add `--context`, `--acceptance`, `--validation`, and `--labels` when known.

4. Report the ticket id, status, priority, and file path.
