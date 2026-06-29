---
name: agent-ticketing-next
description: Pick the next Agent Ticketing OS ticket.
---

# Agent Ticketing Next

Choose the next ticket from the local ticket system.

If `.tickets/config.json` is missing, run or offer `$agent-ticketing-init` first.

Run:

```bash
python3 <package-root>/scripts/ticketctl.py next --root .
```

Report the selected ticket id, priority, type, area, title, and file path. If no ticket is ready, suggest triaging backlog or creating a new ticket.
