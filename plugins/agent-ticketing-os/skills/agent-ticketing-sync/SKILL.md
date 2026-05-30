---
name: agent-ticketing-sync
description: Sync Agent Ticketing OS tickets with external issue platforms through available MCP/tools such as GitHub Issues, Jira, Linear, or another tracker. Use when the user says "$agent-ticketing-sync", "sync tickets with GitHub", "sync to Jira", "import issues", "mirror backlog", or asks to connect an external tracker.
---

# Agent Ticketing Sync

Sync local tickets with an external tracker only when the relevant MCP/tool is available and the user authorizes the integration.

Load `references/sprints-and-sync.md` before designing provider behavior or resolving sync conflicts.

## Default Position

Use hybrid sync:

- Local Markdown keeps implementation details, validation, and agent handoff context.
- External tools keep collaboration state, assignment, comments, and stakeholder visibility.

## Workflow

1. Identify provider: GitHub, Jira, Linear, or another MCP-backed tracker.
2. Check whether the tool/connector is available.
3. Ask before enabling or writing to an external platform.
4. Configure a local provider hook:

```bash
python3 <package-root>/scripts/ticketctl.py sync-hooks --root . --provider github --mode hybrid --external-project "<owner/repo>"
```

Use `--provider jira`, `--provider linear`, or `--provider custom` when appropriate.

5. Store provider settings and external IDs in `.tickets/config.json` or ticket metadata.
6. Never overwrite local or external changes silently.

If the provider is unavailable, keep working locally and create a sync-pending note.
