---
name: agent-ticketing-sprint
description: Plan, start, update, review, or close a lightweight Agent Ticketing OS sprint. Use when the user asks to group ready tickets around a goal, inspect sprint progress, add scoped work, or record carryover and closure.
---

# Agent Ticketing Sprint

Manage lightweight sprint records that group local tickets into a time-boxed plan.

Read `references/sprints.md` when changing sprint policy or resolving unusual carryover.

## Workflow

1. Ensure ticketing is initialized.
2. Confirm one clear sprint goal and exclusions.
3. Use `context` to inspect active work and `context --next` to select actionable work.
4. Start or update the sprint through the deterministic engine.
5. On close, summarize the outcome and identify carryover explicitly.

Prefer the deterministic sprint commands:

```bash
python3 <package-root>/scripts/ticketctl.py sprint start --root . --name "<name>" --goal "<goal>" --tickets T-0001,T-0002
python3 <package-root>/scripts/ticketctl.py sprint add --root . --tickets T-0003
python3 <package-root>/scripts/ticketctl.py sprint status --root .
python3 <package-root>/scripts/ticketctl.py sprint close --root . --summary "<summary>" --carryover T-0004
```

## Rules

- Do not move tickets into a sprint if they are too vague to be actionable.
- Do not start a sprint without a goal.
- Do not commit tickets to a sprint until the plan identifies why each ticket belongs.
- Do not mark a sprint complete until ticket completion records are updated.
- Carryover should include a concise reason.
- Sprint files should link or mention ticket IDs, not duplicate full ticket bodies.
- For fast planning, infer only low-risk details and record the assumptions.
