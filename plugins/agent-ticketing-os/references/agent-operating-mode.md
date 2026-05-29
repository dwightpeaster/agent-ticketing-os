# Agent Operating Mode

Agent Operating Mode is an optional stricter layer on top of Agent Ticketing OS. It turns a repo into an agent-ready working environment with ticket-first audit trail, branch rules, commit standards, review gates, QA intake, release notes, and handoff discipline.

## Package Strategy

Keep Agent Operating Mode inside this package for now.

Reasons:

- It depends on ticketing as the audit trail.
- One install is easier for users.
- Shared profiles, scripts, and docs stay together.
- Users can opt in by calling `$agent-operating-init`.

Split it into a separate package later if:

- provider integrations become large
- branch/commit/PR automation becomes the main product
- non-ticketing users want the operating workflow independently
- install size or skill list noise becomes a problem

## Modes

### Ticketing Layer

Core tool for:

- tickets
- backlog
- board
- sprints
- local/external sync
- completion records

### Agent Operating Mode

Optional strict tool for:

- repo agent instructions
- ticket-first code changes
- branch workflow
- commit workflow
- PR workflow
- review checklist
- QA intake
- release workflow
- security gates
- handoff templates

## Recommended Skill Set

- `$agent-operating-init`
- `$agent-operating-review`

Possible future skills:

- `$agent-operating-branch`
- `$agent-operating-commit`
- `$agent-operating-pr`
- `$agent-operating-qa`
- `$agent-operating-release`
- `$agent-operating-security`
- `$agent-operating-handoff`

Keep these future skills out until the core package proves the workflow.

## Setup Outputs

Fast setup should create a compact operating kit:

- `AGENTS.md`
- `docs/TICKET_STANDARDS.md`
- `docs/DEFINITION_OF_DONE.md`
- `docs/BRANCH_WORKFLOW.md`
- `docs/AGENT_COMMIT_WORKFLOW.md`
- `docs/REVIEW_CHECKLIST.md`

Deep setup may also create:

- `CLAUDE.md`
- `docs/AGENT_QA_GUIDE.md`
- `docs/AGENT_HANDOFF_TEMPLATE.md`
- `docs/RELEASE_RUNBOOK.md`
- `docs/WRITING_STANDARDS.md`
- `docs/IMPLEMENTATION_STANDARDS.md`
- `docs/DEAD_CODE_REMOVAL.md`
- `docs/SECURITY_AGENT_PROTOCOL.md`
- `.github/pull_request_template.md`
- `.github/ISSUE_TEMPLATE/*.md`

## Principles

- Do not overwrite existing mature repo instructions without permission.
- Prefer profile-specific guidance over generic filler.
- Keep generated docs short enough that agents will actually read them.
- The active ticket is the center of gravity.
- External platforms may mirror status, but local handoff and validation details should remain easy to inspect in git.
- Strict mode should make good agent behavior the path of least resistance.

## Agent Feature Orchestration

When the host agent supports workflow primitives such as `/goal`, `/plan`, task lists, or equivalent built-in features, Agent Operating Mode should use them instead of treating every workflow as plain Markdown.

Recommended usage:

- Sprint start: create a goal, enter planning mode, then write the sprint file.
- Large feature intake: use planning mode before moving a ticket to `Ready`.
- Multi-ticket work: use a task list to track ticket selection, branch setup, implementation, verification, and completion.
- Release prep: use a goal for the release candidate and a plan for verification/release notes.
- Handoff: close or update the active goal after ticket records and sprint records are current.

Fallback:

- If those host features do not exist, write the same information into the local ticket, sprint, or handoff Markdown files.
