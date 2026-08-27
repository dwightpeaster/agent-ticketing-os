# Storage Schema

## Authority

- `.tickets/tickets/*.md` files are canonical.
- `.tickets/REGISTRY.json` is a generated index and may be rebuilt.
- `BOARD.md`, `BACKLOG.md`, `CHANGELOG.md`, and sprint reports are generated views.
- `.tickets/config.json` is authoritative configuration.

Never repair a ticket by editing the registry. Edit the canonical ticket or use the command engine, then run `render`.

## Ticket Metadata

Each ticket begins with JSON metadata between `---` delimiters. Required fields are `id`, `title`, `type`, `status`, `priority`, `area`, `created`, and `updated`. Lists such as `labels`, `depends_on`, and `blocks` are JSON arrays.

Optional fields are omitted when empty or set to their normal defaults. The parser supplies `owner: agent`, `risk: medium`, `source: agent`, empty lists, and an empty external-id map in memory, so agents do not need to repeat them in every ticket.

Optional `external_ids` map tracker providers to stable external record ids. Update them through `edit --external-id provider=id`; do not store tracker credentials or tokens.

Required narrative sections are Context, Acceptance Criteria, Implementation Notes, Validation Plan, Validation Evidence, Agent Handoff, Activity Log, and Closure.

## Schema And Migration

Configuration and registry files carry `schema_version`. Version 0.4.0 uses schema 2. The installer migrates supported schema-1 repositories after writing a backup under `.tickets/backups/`. Use `migrate --dry-run` to inspect an upgrade without changing files.

Unknown newer schemas must be refused rather than guessed at.

## IDs And Links

- IDs use the configured prefix and a monotonically increasing number.
- IDs are allocated while holding the repository ticket lock.
- Never reuse a closed ticket id.
- Dependencies must point to existing tickets and must not form cycles.
- An actionable dependency is satisfied only when the dependency ticket is `done`.
