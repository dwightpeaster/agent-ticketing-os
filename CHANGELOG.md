# Changelog

## 0.4.0 — 2026-08-27

### Changed

- Make Markdown ticket files canonical and generate `REGISTRY.json` from them.
- Replace project-specific defaults with neutral repository detection.
- Make `$agent-ticketing-os` an idempotent one-command install and upgrade path.
- Replace strict mode with standard and guarded workflow policies while retaining the legacy profile alias.
- Consolidate the public skill surface to five focused skills.
- Move generated operating guidance into concise, namespaced workflow documents.
- Rename external synchronization behavior to explicit tracker and connector guidance.
- Simplify installation, daily-use, policy, tracker, and upgrade documentation.
- Route installed agent instructions by workflow phase instead of loading every document up front.
- Omit empty and default optional metadata from canonical ticket frontmatter and generated indexes.
- Restore durable safety, scope, validation, and handoff guardrails to the managed agent-instruction block.

### Added

- Schema versioning, schema-1 backups, dry-run migration reporting, and safe migration.
- Atomic writes and repository-level locking for concurrent agents.
- Deterministic rendering that avoids no-op Git churn.
- Ticket editing, dependency links, validation evidence, reopening, JSON output, and stronger health checks.
- Compact `context`, `context --next`, and `context <id>` packets for low-token session startup and resumption.
- Per-skill UI metadata plus activation cases and explicit context-budget tests.
- A phase-loaded implementation workflow covering repository patterns, abstractions, dependencies, and safe deletion.
- Stable external tracker ids on canonical tickets without enabling automatic synchronization.
- Generic ticket templates for every supported ticket type.
- Clean-install, idempotency, migration, concurrency, policy, sprint, tracker, and manifest tests.
- Python 3.10–3.14 continuous-integration coverage.
- Repository-bound path checks and symbolic-link protections for managed state and workflow files.

### Hardened

- Guarded closure now requires a passed validation result or a documented skipped check; failed evidence alone cannot close work.
- Skipped validation requires an explanatory note for the reason and remaining risk.
- Generated ticket links resolve correctly from boards, sprint reports, and split-board documents.
- Explicit standard or guarded policy changes apply to existing installations without changing policy on ordinary reinstalls.
- Guarded closure rejects unchecked acceptance criteria unless an auditable override is used.
- Ready tickets with unresolved dependencies appear separately as waiting and are excluded from actionable work.

### Upgrade Notes

- Refresh and reinstall the plugin, then run `$agent-ticketing-os` once in every repository that should be upgraded.
- Existing schema-1 installations are backed up before migration to schema 2. Use `migrate --dry-run` first when you want to inspect the migration report without changing repository files.
- Narrow legacy skill aliases such as `$agent-ticketing-init`, `$agent-ticketing-next`, `$ticket-board`, and `$linear-setup` are no longer published. Use `$agent-ticketing-os` for install and upgrade, `$agent-ticketing` for ticket operations, and `$agent-ticketing-tracker` for external tracker guidance.

### Compatibility

- The repository, marketplace, plugin name, and `$agent-ticketing-os` activation remain unchanged.
- Legacy CLI commands for rendering, operating setup, tracker hooks, and Linear setup remain available as aliases.
- Narrow legacy skill aliases are removed; natural-language ticket requests route through `$agent-ticketing`.
