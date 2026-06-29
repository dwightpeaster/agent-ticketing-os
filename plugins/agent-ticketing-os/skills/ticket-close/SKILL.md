---
name: ticket-close
description: Close or resolve a repo-local ticket.
---

# Ticket Close

Delegate to the root `$agent-ticketing` workflow. Close with `scripts/ticketctl.py close --root . <ticket-id> --resolution "<summary>"`.

If the user did not provide a ticket id, infer it from the current context only when unambiguous. Otherwise ask for the id. Include validation evidence in the resolution when available.
