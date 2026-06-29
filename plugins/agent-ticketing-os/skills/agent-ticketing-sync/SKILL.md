---
name: agent-ticketing-sync
description: Configure external tracker sync for Agent Ticketing OS.
---

# Agent Ticketing Sync

Sync local tickets with an external tracker only when the relevant MCP/tool is available and the user authorizes the integration.

Load `references/sprints-and-sync.md` before designing provider behavior or resolving sync conflicts.

## Default Position

Use hybrid sync:

- Local Markdown keeps implementation details, validation, and agent handoff context.
- External tools keep collaboration state, assignment, comments, and stakeholder visibility.

For Linear-specific setup, use `$linear-setup` when the user wants to choose between repo-primary, hybrid, and Linear-primary operation.

## Workflow

1. Identify provider: GitHub, Jira, Linear, or another MCP-backed tracker.
2. Check whether the tool/connector is available.
3. Ask before enabling or writing to an external platform.
4. Configure a local provider hook:

```bash
python3 <package-root>/scripts/ticketctl.py sync-hooks --root . --provider github --mode hybrid --external-project "<owner/repo>"
```

Use `--provider jira`, `--provider linear`, or `--provider custom` when appropriate.

For Linear with source-of-truth policy:

```bash
python3 <package-root>/scripts/ticketctl.py linear-setup --root . --mode linear-primary --team "<team>" --project "<project>"
```

5. Store provider settings and external IDs in `.tickets/config.json` or ticket metadata.
6. Never overwrite local or external changes silently.

If the provider is unavailable, keep working locally and create a sync-pending note.
