"""Deterministic generated views for canonical ticket files."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from .constants import ACTIVE_STATUSES, DISPLAY_STATUS, PRIORITY_SCORE, STATUSES
from .util import atomic_write, latest_timestamp, load_json, write_if_missing


def sort_key(ticket: dict[str, Any]) -> tuple[int, str]:
    return (-PRIORITY_SCORE.get(str(ticket.get("priority", "P4")), 0), str(ticket.get("id", "")))


def _unresolved_dependencies(ticket: dict[str, Any], by_id: dict[str, dict[str, Any]]) -> list[str]:
    return [
        dependency
        for dependency in ticket.get("depends_on", [])
        if dependency not in by_id or by_id[dependency].get("status") != "done"
    ]


def ticket_line(
    ticket: dict[str, Any],
    view_path: Path,
    include_status: bool = False,
    waiting_on: list[str] | None = None,
) -> str:
    relative = Path(os.path.relpath(ticket["_path"], start=view_path.parent)).as_posix()
    status = f"{DISPLAY_STATUS.get(ticket['status'], ticket['status'])} · " if include_status else ""
    labels = ", ".join(ticket.get("labels", []))
    label_text = f" · {labels}" if labels else ""
    waiting_text = f" · waiting on {', '.join(waiting_on)}" if waiting_on else ""
    return (
        f"- [{ticket['id']}]({relative}) — {status}{ticket['priority']} · "
        f"{ticket['type']} · {ticket['area']} — {ticket['title']}{label_text}{waiting_text}"
    )


def _stamp(config: dict[str, Any], tickets: list[dict[str, Any]]) -> str:
    return latest_timestamp(
        [str(ticket.get("updated", "")) for ticket in tickets],
        str(config.get("updated", config.get("created", "not set"))),
    )


def _grouped_view(
    store: Any,
    title: str,
    config: dict[str, Any],
    tickets: list[dict[str, Any]],
    statuses: list[str],
    view_path: Path,
) -> str:
    lines = [f"# {title}", "", f"Project: {config['project']['name']}", f"Latest source update: {_stamp(config, tickets)}", ""]
    ordered = sorted(tickets, key=sort_key)
    by_id = {ticket["id"]: ticket for ticket in tickets}
    for status in statuses:
        status_tickets = [ticket for ticket in ordered if ticket.get("status") == status]
        if status == "ready":
            waiting = [ticket for ticket in status_tickets if _unresolved_dependencies(ticket, by_id)]
            lines.extend(["## Waiting On Dependencies", ""])
            lines.extend(
                ticket_line(ticket, view_path, waiting_on=_unresolved_dependencies(ticket, by_id))
                for ticket in waiting
            )
            if not waiting:
                lines.append("_None._")
            lines.append("")
            grouped = [ticket for ticket in status_tickets if not _unresolved_dependencies(ticket, by_id)]
        else:
            grouped = status_tickets
        lines.extend([f"## {DISPLAY_STATUS.get(status, status)}", ""])
        lines.extend(ticket_line(ticket, view_path) for ticket in grouped)
        if not grouped:
            lines.append("_None._")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _changelog(store: Any, config: dict[str, Any], tickets: list[dict[str, Any]]) -> str:
    closed = sorted(
        [ticket for ticket in tickets if ticket.get("status") in {"done", "wont_do"}],
        key=lambda ticket: str(ticket.get("updated", "")),
        reverse=True,
    )
    lines = ["# Ticket Changelog", "", f"Latest source update: {_stamp(config, tickets)}", ""]
    lines.extend(
        f"- {ticket.get('updated', '')} [{ticket['id']}] {DISPLAY_STATUS[ticket['status']]} — {ticket['title']}"
        for ticket in closed
    )
    if not closed:
        lines.append("_No closed tickets yet._")
    return "\n".join(lines) + "\n"


def _sprint_report(store: Any, config: dict[str, Any], tickets: list[dict[str, Any]], view_path: Path) -> str:
    sprint_path = store.directory / "sprints" / "current.json"
    sprint = load_json(sprint_path, None)
    if not sprint:
        return "# Current Sprint\n\n_No active sprint._\n"
    by_id = {ticket["id"]: ticket for ticket in tickets}
    selected = [by_id[ticket_id] for ticket_id in sprint.get("tickets", []) if ticket_id in by_id]
    lines = [
        f"# {sprint['name']}",
        "",
        f"Status: {sprint['status']}",
        f"Goal: {sprint['goal']}",
        f"Dates: {sprint.get('start', 'not set')} to {sprint.get('end') or 'not set'}",
        f"Latest source update: {latest_timestamp([str(item.get('updated', '')) for item in selected], sprint.get('updated', ''))}",
        "",
    ]
    for status in ["in_progress", "review", "blocked", "ready", "done", "wont_do", "backlog", "inbox"]:
        status_tickets = [ticket for ticket in selected if ticket.get("status") == status]
        if status == "ready":
            waiting = [ticket for ticket in status_tickets if _unresolved_dependencies(ticket, by_id)]
            if waiting:
                lines.extend(["## Waiting On Dependencies", ""])
                lines.extend(
                    ticket_line(ticket, view_path, waiting_on=_unresolved_dependencies(ticket, by_id))
                    for ticket in sorted(waiting, key=sort_key)
                )
                lines.append("")
            grouped = [ticket for ticket in status_tickets if not _unresolved_dependencies(ticket, by_id)]
        else:
            grouped = status_tickets
        if not grouped:
            continue
        lines.extend([f"## {DISPLAY_STATUS[status]}", ""])
        lines.extend(ticket_line(ticket, view_path, include_status=False) for ticket in sorted(grouped, key=sort_key))
        lines.append("")
    lines.extend(["## Risks", "", sprint.get("risks", "None recorded."), "", "## Validation", "", sprint.get("validation", "Use each ticket's validation plan."), ""])
    return "\n".join(lines).rstrip() + "\n"


def _decisions_template(project: str) -> str:
    return f"""# Decisions

