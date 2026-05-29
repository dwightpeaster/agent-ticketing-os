# Product Decisions

## Product Name

The package name is **Agent Ticketing OS**.

Users can install the complete OS or use one side:

- Full OS: ticketing plus operating mode.
- Ticketing only: local tickets, backlog, board, sprints, and sync.
- Operating only: branch, commit, PR, QA, review, release, security, and handoff guardrails on top of an existing ticketing workflow.

These are current product decisions for Agent Ticketing OS.

## Audience

Build this as a polished public tool. The default package should be useful to any repo, but the suite should be opinionated enough that agents are strongly guided into ticket-first work, concrete acceptance criteria, validation notes, and completion records.

Users can fork and relax the workflow, but the published package should model the stricter operating system.

## Ticket-First Audit Trail

Agents should create or select a ticket before meaningful code changes.

Reasons:

- Creates an audit trail.
- Makes work handoffs easier.
- Prevents scope drift.
- Gives commits, branches, PRs, and release notes a traceable source.

Tiny typo fixes and direct user-requested prose edits may be exempt when the repo profile allows it.

## Setup Modes

`$agent-ticketing-init` should support two modes:

- **Fast setup**: use sensible defaults, create the core files, seed one setup ticket, and get out of the way.
- **Deep setup**: ask detailed questions about repo type, ticket layout, sprint style, integrations, validation commands, branch policy, definition of done, and platform sync.

If the user does not specify a mode, ask which setup mode they want.

## Organization

Use both status and product area.

Recommended model:

- Board view groups by status first so agents know what is actionable now.
- Backlog and planning views can also group/filter by area so product owners can reason about roadmap coverage.
- Ticket metadata stores both `status` and `area`.

## Sprints

Add optional sprint support.

Sprints should be lightweight Markdown records, not a required heavyweight process:

- `.tickets/sprints/current.md` for the active sprint.
- `.tickets/sprints/YYYY-WW.md` or `docs/sprints/YYYY-WW.md` for archives.
- Each sprint should list goals, committed tickets, carryover, completed tickets, blocked tickets, and retro notes.

Sprints should work whether the repo uses `.tickets/` ticket files or strict split-board `tickets.md` and `docs/tickets/*`.

Sprint start should use host agent workflow features when available. In clients with `/goal` and `/plan`, the skill should create a sprint goal and draft a plan before committing tickets into the sprint. In clients without those features, the sprint file becomes the fallback source for goal and plan.

## Platform Sync

Support external platforms through adapters.

Principle:

- Local Markdown remains the source of truth unless the user chooses otherwise.
- External tools are mirrors or references by default.
- Sync should happen only when the required MCP/tool is available and the user has authorized the integration.

Targets:

- GitHub Issues and PRs.
- Jira issues.
- Linear issues.
- Other MCP-backed trackers when available.

The first implementation should use an adapter contract rather than hard-code one provider.

## Numbering

Ticket IDs should be configurable.

Default:

- `T-0001`, `T-0002`, etc.

Profiles can use phase ranges, such as `T-0100`, `T-0200`, and so on.

The user does not need to care about numbering unless the profile uses meaningful ranges.

## Readiness Gate

If there is no ticket yet for a new feature, design, or workflow idea, the agent should create one before implementation.

For strict profiles, new ideas should start as `Backlog` until enough scope is known. Strict split-board profiles should enforce the 10-question gate before moving those tickets to `Ready`, unless the user explicitly waives it.
