#!/usr/bin/env python3
"""Repo-local ticket manager for the agent-ticketing skill."""

from __future__ import annotations

import argparse
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STATUSES = ["inbox", "backlog", "ready", "in_progress", "review", "blocked", "done", "wont_do"]
TYPES = ["feature", "bug", "change", "repo", "research", "design", "security"]
PRIORITIES = ["P0", "P1", "P2", "P3", "P4"]
PRIORITY_SCORE = {"P0": 500, "P1": 400, "P2": 300, "P3": 200, "P4": 100}
STATUS_SCORE = {"ready": 50, "inbox": 10, "backlog": 20, "blocked": -100, "in_progress": -50, "review": -25}
ACTIVE_STATUSES = {"ready", "in_progress", "review", "blocked"}
SYNC_PROVIDERS = ["github", "jira", "linear", "custom"]
SYNC_MODES = ["local-first", "hybrid", "external-first"]


DISPLAY_STATUS = {
    "inbox": "Inbox",
    "backlog": "Backlog",
    "ready": "Ready",
    "in_progress": "In Progress",
    "review": "Review",
    "blocked": "Blocked",
    "done": "Done",
    "wont_do": "Won't Do",
}

STRICT_WORKING_SECTIONS = [
    ("in_progress", "In Progress"),
    ("review", "Review"),
    ("blocked", "Blocked"),
    ("ready", "Ready"),
]


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return re.sub(r"-+", "-", value).strip("-") or "ticket"


