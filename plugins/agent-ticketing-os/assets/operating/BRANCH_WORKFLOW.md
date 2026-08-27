# Branch Workflow

Branches keep work isolated, reviewable, and reversible. Follow an existing repository convention when one is present.

## Before Creating Or Switching Branches

1. Use `context <ticket-id>` to read the active working packet and repository instructions.
2. Inspect the current branch and working tree.
3. Preserve unrelated user changes; do not reset, clean, or overwrite them.
4. Confirm the base branch only when the repository does not make it obvious.
5. Fetch or pull only when requested or required by the repository workflow.

## Naming

Prefer a short type, ticket id, and outcome:

```text
feature/T-0042-account-search
bugfix/T-0048-session-expiry
repo/T-0051-ci-matrix
security/T-0057-token-scope
```

## While Working

- Keep the branch aligned to one ticket or one inseparable ticket group.
- Do not mix unrelated cleanup, generated artifacts, or formatting churn.
- Recheck the diff when scope changes.
- If blocked, record the exact missing input and leave a resumable state.

## Before Review

- Confirm the diff matches the ticket.
- Run proportional validation and record the result.
- Update affected setup, behavior, or workflow documentation.
- Move the ticket to `review` and identify known risks or skipped checks.

Never implement directly on a protected branch unless the user explicitly authorizes that workflow.
