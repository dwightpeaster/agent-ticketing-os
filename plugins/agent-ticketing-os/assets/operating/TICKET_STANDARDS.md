# Ticket Standards

Use tickets as compact execution contracts, not as substitutes for conversation or implementation.

## Before Meaningful Work

1. Run the ticket engine's `context` command and read relevant repository instructions.
2. Select one ticket or create one focused ticket.
3. Confirm the outcome, scope, acceptance criteria, dependencies, and validation plan.
4. Move the ticket to `in_progress` only when work actually begins.

## Ticket Quality

A `ready` ticket has:

- A concrete problem or outcome.
- Observable acceptance criteria.
- A responsible repository area.
- Known dependencies or an explicit statement that there are none. Unresolved dependencies appear as waiting and are not selected by `context --next`.
- A validation plan proportional to risk.

Do not promote placeholders such as “TBD” or “criteria to be confirmed” to `ready`.

## Scope Control

- Keep one coherent outcome per ticket; multiple files are fine.
- Create linked follow-ups for separate discoveries.
- Record decisions that affect implementation or future work.
- Do not silently broaden the requested outcome.

## Activity And Handoff

Record only information the next agent cannot cheaply rediscover:

- Decisions and constraints.
- Important files changed or inspected.
- Validation commands and outcomes.
- Remaining risks, blockers, and the next action.

Do not paste long logs or repeat the Git diff.

## Closure

Use the close operation rather than moving directly to `done`. Closure requires a resolution, validation evidence or a skipped-validation reason, and follow-up tickets for deferred work.
