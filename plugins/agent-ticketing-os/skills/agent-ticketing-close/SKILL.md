---
name: agent-ticketing-close
description: Close or resolve an Agent Ticketing OS ticket.
---

# Agent Ticketing Close

Close a ticket with a clear resolution.

If the user does not provide a ticket id, infer it from immediate context only when unambiguous. Otherwise ask for the id.

Run:

```bash
python3 <package-root>/scripts/ticketctl.py close --root . <ticket-id> --resolution "<summary>"
```

For intentionally rejected work:

```bash
python3 <package-root>/scripts/ticketctl.py close --root . <ticket-id> --wont-do --resolution "<summary>"
```

Include validation evidence in the resolution when available.
