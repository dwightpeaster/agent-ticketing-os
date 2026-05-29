#!/usr/bin/env python3
"""Repo-local ticket manager for the agent-ticketing skill."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STATUSES = ["inbox", "backlog", "ready", "in_progress", "review", "blocked", "done", "wont_do"]
TYPES = ["feature", "bug", "change", "repo", "research", "design", "security"]
PRIORITIES = ["P0", "P1", "P2", "P3", "P4"]
PRIORITY_SCORE = {"P0": 500, "P1": 400, "P2": 300, "P3": 200, "P4": 100}
STATUS_SCORE = {"ready": 50, "inbox": 10, "backlog": 20, "blocked": -100, "in_progress": -50, "review": -25}


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return re.sub(r"-+", "-", value).strip("-") or "ticket"


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
                "default_status": "Ready",
                "statuses": ["Backlog", "Ready", "In Progress", "Blocked", "Review", "Complete"],
                "types": ["Bug", "Feature", "Security", "Design/UX", "Docs", "Chore", "Test", "Remove"],
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
                    "applies_to": ["Feature", "Design/UX"],
                    "waive_only_when_user_says_scope_complete": True,
                },
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
    tickets = [ticket for ticket in registry.get("tickets", []) if ticket.get("status") in {"ready", "in_progress", "review", "blocked"}]
    lines = ["# Current Sprint", "", f"Updated: {now()}", ""]
    for ticket in sorted(tickets, key=ticket_sort_key):
        lines.append(ticket_line(ticket))
    if not tickets:
        lines.append("- No active tickets.")
    report = tickets_dir(root) / "reports" / "current-sprint.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_templates(root: Path) -> None:
    template_dir = tickets_dir(root) / "templates"
    template_dir.mkdir(parents=True, exist_ok=True)
    examples = {
        "feature.md": "Feature tickets should describe the user, workflow, acceptance criteria, and validation.",
        "bug.md": "Bug tickets should include expected behavior, actual behavior, reproduction, severity, and regression tests.",
        "repo.md": "Repo tickets should include maintenance value, affected systems, risk, rollback, and validation commands.",
        "research.md": "Research tickets should define the question, decision needed, sources inspected, and resulting follow-ups.",
    }
    for name, text in examples.items():
        path = template_dir / name
        if not path.exists():
            path.write_text(f"# {name.removesuffix('.md').title()} Template\n\n{text}\n", encoding="utf-8")


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
        "backlog": "# Backlog Tickets\n\nDeferred `Backlog` tickets that are not ready for implementation.\n",
        "completed": "# Completed Tickets\n\nOne-line archive records for `Complete` tickets.\n",
        "roadmap": "# Roadmap\n\nDelivery phases, release milestones, and phase-level ticket ranges.\n",
        "decisions": "# Product Decisions\n\nDurable product decisions and open product or architecture decisions.\n",
    }
    for key, content in defaults.items():
        path = root / locations[key]
        if not path.exists():
            path.write_text(content, encoding="utf-8")


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
    if args.type not in TYPES:
        raise SystemExit(f"Invalid type: {args.type}")
    if args.priority not in PRIORITIES:
        raise SystemExit(f"Invalid priority: {args.priority}")
    status = args.status or config["ticketing"]["default_status"]
    if status not in STATUSES:
        raise SystemExit(f"Invalid status: {status}")
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
    if args.status not in STATUSES:
        raise SystemExit(f"Invalid status: {args.status}")
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
