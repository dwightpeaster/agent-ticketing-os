---
name: agent-operating-review
description: Check readiness for agent work, tickets, PRs, or handoffs.
---

# Agent Operating Review

Run a non-mutating readiness review against the repo's operating rules.

Load `references/agent-operating-mode.md` and relevant local docs such as `AGENTS.md`, `docs/DEFINITION_OF_DONE.md`, `docs/BRANCH_WORKFLOW.md`, and `docs/REVIEW_CHECKLIST.md` when they exist.

Check:

- active ticket exists and status is appropriate
- ticket body lives in one correct location
- branch is not protected for implementation work
- changed files match ticket scope
- acceptance criteria are satisfied or gaps are documented
- tests/validation are recorded
- product decisions/ADRs are updated when needed
- no secrets or generated dependency folders are included
- follow-up work is ticketed

Lead with blockers first. Do not mutate files unless the user asks for fixes.
