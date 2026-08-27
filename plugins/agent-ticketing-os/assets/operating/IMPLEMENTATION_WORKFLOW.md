# Implementation Workflow

Use this guidance before adding tools, abstractions, dependencies, shared patterns, or removing code.

## Before Editing

1. Use `context <ticket-id>` to confirm the outcome, scope, acceptance criteria, and validation plan.
2. Inspect the current branch, working tree, nearby code, tests, and repository-specific instructions.
3. Identify the existing pattern that best fits the change. Prefer extending it over creating a parallel approach.
4. Decide which focused validation will prove the behavior before implementation begins.

## While Implementing

- Make the smallest coherent change that satisfies the ticket.
- Keep file edits, dependencies, and abstractions aligned to the active outcome.
- Update affected tests, documentation, routes, configuration examples, and setup instructions when behavior changes.
- Record material decisions or constraints that another agent cannot cheaply rediscover.
- Create a linked follow-up ticket for separate discoveries; continue only when doing so is safe and does not broaden the active scope.

## Abstractions And Dependencies

- Reuse stable repository patterns before introducing a new helper, layer, component, or package.
- Add a dependency only when its benefit outweighs its maintenance, security, and migration cost.
- Keep public interfaces and configuration compatible unless the ticket explicitly authorizes a breaking change.

## Safe Removal

Before deleting code, files, exports, routes, configuration, or dependencies:

1. Search for direct, indirect, generated, documented, and runtime references.
2. Check compatibility, migration, rollback, and data-retention requirements.
3. Remove or update affected tests, documentation, examples, and configuration in the same coherent change.
4. Validate both the removal and the neighboring behavior that should remain.

Do not delete uncertain or unrelated material merely because it appears unused.
