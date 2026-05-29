# Strict Split-Board Profile

This profile defines an opinionated ticket-first workflow for agent-led repositories.

## Core Principles

- Every meaningful repo change connects to a ticket.
- `tickets.md` is the working board, not a permanent archive.
- `docs/tickets/BACKLOG.md` holds deferred `Backlog` tickets.
- `docs/tickets/COMPLETED.md` holds one-line `Complete` archive records.
- `docs/ROADMAP.md` owns delivery phases and release milestones.
- `docs/PRODUCT_DECISIONS.md` owns durable decisions and open product/architecture questions.
- A ticket body lives in exactly one place at a time.
- Completed ticket detail belongs in git history, not the live board.

## Lifecycle

Use only these statuses:

- `Backlog`
- `Ready`
- `In Progress`
- `Blocked`
- `Review`
- `Complete`

Location rules:

- `Backlog` -> `docs/tickets/BACKLOG.md`
- `Ready`, `In Progress`, `Blocked`, `Review` -> `tickets.md`
- `Complete` -> one-line archive in `docs/tickets/COMPLETED.md`

## New Idea Gate

New feature, design, or workflow ideas begin as `Backlog` discovery/planning tickets until scope is clear.

Before moving one to `Ready`, agents must ask at least 10 clarifying questions and record answers in the ticket. Waive this only when the user explicitly says the scope is already complete.

## Definition Of Done

Every ticket must satisfy:

- The change maps to one active ticket.
- Acceptance criteria are satisfied or gaps are documented.
- No unrelated behavior is included.
- Work happened on a ticket branch, not directly on the protected branch.
- Ticket file has updated status, implementation notes, changed files, and tests run.
- Completed tickets move from `tickets.md` to `docs/tickets/COMPLETED.md` as one-line archives.
- Relevant docs are updated when setup, commands, env vars, routes, workflows, or product decisions change.
- `git diff --check` passes.
