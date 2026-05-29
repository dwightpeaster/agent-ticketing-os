---
name: agent-ticketing-next
description: Select the next best Agent Ticketing OS ticket to work on. Use when the user says "$agent-ticketing-next", "what should we work on next", "pick the next ticket", "next backlog item", or asks what an agent should do next.
---

# Agent Ticketing Next

Choose the next ticket from the local ticket system.

If `.tickets/config.json` is missing, run or offer `$agent-ticketing-init` first.

Run:

```bash
python3 <package-root>/scripts/ticketctl.py next --root .
```

Report the selected ticket id, priority, type, area, title, and file path. If no ticket is ready, suggest triaging backlog or creating a new ticket.