def csv_items(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def display_status(status: str) -> str:
    return DISPLAY_STATUS.get(status, status.replace("_", " ").title())


def validate_choice(value: str, choices: list[str], label: str) -> None:
    if value not in choices:
        joined = ", ".join(choices)
        raise SystemExit(f"Invalid {label}: {value}. Expected one of: {joined}")


def root_path(args: argparse.Namespace) -> Path:
    return Path(args.root).expanduser().resolve()


def tickets_dir(root: Path) -> Path:
    return root / ".tickets"


def config_path(root: Path) -> Path:
    return tickets_dir(root) / "config.json"


def registry_path(root: Path) -> Path:
    return tickets_dir(root) / "REGISTRY.json"


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_if_missing(path: Path, content: str, force: bool = False) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not force:
        return False
    path.write_text(content.rstrip() + "\n", encoding="utf-8")
    return True


def prompt(label: str, default: str) -> str:
    raw = input(f"{label} [{default}]: ").strip()
    return raw or default


def detect_repo(root: Path) -> dict[str, Any]:
    files = {p.name for p in root.iterdir()} if root.exists() else set()
    kind = "generic"
    commands: list[str] = []
    areas = ["app", "components", "api", "data", "tests", "docs", "repo"]

    if "package.json" in files:
        kind = "node"
        package = load_json(root / "package.json", {})
        scripts = package.get("scripts", {})
        if "test" in scripts:
            commands.append("npm test")
        if "lint" in scripts:
            commands.append("npm run lint")
        if "typecheck" in scripts:
            commands.append("npm run typecheck")
        if "build" in scripts:
            commands.append("npm run build")
        deps = {**package.get("dependencies", {}), **package.get("devDependencies", {})}
        if "expo" in deps:
            kind = "expo"
            areas = ["dashboard", "customers", "leads", "calls", "inventory", "navigation", "components", "hooks", "types", "repo"]
    elif "pyproject.toml" in files:
        kind = "python"
        commands = ["python -m pytest"]
        areas = ["package", "tests", "docs", "repo"]
    elif "composer.json" in files:
        kind = "php"
        commands = ["composer test"]
        areas = ["app", "routes", "database", "tests", "docs", "repo"]

    return {"kind": kind, "validation_commands": commands, "areas": areas}


def default_config(root: Path, profile: str = "generic") -> dict[str, Any]:
    detected = detect_repo(root)
    config = {
        "project": {
            "name": root.name,
            "mission": "Track repo work clearly enough that any agent can continue it.",
            "repo_kind": detected["kind"],
            "profile": profile,
        },
        "ticketing": {
            "prefix": "T",
            "layout": "local-ticket-files",
            "default_status": "ready",
            "default_priority": "P2",
            "statuses": STATUSES,
            "types": TYPES,
            "priorities": PRIORITIES,
            "areas": detected["areas"],
        },
        "agent_policy": {
            "implementation_mode": "direct-for-low-risk-plan-first-for-high-risk",
            "requires_ticket_for": ["multi-file changes", "bugs", "features", "repo management", "security", "release work"],
            "forbidden_ticket_content": ["secrets", "credentials", "private customer data", "access tokens"],
        },
        "validation": {
            "commands": detected["validation_commands"],
            "definition_of_done": [
                "Acceptance criteria satisfied",
                "Validation run or explicitly skipped with reason",
                "Ticket activity log updated",
                "Follow-up tickets created for deferred work",
            ],
        },
    }
    if profile == "strict":
        config["project"]["mission"] = "Track work with one readable working board, a deferred backlog, one-line completed archives, and strict agent handoffs."
        config["ticketing"].update(
            {
                "layout": "split-board",
                "default_status": "ready",
                "statuses": STATUSES,
                "types": TYPES,
                "areas": ["backend", "mobile", "dashboard", "public", "notifications", "security", "deployment", "docs", "repo"],
                "locations": {
                    "working": "tickets.md",
                    "backlog": "docs/tickets/BACKLOG.md",
                    "completed": "docs/tickets/COMPLETED.md",
                    "roadmap": "docs/ROADMAP.md",
                    "decisions": "docs/PRODUCT_DECISIONS.md",
                },
                "phase_ranges": {
                    "T-0000": "agent/repo foundation",
                    "T-0100": "backend domain",
                    "T-0200": "leads and sales",
                    "T-0300": "images and public sharing",
                    "T-0400": "mobile foundation",
                    "T-0500": "dashboard foundation",
                    "T-0600": "MVP mobile completion",
                    "T-0700": "MVP dashboard completion",
                    "T-0800": "public, notifications, security",
                    "T-0900": "deployment and release readiness",
                    "T-1000": "v2/post-MVP backlog",
                },
                "readiness_gate": {
                    "new_idea_min_questions": 10,
                    "applies_to": ["feature", "design"],
                    "waive_only_when_user_says_scope_complete": True,
                },
                "display_statuses": DISPLAY_STATUS,
            }
        )
        config["validation"]["definition_of_done"] = [
            "The change maps to one active ticket",
            "Acceptance criteria are satisfied or gaps are documented",
            "No unrelated behavior is included",
            "Implementation work happened on a ticket branch, not directly on master",
            "The owning ticket file is updated with status, implementation notes, changed files, and tests run",
            "Completed tickets move from tickets.md to docs/tickets/COMPLETED.md as one-line archive records",
            "Relevant docs are updated when setup, commands, env vars, routes, workflows, or product decisions change",
            "git diff --check passes",
        ]
    return config


def ensure_initialized(root: Path) -> None:
    if not config_path(root).exists():
        raise SystemExit("No .tickets/config.json found. Run: ticketctl.py init --root .")


def load_config(root: Path) -> dict[str, Any]:
    ensure_initialized(root)
    return load_json(config_path(root), {})


def load_registry(root: Path) -> dict[str, Any]:
    return load_json(registry_path(root), {"next_number": 1, "tickets": []})


def save_registry(root: Path, registry: dict[str, Any]) -> None:
    registry["updated"] = now()
    write_json(registry_path(root), registry)


def ticket_file(root: Path, ticket: dict[str, Any]) -> Path:
    existing = ticket.get("file")
    if existing:
        return root / existing
    return tickets_dir(root) / "tickets" / f"{ticket['id']}-{slugify(ticket['title'])}.md"


def frontmatter(ticket: dict[str, Any]) -> str:
    fields = [
        "id",
        "title",
        "type",
        "status",
        "priority",
        "severity",
        "area",
        "owner",
        "estimate",
        "risk",
        "labels",
        "depends_on",
        "blocks",
        "source",
        "created",
        "updated",
    ]
    lines = ["---"]
    for key in fields:
        value = ticket.get(key, "")
        if isinstance(value, list):
            value = ", ".join(value)
        lines.append(f"{key}: {value}")
    lines.append("---")
    return "\n".join(lines)


def render_ticket(ticket: dict[str, Any]) -> str:
    body = ticket.get("body", {})
    activity = ticket.get("activity", [])
    activity_lines = "\n".join(f"- {item}" for item in activity) or "- No activity yet."
    return f"""{frontmatter(ticket)}

# {ticket['id']}: {ticket['title']}

## Context
{body.get('context', 'Describe the problem, opportunity, or maintenance need.')}

## Acceptance Criteria
{body.get('acceptance', '- [ ] Define observable completion criteria.')}

## Implementation Notes
{body.get('notes', 'Relevant files, constraints, dependencies, and implementation thoughts.')}

## Validation Plan
{body.get('validation', '- [ ] Run the configured validation or explain why it was skipped.')}

## Agent Handoff
{body.get('handoff', 'No handoff notes yet.')}

## Activity Log
{activity_lines}

## Closure
{body.get('closure', 'Open.')}
"""


def write_ticket(root: Path, ticket: dict[str, Any]) -> None:
    path = ticket_file(root, ticket)
    ticket["file"] = os.path.relpath(path, root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_ticket(ticket), encoding="utf-8")


def sync_files(root: Path) -> None:
    config = load_config(root)
    registry = load_registry(root)
    for ticket in registry.get("tickets", []):
        write_ticket(root, ticket)
    write_backlog(root, config, registry)
    write_board(root, config, registry)
    write_changelog(root, registry)
    write_current_sprint(root, registry)
    if config["ticketing"].get("layout") == "split-board":
        write_split_board_files(root, config, registry)


def ticket_sort_key(ticket: dict[str, Any]) -> tuple[int, str]:
    score = PRIORITY_SCORE.get(ticket.get("priority", "P4"), 0) + STATUS_SCORE.get(ticket.get("status", ""), 0)
    return (-score, ticket.get("id", ""))


def ticket_line(ticket: dict[str, Any]) -> str:
    labels = ticket.get("labels", "")
    label_text = f" `{labels}`" if labels else ""
    return f"- [{ticket['id']}] {ticket['priority']} {ticket['type']} {ticket['area']} - {ticket['title']} ({ticket['file']}){label_text}"


def write_backlog(root: Path, config: dict[str, Any], registry: dict[str, Any]) -> None:
    lines = [
        "# Backlog",
        "",
        f"Project: {config['project']['name']}",
        f"Updated: {now()}",
        "",
    ]
    tickets = sorted(registry.get("tickets", []), key=ticket_sort_key)
    for status in STATUSES:
        grouped = [ticket for ticket in tickets if ticket.get("status") == status]
        lines.extend([f"## {status}", ""])
        lines.extend(ticket_line(ticket) for ticket in grouped)
        if not grouped:
            lines.append("- None")
        lines.append("")
    (tickets_dir(root) / "BACKLOG.md").write_text("\n".join(lines), encoding="utf-8")


def write_board(root: Path, config: dict[str, Any], registry: dict[str, Any]) -> None:
    active = {"ready", "in_progress", "review", "blocked"}
    tickets = [ticket for ticket in registry.get("tickets", []) if ticket.get("status") in active]
    tickets = sorted(tickets, key=ticket_sort_key)
    lines = [
        "# Board",
        "",
        f"Project: {config['project']['name']}",
        f"Updated: {now()}",
        "",
    ]
    for status in ["ready", "in_progress", "review", "blocked"]:
        grouped = [ticket for ticket in tickets if ticket.get("status") == status]
        lines.extend([f"## {status}", ""])
        lines.extend(ticket_line(ticket) for ticket in grouped)
        if not grouped:
            lines.append("- None")
        lines.append("")
    (tickets_dir(root) / "BOARD.md").write_text("\n".join(lines), encoding="utf-8")


def write_changelog(root: Path, registry: dict[str, Any]) -> None:
    done = [ticket for ticket in registry.get("tickets", []) if ticket.get("status") in {"done", "wont_do"}]
    done = sorted(done, key=lambda t: t.get("updated", ""), reverse=True)
    lines = ["# Ticket Changelog", "", f"Updated: {now()}", ""]
    for ticket in done:
        lines.append(f"- {ticket['updated']} [{ticket['id']}] {ticket['status']} - {ticket['title']}")
    if not done:
        lines.append("- No closed tickets yet.")
    (tickets_dir(root) / "CHANGELOG.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_current_sprint(root: Path, registry: dict[str, Any]) -> None:
    sprint = load_active_sprint(root)
    if sprint:
        sprint_ids = set(sprint.get("tickets", []))
        tickets = [ticket for ticket in registry.get("tickets", []) if ticket.get("id") in sprint_ids]
        lines = [
            f"# {sprint['name']}",
            "",
            f"Status: {sprint['status']}",
            f"Goal: {sprint['goal']}",
            f"Start: {sprint.get('start', '') or 'not set'}",
            f"End: {sprint.get('end', '') or 'not set'}",
            f"Updated: {now()}",
            "",
            "## Tickets",
            "",
        ]
        for ticket in sorted(tickets, key=ticket_sort_key):
            lines.append(ticket_line(ticket))
        if not tickets:
            lines.append("- No committed tickets.")
        lines.extend(["", "## Risks", "", sprint.get("risks", "None recorded."), "", "## Validation", "", sprint.get("validation", "Use each ticket's validation plan.")])
    else:
        tickets = [ticket for ticket in registry.get("tickets", []) if ticket.get("status") in ACTIVE_STATUSES]
        lines = ["# Current Sprint", "", f"Updated: {now()}", ""]
        for ticket in sorted(tickets, key=ticket_sort_key):
            lines.append(ticket_line(ticket))
        if not tickets:
            lines.append("- No active tickets.")
    report = tickets_dir(root) / "reports" / "current-sprint.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")


def sprints_dir(root: Path) -> Path:
    return tickets_dir(root) / "sprints"


def active_sprint_path(root: Path) -> Path:
    return sprints_dir(root) / "current.json"


def sprint_archive_path(root: Path, sprint: dict[str, Any]) -> Path:
    closed = sprint.get("closed", now())[:10]
    return sprints_dir(root) / f"{closed}-{slugify(sprint['name'])}.json"


def sprint_markdown_path(root: Path, sprint: dict[str, Any]) -> Path:
    return sprints_dir(root) / f"{slugify(sprint['name'])}.md"


def load_active_sprint(root: Path) -> dict[str, Any] | None:
    path = active_sprint_path(root)
    if not path.exists():
        return None
    return load_json(path, {})


def save_active_sprint(root: Path, sprint: dict[str, Any]) -> None:
    sprint["updated"] = now()
    write_json(active_sprint_path(root), sprint)
    write_sprint_markdown(root, sprint)


def ticket_lookup(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {ticket["id"]: ticket for ticket in registry.get("tickets", [])}


def ensure_ticket_ids(registry: dict[str, Any], ticket_ids: list[str]) -> None:
    by_id = ticket_lookup(registry)
    missing = [ticket_id for ticket_id in ticket_ids if ticket_id not in by_id]
    if missing:
        raise SystemExit(f"Ticket not found: {', '.join(missing)}")


def write_sprint_markdown(root: Path, sprint: dict[str, Any]) -> None:
    lines = [
        f"# {sprint['name']}",
        "",
        f"Status: {sprint['status']}",
        f"Goal: {sprint['goal']}",
        f"Start: {sprint.get('start', '') or 'not set'}",
        f"End: {sprint.get('end', '') or 'not set'}",
        f"Updated: {sprint.get('updated', now())}",
        "",
        "## Tickets",
        "",
    ]
    tickets = sprint.get("tickets", [])
    lines.extend(f"- {ticket_id}" for ticket_id in tickets)
    if not tickets:
        lines.append("- None")
    lines.extend(
        [
            "",
            "## Risks",
            "",
            sprint.get("risks", "None recorded."),
            "",
            "## Validation",
            "",
            sprint.get("validation", "Use each ticket's validation plan."),
            "",
            "## Close Summary",
            "",
            sprint.get("summary", "Open."),
            "",
            "## Carryover",
            "",
        ]
    )
    carryover = sprint.get("carryover", [])
    lines.extend(f"- {ticket_id}" for ticket_id in carryover)
    if not carryover:
        lines.append("- None")
    path = sprint_markdown_path(root, sprint)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_templates(root: Path) -> None:
    template_dir = tickets_dir(root) / "templates"
    template_dir.mkdir(parents=True, exist_ok=True)
    templates = {
        "bug.md": """# Bug Ticket Template

Use this template when broken behavior, regressions, crashes, bad data, or UI defects need to be tracked.

## Summary

One sentence describing the broken behavior.

## Expected Behavior

- What should happen?
- What does the user or system expect?

## Actual Behavior

- What happens instead?
- Include error text, screenshots, logs, or symptoms when useful.

## Reproduction Steps

1.
2.
3.

## Impact

- Severity: P0/P1/P2/P3/P4
- Affected users or workflows:
- Frequency:
- Regression: yes/no/unknown

## Suspected Area

- Module, route, screen, API, job, workflow, or system likely involved:
- Files already inspected:

## Acceptance Criteria

- [ ] The bug is fixed for the reported path.
- [ ] A regression check exists or the reason it cannot exist is documented.
- [ ] Related edge cases are covered or follow-up tickets exist.

## Validation Plan

- Automated command:
- Manual check:
- Data/log check:

## Agent Handoff

- Current hypothesis:
- What was tried:
- What the next agent should inspect first:
""",
        "feature.md": """# Feature Ticket Template

Use this template for new user-facing behavior, workflow improvements, or product capabilities.

## Summary

One sentence describing the outcome.

## User And Workflow

- User or actor:
- Current workflow:
- Desired workflow:
- Why this matters:

## Problem Or Opportunity

- What pain, gap, or goal does this address?
- What happens if this is not built?

## Scope

### In Scope

-

### Out Of Scope

-

## Acceptance Criteria

- [ ] User can...
- [ ] System handles...
- [ ] Error/empty/loading states are handled when relevant.

## UX And Content Notes

- Screens, routes, commands, copy, or interactions affected:
- Accessibility or responsive behavior:

## Data/API Notes

- Data needed:
- API or schema changes:
- Permissions/auth considerations:

## Dependencies

- Depends on:
- Blocks:
- External decisions:

## Validation Plan

- Automated command:
- Manual workflow:
- Screenshot or visual check:

## Agent Handoff

- Key files to inspect:
- Risks:
- Follow-up tickets:
""",
        "repo.md": """# Repo Ticket Template

Use this template for maintenance, build, CI, dependency, architecture, docs, setup, or agent-workflow changes.

## Summary

One sentence describing the repo improvement.

## Maintenance Value

- What does this improve?
- Who benefits?
- What gets easier, safer, faster, or clearer?

## Affected Systems

- Build:
- Tests:
- CI/CD:
- Dependencies:
- Docs:
- Local setup:
- Agent workflow:

## Current State

- What is happening now?
- What evidence shows this needs work?

## Target State

- What should be true after this ticket?
- What should not change?

## Risk And Rollback

- Risk level: low/medium/high
- Possible breakage:
- Rollback plan:

## Acceptance Criteria

- [ ] The repo improvement is implemented.
- [ ] Existing workflows still work.
- [ ] Docs or commands are updated when needed.
- [ ] Validation proves the repo remains healthy.

## Validation Plan

- Command:
- Manual check:
- CI check:

## Agent Handoff

- Files to inspect:
- Decisions to preserve:
- Follow-up cleanup:
""",
        "research.md": """# Research Ticket Template

Use this template when the output is understanding, a recommendation, a decision, or follow-up tickets rather than immediate implementation.

## Research Question

What question needs to be answered?

## Decision Needed

- What decision will this research unblock?
- Who or what depends on the answer?

## Context

- Why does this matter now?
- What is already known?
- What assumptions should be tested?

## Sources To Inspect

- Code paths:
- Docs:
- Issues/tickets:
- External references:
- People/user input:

## Options

### Option A

- Pros:
- Cons:
- Risks:

### Option B

- Pros:
- Cons:
- Risks:

## Recommendation

- Recommended path:
- Reason:
- Confidence:
- Open questions:

## Acceptance Criteria

- [ ] Relevant sources were inspected.
- [ ] Options and tradeoffs are documented.
- [ ] Recommendation or decision is recorded.
- [ ] Follow-up tickets exist for implementation work.

## Validation Plan

- How to verify the recommendation is grounded:
- Commands or experiments:

## Agent Handoff

- Sources inspected:
- Key findings:
- Next step:
""",
    }
    for name, text in templates.items():
        path = template_dir / name
        if not path.exists():
            path.write_text(text.rstrip() + "\n", encoding="utf-8")


def write_split_board_scaffold(root: Path, config: dict[str, Any]) -> None:
    locations = config["ticketing"].get("locations", {})
    for location in locations.values():
        (root / location).parent.mkdir(parents=True, exist_ok=True)

    working = root / locations["working"]
    if not working.exists():
        working.write_text(
            f"""# {config['project']['name']} Tickets

This file is the working ticket board. Deferred backlog tickets live in `docs/tickets/BACKLOG.md`. Completed tickets live in `docs/tickets/COMPLETED.md`.

## How Agents Should Use This File

1. Read agent instructions and ticket standards before changing code.
2. Pick or create one active ticket before implementation.
3. Keep ticket scope tight and split large tickets instead of hiding unrelated work.
4. Update product decisions and ADRs when durable decisions change.
5. When completing a ticket, update status, changed files, tests run, and the completed archive.

## Ticket Statuses

- `Backlog`: known work, not ready to implement.
- `Ready`: scope and acceptance criteria are clear enough to start.
- `In Progress`: currently being worked.
- `Blocked`: cannot continue without a decision or dependency.
- `Review`: implementation is done and awaiting review/final verification.
- `Complete`: shipped or accepted.

## Working Tickets

### In Progress

_None._

### Review

_None._

### Blocked

_None._

## Ready

### Bugs

_None._

### Features

_None._

### Security

_None._

### Design/UX

_None._

### Docs

_None._

### Chores

_None._
""",
            encoding="utf-8",
        )

    defaults = {
        "backlog": """# Backlog Tickets

Deferred tickets that are not ready for implementation.

## Backlog Rules

- Keep discovery, vague ideas, deferred improvements, and unscheduled work here.
- Do not move a ticket to `ready` until the outcome, acceptance criteria, owner area, and validation plan are clear.
- Create follow-up tickets for work discovered during implementation instead of expanding active ticket scope silently.
- Review backlog regularly during sprint planning or roadmap planning.

## Triage Questions

- What user, system, or repo problem does this solve?
- What happens if this is not done?
- What is the smallest useful outcome?
- What is out of scope?
- What validation would prove it is done?
- Does this block or depend on another ticket?
""",
        "completed": """# Completed Tickets

One-line archive records for completed or intentionally closed tickets.

## Archive Rules

- Keep completed ticket bodies out of the live working board.
- Preserve detailed implementation history in git and the ticket file.
- Record ticket id, completion date, status, and short outcome.
- Create follow-up tickets for deferred work before archiving.

## Records
""",
        "roadmap": """# Roadmap

Use this document to group ticket work into phases, releases, and product milestones. The roadmap should explain direction without replacing tickets.

## Roadmap Rules

- Roadmap items should link to ticket ids or ticket ranges.
- Keep implementation detail in tickets.
- Update this document when release goals, milestone order, or major scope changes.
- Do not treat the roadmap as a promise unless the user marks it committed.

## Now

Current committed work.

- Goal:
- Ticket range:
- Success criteria:
- Risks:

## Next

Likely upcoming work after the current focus.

- Goal:
- Ticket range:
- Success criteria:
- Dependencies:

## Later

Known work that is not yet scheduled.

- Goal:
- Ticket range:
- Open questions:

## Release Milestones

| Milestone | Goal | Ticket Range | Status | Notes |
| --- | --- | --- | --- | --- |
| M1 | Define the first milestone | T-0001+ | planning | Update during setup |

## Open Roadmap Questions

- Which work is required before the next release?
- Which tickets are user-facing vs repo/internal?
- Which risks need discovery before commitment?
- Which external dependencies can block delivery?
""",
        "decisions": """# Product Decisions

Use this document for durable product, architecture, workflow, and roadmap decisions. Tickets should link here when a decision affects future work.

## Decision Rules

- Record decisions that future agents should not rediscover.
- Include context, options, decision, consequences, and follow-up tickets.
- Keep secrets and private customer data out of decision records.
- Mark open questions separately from accepted decisions.

## Decision Template

```md
### DEC-0001: Title

Status: proposed | accepted | superseded
Date: YYYY-MM-DD
Related tickets: T-0000

Context:

Options:

Decision:

Consequences:

Follow-ups:
```

## Accepted Decisions

- None yet.

## Proposed Decisions

- None yet.

## Open Questions

- What decisions must be made before tickets can move from backlog to ready?
- Which product behaviors are intentionally out of scope?
- Which architecture choices should agents preserve?
""",
    }
    for key, content in defaults.items():
        path = root / locations[key]
        if not path.exists():
            path.write_text(content, encoding="utf-8")


def write_split_board_files(root: Path, config: dict[str, Any], registry: dict[str, Any]) -> None:
    locations = config["ticketing"].get("locations", {})
    if not locations:
        return
    for location in locations.values():
        (root / location).parent.mkdir(parents=True, exist_ok=True)

    tickets = sorted(registry.get("tickets", []), key=ticket_sort_key)
    project = config["project"]["name"]
    updated = now()

    working_lines = [
        f"# {project} Tickets",
        "",
        "This is the strict working board. Deferred tickets live in `docs/tickets/BACKLOG.md`; completed tickets live in `docs/tickets/COMPLETED.md`.",
        "",
        f"Updated: {updated}",
        "",
        "## Working Tickets",
        "",
    ]
    for status, heading in STRICT_WORKING_SECTIONS:
        grouped = [ticket for ticket in tickets if ticket.get("status") == status]
        working_lines.extend([f"### {heading}", ""])
        working_lines.extend(ticket_line(ticket) for ticket in grouped)
        if not grouped:
            working_lines.append("_None._")
        working_lines.append("")
    (root / locations["working"]).write_text("\n".join(working_lines), encoding="utf-8")

    backlog = [ticket for ticket in tickets if ticket.get("status") in {"inbox", "backlog"}]
    backlog_lines = ["# Backlog Tickets", "", f"Updated: {updated}", ""]
    for status in ["inbox", "backlog"]:
        grouped = [ticket for ticket in backlog if ticket.get("status") == status]
        backlog_lines.extend([f"## {display_status(status)}", ""])
        backlog_lines.extend(ticket_line(ticket) for ticket in grouped)
        if not grouped:
            backlog_lines.append("_None._")
        backlog_lines.append("")
    (root / locations["backlog"]).write_text("\n".join(backlog_lines), encoding="utf-8")

    complete = [ticket for ticket in tickets if ticket.get("status") in {"done", "wont_do"}]
    complete_lines = ["# Completed Tickets", "", f"Updated: {updated}", ""]
    for ticket in sorted(complete, key=lambda t: t.get("updated", ""), reverse=True):
        complete_lines.append(f"- {ticket.get('updated', '')} [{ticket['id']}] {display_status(ticket['status'])} - {ticket['title']}")
    if not complete:
        complete_lines.append("_No completed tickets yet._")
    complete_lines.append("")
    (root / locations["completed"]).write_text("\n".join(complete_lines), encoding="utf-8")


def seed_ticket(root: Path, config: dict[str, Any], registry: dict[str, Any]) -> None:
    if registry.get("tickets"):
        return
    prefix = config["ticketing"]["prefix"]
    created = now()
    ticket = {
        "id": f"{prefix}-0001",
        "title": "Establish project ticketing workflow",
        "type": "repo",
        "status": "ready",
        "priority": "P2",
        "severity": "",
        "area": "repo",
        "owner": "agent",
        "estimate": "S",
        "risk": "low",
        "labels": "setup,agent-workflow",
        "depends_on": "",
        "blocks": "",
        "source": "init",
        "created": created,
        "updated": created,
        "body": {
            "context": "The repo needs a durable local ticketing workflow that agents can use before and during implementation.",
            "acceptance": "- [ ] Review `.tickets/config.json`\n- [ ] Adjust areas and validation commands\n- [ ] Confirm when agents should create tickets",
            "notes": "This is the seed ticket created during initialization.",
            "validation": "- [ ] Run `python3 scripts/ticketctl.py doctor --root .` from the skill path or equivalent installed path.",
            "handoff": "Start by reviewing config and updating project-specific fields.",
        },
        "activity": [f"{created} initialized ticketing system."],
    }
    ticket["file"] = os.path.relpath(ticket_file(root, ticket), root)
    registry["tickets"].append(ticket)
    registry["next_number"] = 2


def cmd_init(args: argparse.Namespace) -> None:
    root = root_path(args)
    root.mkdir(parents=True, exist_ok=True)
    td = tickets_dir(root)
    td.mkdir(parents=True, exist_ok=True)
    (td / "tickets").mkdir(exist_ok=True)
    (td / "reports").mkdir(exist_ok=True)
    (td / "sprints").mkdir(exist_ok=True)
    (td / "sync").mkdir(exist_ok=True)

    config = default_config(root, args.profile)
    if args.interactive:
        config["project"]["name"] = prompt("Project name", config["project"]["name"])
        config["project"]["mission"] = prompt("Project mission", config["project"]["mission"])
        config["ticketing"]["prefix"] = prompt("Ticket prefix", config["ticketing"]["prefix"]).upper()
        config["ticketing"]["default_priority"] = prompt("Default priority", config["ticketing"]["default_priority"]).upper()
        commands = prompt("Validation commands, comma-separated", ", ".join(config["validation"]["commands"]))
        config["validation"]["commands"] = [item.strip() for item in commands.split(",") if item.strip()]
        areas = prompt("Areas, comma-separated", ", ".join(config["ticketing"]["areas"]))
        config["ticketing"]["areas"] = [item.strip() for item in areas.split(",") if item.strip()]

    if config_path(root).exists() and not args.force:
        raise SystemExit(".tickets/config.json already exists. Use --force to overwrite config.")

    write_json(config_path(root), config)
    registry = load_registry(root)
    registry.setdefault("created", now())
    registry.setdefault("next_number", 1)
    registry.setdefault("tickets", [])
    seed_ticket(root, config, registry)
    save_registry(root, registry)
    write_templates(root)
    if config["ticketing"].get("layout") == "split-board":
        write_split_board_scaffold(root, config)
    decisions = td / "DECISIONS.md"
    if not decisions.exists():
        decisions.write_text("# Decisions\n\n- No decisions recorded yet.\n", encoding="utf-8")
    sync_files(root)
    print(f"Initialized ticketing system in {td}")


def next_id(config: dict[str, Any], registry: dict[str, Any]) -> str:
    prefix = config["ticketing"]["prefix"]
    number = int(registry.get("next_number", 1))
    registry["next_number"] = number + 1
    return f"{prefix}-{number:04d}"


def cmd_new(args: argparse.Namespace) -> None:
    root = root_path(args)
    config = load_config(root)
    registry = load_registry(root)
    validate_choice(args.type, TYPES, "type")
    validate_choice(args.priority, PRIORITIES, "priority")
    status = args.status or config["ticketing"]["default_status"]
    validate_choice(status, STATUSES, "status")
    created = now()
    ticket = {
        "id": next_id(config, registry),
        "title": args.title,
        "type": args.type,
        "status": status,
        "priority": args.priority,
        "severity": args.severity or "",
        "area": args.area,
        "owner": args.owner or "agent",
        "estimate": args.estimate or "",
        "risk": args.risk or "medium",
        "labels": args.labels or "",
        "depends_on": args.depends_on or "",
        "blocks": args.blocks or "",
        "source": args.source or "agent",
        "created": created,
        "updated": created,
        "body": {
            "context": args.context or "Context to be expanded.",
            "acceptance": args.acceptance or "- [ ] Acceptance criteria to be confirmed.",
            "notes": args.notes or "Implementation notes to be added.",
            "validation": args.validation or "- [ ] Validation plan to be confirmed.",
            "handoff": args.handoff or "No handoff notes yet.",
        },
        "activity": [f"{created} created by ticketctl."],
    }
    ticket["file"] = os.path.relpath(ticket_file(root, ticket), root)
    registry["tickets"].append(ticket)
    save_registry(root, registry)
    sync_files(root)
    print(f"Created {ticket['id']} {ticket['file']}")


def find_ticket(registry: dict[str, Any], ticket_id: str) -> dict[str, Any]:
    for ticket in registry.get("tickets", []):
        if ticket.get("id") == ticket_id:
            return ticket
    raise SystemExit(f"Ticket not found: {ticket_id}")


def cmd_list(args: argparse.Namespace) -> None:
    root = root_path(args)
    ensure_initialized(root)
    registry = load_registry(root)
    tickets = registry.get("tickets", [])
    if args.status:
        tickets = [ticket for ticket in tickets if ticket.get("status") == args.status]
    if args.type:
        tickets = [ticket for ticket in tickets if ticket.get("type") == args.type]
    if args.area:
        tickets = [ticket for ticket in tickets if ticket.get("area") == args.area]
    for ticket in sorted(tickets, key=ticket_sort_key):
        print(f"{ticket['id']}\t{ticket['status']}\t{ticket['priority']}\t{ticket['type']}\t{ticket['area']}\t{ticket['title']}")


def cmd_next(args: argparse.Namespace) -> None:
    root = root_path(args)
    ensure_initialized(root)
    registry = load_registry(root)
    candidates = [
        ticket for ticket in registry.get("tickets", [])
        if ticket.get("status") in {"ready", "backlog", "inbox"} and not ticket.get("depends_on")
    ]
    if not candidates:
        print("No ready tickets found.")
        return
    ticket = sorted(candidates, key=ticket_sort_key)[0]
    print(f"{ticket['id']}\t{ticket['priority']}\t{ticket['type']}\t{ticket['area']}\t{ticket['title']}\t{ticket['file']}")


def cmd_move(args: argparse.Namespace) -> None:
    root = root_path(args)
    ensure_initialized(root)
    validate_choice(args.status, STATUSES, "status")
    registry = load_registry(root)
    ticket = find_ticket(registry, args.ticket_id)
    old = ticket["status"]
    stamp = now()
    ticket["status"] = args.status
    ticket["updated"] = stamp
    ticket.setdefault("activity", []).append(f"{stamp} moved from {old} to {args.status}.")
    save_registry(root, registry)
    sync_files(root)
    print(f"Moved {ticket['id']} {old} -> {args.status}")


def cmd_comment(args: argparse.Namespace) -> None:
    root = root_path(args)
    ensure_initialized(root)
    registry = load_registry(root)
    ticket = find_ticket(registry, args.ticket_id)
    stamp = now()
    ticket["updated"] = stamp
    ticket.setdefault("activity", []).append(f"{stamp} {args.message}")
    save_registry(root, registry)
    sync_files(root)
    print(f"Updated {ticket['id']}")


def cmd_close(args: argparse.Namespace) -> None:
    root = root_path(args)
    ensure_initialized(root)
    registry = load_registry(root)
    ticket = find_ticket(registry, args.ticket_id)
    stamp = now()
    status = "wont_do" if args.wont_do else "done"
    ticket["status"] = status
    ticket["updated"] = stamp
    ticket.setdefault("body", {})["closure"] = args.resolution
    ticket.setdefault("activity", []).append(f"{stamp} closed as {status}: {args.resolution}")
    save_registry(root, registry)
    sync_files(root)
    print(f"Closed {ticket['id']} as {status}")


def cmd_sync(args: argparse.Namespace) -> None:
    root = root_path(args)
    ensure_initialized(root)
    sync_files(root)
    print("Synced ticket files.")


def cmd_sprint_start(args: argparse.Namespace) -> None:
    root = root_path(args)
    ensure_initialized(root)
    registry = load_registry(root)
    if active_sprint_path(root).exists() and not args.force:
        raise SystemExit("An active sprint already exists. Close it first or use --force.")
    ticket_ids = csv_items(args.tickets)
    ensure_ticket_ids(registry, ticket_ids)
    stamp = now()
    sprint = {
        "name": args.name,
        "goal": args.goal,
        "status": "active",
        "start": args.start or stamp[:10],
        "end": args.end or "",
        "tickets": ticket_ids,
        "risks": args.risks or "None recorded.",
        "validation": args.validation or "Use each ticket's validation plan.",
        "created": stamp,
        "updated": stamp,
    }
    save_active_sprint(root, sprint)
    sync_files(root)
    print(f"Started sprint: {sprint['name']}")


def cmd_sprint_add(args: argparse.Namespace) -> None:
    root = root_path(args)
    ensure_initialized(root)
    sprint = load_active_sprint(root)
    if not sprint:
        raise SystemExit("No active sprint found. Run: ticketctl.py sprint start ...")
    registry = load_registry(root)
    ticket_ids = csv_items(args.tickets)
    ensure_ticket_ids(registry, ticket_ids)
    current = list(dict.fromkeys([*sprint.get("tickets", []), *ticket_ids]))
    sprint["tickets"] = current
    save_active_sprint(root, sprint)
    sync_files(root)
    print(f"Added {len(ticket_ids)} ticket(s) to sprint: {sprint['name']}")


def cmd_sprint_status(args: argparse.Namespace) -> None:
    root = root_path(args)
    ensure_initialized(root)
    sync_files(root)
    sprint = load_active_sprint(root)
    if not sprint:
        print("No active sprint.")
        return
    print(f"{sprint['name']}\t{sprint['status']}\t{sprint['goal']}\t{','.join(sprint.get('tickets', []))}")


def cmd_sprint_close(args: argparse.Namespace) -> None:
    root = root_path(args)
    ensure_initialized(root)
    sprint = load_active_sprint(root)
    if not sprint:
        raise SystemExit("No active sprint found.")
    sprint["status"] = "closed"
    sprint["closed"] = now()
    sprint["summary"] = args.summary
    sprint["carryover"] = csv_items(args.carryover)
    write_sprint_markdown(root, sprint)
    archive = sprint_archive_path(root, sprint)
    write_json(archive, sprint)
    active_sprint_path(root).unlink()
    sync_files(root)
    print(f"Closed sprint: {sprint['name']}")


def operating_docs(project: str, mode: str) -> dict[str, str]:
    docs = {
        "AGENTS.md": f"""# Agent Instructions

This repo uses Agent Ticketing OS. Treat the ticket trail as the source of truth for agent work: pick one active ticket, keep the status current, record validation, and leave the next agent enough context to continue without re-discovery.

## Non-Negotiable Rules

- Do not start meaningful implementation without a ticket unless the user explicitly says the work is too small for one.
- Do not work on multiple unrelated outcomes under one ticket.
- Do not silently expand scope. Create linked follow-up tickets for discovered work.
- Do not store secrets, credentials, private customer data, tokens, or private URLs in tickets or docs.
- Do not mark work done without validation evidence or a clear reason validation could not run.
- Do not overwrite existing project instructions unless the user explicitly asks for replacement.

## Standard Agent Loop

1. Read `.tickets/BOARD.md`, `.tickets/BACKLOG.md`, and the active ticket.
2. If no active ticket exists, create or select one before implementation.
3. Confirm the ticket has context, acceptance criteria, scope, and validation.
4. Move the ticket to `in_progress` when work begins.
5. Make the smallest coherent change that satisfies the ticket.
6. Update the ticket with changed files, decisions, commands run, and validation results.
7. Move the ticket to `review`, `done`, or `blocked` based on the current state.
8. Run ticket sync or board refresh before handoff.

## Before Editing Files

- Identify the active ticket id.
- Read any repo-specific docs under `docs/`.
- Check the current branch and avoid protected branches for implementation work.
- Inspect nearby code and existing conventions before adding new patterns.
- Decide which validation command should prove the change.

## During Implementation

- Keep commits and file edits aligned to the active ticket.
- Prefer existing project patterns over new abstractions.
- Update tests, docs, routes, env examples, and setup instructions when behavior changes.
- If the work reveals a separate bug or feature, create a follow-up ticket and continue the current ticket only if safe.

## Handoff Requirements

Every handoff must include:

- Ticket id and status.
- Summary of what changed.
- Files touched or inspected.
- Commands run and results.
- Known risks, blockers, or skipped validation.
- Next recommended action.
""",
        "docs/TICKET_STANDARDS.md": f"""# Ticket Standards

Every meaningful repo change in {project} should map to one focused ticket. A ticket is not just a task title; it is the working contract between the user, the agent, and the next person who touches the repo.

## Ticket Purpose

Tickets exist to:

- Define the outcome before implementation starts.
- Keep scope visible.
- Preserve the reasoning and validation trail.
- Make work resumable by another agent.
- Create a durable history in git.

## Required Ticket Fields

- Context
- Type
- Status
- Priority
- Area
- Acceptance criteria
- Validation plan
- Implementation notes
- Activity log
- Agent handoff

## Ticket Types

- `feature`: new user-facing behavior.
- `bug`: broken behavior, regression, data loss, error, or UI defect.
- `change`: intentional adjustment to existing behavior.
- `repo`: build, CI, docs, dependencies, architecture, or maintenance.
- `research`: investigation where the output may be a decision or follow-up ticket.
- `design`: UX, UI, visual system, interaction, or content structure.
- `security`: auth, permissions, secrets, injection, dependency, or data exposure risk.

## Status Rules

- `inbox`: captured but not clarified.
- `backlog`: valid but not ready to start.
- `ready`: clear enough for an agent to begin.
- `in_progress`: actively being worked.
- `review`: implementation is ready for review or final verification.
- `blocked`: waiting on an external decision, access, dependency, or failing prerequisite.
- `done`: completed and validated.
- `wont_do`: intentionally closed without implementation.

## Priority Rules

- `P0`: outage, data loss, security exposure, or unusable core workflow.
- `P1`: urgent user-impacting issue or high-value work needed soon.
- `P2`: normal planned work.
- `P3`: useful cleanup or polish.
- `P4`: idea parking lot.

## Ready Criteria

A ticket may move to `ready` only when it has:

- A clear problem or opportunity.
- Observable acceptance criteria.
- A likely area or module.
- Known dependencies or an explicit "none".
- A validation plan.
- Risk notes for migrations, data, auth, payments, releases, or user-visible behavior.

## Bug Intake Checklist

Bug tickets should capture:

- Expected behavior.
- Actual behavior.
- Reproduction steps.
- Affected environment.
- Severity and user impact.
- Suspected area.
- Whether this is a regression.
- Validation needed to prove the fix.

## Feature Intake Checklist

Feature tickets should capture:

- User or actor.
- Workflow being improved.
- Success criteria.
- Out-of-scope items.
- UX/content implications.
- Data/API implications.
- Analytics, logging, or notification needs.
- Validation and review expectations.

## Splitting Rules

Split a ticket when:

- It touches unrelated areas.
- It needs separate review or validation paths.
- It mixes refactor work with behavior changes.
- It contains work that can ship independently.
- It becomes too large for a clear handoff.

Do not split merely because several files are involved. One coherent outcome can touch multiple files.

## Activity Log Rules

Keep activity entries factual and compact:

- Files changed.
- Commands run.
- Decisions made.
- Blockers found.
- Follow-up tickets created.

Do not paste long command output. Summarize the result and keep only the important failure text.

## Closure Rules

Closing a ticket requires:

- Resolution summary.
- Validation evidence or skipped-validation reason.
- Follow-up tickets for deferred work.
- Updated docs when setup, routes, env vars, commands, or workflows changed.
""",
        "docs/DEFINITION_OF_DONE.md": """# Definition Of Done

Use this checklist before moving a ticket to `done`.

## Universal Done Criteria

- The change maps to one active ticket.
- Acceptance criteria are satisfied, or gaps are clearly documented.
- No unrelated behavior is included.
- The ticket activity log includes changed files, decisions, and validation.
- Follow-up tickets exist for deferred work.
- `git diff --check` passes.
- The handoff notes explain what changed and what to watch next.

## Validation Criteria

At least one of these must be true:

- Automated tests passed.
- Lint/typecheck/build passed.
- Manual verification steps are recorded.
- Screenshots or visual checks are recorded when UI changed.
- Validation was not possible and the reason is documented.

Skipped validation must include:

- Why it was skipped.
- What risk remains.
- What command or manual check should run later.

## Code Quality Criteria

- Code follows local patterns.
- New abstractions are justified by real duplication or complexity.
- Error handling covers expected failure modes.
- User-facing copy is clear and actionable.
- Logging does not expose secrets or private data.
- Dead code introduced by the change is removed.

## Documentation Criteria

Update docs when the change affects:

- Setup commands.
- Environment variables.
- Public APIs.
- Routes or navigation.
- Database schema or migrations.
- Release process.
- Security expectations.
- Agent workflow.

## Ticket-Specific Done Criteria

### Bug

- Reproduction is understood or documented as unknown.
- Fix addresses the cause, not only the symptom.
- Regression validation is recorded.
- User impact is summarized.

### Feature

- Acceptance criteria are demonstrably met.
- Edge cases are handled or ticketed.
- UX/content implications are reviewed.
- Any follow-up improvements are ticketed.

### Repo/Chore

- Tooling or workflow impact is documented.
- Rollback path is clear for risky changes.
- CI or local validation proves the repo still works.

### Security

- Sensitive details are not exposed in tickets or logs.
- Risk and mitigation are documented.
- Validation covers the security boundary involved.

## Done Is Not

- "Code compiles on my machine" without recording the command.
- "Looks good" without acceptance criteria.
- Closing a ticket while known related work is hidden in the implementation.
- Leaving the next agent to rediscover what happened.
""",
        "docs/BRANCH_WORKFLOW.md": """# Branch Workflow

Use branches to keep implementation work reviewable, reversible, and tied to tickets.

## Branch Policy

- Work from the repo's default integration branch unless the project says otherwise.
- Avoid implementing directly on protected branches.
- Keep one branch aligned to one ticket or one tightly related ticket group.
- Do not mix unrelated cleanup with feature or bug work.
- Mention ticket ids in branch names when practical.

## Naming Convention

Preferred branch names:

```text
feature/T-0004-login-redirect
bugfix/T-0012-settings-crash
repo/T-0020-ci-cache
security/T-0031-token-scope
```

If the host repo has an existing convention, follow it and keep the ticket id visible.

## Before Creating A Branch

- Confirm the active ticket id.
- Check current branch and uncommitted changes.
- Pull or fetch when the user asks or repo workflow requires it.
- Make sure the ticket is `ready` or document why work is starting early.

## During Branch Work

- Keep branch changes inside ticket scope.
- Do not include generated dependency folders, local env files, secrets, or unrelated formatting churn.
- Update ticket activity when important files or decisions change.
- Create follow-up tickets for discovered work.

## Blocked Branches

If work becomes blocked:

- Move the ticket to `blocked`.
- Record the blocker and exact missing input.
- Leave the branch in a resumable state.
- Do not keep guessing across security, data, billing, auth, or migration uncertainty.

## Ready For Review

Before asking for review:

- Move the ticket to `review`.
- Record validation.
- Summarize changed files.
- Confirm known risks and follow-ups.
- Ensure docs are updated when behavior or workflow changed.
""",
        "docs/AGENT_COMMIT_WORKFLOW.md": """# Agent Commit Workflow

Commit intentionally. A commit should tell the next reader what changed and why.

## Commit Rules

- Commit only cohesive changes.
- Keep commits aligned to the active ticket.
- Mention ticket ids when practical.
- Do not commit secrets, local env files, generated dependency folders, caches, or unrelated churn.
- Run configured validation before asking for merge or handoff.

## Commit Message Format

Preferred:

```text
T-0004 Fix login redirect after password reset
```

For repo-only work:

```text
T-0021 Update CI test workflow
```

If the repo has a conventional commit policy, use it and include the ticket id:

```text
fix(auth): handle password reset redirect (T-0004)
```

## Before Committing

- Review `git diff`.
- Confirm the diff matches the ticket scope.
- Remove debugging output and temporary files.
- Run validation or record why it could not run.
- Update the ticket with changed files and validation.

## Commit Body Guidance

Use a body when the change needs context:

```text
T-0004 Fix login redirect after password reset

- Preserves return URL through reset flow
- Adds regression coverage for expired reset token
- Updates ticket validation with npm test result
```

## When Not To Commit

Do not commit when:

- The user asked only for analysis.
- Tests are failing and the failure is not documented.
- The branch contains unrelated user changes.
- The active ticket does not match the diff.
- Sensitive data appears in the patch.

## Handoff Without Commit

If the agent cannot commit, the handoff must include:

- Current branch.
- Changed files.
- Commands run.
- Validation status.
- Remaining work.
""",
        "docs/REVIEW_CHECKLIST.md": """# Review Checklist

Use this checklist before handoff, commit, PR, or merge.

## Blockers

Stop and resolve before review if:

- No active ticket exists for meaningful work.
- The diff includes unrelated changes.
- Secrets, tokens, private customer data, or local credentials are present.
- Validation was skipped without a reason.
- The work changes auth, permissions, payments, data, migrations, or release behavior without risk notes.
- The ticket status does not match reality.

## Ticket Review

- Ticket id is clear.
- Ticket type, priority, area, and status are accurate.
- Acceptance criteria are met or gaps are documented.
- Activity log names changed files and commands run.
- Follow-up tickets exist for deferred work.
- Handoff notes are short and actionable.

## Code Review

- Code follows local conventions.
- Error paths are handled.
- Edge cases are covered or ticketed.
- No new dead code or unused files were introduced.
- No unrelated formatting churn.
- Comments explain non-obvious decisions, not obvious syntax.

## Test And Validation Review

- Relevant automated tests ran.
- Lint/typecheck/build ran when configured.
- Manual QA is recorded for UI or workflow changes.
- Screenshots are captured or noted when visual output changed.
- Known failing tests are explained.

## Documentation Review

Docs are updated if the change affects:

- Setup or install steps.
- Commands.
- Environment variables.
- Routes, APIs, or schemas.
- Product behavior.
- Security posture.
- Agent workflow.

## Handoff Review

The final handoff should include:

- What changed.
- Why it changed.
- How it was validated.
- What remains.
- Any risks or rollback notes.
""",
    }
    if mode == "deep":
        docs.update(
            {
                "CLAUDE.md": """# Claude Code Project Memory

Use Agent Ticketing OS for repo work.

## Operating Rules

- Prefer natural language requests, but keep ticket records current.
- Use one ticket per coherent outcome.
- Move tickets as the work state changes.
- Use planning mode for high-risk, multi-file, security, data, release, or architecture changes.
- Keep handoff notes short, specific, and operational.

## Claude Code Notes

- Direct plugin skill calls use `/agent-ticketing-os:skill-name`.
- `@` references files; it does not invoke plugin skills.
- If a workflow feature such as planning or goals is available, use it for sprints and larger work before editing files.

## Before Final Response

- Confirm ticket status.
- Summarize changed files and validation.
- Mention skipped validation and risk.
- Mention follow-up tickets.
""",
                "docs/AGENT_QA_GUIDE.md": """# Agent QA Guide

QA is the evidence that a ticket is actually done. Record enough detail that another agent or human can trust the result without rerunning the entire investigation.

## QA Principles

- Validate the behavior the ticket promised, not just the file you changed.
- Prefer existing project commands over invented checks.
- Record commands exactly as run.
- Summarize important output; do not paste long logs.
- If validation cannot run, explain why and what should run later.

## Validation Levels

### Level 0: Static Review

Use for docs-only or planning-only work.

- Read changed files.
- Check formatting.
- Confirm links, paths, and command names.
- Run `git diff --check` when available.

### Level 1: Targeted Validation

Use for focused code changes.

- Run the smallest relevant test.
- Run related lint/typecheck if configured.
- Manually exercise the changed path when automated tests do not cover it.

### Level 2: Broad Validation

Use for shared code, data, auth, routing, API, CI, build, or release changes.

- Run test suite or relevant package tests.
- Run lint/typecheck/build when configured.
- Check migrations or generated artifacts.
- Review backward compatibility and rollback.

### Level 3: Release Validation

Use before release, deployment, or external handoff.

- Run full configured validation.
- Review completed tickets.
- Confirm release notes or changelog.
- Confirm rollback plan.
- Verify environment and secret requirements without exposing secret values.

## UI QA

For UI changes, record:

- Viewport or device checked.
- Browser/platform checked.
- Main happy path.
- Empty, loading, error, and overflow states when relevant.
- Screenshots or notes for visual changes.

## API QA

For API changes, record:

- Endpoint or method checked.
- Request shape.
- Response shape.
- Auth/permission behavior.
- Error cases.
- Backward compatibility notes.

## Data/Migration QA

For data changes, record:

- Migration command.
- Rollback or restore approach.
- Data risk.
- Backfill or cleanup requirement.
- Verification query or check.

## QA Log Template

```text
Validation:
- Command: <exact command>
  Result: passed/failed/skipped
  Notes: <short summary>
- Manual check: <workflow>
  Result: passed/failed/skipped
  Notes: <short summary>
```

## Skipped Validation Template

```text
Validation skipped:
- Reason:
- Risk:
- Recommended next command:
- Follow-up ticket:
```
""",
                "docs/AGENT_HANDOFF_TEMPLATE.md": """# Agent Handoff Template

Use this template when pausing, handing off, opening review, or closing a ticket.

## Ticket

- ID:
- Title:
- Status:
- Branch:
- Related tickets:

## Outcome

- What changed:
- Why it changed:
- User-visible impact:

## Scope

- In scope:
- Out of scope:
- Follow-up tickets:

## Files Touched

```text
path/to/file - reason
```

## Files Inspected

```text
path/to/file - what was learned
```

## Decisions Made

- Decision:
  - Reason:
  - Alternatives considered:
  - Follow-up:

## Validation

- Command:
  - Result:
  - Notes:
- Manual check:
  - Result:
  - Notes:
- Skipped validation:
  - Reason:
  - Risk:
  - Recommended next step:

## Risks And Blockers

- Risk:
- Blocker:
- Mitigation:

## Next Agent Should

1.
2.
3.

## Final Notes

- Anything surprising:
- Anything intentionally deferred:
- Anything the user should decide:
""",
                "docs/RELEASE_RUNBOOK.md": """# Release Runbook

Use this runbook when preparing a release, deployment, client handoff, or milestone close.

## Release Intake

- Release name:
- Target date:
- Owner:
- Environment:
- Included tickets:
- Excluded tickets:
- Risk level:

## Pre-Release Checklist

- Completed tickets reviewed.
- Blocked tickets are not accidentally included.
- Validation evidence exists for included tickets.
- Release notes or changelog updated.
- Migrations and env var changes are documented.
- Rollback plan exists for risky changes.
- Security-sensitive changes have explicit review notes.
- User-facing behavior changes are summarized.

## Ticket Review

For each included ticket, confirm:

- Status is `done` or explicitly approved for release.
- Acceptance criteria are met.
- Validation is recorded.
- Follow-ups exist for deferred work.
- User-facing changes are included in release notes.

## Validation Matrix

```text
Area:
Command/manual check:
Result:
Owner:
Notes:
```

## Rollback Plan

- What can be reverted:
- What cannot be safely reverted:
- Data restore requirement:
- Feature flag or config rollback:
- Owner for rollback decision:

## Release Notes Template

```md
## Added

## Changed

## Fixed

## Security

## Known Issues

## Validation
```

## Post-Release

- Monitor logs/errors.
- Confirm critical workflows.
- Move release tickets to completed archive.
- Create follow-up tickets for issues found after release.
""",
                "docs/SECURITY_AGENT_PROTOCOL.md": """# Security Agent Protocol

Security-sensitive work needs stricter handling than ordinary tickets.

## Security-Sensitive Areas

Treat these as security work:

- Authentication.
- Authorization and permissions.
- Secrets and token handling.
- PII, customer data, or private business data.
- File upload/download.
- Webhooks.
- Payment or billing flows.
- Dependency vulnerabilities.
- Injection, XSS, SSRF, CSRF, path traversal, deserialization.
- Logging and analytics that may expose sensitive data.

## Handling Rules

- Do not paste secrets into tickets, logs, docs, commits, or PR text.
- Refer to secret names, not values.
- Do not weaken auth, validation, or permission checks to make tests pass.
- Do not add broad permissions without documenting why.
- Do not store sensitive reproduction data in repo files.
- Create a `security` ticket for discovered risks.

## Security Ticket Requirements

- Affected boundary.
- Impact.
- Exploit preconditions.
- Risk level.
- Mitigation approach.
- Validation plan.
- Residual risk.

## Validation Expectations

Security validation should include:

- Positive case: allowed user/action succeeds.
- Negative case: disallowed user/action fails.
- Input validation or sanitization check.
- No sensitive values in logs or errors.
- Dependency or configuration check when relevant.

## Disclosure And Handoff

If a vulnerability may already exist:

- Keep details minimal in broad docs.
- Put sensitive details only where the project expects them.
- Ask the user before creating public issues.
- Record that a security-sensitive follow-up exists without exposing exploit details.
""",
                ".github/pull_request_template.md": """# Pull Request

## Ticket

- Ticket:
- Ticket status:
- Related tickets:
- Sprint/milestone:

## Summary

- What changed:
- Why it changed:
- User or system impact:

## Scope

### In Scope

-

### Out Of Scope

-

## Changes Made

-

## Validation

- [ ] Tests:
- [ ] Lint:
- [ ] Typecheck:
- [ ] Build:
- [ ] Manual QA:
- [ ] Screenshot or visual check:
- [ ] Migration/data check:
- [ ] Security/permission check:
- [ ] Not run, reason:

## Acceptance Criteria

- [ ] Ticket acceptance criteria are satisfied.
- [ ] Gaps are documented.
- [ ] Deferred work has follow-up tickets.

## Risk And Rollback

- Risk level: low/medium/high
- Risk summary:
- Rollback plan:
- Data or migration risk:
- Feature flag/config rollback:

## Security And Privacy

- [ ] No secrets, tokens, credentials, private customer data, or private URLs are included.
- [ ] Auth/permission changes are documented.
- [ ] Logs/errors do not expose sensitive data.
- [ ] Security-sensitive behavior was validated or a follow-up ticket exists.

## Documentation

- [ ] User-facing docs updated.
- [ ] Developer/setup docs updated.
- [ ] Agent/ticketing docs updated.
- [ ] No docs needed, reason:

## Review Notes

- Files/areas needing close review:
- Known tradeoffs:
- Questions for reviewer:

## Handoff

- Next step after merge:
- Monitoring or follow-up:
- Release note:

## Follow-ups

-
""",
            }
        )
    return docs


def cmd_operating_init(args: argparse.Namespace) -> None:
    root = root_path(args)
    ensure_initialized(root)
    config = load_config(root)
    created: list[str] = []
    skipped: list[str] = []
    docs = operating_docs(config["project"]["name"], args.mode)
    for relative, content in docs.items():
        if write_if_missing(root / relative, content, force=args.force):
            created.append(relative)
        else:
            skipped.append(relative)
    marker = {
        "mode": args.mode,
        "created": created,
        "skipped_existing": skipped,
        "updated": now(),
    }
    write_json(tickets_dir(root) / "operating.json", marker)
    print(f"Operating docs created: {len(created)}; skipped existing: {len(skipped)}")


def sync_hook_doc(provider: str, mode: str, external_project: str) -> str:
    external_label = external_project or "not configured"
    command_name = {
        "github": "GitHub Issues",
        "jira": "Jira",
        "linear": "Linear",
        "custom": "custom tracker",
    }[provider]
    return f"""# {command_name} Sync Hook

Provider: `{provider}`
Mode: `{mode}`
External project: `{external_label}`

## Contract

- Local tickets keep implementation notes, validation, decisions, and agent handoffs.
- The external tracker keeps collaboration status, assignment, stakeholder comments, and cross-team visibility.
- Every synced local ticket stores external ids in ticket metadata or `.tickets/sync/{provider}.json`.
- Sync must never overwrite local or external changes silently.

## MCP Expectations

When an MCP connector is available, the agent should:

1. Read local `.tickets/REGISTRY.json`.
2. Read external issues from {command_name}.
3. Match by stored external id first, then by ticket id in title/body.
4. Propose conflict resolution before writing either side.
5. Record sync decisions in `.tickets/DECISIONS.md` or the affected ticket activity log.

## Write Policy

- `local-first`: local tickets are source of truth; external issues mirror state.
- `hybrid`: local implementation detail and external collaboration state are both authoritative in their lanes.
- `external-first`: external tracker controls planning state; local tickets keep execution detail.
"""


def cmd_sync_hooks(args: argparse.Namespace) -> None:
    root = root_path(args)
    config = load_config(root)
    validate_choice(args.provider, SYNC_PROVIDERS, "provider")
    validate_choice(args.mode, SYNC_MODES, "mode")
    sync_root = tickets_dir(root) / "sync"
    provider_config = {
        "provider": args.provider,
        "mode": args.mode,
        "external_project": args.external_project or "",
        "enabled": True,
        "mcp_server": args.mcp_server or args.provider,
        "id_field": f"{args.provider}_id",
        "updated": now(),
    }
    write_json(sync_root / f"{args.provider}.json", provider_config)
    write_if_missing(
        sync_root / "README.md",
        "# External Tracker Sync\n\nProvider hook files describe how agents should sync local tickets with external issue trackers when MCP tools are available.\n",
    )
    write_if_missing(sync_root / f"{args.provider}-mcp.md", sync_hook_doc(args.provider, args.mode, args.external_project or ""), force=True)
    config.setdefault("sync", {})[args.provider] = provider_config
    write_json(config_path(root), config)
    print(f"Configured {args.provider} sync hook in {sync_root}")


def cmd_doctor(args: argparse.Namespace) -> None:
    root = root_path(args)
    ensure_initialized(root)
    config = load_config(root)
    registry = load_registry(root)
    errors: list[str] = []
    seen: set[str] = set()
    for ticket in registry.get("tickets", []):
        ticket_id = ticket.get("id", "")
        if ticket_id in seen:
            errors.append(f"Duplicate id: {ticket_id}")
        seen.add(ticket_id)
        if ticket.get("status") not in STATUSES:
            errors.append(f"{ticket_id}: invalid status {ticket.get('status')}")
        if ticket.get("type") not in TYPES:
            errors.append(f"{ticket_id}: invalid type {ticket.get('type')}")
        if ticket.get("priority") not in PRIORITIES:
            errors.append(f"{ticket_id}: invalid priority {ticket.get('priority')}")
        path = ticket_file(root, ticket)
        if not path.exists():
            errors.append(f"{ticket_id}: missing file {path}")
    for command in config.get("validation", {}).get("commands", []):
        if not isinstance(command, str):
            errors.append(f"Invalid validation command: {command!r}")
    if errors:
        print("Doctor found problems:")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)
    print(f"Doctor OK: {len(registry.get('tickets', []))} tickets checked.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage repo-local Markdown tickets.")
    parser.add_argument("--root", default=".", help="Target repository root.")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="Initialize .tickets.")
    init.add_argument("--root", default=argparse.SUPPRESS, help="Target repository root.")
    init.add_argument("--profile", default="generic", choices=["generic", "strict"])
    init.add_argument("--interactive", action="store_true")
    init.add_argument("--force", action="store_true")
    init.set_defaults(func=cmd_init)

    new = sub.add_parser("new", help="Create a ticket.")
    new.add_argument("--root", default=argparse.SUPPRESS, help="Target repository root.")
    new.add_argument("--title", required=True)
    new.add_argument("--type", default="feature")
    new.add_argument("--status")
    new.add_argument("--priority", default="P2")
    new.add_argument("--severity")
    new.add_argument("--area", default="repo")
    new.add_argument("--owner")
    new.add_argument("--estimate")
    new.add_argument("--risk")
    new.add_argument("--labels")
    new.add_argument("--depends-on", dest="depends_on")
    new.add_argument("--blocks")
    new.add_argument("--source")
    new.add_argument("--context")
    new.add_argument("--acceptance")
    new.add_argument("--notes")
    new.add_argument("--validation")
    new.add_argument("--handoff")
    new.set_defaults(func=cmd_new)

    list_cmd = sub.add_parser("list", help="List tickets.")
    list_cmd.add_argument("--root", default=argparse.SUPPRESS, help="Target repository root.")
    list_cmd.add_argument("--status")
    list_cmd.add_argument("--type")
    list_cmd.add_argument("--area")
    list_cmd.set_defaults(func=cmd_list)

    next_cmd = sub.add_parser("next", help="Show the best next ticket.")
    next_cmd.add_argument("--root", default=argparse.SUPPRESS, help="Target repository root.")
    next_cmd.set_defaults(func=cmd_next)

    move = sub.add_parser("move", help="Move a ticket to a new status.")
    move.add_argument("--root", default=argparse.SUPPRESS, help="Target repository root.")
    move.add_argument("ticket_id")
    move.add_argument("status")
    move.set_defaults(func=cmd_move)

    comment = sub.add_parser("comment", help="Append an activity log message.")
    comment.add_argument("--root", default=argparse.SUPPRESS, help="Target repository root.")
    comment.add_argument("ticket_id")
    comment.add_argument("message")
    comment.set_defaults(func=cmd_comment)

    close = sub.add_parser("close", help="Close a ticket.")
    close.add_argument("--root", default=argparse.SUPPRESS, help="Target repository root.")
    close.add_argument("ticket_id")
    close.add_argument("--resolution", required=True)
    close.add_argument("--wont-do", action="store_true")
    close.set_defaults(func=cmd_close)

    sync = sub.add_parser("sync", help="Regenerate board and ticket Markdown.")
    sync.add_argument("--root", default=argparse.SUPPRESS, help="Target repository root.")
    sync.set_defaults(func=cmd_sync)

    sprint = sub.add_parser("sprint", help="Manage Markdown sprints.")
    sprint_sub = sprint.add_subparsers(dest="sprint_command", required=True)

    sprint_start = sprint_sub.add_parser("start", help="Start an active sprint.")
    sprint_start.add_argument("--root", default=argparse.SUPPRESS, help="Target repository root.")
    sprint_start.add_argument("--name", required=True)
    sprint_start.add_argument("--goal", required=True)
    sprint_start.add_argument("--tickets", default="", help="Comma-separated ticket ids.")
    sprint_start.add_argument("--start")
    sprint_start.add_argument("--end")
    sprint_start.add_argument("--risks")
    sprint_start.add_argument("--validation")
    sprint_start.add_argument("--force", action="store_true")
    sprint_start.set_defaults(func=cmd_sprint_start)

    sprint_add = sprint_sub.add_parser("add", help="Add tickets to the active sprint.")
    sprint_add.add_argument("--root", default=argparse.SUPPRESS, help="Target repository root.")
    sprint_add.add_argument("--tickets", required=True, help="Comma-separated ticket ids.")
    sprint_add.set_defaults(func=cmd_sprint_add)

    sprint_status = sprint_sub.add_parser("status", help="Show active sprint status.")
    sprint_status.add_argument("--root", default=argparse.SUPPRESS, help="Target repository root.")
    sprint_status.set_defaults(func=cmd_sprint_status)

    sprint_close = sprint_sub.add_parser("close", help="Close the active sprint.")
    sprint_close.add_argument("--root", default=argparse.SUPPRESS, help="Target repository root.")
    sprint_close.add_argument("--summary", required=True)
    sprint_close.add_argument("--carryover", default="", help="Comma-separated carryover ticket ids.")
    sprint_close.set_defaults(func=cmd_sprint_close)

    operating = sub.add_parser("operating-init", help="Create deterministic agent operating docs.")
    operating.add_argument("--root", default=argparse.SUPPRESS, help="Target repository root.")
    operating.add_argument("--mode", default="fast", choices=["fast", "deep"])
    operating.add_argument("--force", action="store_true")
    operating.set_defaults(func=cmd_operating_init)

    sync_hooks = sub.add_parser("sync-hooks", help="Configure external tracker sync hook files.")
    sync_hooks.add_argument("--root", default=argparse.SUPPRESS, help="Target repository root.")
    sync_hooks.add_argument("--provider", required=True, choices=SYNC_PROVIDERS)
    sync_hooks.add_argument("--mode", default="hybrid", choices=SYNC_MODES)
    sync_hooks.add_argument("--external-project", default="")
    sync_hooks.add_argument("--mcp-server", default="")
    sync_hooks.set_defaults(func=cmd_sync_hooks)

    doctor = sub.add_parser("doctor", help="Validate ticket state.")
    doctor.add_argument("--root", default=argparse.SUPPRESS, help="Target repository root.")
    doctor.set_defaults(func=cmd_doctor)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
