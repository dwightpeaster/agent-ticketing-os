# Agent Ticketing Workflow

## Initialization Interview

When the user wants an in-depth setup, ask these in batches and then run `init --interactive` or write the answers into `.tickets/config.json`:

1. Project name and one-sentence product mission.
2. Primary users and the jobs they need done.
3. Repo shape: web app, mobile app, API, package, monorepo, docs, or mixed.
4. Ticket prefix, default priority, and whether GitHub Issues should be mirrored manually.
5. Main work lanes: product, bugs, design, repo, security, data, release, research.
6. Agent policy: can agents implement directly, or should high-risk work require a plan first?
7. Validation commands: tests, lint, typecheck, build, migrations, screenshots, app launch.
8. Definition of done for bugs, features, repo changes, and design changes.
9. Release cadence: continuous, sprint, milestone, client review, or ad hoc.
10. Any forbidden content in tickets: secrets, customer data, contract details, private URLs.

## Daily Agent Loop

1. Read `.tickets/BOARD.md`, `.tickets/BACKLOG.md`, and the target ticket.
2. Move the ticket to `in_progress`.
3. Implement the requested work.
4. Update the ticket activity log with files changed, decisions, and validation.
5. If scope changes, create follow-up tickets and link them.
6. Move to `review` or `done` depending on the user's workflow.
7. Run `sync` and `doctor`.

## Readiness Rules

A ticket is `ready` only when it has:

- Problem or opportunity context.
- Acceptance criteria that can be checked.
- A clear area or module.
- Priority.
- Known dependencies or an explicit "none".
- Validation plan.

## Done Rules

A ticket can be `done` only when it has:

- Resolution summary.
- Validation evidence or an explicit reason validation was skipped.
- Any follow-up tickets created for deferred work.
- User-facing behavior notes when behavior changed.

## Bug Intake

For bugs, capture:

- Expected behavior.
- Actual behavior.
- Reproduction steps.
- Affected environment.
- Severity.
- Suspected area.
- Regression status if known.

## Repo Management Intake

For repo tasks, capture:

- Why this improves maintenance, delivery, reliability, or agent performance.
- Files or systems likely affected.
- Risk level.
- Rollback plan for risky changes.
- Validation commands.

## Agent Handoff Notes

Every ticket has an "Agent Handoff" section. Use it for:

- Current hypothesis.
- Files already inspected.
- Commands already run.
- Partial work status.
- What the next agent should do first.

Keep handoffs short and operational. The next agent should not need a novella to find the door.
