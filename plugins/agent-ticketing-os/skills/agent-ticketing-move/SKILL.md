---
name: agent-ticketing-move
description: Move or update the status of an Agent Ticketing OS ticket. Use when the user says "$agent-ticketing-move", "start T-0001", "move T-0001 to review", "mark T-0001 blocked", or changes a ticket state.
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
