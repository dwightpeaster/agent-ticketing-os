# External Tracker Guidance

Agent Ticketing OS does not contain a background agent, scheduler, webhook service, or automatic synchronization engine. Tracker setup stores policy for an active Codex or Claude session that has an authorized connector.

## Modes

- `local-primary`: Markdown tickets own planning and implementation state; external issues are optional mirrors.
- `hybrid`: Markdown owns implementation detail and handoff; the tracker owns collaboration state such as assignment and stakeholder comments.
- `external-primary`: the tracker owns planning state; local tickets exist only when execution detail or offline handoff is useful.

## Connector Procedure

1. Read local configuration and canonical tickets.
2. Read external records before creating or updating them.
3. Match by stored external id; use ticket ids in titles or bodies only as a fallback.
4. Compare status, title, ownership, and relevant notes.
5. Show conflicts and confirm the resolution before writing.
6. Record external ids and a compact activity note.

Do not duplicate records, overwrite conflicts silently, or store credentials in the repository. Bulk closing, moving, relabeling, or restructuring requires explicit approval.
