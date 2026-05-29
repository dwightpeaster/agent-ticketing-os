# Ticket Schema

Each ticket is a Markdown file in `.tickets/tickets/` with YAML-like frontmatter followed by fixed sections.

## Required Frontmatter

- `id`: stable ticket id, for example `T-0007`.
- `title`: concise human-readable title.
- `type`: `feature`, `bug`, `change`, `repo`, `research`, `design`, or `security`.
- `status`: `inbox`, `backlog`, `ready`, `in_progress`, `review`, `blocked`, `done`, or `wont_do`.
- `priority`: `P0`, `P1`, `P2`, `P3`, or `P4`.
- `area`: repo area such as `app`, `api`, `components`, `infra`, `docs`, `tests`, or `unknown`.
- `created`: ISO timestamp.
- `updated`: ISO timestamp.

## Optional Frontmatter

- `severity`: bug/security severity such as `S1`, `S2`, `S3`, or `S4`.
- `owner`: person or agent responsible.
- `estimate`: `XS`, `S`, `M`, `L`, or `XL`.
- `risk`: `low`, `medium`, or `high`.
- `labels`: comma-separated labels.
- `depends_on`: comma-separated ticket ids.
- `blocks`: comma-separated ticket ids.
- `source`: user, agent, GitHub, CI, audit, support, planning.

## Required Sections

- `Context`
- `Acceptance Criteria`
- `Implementation Notes`
- `Validation Plan`
- `Agent Handoff`
- `Activity Log`
- `Closure`

## Registry

`.tickets/REGISTRY.json` is the machine index. It stores project metadata and a summarized entry for every ticket. The Markdown ticket files remain the canonical human-readable record; the registry exists so agents can list, rank, and sync quickly.

## ID Rules

- Use the configured prefix, default `T`.
- IDs are monotonically increasing.
- Never reuse a ticket id, even after `wont_do`.
- Keep filenames as `<id>-<slug>.md`.

## Link Rules

Mention linked tickets by id in text and in frontmatter fields. If external issue trackers are used, put links in `source` or `Implementation Notes`, but keep local ticket ids primary for agent work.
