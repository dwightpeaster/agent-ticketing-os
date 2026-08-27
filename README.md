# Agent Ticketing OS

Agent Ticketing OS is a local-first ticketing and workflow system for coding agents. It keeps project work in readable Markdown files alongside the code so agents can capture tasks, select ready work, track progress, record validation, and leave useful handoffs.

The default setup requires no hosted service and does not install a background agent.

## Install

### Codex

Add the marketplace:

```bash
codex plugin marketplace add dwightpeaster/agent-ticketing-os
```

Install the plugin:

```bash
codex plugin add agent-ticketing-os@agent-ticketing-os
```

Restart Codex after installation.

### Claude Code

Run these commands inside Claude Code:

```text
/plugin marketplace add dwightpeaster/agent-ticketing-os
/plugin install agent-ticketing-os@agent-ticketing-os
/reload-plugins
```

## Set Up A Repository

Open the repository in Codex or Claude Code and run the installer.

In Codex:

```text
$agent-ticketing-os
```

In Claude Code:

```text
/agent-ticketing-os:agent-ticketing-os
```

The installer creates the local ticket system and concise guidance for tickets, branches, commits, validation, review, and handoff. It can also safely upgrade an existing Agent Ticketing OS installation.

Running the installer again is safe. Customized workflow documents are preserved.

## Use

Ask the agent naturally for the work you want to manage:

```text
Create a ticket for the login redirect bug.
Show me the current ticket board.
What is ready to work on next?
Move T-0004 to review.
Record that the authentication tests passed for T-0004.
Close T-0004 with the final resolution.
```

Agent Ticketing OS stores canonical tickets under `.tickets/tickets/` and generates the board, backlog, registry, changelog, and sprint views from those tickets.

### Main Capabilities

- `$agent-ticketing-os` installs, upgrades, or repairs the system.
- `$agent-ticketing` manages tickets, dependencies, status, validation, and closure.
- `$agent-operating-review` checks whether work is ready to start, review, close, or hand off.
- `$agent-ticketing-sprint` manages optional goal-based sprints.
- `$agent-ticketing-tracker` configures optional guidance for GitHub Issues, Jira, Linear, or another external tracker.

### Guarded Workflow

The default workflow provides guidance without blocking ordinary work. To enforce ticket-readiness and completion requirements, ask the installer to use guarded policy:

```text
$agent-ticketing-os using guarded policy
```

### Extended Guidance

To add optional QA, release, security, writing, and repository-map guidance:

```text
$agent-ticketing-os using the extended operating kit
```

### External Trackers

External tracker support is optional. It stores connector policy and stable external record IDs for use during active agent sessions. It does not install automatic synchronization, polling, webhooks, or a background agent.

Ask the agent to configure the tracker and choose which system is the source of truth:

```text
Configure GitHub Issues as a hybrid external tracker.
Use Linear as the primary planning system for this repository.
```

## Update

Refresh the marketplace and reinstall the plugin:

```bash
codex plugin marketplace upgrade agent-ticketing-os
codex plugin add agent-ticketing-os@agent-ticketing-os
```

Then run `$agent-ticketing-os` inside each repository that should be upgraded.
