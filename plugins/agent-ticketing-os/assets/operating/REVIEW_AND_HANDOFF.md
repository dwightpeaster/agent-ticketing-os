# Review And Handoff

## Review Order

1. Correctness and user impact.
2. Security, privacy, data, and permission boundaries.
3. Regressions and missing failure handling.
4. Acceptance criteria and scope.
5. Validation quality.
6. Maintainability and documentation.

Lead with actionable findings. Each finding should identify the affected location, the concrete failure mode, and why it matters. Do not bury blockers beneath summaries or style comments.

## Readiness Review

Check that:

- The active ticket and branch agree with the diff.
- Required behavior and important edge cases are covered.
- Tests prove the changed behavior rather than only exercising code paths.
- Skipped validation and residual risks are explicit.
- No secrets, local artifacts, or unrelated user changes are included.

## Handoff

A useful handoff answers:

- What outcome was completed?
- What remains incomplete or uncertain?
- Which decisions or constraints must be preserved?
- What validation ran, with what result?
- What should the next agent or reviewer do first?

Keep the handoff concise and operational. Do not repeat information already obvious from the ticket or diff.
