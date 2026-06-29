---
name: new-ticket
description: Create a repo-local ticket.
---

# New Ticket

Delegate to the root `$agent-ticketing` workflow. If `.tickets/config.json` is missing, initialize ticketing first or ask whether to initialize it.

Create one focused ticket with `scripts/ticketctl.py new --root .`, inferring type, priority, area, and status from the user's request. Ask at most one clarifying question only when the ticket would be misleading without it.

After creating the ticket, report the ticket id, title, status, and file path.
