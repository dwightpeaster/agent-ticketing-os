---
name: agent-ticketing-sprint
description: Manage lightweight Agent Ticketing OS sprints.
---

# Agent Ticketing Sprint

Manage lightweight sprint records that group local tickets into a time-boxed plan.

Load `references/sprints-and-sync.md` when designing or changing sprint workflow.

## Workflow

1. Ensure ticketing is initialized.
2. For a new sprint, start with the agent's planning/goal features when available:
   - If a `/goal` or goal-tracking feature exists, create a goal for the sprint outcome.
   - If a `/plan` or plan mode exists, use it to build the sprint plan before editing files.
   - If those features are not available, write the sprint goal and plan directly into the sprint file.
3. Find or create the active sprint file.
4. Add committed tickets by id only after the sprint goal is clear.
5. Keep sprint status aligned with ticket status.
6. On close, record completed tickets, carryover tickets, blocked tickets, and retro notes.

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
- Carryover requires a reason.
- Sprint files should link or mention ticket IDs, not duplicate full ticket bodies.

## Sprint Start

When the user says "start a sprint" or "plan this sprint":

1. Ask for or infer the sprint goal.
2. Use `/goal` or equivalent goal tracking when the client supports it.
3. Use `/plan` or equivalent planning mode when the client supports it.
4. Select candidate tickets from `Ready` and `Backlog`.
5. Reject vague tickets or move them through readiness triage first.
6. Create the sprint file with goal, dates, committed tickets, risks, and validation expectations.

If the user says to use fast mode, create the sprint from ready tickets with a concise inferred goal and record assumptions.
