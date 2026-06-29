---
name: linear-setup
description: Explicit setup hook for Linear sync.
---

# Linear Setup

Use only when the user explicitly invokes `$linear-setup`, asks to set up Linear for Agent Ticketing OS, or asks to switch between repo-primary, hybrid, and Linear-primary ticketing.

## Purpose

Configure Linear as the external project operating layer for Agent Ticketing OS.

Modes:

- `repo-primary`: local tickets are primary; Linear mirrors stakeholder-visible work.
- `hybrid`: local tickets keep implementation detail; Linear keeps stakeholder status and planning.
- `linear-primary`: Linear is primary; local files only keep lightweight references or implementation handoff detail when needed.

## Setup Questions

Ask in one compact batch unless the user already answered:

- Linear team name.
- Linear project name.
- Mode: `repo-primary`, `hybrid`, or `linear-primary`.
- Labels to use, or accept defaults.
- Work lanes/milestones to use, or accept defaults.
- Changelog document title, or accept `<project> Changelog`.
- Whether agents may create Linear issues without asking for obvious bugs/features/requests.

Defaults:

- Mode: `repo-primary`.
- Labels: `bug`, `feature`, `request`, `documentation`, `testing`, `deployment`, `blocked`, `changelog`.
- Work lanes: `Quote Workflow`, `Salesforce Build`, `Assistant Behavior`, `Testing & Validation`, `Deployment`, `Backlog`.

## Repo Configuration

Ensure ticketing exists first. If `.tickets/config.json` is missing, run or offer `$agent-ticketing-init`.

Then configure the Linear hook:

```bash
python3 <package-root>/scripts/ticketctl.py linear-setup --root . --mode <mode> --team "<team>" --project "<project>"
```

Pass custom labels or lanes when the user provides them:

```bash
python3 <package-root>/scripts/ticketctl.py linear-setup --root . --mode linear-primary --team "SalesForce" --project "ProFence Quote System" --labels "bug,feature,request,documentation,testing,deployment,blocked,changelog" --work-lanes "Quote Workflow,Salesforce Build,Assistant Behavior,Testing & Validation,Deployment,Backlog"
```

## Linear Writes

When Linear MCP/tools are available and the user authorizes setup:

1. Read existing teams, projects, labels, documents, and issues first.
2. Create or update the Linear project only if it does not already exist.
3. Create missing labels only.
4. Create work lanes as milestones when the Linear tool supports milestones for the project.
5. Create the changelog document if missing.
6. Add a short status update that Linear is now configured as the project operating layer.

Do not duplicate existing records. Ask before renaming/deleting labels, moving many issues, or changing project structure.

## Agent Behavior After Setup

In `linear-primary` mode:

- Create Linear issues first.
- Keep local tickets optional and lightweight.
- Put long implementation notes in Linear comments only when they are useful to the next agent.
- Keep the changelog in Linear.

In `repo-primary` mode:

- Create local tickets first.
- Mirror stakeholder-visible work to Linear only when useful.

In `hybrid` mode:

- Use local tickets for implementation detail, validation, and handoff.
- Use Linear for boss-visible state, assignments, status updates, and project summaries.