Project: {project}

Record durable product, architecture, workflow, and release decisions here. Do not use this file for routine ticket activity.

## Decision Template

### YYYY-MM-DD — Short decision

- Context:
- Decision:
- Alternatives considered:
- Consequences:
- Related tickets:

## Open Questions

- None recorded.
"""


def render_views(store: Any, config: dict[str, Any], tickets: list[dict[str, Any]]) -> dict[str, int]:
    changed: dict[str, int] = {}
    backlog_path = store.directory / "BACKLOG.md"
    board_path = store.directory / "BOARD.md"
    changelog_path = store.directory / "CHANGELOG.md"
    sprint_report_path = store.directory / "reports" / "current-sprint.md"
    outputs = {
        backlog_path: _grouped_view(store, "Backlog", config, tickets, STATUSES, backlog_path),
        board_path: _grouped_view(store, "Board", config, tickets, ["review", "blocked", "in_progress", "ready"], board_path),
        changelog_path: _changelog(store, config, tickets),
        sprint_report_path: _sprint_report(store, config, tickets, sprint_report_path),
    }
    for path, content in outputs.items():
        if atomic_write(path, content):
            changed[str(path.relative_to(store.root))] = 1
    write_if_missing(store.directory / "DECISIONS.md", _decisions_template(config["project"]["name"]))

    if config.get("ticketing", {}).get("layout") == "split-board":
        working_path = store.root / "tickets.md"
        deferred_path = store.root / "docs" / "tickets" / "BACKLOG.md"
        completed_path = store.root / "docs" / "tickets" / "COMPLETED.md"
        split = {
            working_path: _grouped_view(store, f"{config['project']['name']} Working Tickets", config, tickets, ["review", "blocked", "in_progress", "ready"], working_path),
            deferred_path: _grouped_view(store, "Deferred Tickets", config, tickets, ["inbox", "backlog"], deferred_path),
            completed_path: _grouped_view(store, "Completed Tickets", config, tickets, ["done", "wont_do"], completed_path),
        }
        for path, content in split.items():
            if atomic_write(path, content):
                changed[str(path.relative_to(store.root))] = 1
    return changed
