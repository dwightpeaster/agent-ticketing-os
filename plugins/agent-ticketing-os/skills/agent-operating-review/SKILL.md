---
name: agent-operating-review
description: Perform a non-mutating readiness, review, or handoff assessment for an Agent Ticketing OS repository. Use when the user asks whether work is ready to start, review, close, hand off, commit, or release, or asks for blockers and missing validation.
---

# Agent Operating Review

Run a non-mutating readiness review against the repo's operating rules.

Read `AGENTS.md`, then use the compact ticket packet and health check without modifying ticket state:

```bash
python3 <package-root>/scripts/ticketctl.py context --root .
python3 <package-root>/scripts/ticketctl.py doctor --root .
```

Use `context <id>` for the relevant ticket. Load only the workflow document for the phase being reviewed; use the full canonical ticket when history or implementation notes are material.

Check:

- active ticket exists and status is appropriate
- ticket body lives in one correct location
- branch is not protected for implementation work
- changed files match ticket scope
- acceptance criteria are satisfied or gaps are documented
- tests/validation are recorded
- product decisions/ADRs are updated when needed
- no secrets or generated dependency folders are included
- follow-up work is ticketed

Lead with actionable blockers, then risks and optional improvements. Distinguish evidence from inference. Do not render, move, edit, or close tickets unless the user asks for changes.
