# Definition Of Done

Work is done when the requested outcome is complete, reviewable, and safe to continue from—not merely when files were edited.

## Required

- The implementation matches one active ticket and its acceptance criteria.
- Acceptance checklists have no unchecked items unless an explicit exception records why.
- The diff contains no unrelated behavior or accidental generated files.
- Validation appropriate to the risk has passed, or the skipped check and remaining risk are recorded.
- Documentation is current when setup, commands, configuration, interfaces, or workflows changed.
- The ticket records material decisions, validation evidence, and handoff state.
- Deferred work is explicit and separately ticketed.

## Risk-Proportional Validation

- **Low risk:** targeted test, lint, or direct manual check.
- **Medium risk:** targeted checks plus the affected workflow or build.
- **High risk:** broader regression coverage, rollback plan, and explicit review of the affected boundary.

Never claim a check passed unless it actually ran. A skipped check must include why it was skipped, what risk remains, and what should run next.

## Before Closure

1. Review the final diff against acceptance criteria.
2. Record validation evidence.
3. Resolve or ticket open findings.
4. Write a concise resolution and next action.
5. Close through the ticket engine so completion rules are applied.
