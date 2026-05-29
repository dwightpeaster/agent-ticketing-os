# Agent Ticketing OS

A downloadable package of related skills for Claude Code, Codex, and other Agent Skills-compatible coding agents. It can install the full Agent Ticketing OS, ticketing only, or operating mode only.

The OS shares one deterministic engine: [scripts/ticketctl.py](scripts/ticketctl.py).

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

## Skills In The Package

- `$agent-ticketing-os` - install/init the complete ticketing plus operating system.
- `$agent-ticketing-init` - set up `.tickets/` in the current repo.
- `$agent-ticketing-new` - create a ticket from natural language.
- `$agent-ticketing-next` - pick the next best ticket.
- `$agent-ticketing-board` - show or refresh board/backlog state.
- `$agent-ticketing-move` - move tickets between statuses.
- `$agent-ticketing-close` - close or won't-do tickets.
- `$agent-ticketing-sprint` - plan and close lightweight Markdown sprints.
- `$agent-ticketing-sync` - sync with GitHub/Jira/Linear-style external trackers when tools are available.
- `$agent-ticketing` - broad fallback skill for the whole workflow.
- `$agent-operating-init` - optional full agent operating mode setup.
- `$agent-operating-review` - non-mutating readiness review for tickets, branches, PRs, and handoffs.

## Install Modes

- **Full OS**: `$agent-ticketing-os`
- **Ticketing only**: `$agent-ticketing-init`
- **Operating only**: `$agent-operating-init`

Full OS installs both pieces: local ticketing plus the stricter agent operating workflow.

Legacy short aliases are also included for now:

- `$new-ticket`
- `$ticket-next`
- `$ticket-board`
- `$ticket-close`

## First Use

Ask your agent:

```text
$agent-ticketing-os
```

For ticketing only:

```text
$agent-ticketing-init
```

For operating mode only:

```text
$agent-operating-init
```

For the stricter split-board ticketing workflow:

```text
$agent-ticketing-init using the strict profile
```

Natural language should also work once the skill is installed:

```text
Set up ticketing for this repo.
Create a ticket for the add customer form being blank.
File a P1 bug for the login redirect loop.
Add repo cleanup to the backlog.
What ticket should we work on next?
Move T-0004 to review.
Close T-0004; it was fixed by the route guard change.
```

Or run the setup script directly from inside any repo:

```bash
python3 ~/.codex/skills/agent-ticketing-os/scripts/ticketctl.py init --root . --interactive
```

## What It Creates

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

## Common Commands

```bash
python3 scripts/ticketctl.py init --root .
python3 scripts/ticketctl.py new --root . --type bug --priority P1 --area auth --title "Fix login redirect loop"
python3 scripts/ticketctl.py list --root . --status ready
python3 scripts/ticketctl.py next --root .
python3 scripts/ticketctl.py move --root . T-0001 in_progress
python3 scripts/ticketctl.py comment --root . T-0001 "Reproduced and found failing route guard."
python3 scripts/ticketctl.py close --root . T-0001 --resolution "Fixed route guard and added regression test."
python3 scripts/ticketctl.py doctor --root .
```

## Design Goals

- Local-first: no service required.
- Agent-friendly: deterministic commands, Markdown records, compact handoff sections.
- Public and portable: one skill folder works across Claude and Codex.
- Deep enough for real work: backlog, board, changelog, decisions, validation, and repo management.
