---
name: ticket-board
description: Show or refresh the repo-local ticket board and backlog. Use when the user says "$ticket-board", "show the board", "show backlog", "list tickets", "what is open", or asks for ticket status.
---

# Ticket Board

Delegate to the root `$agent-ticketing` workflow. Prefer `scripts/ticketctl.py sync --root .` followed by reading `.tickets/BOARD.md` or `.tickets/BACKLOG.md`.

Summarize active tickets by status and call out blocked or review items first.
