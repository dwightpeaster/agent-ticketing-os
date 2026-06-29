---
name: agent-ticketing
description: Repo-local agent tickets, backlog, board, sync, and handoff workflow.
---

# Agent Ticketing

Use this broad fallback skill to create and maintain a fast, local-first ticketing system inside the current repository. The system is optimized for AI coding agents: every ticket is Markdown for human review, every state transition is scriptable, and every work item carries enough context for another agent to pick it up later.

## Invocation Model

This repository is a package of related skills. Users should be able to speak naturally most of the time; the smaller skills exist as routing hooks so the host agent can reliably choose the right workflow.

In clients that support multi-skill packages, direct calls are available when useful:

- `$agent-ticketing-os` for the complete ticketing plus operating system setup.
- `$agent-ticketing-init` for setup.
- `$agent-ticketing-new` for ticket creation.
- `$agent-ticketing-next` for next-work selection.
- `$agent-ticketing-board` for board/backlog status.
- `$agent-ticketing-move` for status changes.
- `$agent-ticketing-close` for closing work.
- `$agent-ticketing-sprint` for lightweight sprint planning.
- `$agent-ticketing-sync` for optional external tracker sync.
- `$agent-operating-init` for the optional full agent operating mode.
- `$agent-operating-review` for non-mutating readiness checks.

Linear is optional and configured after normal setup. If the user asks to connect Agent Ticketing OS to Linear or switch to Linear-primary operation, use `$linear-setup`.

In Claude Code, plugin skills are invoked as namespaced slash commands. For example:

- `/agent-ticketing-os:agent-ticketing-os`
- `/agent-ticketing-os:agent-ticketing-init`
- `/agent-ticketing-os:agent-ticketing-new`
- `/agent-ticketing-os:agent-operating-init`

Do not use `@` to invoke these skills in Claude Code. `@` is for file references.

In clients that load only the root skill, `$agent-ticketing` handles all of those intents. Natural language should also trigger ticketing when the request is clearly about tickets, issues, backlog, bugs, repo tasks, triage, board state, or handoff tracking.

Prefer automatic routing over asking the user to invoke low-level skills. For example, if the user says "move T-0004 to review", use the status-change workflow directly; do not ask them to run `$agent-ticketing-move`.

## Install Modes

Support three setup paths:

- **Full OS**: `$agent-ticketing-os` initializes ticketing and the operating layer.
- **Ticketing only**: `$agent-ticketing-init` initializes tickets, backlog, board, sprints, and sync config.
- **Operating only**: `$agent-operating-init` adds branch, commit, PR, QA, review, release, security, and handoff guardrails on top of an existing ticketing workflow.

Linear setup is a post-install reconfiguration step. Agent Ticketing OS remains repo-primary until `$linear-setup` is run.

## Intent Routing

Map common user phrasing to these actions:

- "create a ticket for x", "new ticket x", "$new-ticket x" -> create a ticket with `new`.
- "bug for x", "track this bug", "file a bug" -> create a `bug` ticket.
- "add x to the backlog" -> create a ticket in `backlog` unless it is ready to start.
- "what should we work on next" -> run `next`.
- "show tickets", "show backlog", "what is open" -> run `list` or read `BACKLOG.md`.
- "start T-0001" -> move the ticket to `in_progress`.
- "move T-0001 to review" -> move the ticket to `review`.
- "T-0001 is blocked because x" -> move to `blocked` and add an activity comment.
- "close T-0001", "mark it done" -> close with a resolution summary.
- "sync tickets", "rebuild the board" -> run `sync`.
- "check ticket health" -> run `doctor`.

When creating a ticket from casual language, infer `type`, `priority`, `area`, and `status` conservatively. Ask at most one clarifying question only if the ticket would be misleading without it. Otherwise create the ticket and note any assumptions in the ticket context.

## Core Workflow

1. Check for `.tickets/config.json`.
   - If missing, initialize the system with `python3 <skill>/scripts/ticketctl.py init --root . --interactive`.
   - If the user wants defaults or this is non-interactive, use `python3 <skill>/scripts/ticketctl.py init --root .`.
