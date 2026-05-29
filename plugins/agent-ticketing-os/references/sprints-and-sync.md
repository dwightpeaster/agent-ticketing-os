# Sprints And Platform Sync

## Sprint Model

A sprint is a time-boxed selection of tickets with a goal and handoff state.

Sprints should orchestrate the agent's available workflow features. If the client supports goal tracking, planning mode, or slash commands such as `/goal` and `/plan`, sprint start should use them before writing the final sprint file.

Suggested sprint file:

```md
# Sprint YYYY-WW

Status: Active
Dates: YYYY-MM-DD to YYYY-MM-DD
Goal: one sentence.

## Committed Tickets

- T-####

## In Progress

- T-####

## Completed

- T-####

## Blocked

- T-#### - blocker.

## Carryover

- T-#### - reason.

## Retro Notes

- Keep:
- Change:
- Follow-up tickets:
```

## Sprint Commands

Future CLI commands should support:

- `sprint start`
- `sprint add <ticket-id>`
- `sprint remove <ticket-id>`
- `sprint status`
- `sprint close`
- `sprint carryover`

The skill can provide the workflow before the script implements every command.

## Agent Feature Orchestration

When starting a sprint, use the richest local agent workflow available:

- `/goal` or equivalent: create a tracked sprint objective.
- `/plan` or equivalent: draft the sprint plan, risks, and ticket selection before edits.
- task/checklist feature: track setup, ticket selection, readiness review, and sprint file creation.
- memory/context feature: record durable sprint preferences only when the user asks.

Fallback when those features are unavailable:

- Ask for a sprint goal.
- List candidate tickets.
- Propose a short sprint plan in the response.
- Write the sprint file after the user confirms or when the user asked for fast setup.

The sprint file should record which orchestration features were used, for example:

```md
Planning:

- Goal tracked: yes
- Plan reviewed: yes
- Candidate tickets checked: T-0001, T-0002
```

## Sprint Start Questions

Deep sprint planning should ask:

- What is the sprint goal?
- What dates or duration should this sprint cover?
- What areas should be prioritized?
- What must not be included?
- Should carryover from the previous sprint be considered?
- Are there external platform tickets to sync first?
- What validation must pass before closing the sprint?

Fast sprint planning may infer these from ready tickets and repo defaults.

## Sync Model

Use a provider adapter pattern:

```text
local ticket <-> adapter <-> external platform
```

The adapter should map:

- ticket id
- title
- status
- type
- priority
- area/labels
- acceptance criteria
- implementation notes
- external URL/id
- last synced timestamp

## Source Of Truth Options

### Local Primary

Markdown tickets are canonical. GitHub/Jira/Linear mirror the local state.

Pros:

- Works offline.
- Easy for agents to read and edit.
- Auditable in git.
- Avoids external-tool lock-in.

Cons:

- External boards can drift if sync is not run.
- External users may update Jira/GitHub and expect it to flow back.

### External Primary

Jira/GitHub/Linear are canonical. Markdown is a local cache or working copy.

Pros:

- Better for teams already living in an external tracker.
- Permissions, notifications, and dashboards are handled by the platform.
- Non-agent teammates can work normally.

Cons:

- Agents need tool access.
- Work can stall without network/auth/tool availability.
- Git history no longer captures the full planning record.

### Hybrid

Local tickets are canonical for implementation details and handoffs; external tools hold high-level status and collaboration.

Pros:

- Best balance for agent-led repos.
- Human stakeholders can use external boards.
- Agents keep rich local context.

Cons:

- Requires clear sync rules.
- Needs conflict handling.

Recommended default: **Hybrid with local implementation detail as canonical**.

## MCP Strategy

Do not make GitHub, Jira, or Linear mandatory dependencies.

Instead:

- Detect available tools/MCP connectors.
- Ask the user before enabling a sync provider.
- Store sync config in `.tickets/config.json`.
- Store external IDs in ticket metadata.
- If a provider is unavailable, create local tickets and note that sync is pending.

## Conflict Policy

When both local and external ticket changed since last sync:

1. Do not overwrite silently.
2. Show both versions.
3. Prefer local implementation notes and validation evidence.
4. Prefer external assignee/comment/status only when the user confirms.
5. Record the conflict resolution in the ticket activity log.
