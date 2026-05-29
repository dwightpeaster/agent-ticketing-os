# Intent Routing

The main skill should be able to respond to explicit skill calls and casual language.

## Natural Language Examples

- "We need a ticket for the add customer form being blank."
- "Create a P1 bug for the login redirect loop."
- "Add repo cleanup to the backlog."
- "Start T-0004."
- "Move the customer search ticket to review."
- "Close that ticket; it was fixed by the route guard change."
- "What ticket should the next agent pick up?"

## Inference Defaults

Use these defaults when the user does not specify details:

- Type: `bug` if the wording says broken, crash, error, regression, failing, blank, missing, or wrong.
- Type: `repo` if the wording says repo, cleanup, dependency, CI, test, lint, build, docs, architecture, or refactor.
- Type: `design` if the wording says UI, UX, layout, spacing, color, polish, screen, or component styling.
- Type: `security` if the wording says auth, permission, token, secret, injection, XSS, CSRF, data leak, or vulnerability.
- Type: `feature` for new user-facing behavior.
- Priority: `P2` unless urgency or impact implies otherwise.
- Status: `ready` when the action is clear; `inbox` when it is only a rough idea; `backlog` when the user explicitly says backlog.
- Area: infer from filenames, route names, product words, or repo modules; otherwise use `repo`.

## Clarifying Questions

Do not interview the user for every ticket. Ask one short question only when:

- The requested ticket could point at multiple unrelated systems.
- Severity is ambiguous and could be `P0` or `P1`.
- The user asks for a ticket but gives no actual issue or outcome.

Otherwise create the ticket and record assumptions.

## Companion Alias Skills

Clients that support multi-skill packages may expose small alias skills such as:

- `$new-ticket`
- `$ticket-next`
- `$ticket-board`
- `$ticket-close`

These should not duplicate the full workflow. They should delegate to `$agent-ticketing` and use `scripts/ticketctl.py` so all ticket behavior stays consistent.
