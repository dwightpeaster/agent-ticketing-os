---
name: agent-operating-init
description: Initialize the optional Agent Operating Mode on top of Agent Ticketing OS. Use when the user says "$agent-operating-init", "set up agent operating mode", "install the full agent workflow", "make this repo agent-ready", or wants ticketing plus branch, commit, PR, QA, review, release, security, and handoff guardrails.
---

# Agent Operating Init

Set up the full agent operating mode. This is optional and stricter than ticketing-only setup.

Load `references/agent-operating-mode.md` before making changes.

## Positioning

Agent Operating Mode lives inside Agent Ticketing OS because it depends on tickets as the audit trail. Treat it as a higher-control profile:

- ticket-first implementation
- sprint planning
- branch rules
- commit grouping
- PR readiness
- QA intake
- review checklist
- security gates
- release notes
- agent handoffs

## Workflow

1. Ensure ticketing is initialized. If not, run `$agent-ticketing-init` first.
2. Ask whether the user wants:
   - fast operating setup
   - deep operating setup
3. Create or update operating docs without overwriting existing repo-specific rules unless the user explicitly approves replacement.
4. Prefer adding missing sections over replacing mature docs.
5. Report the files created, files skipped, and next recommended setup step.

## Fast Setup

Create a compact set of docs:

- `AGENTS.md`
- `docs/TICKET_STANDARDS.md`
- `docs/DEFINITION_OF_DONE.md`
- `docs/BRANCH_WORKFLOW.md`
- `docs/AGENT_COMMIT_WORKFLOW.md`
- `docs/REVIEW_CHECKLIST.md`

## Deep Setup

Ask about:

- branch model
- commit policy
- PR policy
- external tracker sync
- sprint cadence
- QA modes
- release cadence
- security sensitivity
- required verification commands
- docs that should be generated

Then scaffold the fuller operating system.
