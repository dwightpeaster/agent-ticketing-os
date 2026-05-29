# Agent Ticketing OS

Agent Ticketing OS is a portable skill package for coding agents. It gives Claude Code, Codex, and other Agent Skills-compatible tools a shared way to plan work, create tickets, track implementation, run lightweight sprints, and keep an audit trail inside the repo.

The core idea is simple: agents should not freewheel through a codebase. They should create or select a ticket, capture the goal, record acceptance criteria, update status as work moves, and leave enough context for the next agent or human to continue.

## What It Does

Agent Ticketing OS can be used in three ways:

- **Full OS**: installs ticketing plus stricter agent workflow guardrails.
- **Ticketing only**: creates local tickets, backlog, board, sprints, and sync config.
- **Operating only**: adds branch, commit, PR, QA, review, release, security, and handoff rules on top of an existing ticket workflow.

The package includes a deterministic Python engine, [scripts/ticketctl.py](scripts/ticketctl.py), plus skill wrappers that let agents respond to natural language like:

```text
Create a ticket for the login redirect bug.
What should we work on next?
Start a sprint for the dashboard cleanup work.
Move T-0004 to review.
Close T-0004 with the tests we ran.
```

## Install

Codex plugin-style package:

```bash
git clone https://github.com/dwightpeaster/agent-ticketing-os.git ~/.agents/plugins/agent-ticketing-os
```

Claude Code skill package:

```bash
git clone https://github.com/dwightpeaster/agent-ticketing-os.git ~/.claude/skills/agent-ticketing-os
```

Codex plain skill fallback:

```bash
git clone https://github.com/dwightpeaster/agent-ticketing-os.git ~/.codex/skills/agent-ticketing-os
```

Restart the agent after installing.

## First Use

Use the whole system:

```text
$agent-ticketing-os
```

Use only the ticketing layer:

```text
$agent-ticketing-init
```

Use only the operating layer:

```text
$agent-operating-init
```

For a stricter split-board workflow:

```text
$agent-ticketing-init using the strict profile
```

## Skills Included

- `$agent-ticketing-os` - initialize the complete ticketing plus operating system.
- `$agent-ticketing-init` - set up repo-local ticketing.
- `$agent-ticketing-new` - create a ticket from natural language.
- `$agent-ticketing-next` - pick the next best ticket.
- `$agent-ticketing-board` - show or refresh board and backlog state.
- `$agent-ticketing-move` - move tickets between statuses.
- `$agent-ticketing-close` - close or won't-do tickets.
- `$agent-ticketing-sprint` - plan and close lightweight Markdown sprints.
- `$agent-ticketing-sync` - sync with external trackers when tools are available.
- `$agent-operating-init` - set up stricter agent operating mode.
- `$agent-operating-review` - review readiness for tickets, branches, PRs, and handoffs.
- `$agent-ticketing` - broad fallback skill for clients that load only the root skill.

Legacy short aliases are also included for now: `$new-ticket`, `$ticket-next`, `$ticket-board`, and `$ticket-close`.

## What Gets Created

Default ticketing setup creates:

```text
.tickets/
  config.json
  REGISTRY.json
  BACKLOG.md
  BOARD.md
  CHANGELOG.md
  DECISIONS.md
  tickets/
  templates/
  reports/current-sprint.md
```

The strict profile also creates human-facing planning files:

```text
tickets.md
docs/tickets/BACKLOG.md
docs/tickets/COMPLETED.md
docs/ROADMAP.md
docs/PRODUCT_DECISIONS.md
```

Agent Operating Mode can add repo workflow docs such as `AGENTS.md`, ticket standards, definition of done, branch workflow, commit workflow, review checklist, QA guide, and handoff templates.

## Direct CLI Use

You can run the engine directly from inside any repo:

```bash
python3 ~/.codex/skills/agent-ticketing-os/scripts/ticketctl.py init --root .
python3 ~/.codex/skills/agent-ticketing-os/scripts/ticketctl.py init --root . --profile strict
python3 ~/.codex/skills/agent-ticketing-os/scripts/ticketctl.py new --root . --type bug --priority P1 --area auth --title "Fix login redirect loop"
python3 ~/.codex/skills/agent-ticketing-os/scripts/ticketctl.py next --root .
python3 ~/.codex/skills/agent-ticketing-os/scripts/ticketctl.py move --root . T-0001 in_progress
python3 ~/.codex/skills/agent-ticketing-os/scripts/ticketctl.py close --root . T-0001 --resolution "Fixed and tested."
python3 ~/.codex/skills/agent-ticketing-os/scripts/ticketctl.py doctor --root .
```

## Design Goals

- Local-first: useful without a hosted service.
- Agent-friendly: natural language skills plus deterministic file operations.
- Auditable: tickets, decisions, sprints, tests, and handoffs live in git.
- Portable: works as a Codex plugin package or plain skill folder.
- Extensible: external tracker sync can be added through available tools or MCP connectors.
