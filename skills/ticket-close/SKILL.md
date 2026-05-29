---
name: ticket-close
description: Close or mark done a repo-local ticket using the agent-ticketing system. Use when the user says "$ticket-close", "close ticket", "mark this done", "resolve T-0001", or says a ticket is won't-do.
---

# Ticket Close

Delegate to the root `$agent-ticketing` workflow. Close with `scripts/ticketctl.py close --root . <ticket-id> --resolution "<summary>"`.

If the user did not provide a ticket id, infer it from the current context only when unambiguous. Otherwise ask for the id. Include validation evidence in the resolution when available.
