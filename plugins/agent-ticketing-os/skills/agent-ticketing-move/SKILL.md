---
name: agent-ticketing-move
description: Move an Agent Ticketing OS ticket.
---

# Agent Ticketing Move

Move a ticket to a new status with the shared ticket engine.

Valid statuses:

- `inbox`
- `backlog`
- `ready`
- `in_progress`
- `review`
- `blocked`
- `done`
- `wont_do`

For ordinary status changes, run:

```bash
python3 <package-root>/scripts/ticketctl.py move --root . <ticket-id> <status>
```

If the user gives a reason, also run:

```bash
python3 <package-root>/scripts/ticketctl.py comment --root . <ticket-id> "<reason>"
```

For closing work, prefer `$agent-ticketing-close`.