2. Before meaningful repo work, create or select a ticket.
   - New work: `python3 <skill>/scripts/ticketctl.py new --root . --type feature --priority P2 --area app --title "Short title"`.
   - Existing work: `python3 <skill>/scripts/ticketctl.py next --root .` or `python3 <skill>/scripts/ticketctl.py list --root . --status ready`.
3. Move work as it changes:
   - `move <id> in_progress`
   - `comment <id> "What changed, with files/tests"`
   - `close <id> --resolution "Done, tested with ..."`
4. Regenerate dashboard files after edits:
   - `python3 <skill>/scripts/ticketctl.py sync --root .`
5. Validate before handoff:
   - `python3 <skill>/scripts/ticketctl.py doctor --root .`

If the user asks only to think or plan, do not mutate files unless they ask to build or initialize the system.

## What Gets Created

The initialized repo receives:

- `.tickets/config.json` - project settings and workflow policy.
- `.tickets/REGISTRY.json` - machine-readable ticket index.
- `.tickets/BACKLOG.md` - prioritized backlog grouped by status.
- `.tickets/BOARD.md` - current working board.
- `.tickets/CHANGELOG.md` - durable work history.
- `.tickets/DECISIONS.md` - lightweight decision log.
- `.tickets/tickets/T-0001-*.md` - ticket files.
- `.tickets/templates/*.md` - examples for humans and agents.
- `.tickets/reports/current-sprint.md` - active work summary.

## Ticket Types

- `feature` - new user-facing behavior.
- `bug` - broken behavior, regressions, errors, data loss, UI defects.
- `change` - intentional modification to existing behavior.
- `repo` - repo hygiene, build, CI, docs, dependencies, architecture.
- `research` - investigation where the output may be a decision or future tickets.
- `design` - UX/UI/design-system work.
- `security` - auth, secrets, permissions, injection, dependency, or data exposure risks.

## Status Model

Use these statuses exactly unless the project config says otherwise:

- `inbox` - captured, not yet clarified.
- `backlog` - valid but not ready.
- `ready` - clear enough for an agent to start.
- `in_progress` - actively being worked.
- `review` - implementation is ready for human or automated review.
- `blocked` - cannot proceed without an external decision or dependency.
- `done` - completed and validated.
- `wont_do` - intentionally closed without implementation.

## Priority Model

- `P0` - production outage, security exposure, data loss, or unusable core workflow.
- `P1` - urgent user-impacting bug or high-value work needed soon.
- `P2` - normal planned feature, fix, or repo improvement.
- `P3` - useful polish, cleanup, or non-urgent improvement.
- `P4` - idea parking lot.

## Agent Rules

- Prefer one ticket per coherent outcome, not one ticket per file.
- A ticket must include context, acceptance criteria, and validation before it is `ready`.
- A ticket in `done` must include resolution notes and tests or a clear reason tests were not run.
- Keep ticket updates factual and compact. Do not paste long command output.
- Do not let the ticket system replace the user's direct request. If the user asks for a fix, fix it and keep the ticket trail current.
- If work discovers extra problems, create linked follow-up tickets instead of expanding scope silently.
- Never store secrets, credentials, private customer data, or sensitive tokens in ticket files.

## References

Load these only when needed:

- `references/workflow.md` - detailed operating model, onboarding questions, sprint rituals, and agent handoff rules.
- `references/intents.md` - natural-language command mapping and companion skill behavior.
- `references/product-decisions.md` - current product decisions for setup modes, audit trail, sprints, sync, and public-tool posture.
- `references/sprints-and-sync.md` - sprint model, external platform sync model, source-of-truth options, and MCP strategy.
- `references/agent-operating-mode.md` - optional stricter agent operating mode, package strategy, setup outputs, and principles.
- `references/schema.md` - ticket frontmatter fields, status rules, and registry format.
- `references/strict-profile.md` - strict split-board profile with ticket standards, definition of done, working board, and workflow plan.
- `references/agent-operating-expansion-ideas.md` - additional skill and profile ideas for the broader agent operating system.
- `references/publication.md` - how to publish and install this skill from GitHub for Claude and Codex.
