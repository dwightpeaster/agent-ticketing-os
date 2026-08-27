# Commit Workflow

Create commits only when the user or repository workflow calls for them.

## Before Staging

1. Review the working tree and full diff.
2. Separate unrelated user changes from the ticket scope.
3. Remove temporary output, secrets, local environment files, and generated dependencies.
4. Run or record the required validation.

## Staging

- Stage explicit files or coherent groups.
- Do not use broad staging when unrelated changes are present.
- Inspect the staged diff before committing.

## Commit Shape

- One commit should describe one coherent change.
- Prefer the repository's existing message convention.
- Include the ticket id when practical.

Examples:

```text
T-0042 Add account search filters
fix(auth): handle expired sessions (T-0048)
```

## After Committing

- Verify the working tree contains only expected remaining work.
- Update the ticket when the commit changes handoff state.
- Do not push, merge, or open a pull request unless requested or required by the active workflow.
