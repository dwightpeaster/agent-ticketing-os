# Ticket Workflow

## Statuses

- `inbox`: captured but not triaged.
- `backlog`: valid, intentionally deferred.
- `ready`: triaged and otherwise actionable; unresolved dependencies are shown separately as waiting.
- `in_progress`: actively being implemented.
- `review`: implementation awaits review or final verification.
- `blocked`: progress requires external input or a prerequisite.
- `done`: completed with resolution and validation evidence.
- `wont_do`: intentionally closed without implementation.

Use `close` rather than `move` for closed statuses. Use `reopen` to return closed work to the active workflow.

## Standard And Guarded Policy

Standard policy provides workflow guidance and warnings. Guarded policy rejects promotion or closure when required context, acceptance criteria, validation plans, or evidence are missing. Both policies reject invalid state transitions and require an explicit reason for overrides.

## Readiness

Promote a ticket to `ready` only when it has a concrete outcome, observable acceptance criteria, an area, known dependencies, and a proportional validation plan. A fixed number of questions is not required; clarity is the gate.

## Completion

Before `done`, record what changed, what validation ran, its result, remaining risk, and follow-up work. Do not claim validation that did not run. Use a skipped result with a reason when a check is unavailable.

## Next Work

`context --next` returns the working packet for the highest-priority `ready` ticket whose dependencies are all `done`. The shorter legacy `next` command returns the same selection as a one-line summary. Generated boards and sprint reports place other ready tickets under Waiting On Dependencies. Inbox and backlog triage are separate activities.

## Handoff

Record decisions, validation, blockers, and the next action. Avoid repeating the diff, pasting long logs, or writing information that is cheap to rediscover.
