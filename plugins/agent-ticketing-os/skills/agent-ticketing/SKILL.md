---
name: agent-ticketing
description: Create, inspect, prioritize, edit, link, move, validate, close, reopen, and render repo-local Agent Ticketing OS tickets. Use for natural-language requests about bugs, features, tasks, backlog, board state, next work, blockers, dependencies, validation evidence, ticket handoffs, or completion.
---

# Agent Ticketing

Use the deterministic engine for ticket state and keep narrative content concise. If `.tickets/config.json` is missing, use `$agent-ticketing-os` first.

## Route The Intent

- Create: `new --title ...` with context, acceptance criteria, and validation when known.
- Start or resume: `context` for the compact session brief.
- Inspect: `context <id>` for a working packet; use `show` only when full history or implementation notes are needed.
- Select work: `context --next`; it returns the full packet for the highest-priority dependency-clear `ready` ticket.
- Update content: `edit`, `comment`, `link`, or `unlink`.
- Change state: `move`; use `close` for `done` or `wont_do`.
- Record evidence: `validate` before closure.
- Refresh derived views: `render`.
- Diagnose: `doctor` without mutating state.

Run commands as:

```bash
python3 <package-root>/scripts/ticketctl.py <command> --root .
```

Infer type, priority, area, and status conservatively. Rough ideas go to `inbox`; deferred work goes to `backlog`; only actionable work goes to `ready`. Ask one focused question only when the resulting ticket would otherwise be misleading.

Do not mutate tickets when the user asks only to inspect, explain, plan, or review. Never store secrets, credentials, private customer data, access tokens, or sensitive exploit detail in tickets.

Read `references/workflow.md` only for status gates or overrides. Read `references/schema.md` only when diagnosing storage or migration behavior.
