# Agent Ticketing OS

Ticket-first workflows for coding agents.

Agent Ticketing OS is a portable workflow system for Codex, Claude Code, and other Agent Skills-compatible tools. It gives agents a repo-local way to create tickets, manage backlog, run lightweight sprints, track validation, and leave handoff notes in git.

The goal is simple: you should be able to open a repo, install the system, and then talk normally:

```text
Create a ticket for the login redirect bug.
What should we work on next?
Start a sprint for the dashboard cleanup work.
Move T-0004 to review.
Close T-0004 with the tests we ran.
```

The agent should handle the ticket mechanics.

## Install

<details open>
<summary><strong>Codex</strong></summary>

Add this repository as a Codex plugin marketplace:

```bash
codex plugin marketplace add dwightpeaster/agent-ticketing-os
```

Install the plugin:

```bash
codex plugin add agent-ticketing-os@agent-ticketing-os
```

Restart Codex after installing.

By default, Codex installs plugins into your Codex home, so the plugin is available across Codex workspaces. To test or use it for only one workspace, install it with a workspace-specific `CODEX_HOME`:

```bash
mkdir -p .codex-agent-ticketing
CODEX_HOME="$PWD/.codex-agent-ticketing" codex plugin marketplace add dwightpeaster/agent-ticketing-os
CODEX_HOME="$PWD/.codex-agent-ticketing" codex plugin add agent-ticketing-os@agent-ticketing-os
CODEX_HOME="$PWD/.codex-agent-ticketing" codex -C .
```

That keeps the plugin install isolated to that local Codex home. The generated ticketing files are always written only to the repo where you run the setup skill.

If Codex says the plugin was not found, refresh the marketplace first:

```bash
codex plugin marketplace add dwightpeaster/agent-ticketing-os
codex plugin list
codex plugin add agent-ticketing-os@agent-ticketing-os
```

</details>

<details>
<summary><strong>Claude Code</strong></summary>

Add this repository as a Claude Code plugin marketplace from inside Claude Code:

```text
/plugin marketplace add dwightpeaster/agent-ticketing-os
```

Install the plugin:

```text
/plugin install agent-ticketing-os@agent-ticketing-os
```

Reload plugins:

```text
/reload-plugins
```

These are Claude Code slash commands. Run them inside Claude Code, not in your shell.

Claude Code supports install scopes. If you want this plugin only for the current repository, open `/plugin`, install from the Discover tab, and choose **Local scope**. Local scope is private to you in this repo. Project scope shares it with collaborators through `.claude/settings.json`; user scope makes it available across your projects.

</details>

## First Use

<details open>
<summary><strong>Codex</strong></summary>

Install the full system:

```text
$agent-ticketing-os
```

Ticketing only:

```text
$agent-ticketing-init
```

Operating rules only:

```text
$agent-operating-init
```

</details>

<details>
<summary><strong>Claude Code</strong></summary>

Install the full system:

```text
/agent-ticketing-os:agent-ticketing-os
```

Ticketing only:

```text
/agent-ticketing-os:agent-ticketing-init
```

Operating rules only:

```text
/agent-ticketing-os:agent-operating-init
```

Claude Code uses `/agent-ticketing-os:skill-name` for direct plugin skill calls. The `@` symbol is for file references.

</details>

## How It Works

Agent Ticketing OS gives agents a repeatable loop:

1. Capture or select a ticket.
2. Clarify the goal and acceptance criteria.
3. Plan the work.
4. Track status through the board or sprint.
5. Record validation, decisions, and handoff notes.

The smaller skills, such as ticket creation, ticket movement, sprint planning, and closing tickets, are routing hooks for the agent. You should not need to call them most of the time. They exist so Codex and Claude can reliably map natural language like "move this to review" or "close the ticket" to the right deterministic engine command.

## Setup Modes

- **Full OS**: ticketing plus stricter agent workflow guardrails.
- **Ticketing only**: local tickets, backlog, board, sprints, and sync config.
- **Operating only**: branch, commit, PR, QA, review, release, security, and handoff rules on top of an existing ticket workflow.

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
  sprints/
  sync/
  reports/current-sprint.md
```

The strict profile also creates:

```text
tickets.md
docs/tickets/BACKLOG.md
docs/tickets/COMPLETED.md
docs/ROADMAP.md
docs/PRODUCT_DECISIONS.md
```

Agent Operating Mode can add repo workflow docs such as `AGENTS.md`, ticket standards, definition of done, branch workflow, commit workflow, review checklist, QA guide, release runbook, security protocol, and handoff templates.

External tracker setup creates provider hook files such as `.tickets/sync/github.json` and `.tickets/sync/github-mcp.md` so agents have a clear contract for GitHub, Jira, Linear, or custom MCP-backed sync.

## Design Goals

- Local-first: useful without a hosted service.
- Automatic: users talk naturally; agents handle ticket operations.
- Auditable: tickets, decisions, sprints, tests, and handoffs live in git.
- Portable: installable in both Codex and Claude Code.
- Extensible: external tracker sync can be added through available tools or MCP connectors.
