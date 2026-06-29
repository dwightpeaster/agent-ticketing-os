---
name: ticket-next
description: Pick the next repo-local ticket.
---

# Ticket Next

Delegate to the root `$agent-ticketing` workflow. Run `scripts/ticketctl.py next --root .` when `.tickets/config.json` exists. If ticketing is not initialized, offer to initialize it.

Report the selected ticket with its id, priority, type, area, title, and file path. If no ready ticket exists, say so and suggest creating or triaging tickets.
