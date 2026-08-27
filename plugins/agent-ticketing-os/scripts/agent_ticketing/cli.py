"""Command-line interface for Agent Ticketing OS."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from . import SCHEMA_VERSION, SYSTEM_VERSION
from .constants import (
    CLOSED_STATUSES,
    DISPLAY_STATUS,
    PRIORITIES,
    PRIORITY_SCORE,
    STATUSES,
    TRACKER_MODES,
    TRACKER_PROVIDERS,
    TRANSITIONS,
    TYPES,
)
from .model import closure_problems, readiness_problems, summary
from .operating import OperatingError, install_operating_docs, install_ticket_templates
from .store import StoreError, TicketStore
from .util import atomic_write, csv_items, load_json, now, slugify, write_json


def root_path(args: argparse.Namespace) -> Path:
    return Path(args.root).expanduser().resolve()


def output(args: argparse.Namespace, data: Any, text: str) -> None:
    if getattr(args, "json", False):
        print(_json_text(data))
    else:
        print(text)


def _json_text(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def _compact(value: str) -> str:
    return " ".join(value.split())


def _profile(value: str) -> str:
    return {"generic": "standard", "strict": "guarded"}.get(value, value)


def _policy(config: dict[str, Any]) -> str:
    return str(config.get("workflow", {}).get("policy", "standard"))


def _override_allowed(args: argparse.Namespace) -> bool:
    if not getattr(args, "override", False):
        return False
    if not str(getattr(args, "reason", "") or "").strip():
        raise StoreError("--override requires --reason so the exception is auditable.")
    return True


def cmd_install(args: argparse.Namespace) -> None:
    store = TicketStore(root_path(args))
    with store.lock():
        created = not store.config_path.exists()
        migration: dict[str, Any] | None = None
        requested_policy = _profile(args.profile) if args.profile else None
        if created:
            store.initialize(requested_policy or "standard")
        else:
            migration = store.migrate(dry_run=False)
            if requested_policy:
                config = store.load_config()
                if _policy(config) != requested_policy:
                    config["workflow"]["policy"] = requested_policy
                    config["updated"] = now()
                    write_json(store.config_path, config)
        docs = install_operating_docs(store, args.operating)
        changed = store.render_all()
        policy = _policy(store.load_config())
    data = {
        "version": SYSTEM_VERSION,
        "created": created,
        "migration": migration,
        "operating": docs,
        "rendered": sorted(changed),
        "policy": policy,
    }
    action = "Installed" if created else "Checked and upgraded"
    output(args, data, f"{action} Agent Ticketing OS {SYSTEM_VERSION} in {store.root}")


def cmd_init(args: argparse.Namespace) -> None:
    store = TicketStore(root_path(args))
    with store.lock():
        config = store.initialize(_profile(args.profile))
        if args.interactive:
            config["project"]["name"] = input(f"Project name [{config['project']['name']}]: ").strip() or config["project"]["name"]
            config["project"]["mission"] = input(f"Project mission [{config['project']['mission']}]: ").strip() or config["project"]["mission"]
            config["updated"] = now()
            write_json(store.config_path, config)
        templates = install_ticket_templates(store)
        changed = store.render_all()
    output(args, {"config": config, "templates": templates, "rendered": sorted(changed)}, f"Initialized ticketing in {store.directory}")


def _ticket_fields(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "title": args.title,
        "type": args.type,
        "status": args.status,
        "priority": args.priority,
        "severity": args.severity,
        "area": args.area,
        "owner": args.owner,
        "estimate": args.estimate,
        "risk": args.risk,
        "labels": csv_items(args.labels),
        "depends_on": csv_items(args.depends_on),
        "blocks": csv_items(args.blocks),
        "source": args.source,
        "context": args.context,
        "acceptance": args.acceptance,
        "notes": args.notes,
        "validation": args.validation,
        "handoff": args.handoff,
    }


def cmd_new(args: argparse.Namespace) -> None:
    store = TicketStore(root_path(args))
    with store.lock():
        ticket = store.create(_ticket_fields(args))
    relative = str(ticket["_path"].relative_to(store.root))
    output(args, summary(ticket, relative), f"Created {ticket['id']} {relative}")


def cmd_show(args: argparse.Namespace) -> None:
    store = TicketStore(root_path(args))
    ticket = store.find(args.ticket_id)
    relative = str(ticket["_path"].relative_to(store.root))
    if args.json:
        data = dict(ticket)
        data.pop("_path", None)
        data["file"] = relative
        print(_json_text(data))
    else:
        print(ticket["_path"].read_text(encoding="utf-8"), end="")


def _sort_key(ticket: dict[str, Any]) -> tuple[int, str]:
    return (-PRIORITY_SCORE.get(str(ticket.get("priority", "P4")), 0), str(ticket.get("id", "")))


def cmd_list(args: argparse.Namespace) -> None:
    store = TicketStore(root_path(args))
    tickets = store.load_tickets()
    for key in ("status", "type", "area"):
        value = getattr(args, key)
        if value:
            tickets = [ticket for ticket in tickets if ticket.get(key) == value]
    tickets = sorted(tickets, key=_sort_key)
    data = [summary(ticket, str(ticket["_path"].relative_to(store.root))) for ticket in tickets]
    if args.json:
        print(_json_text(data))
        return
    for ticket in tickets:
        print(f"{ticket['id']}\t{ticket['status']}\t{ticket['priority']}\t{ticket['type']}\t{ticket['area']}\t{ticket['title']}")


def _unresolved_dependencies(ticket: dict[str, Any], by_id: dict[str, dict[str, Any]]) -> list[str]:
    return [
        dependency
        for dependency in ticket.get("depends_on", [])
        if dependency not in by_id or by_id[dependency].get("status") != "done"
    ]


def _actionable_candidates(
    tickets: list[dict[str, Any]],
    by_id: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    return sorted(
        [
            ticket
            for ticket in tickets
            if ticket.get("status") == "ready" and not _unresolved_dependencies(ticket, by_id)
        ],
        key=_sort_key,
    )


def cmd_next(args: argparse.Namespace) -> None:
    store = TicketStore(root_path(args))
    tickets = store.load_tickets()
    by_id = {ticket["id"]: ticket for ticket in tickets}
    candidates = _actionable_candidates(tickets, by_id)
    if not candidates:
        output(args, None, "No actionable ready tickets. Triage the inbox or backlog first.")
        return
    ticket = candidates[0]
    relative = str(ticket["_path"].relative_to(store.root))
    output(args, summary(ticket, relative), f"{ticket['id']}\t{ticket['priority']}\t{ticket['type']}\t{ticket['area']}\t{ticket['title']}\t{relative}")


def _context_summary(ticket: dict[str, Any], unresolved: list[str] | None = None) -> dict[str, Any]:
    data = {
        "id": ticket["id"],
        "title": ticket["title"],
        "status": ticket["status"],
        "priority": ticket["priority"],
        "type": ticket["type"],
        "area": ticket["area"],
    }
    if unresolved:
        data["waiting_on"] = unresolved
    return data


def _latest_evidence(ticket: dict[str, Any]) -> str:
    evidence = str(ticket.get("body", {}).get("evidence", "")).strip()
    if evidence in {"", "Not recorded."}:
        return ""
    lines = [line.strip() for line in evidence.splitlines() if line.strip()]
    return lines[-1] if lines else ""


def _next_action(ticket: dict[str, Any], unresolved: list[str]) -> str:
    if unresolved:
        return "Resolve dependencies: " + ", ".join(unresolved) + "."
    return {
        "inbox": "Triage the request into backlog or ready.",
        "backlog": "Refine the ticket, then move it to ready when actionable.",
        "ready": "Move to in_progress and implement the acceptance criteria.",
        "in_progress": "Complete the work, record validation, then move to review.",
        "review": "Review the evidence; close the ticket or return it to in_progress.",
        "blocked": "Record or resolve the blocker before resuming work.",
        "done": "No action; the ticket is complete.",
        "wont_do": "No action; the ticket is closed without implementation.",
    }.get(str(ticket.get("status")), "Inspect the canonical ticket.")


def _ticket_context(
    ticket: dict[str, Any],
    config: dict[str, Any],
    by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    body = ticket.get("body", {})
    unresolved = _unresolved_dependencies(ticket, by_id)
    packet = {
        **_context_summary(ticket),
        "policy": _policy(config),
        "context": body.get("context", ""),
        "acceptance": body.get("acceptance", ""),
        "validation": body.get("validation", ""),
        "next_action": _next_action(ticket, unresolved),
    }
    if ticket.get("depends_on"):
        packet["depends_on"] = ticket["depends_on"]
    if unresolved:
        packet["waiting_on"] = unresolved
    evidence = _latest_evidence(ticket)
    if evidence:
        packet["latest_evidence"] = evidence
    handoff = str(body.get("handoff", "")).strip()
    if handoff not in {"", "No handoff notes yet."}:
        packet["handoff"] = handoff
    closure = str(body.get("closure", "")).strip()
    if ticket.get("status") in CLOSED_STATUSES and closure not in {"", "Open."}:
        packet["closure"] = closure
    return packet


def _ticket_context_text(packet: dict[str, Any]) -> str:
    label = DISPLAY_STATUS.get(str(packet["status"]), str(packet["status"]))
    lines = [
        f"{packet['id']} · {label} · {packet['priority']} · {packet['type']} · {packet['area']}",
        f"Policy: {str(packet['policy']).title()}",
        f"Goal: {packet['context']}",
        "Acceptance:",
        str(packet["acceptance"]),
    ]
    if packet.get("waiting_on"):
        lines.append("Dependencies: waiting on " + ", ".join(packet["waiting_on"]))
    elif packet.get("depends_on"):
        lines.append("Dependencies: clear (" + ", ".join(packet["depends_on"]) + ")")
    else:
        lines.append("Dependencies: clear")
    lines.extend(["Validation:", str(packet["validation"])])
    if packet.get("latest_evidence"):
        lines.append("Latest evidence: " + str(packet["latest_evidence"]))
    if packet.get("handoff"):
        lines.extend(["Handoff:", str(packet["handoff"])])
    if packet.get("closure"):
        lines.append("Closure: " + str(packet["closure"]))
    lines.append("Next action: " + str(packet["next_action"]))
    return "\n".join(lines)


def _session_context(
    tickets: list[dict[str, Any]],
    config: dict[str, Any],
    by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    active = sorted(
        [ticket for ticket in tickets if ticket.get("status") in {"in_progress", "review", "blocked"}],
        key=_sort_key,
    )
    candidates = _actionable_candidates(tickets, by_id)
    waiting = sorted(
        [
            ticket
            for ticket in tickets
            if ticket.get("status") == "ready" and _unresolved_dependencies(ticket, by_id)
        ],
        key=_sort_key,
    )
    packet: dict[str, Any] = {
        "project": config.get("project", {}).get("name", "Repository"),
        "policy": _policy(config),
        "active": [
            _context_summary(ticket, _unresolved_dependencies(ticket, by_id))
            for ticket in active
        ],
        "next": _context_summary(candidates[0]) if candidates else None,
        "waiting": [
            _context_summary(ticket, _unresolved_dependencies(ticket, by_id))
            for ticket in waiting
        ],
        "queue": {
            "inbox": sum(ticket.get("status") == "inbox" for ticket in tickets),
            "backlog": sum(ticket.get("status") == "backlog" for ticket in tickets),
        },
    }
    errors = _dependency_errors(tickets)
    if errors:
        packet["integrity_errors"] = errors
    return packet


def _session_context_text(packet: dict[str, Any]) -> str:
    lines = [f"{packet['project']} · {str(packet['policy']).title()} policy"]
    active = packet["active"]
    if active:
        lines.append("Active:")
        lines.extend(
            f"- {item['id']} · {DISPLAY_STATUS.get(item['status'], item['status'])} · {item['priority']} · {item['title']}"
            for item in active
        )
    else:
        lines.append("Active: none")
    next_ticket = packet["next"]
    lines.append(
        f"Next: {next_ticket['id']} · {next_ticket['priority']} · {next_ticket['title']}"
        if next_ticket
        else "Next: no dependency-clear ready ticket"
    )
    if packet["waiting"]:
        lines.append("Waiting:")
        lines.extend(
            f"- {item['id']} · {item['title']} · waiting on {', '.join(item['waiting_on'])}"
            for item in packet["waiting"]
        )
    queue = packet["queue"]
    lines.append(f"Queue: {queue['inbox']} inbox · {queue['backlog']} backlog")
    errors = packet.get("integrity_errors", [])
    lines.append("Integrity: OK" if not errors else f"Integrity: {len(errors)} dependency error(s); run doctor")
    if active:
        lines.append("Next action: resume the active ticket; use context <id> for its working packet.")
    elif next_ticket:
        lines.append("Next action: use context --next, then move that ticket to in_progress.")
    else:
        lines.append("Next action: triage inbox or backlog work.")
    return "\n".join(lines)


def cmd_context(args: argparse.Namespace) -> None:
    store = TicketStore(root_path(args))
    config = store.load_config()
    tickets = store.load_tickets()
    by_id = {ticket["id"]: ticket for ticket in tickets}
    if args.ticket_id and args.next:
        raise StoreError("Choose a ticket id or --next, not both.")
    if args.next:
        candidates = _actionable_candidates(tickets, by_id)
        if not candidates:
            output(args, None, "No actionable ready tickets. Triage the inbox or backlog first.")
            return
        packet = _ticket_context(candidates[0], config, by_id)
        output(args, packet, _ticket_context_text(packet))
        return
    if args.ticket_id:
        packet = _ticket_context(store.find(args.ticket_id, tickets), config, by_id)
        output(args, packet, _ticket_context_text(packet))
        return
    packet = _session_context(tickets, config, by_id)
    output(args, packet, _session_context_text(packet))


def cmd_edit(args: argparse.Namespace) -> None:
    store = TicketStore(root_path(args))
    with store.lock():
        ticket = store.find(args.ticket_id)
        fields = ["title", "type", "priority", "severity", "area", "owner", "estimate", "risk", "source"]
        changed_fields: list[str] = []
        for field in fields:
            value = getattr(args, field)
            if value is not None:
                ticket[field] = value
                changed_fields.append(field)
        for field in ("labels",):
            value = getattr(args, field)
            if value is not None:
                ticket[field] = csv_items(value)
                changed_fields.append(field)
        for field in ("context", "acceptance", "notes", "validation", "handoff"):
            value = getattr(args, field)
            if value is not None:
                ticket["body"][field] = value
                changed_fields.append(field)
        for assignment in args.external_id or []:
            provider, separator, external_id = assignment.partition("=")
            provider = provider.strip().lower()
            external_id = _compact(external_id)
            if not separator or not provider or not external_id:
                raise StoreError("--external-id must use provider=id, for example linear=ENG-42.")
            ticket.setdefault("external_ids", {})[provider] = external_id
            changed_fields.append(f"external_ids.{provider}")
        for provider in args.remove_external_id or []:
            provider = provider.strip().lower()
            if not provider:
                raise StoreError("--remove-external-id requires a provider name.")
            if provider in ticket.setdefault("external_ids", {}):
                del ticket["external_ids"][provider]
                changed_fields.append(f"external_ids.{provider}")
        if not changed_fields:
            raise StoreError("No edit fields were provided.")
        stamp = now()
        ticket["updated"] = stamp
        ticket.setdefault("activity", []).append(f"{stamp} edited: {', '.join(changed_fields)}.")
        store.save_ticket(ticket)
        store.render_all()
    output(args, {"id": ticket["id"], "changed": changed_fields}, f"Updated {ticket['id']}: {', '.join(changed_fields)}")


def cmd_comment(args: argparse.Namespace) -> None:
    store = TicketStore(root_path(args))
    with store.lock():
        ticket = store.find(args.ticket_id)
        message = _compact(args.message)
        if not message:
            raise StoreError("Activity message cannot be empty.")
        stamp = now()
        ticket["updated"] = stamp
        ticket.setdefault("activity", []).append(f"{stamp} {message}")
        store.save_ticket(ticket)
        store.render_all()
    output(args, {"id": ticket["id"], "updated": stamp}, f"Updated {ticket['id']}")


def cmd_move(args: argparse.Namespace) -> None:
    if args.status in CLOSED_STATUSES:
        raise StoreError("Use close for done or wont_do so resolution rules cannot be bypassed.")
    store = TicketStore(root_path(args))
    with store.lock():
        config = store.load_config()
        ticket = store.find(args.ticket_id)
        old = str(ticket["status"])
        if old in CLOSED_STATUSES:
            raise StoreError(f"{ticket['id']} is closed; use reopen instead of move.")
        override = _override_allowed(args)
        if args.status not in TRANSITIONS.get(old, set()) and not override:
            raise StoreError(f"Invalid transition: {old} -> {args.status}. Use --override with --reason if intentional.")
        problems = readiness_problems(ticket) if args.status in {"ready", "in_progress", "review"} else []
        if problems and _policy(config) == "guarded" and not override:
            raise StoreError("Ticket is not ready for that status:\n- " + "\n- ".join(problems))
        stamp = now()
        ticket["status"] = args.status
        ticket["updated"] = stamp
        note = f"{stamp} moved from {old} to {args.status}."
        if override:
            note += f" Override: {_compact(args.reason)}"
        ticket.setdefault("activity", []).append(note)
        store.save_ticket(ticket)
        store.render_all()
    output(args, {"id": ticket["id"], "from": old, "to": args.status, "override": override}, f"Moved {ticket['id']} {old} -> {args.status}")


def cmd_validate(args: argparse.Namespace) -> None:
    store = TicketStore(root_path(args))
    with store.lock():
        if args.result == "skipped" and not _compact(args.notes or ""):
            raise StoreError("Skipped validation requires --notes with the reason and remaining risk.")
        ticket = store.find(args.ticket_id)
        stamp = now()
        command = _compact(args.command) if args.command else "manual validation"
        note = f"- {stamp} [{args.result.upper()}] `{command}`"
        if args.notes:
            note += f" — {_compact(args.notes)}"
        evidence = str(ticket["body"].get("evidence", "")).strip()
        ticket["body"]["evidence"] = note if evidence in {"", "Not recorded."} else f"{evidence}\n{note}"
        ticket["updated"] = stamp
        ticket.setdefault("activity", []).append(f"{stamp} recorded {args.result} validation: {command}.")
        store.save_ticket(ticket)
        store.render_all()
    output(args, {"id": ticket["id"], "result": args.result, "command": command}, f"Recorded {args.result} validation for {ticket['id']}")


def cmd_close(args: argparse.Namespace) -> None:
    store = TicketStore(root_path(args))
    with store.lock():
        if not _compact(args.resolution):
            raise StoreError("Closure resolution cannot be empty.")
        config = store.load_config()
        ticket = store.find(args.ticket_id)
        if ticket["status"] in CLOSED_STATUSES:
            raise StoreError(f"{ticket['id']} is already {ticket['status']}.")
        status = "wont_do" if args.wont_do else "done"
        override = _override_allowed(args)
        problems = [] if args.wont_do else closure_problems(ticket)
        if not args.wont_do and _policy(config) == "guarded" and ticket["status"] != "review":
            problems.insert(0, "guarded policy requires review status before done")
        if problems and _policy(config) == "guarded" and not override:
            raise StoreError("Ticket does not satisfy guarded closure:\n- " + "\n- ".join(problems))
        stamp = now()
        ticket["status"] = status
        ticket["updated"] = stamp
        ticket["body"]["closure"] = args.resolution.strip()
        note = f"{stamp} closed as {status}: {_compact(args.resolution)}"
        if override:
            note += f" Override: {_compact(args.reason)}"
        ticket.setdefault("activity", []).append(note)
        store.save_ticket(ticket)
        store.render_all()
    output(args, {"id": ticket["id"], "status": status, "override": override}, f"Closed {ticket['id']} as {status}")


def cmd_reopen(args: argparse.Namespace) -> None:
    store = TicketStore(root_path(args))
    with store.lock():
        config = store.load_config()
        ticket = store.find(args.ticket_id)
        if ticket["status"] not in CLOSED_STATUSES:
            raise StoreError(f"{ticket['id']} is not closed.")
        old = ticket["status"]
        if args.status == "ready" and _policy(config) == "guarded":
            problems = readiness_problems(ticket)
            if problems:
                raise StoreError("Ticket is not ready to reopen as ready:\n- " + "\n- ".join(problems))
        stamp = now()
        ticket["status"] = args.status
        ticket["updated"] = stamp
        ticket["body"]["closure"] = "Open."
        ticket.setdefault("activity", []).append(f"{stamp} reopened from {old} to {args.status}: {_compact(args.reason)}")
        store.save_ticket(ticket)
        store.render_all()
    output(args, {"id": ticket["id"], "from": old, "to": args.status}, f"Reopened {ticket['id']} as {args.status}")


def cmd_link(args: argparse.Namespace) -> None:
    store = TicketStore(root_path(args))
    with store.lock():
        tickets = store.load_tickets()
        source = store.find(args.ticket_id, tickets)
        target = store.find(args.target_id, tickets)
        if source["id"] == target["id"]:
            raise StoreError("A ticket cannot link to itself.")
        if args.relationship == "depends-on":
            source_key, target_key = "depends_on", "blocks"
        else:
            source_key, target_key = "blocks", "depends_on"
        if target["id"] not in source[source_key]:
            source[source_key].append(target["id"])
        if source["id"] not in target[target_key]:
            target[target_key].append(source["id"])
        link_errors = _dependency_errors(tickets)
        if link_errors:
            raise StoreError("Invalid dependency link:\n- " + "\n- ".join(link_errors))
        stamp = now()
        for ticket in (source, target):
            ticket["updated"] = stamp
        source.setdefault("activity", []).append(f"{stamp} linked {args.relationship} {target['id']}.")
        target.setdefault("activity", []).append(f"{stamp} linked with {source['id']}.")
        store.save_ticket(source)
        store.save_ticket(target)
        store.render_all()
    output(args, {"id": source["id"], "relationship": args.relationship, "target": target["id"]}, f"Linked {source['id']} {args.relationship} {target['id']}")


def cmd_unlink(args: argparse.Namespace) -> None:
    store = TicketStore(root_path(args))
    with store.lock():
        tickets = store.load_tickets()
        source = store.find(args.ticket_id, tickets)
        target = store.find(args.target_id, tickets)
        if args.relationship == "depends-on":
            source_key, target_key = "depends_on", "blocks"
        else:
            source_key, target_key = "blocks", "depends_on"
        source[source_key] = [item for item in source[source_key] if item != target["id"]]
        target[target_key] = [item for item in target[target_key] if item != source["id"]]
        stamp = now()
        for ticket in (source, target):
            ticket["updated"] = stamp
        source.setdefault("activity", []).append(f"{stamp} removed {args.relationship} link to {target['id']}.")
        target.setdefault("activity", []).append(f"{stamp} removed link with {source['id']}.")
        for ticket in (source, target):
            store.save_ticket(ticket)
        store.render_all()
    output(args, {"id": source["id"], "relationship": args.relationship, "target": target["id"]}, f"Unlinked {source['id']} {args.relationship} {target['id']}")


def cmd_render(args: argparse.Namespace) -> None:
    store = TicketStore(root_path(args))
    with store.lock():
        changed = store.render_all()
    output(args, {"changed": sorted(changed)}, f"Rendered ticket views; changed {len(changed)} file(s).")


def _dependency_errors(tickets: list[dict[str, Any]]) -> list[str]:
    by_id = {ticket["id"]: ticket for ticket in tickets}
    errors: list[str] = []
    for ticket in tickets:
        for dependency in ticket.get("depends_on", []):
            if dependency == ticket["id"]:
                errors.append(f"{ticket['id']}: depends on itself")
            elif dependency not in by_id:
                errors.append(f"{ticket['id']}: missing dependency {dependency}")
            elif ticket["id"] not in by_id[dependency].get("blocks", []):
                errors.append(f"{ticket['id']}: dependency {dependency} is missing the reciprocal blocks link")
        for blocked in ticket.get("blocks", []):
            if blocked not in by_id:
                errors.append(f"{ticket['id']}: missing blocked ticket {blocked}")
            elif ticket["id"] not in by_id[blocked].get("depends_on", []):
                errors.append(f"{ticket['id']}: blocks {blocked} is missing the reciprocal dependency link")
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(ticket_id: str, trail: list[str]) -> None:
        if ticket_id in visiting:
            errors.append("dependency cycle: " + " -> ".join([*trail, ticket_id]))
            return
        if ticket_id in visited or ticket_id not in by_id:
            return
        visiting.add(ticket_id)
        for dependency in by_id[ticket_id].get("depends_on", []):
            visit(dependency, [*trail, ticket_id])
        visiting.remove(ticket_id)
        visited.add(ticket_id)

    for ticket_id in by_id:
        visit(ticket_id, [])
    return list(dict.fromkeys(errors))


def cmd_doctor(args: argparse.Namespace) -> None:
    store = TicketStore(root_path(args))
    config = store.load_config()
    tickets = store.load_tickets()
    errors = _dependency_errors(tickets)
    warnings: list[str] = []
    for ticket in tickets:
        if ticket["status"] in {"ready", "in_progress", "review"}:
            problems = readiness_problems(ticket)
            target = errors if _policy(config) == "guarded" else warnings
            target.extend(f"{ticket['id']}: {problem}" for problem in problems)
        if ticket["status"] == "done":
            problems = closure_problems(ticket)
            target = errors if _policy(config) == "guarded" else warnings
            target.extend(f"{ticket['id']}: {problem}" for problem in problems)
    registry = load_json(store.registry_path, {})
    expected_registry = [
        summary(ticket, str(ticket["_path"].relative_to(store.root)))
        for ticket in sorted(tickets, key=lambda item: item["id"])
    ]
    if registry.get("tickets", []) != expected_registry:
        errors.append("REGISTRY.json is stale; run render")
    data = {"schema_version": config.get("schema_version"), "tickets": len(tickets), "errors": errors, "warnings": warnings}
    if errors:
        if args.json:
            print(_json_text(data))
        else:
            print("Doctor found problems:\n- " + "\n- ".join(errors))
        raise SystemExit(1)
    if args.json:
        print(_json_text(data))
    else:
        print(f"Doctor OK: {len(tickets)} tickets checked; {len(warnings)} warning(s).")
        for warning in warnings:
            print(f"- Warning: {warning}")


def cmd_migrate(args: argparse.Namespace) -> None:
    store = TicketStore(root_path(args))
    with store.lock():
        report = store.migrate(dry_run=args.dry_run)
    output(args, report, f"Migration status: {report['status']} (schema {report['from_schema']} -> {report['to_schema']})")


def _sprint_path(store: TicketStore) -> Path:
    return store.directory / "sprints" / "current.json"


def cmd_sprint_start(args: argparse.Namespace) -> None:
    store = TicketStore(root_path(args))
    with store.lock():
        if not _compact(args.name) or not _compact(args.goal):
            raise StoreError("Sprint name and goal cannot be empty.")
        store.ensure_initialized()
        path = _sprint_path(store)
        if path.exists():
            if not args.force:
                raise StoreError("An active sprint already exists. Close it first or use --force with care.")
            replaced = load_json(path, {})
            replaced_stamp = now()
            replaced["status"] = "superseded"
            replaced["updated"] = replaced_stamp
            archive = store.directory / "sprints" / f"{replaced_stamp[:10]}-{slugify(replaced.get('name', 'sprint'))}-superseded.json"
            counter = 1
            while archive.exists():
                archive = store.directory / "sprints" / f"{replaced_stamp[:10]}-{slugify(replaced.get('name', 'sprint'))}-superseded-{counter}.json"
                counter += 1
            write_json(archive, replaced)
        tickets = store.load_tickets()
        by_id = {ticket["id"]: ticket for ticket in tickets}
        ticket_ids = csv_items(args.tickets)
        missing = [ticket_id for ticket_id in ticket_ids if ticket_id not in by_id]
        if missing:
            raise StoreError("Ticket not found: " + ", ".join(missing))
        stamp = now()
        sprint = {
            "name": _compact(args.name),
            "goal": _compact(args.goal),
            "status": "active",
            "start": args.start or stamp[:10],
            "end": args.end or "",
            "tickets": ticket_ids,
            "risks": args.risks or "None recorded.",
            "validation": args.validation or "Use each ticket's validation plan.",
            "created": stamp,
            "updated": stamp,
        }
        write_json(path, sprint)
        store.render_all()
    output(args, sprint, f"Started sprint: {sprint['name']}")


def cmd_sprint_add(args: argparse.Namespace) -> None:
    store = TicketStore(root_path(args))
    with store.lock():
        path = _sprint_path(store)
        sprint = load_json(path, None)
        if not sprint:
            raise StoreError("No active sprint found.")
        tickets = store.load_tickets()
        known = {ticket["id"] for ticket in tickets}
        additions = csv_items(args.tickets)
        missing = [ticket_id for ticket_id in additions if ticket_id not in known]
        if missing:
            raise StoreError("Ticket not found: " + ", ".join(missing))
        sprint["tickets"] = list(dict.fromkeys([*sprint.get("tickets", []), *additions]))
        sprint["updated"] = now()
        write_json(path, sprint)
        store.render_all()
    output(args, sprint, f"Added {len(additions)} ticket(s) to sprint: {sprint['name']}")


def cmd_sprint_status(args: argparse.Namespace) -> None:
    store = TicketStore(root_path(args))
    sprint = load_json(_sprint_path(store), None)
    if not sprint:
        output(args, None, "No active sprint.")
        return
    output(args, sprint, f"{sprint['name']}\t{sprint['status']}\t{sprint['goal']}\t{','.join(sprint.get('tickets', []))}")


def cmd_sprint_close(args: argparse.Namespace) -> None:
    store = TicketStore(root_path(args))
    with store.lock():
        path = _sprint_path(store)
        sprint = load_json(path, None)
        if not sprint:
            raise StoreError("No active sprint found.")
        carryover = csv_items(args.carryover)
        invalid = [ticket_id for ticket_id in carryover if ticket_id not in sprint.get("tickets", [])]
        if invalid:
            raise StoreError("Carryover tickets must belong to the sprint: " + ", ".join(invalid))
        stamp = now()
        sprint.update({"status": "closed", "closed": stamp, "updated": stamp, "summary": args.summary, "carryover": carryover, "carryover_note": args.carryover_note or ""})
        archive = store.directory / "sprints" / f"{stamp[:10]}-{slugify(sprint['name'])}.json"
        counter = 1
        while archive.exists():
            archive = store.directory / "sprints" / f"{stamp[:10]}-{slugify(sprint['name'])}-{counter}.json"
            counter += 1
        write_json(archive, sprint)
        path.unlink()
        store.render_all()
    output(args, sprint, f"Closed sprint: {sprint['name']}")


def _tracker_document(provider: str, mode: str, project: str) -> str:
    return f"""# External Tracker Setup

Provider: `{provider}`
Mode: `{mode}`
External project: `{project or 'not configured'}`

This file is connector guidance. Agent Ticketing OS does not install a background agent, poll the tracker, or synchronize automatically.

During an active Codex or Claude session, an authorized connector may be used to read or write external issues. Confirm the target and resolve conflicts before writing.

- `local-primary`: local Markdown tickets own planning and implementation state.
- `hybrid`: local tickets own implementation detail; the tracker owns collaboration state.
- `external-primary`: the tracker owns planning state; local tickets hold execution notes when needed.
"""


def cmd_tracker_setup(args: argparse.Namespace) -> None:
    store = TicketStore(root_path(args))
    with store.lock():
        config = store.load_config()
        candidate = {
            "provider": args.provider,
            "mode": args.mode,
            "external_project": _compact(args.external_project) if args.external_project else "",
            "connector": _compact(args.connector) if args.connector else args.provider,
            "enabled": True,
            "automatic_sync": False,
        }
        existing = config.setdefault("trackers", {}).get(args.provider, {})
        comparable_existing = {key: existing.get(key) for key in candidate}
        changed = comparable_existing != candidate
        tracker = {**candidate, "updated": now() if changed else existing.get("updated", now())}
        if changed:
            config["trackers"][args.provider] = tracker
            config["updated"] = tracker["updated"]
        write_json(store.config_path, config)
        write_json(store.directory / "trackers" / f"{args.provider}.json", tracker)
        atomic_write(store.directory / "trackers" / f"{args.provider}.md", _tracker_document(args.provider, args.mode, tracker["external_project"]))
        store.render_all()
    output(args, tracker, f"Configured {args.provider} tracker guidance; no automatic synchronization was enabled.")


def cmd_operating_init(args: argparse.Namespace) -> None:
    store = TicketStore(root_path(args))
    with store.lock():
        profile = "extended" if args.mode == "deep" else "compact"
        report = install_operating_docs(store, profile)
        store.render_all()
    output(args, report, f"Installed {profile} operating guidance; preserved {len(report['preserved'])} customized file(s).")


def cmd_sync_hooks(args: argparse.Namespace) -> None:
    mode = {"local-first": "local-primary", "external-first": "external-primary"}.get(args.mode, args.mode)
    args.mode = mode
    args.connector = args.mcp_server
    cmd_tracker_setup(args)


def cmd_linear_setup(args: argparse.Namespace) -> None:
    mode = {"repo-primary": "local-primary", "linear-primary": "external-primary"}.get(args.mode, args.mode)
    args.provider = "linear"
    args.mode = mode
    args.external_project = args.project
    args.connector = args.mcp_server or "linear"
    cmd_tracker_setup(args)


def _add_common(subparser: argparse.ArgumentParser) -> None:
    subparser.add_argument("--root", default=argparse.SUPPRESS, help="Target repository root.")
    subparser.add_argument("--json", action="store_true", help="Return structured JSON output.")


def _add_override(subparser: argparse.ArgumentParser) -> None:
    subparser.add_argument("--override", action="store_true", help="Bypass a workflow gate.")
    subparser.add_argument("--reason", help="Required explanation for an override.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=f"Agent Ticketing OS {SYSTEM_VERSION}")
    parser.add_argument("--root", default=".", help="Target repository root.")
    parser.add_argument("--version", action="version", version=SYSTEM_VERSION)
    sub = parser.add_subparsers(dest="command", required=True)

    install = sub.add_parser("install", help="Install or safely upgrade the complete system.")
    _add_common(install)
    install.add_argument("--profile", choices=["standard", "guarded", "generic", "strict"])
    install.add_argument("--operating", choices=["compact", "extended"], default="compact")
    install.set_defaults(func=cmd_install)

    init = sub.add_parser("init", help="Initialize ticketing only (legacy-compatible command).")
    _add_common(init)
    init.add_argument("--profile", choices=["standard", "guarded", "generic", "strict"], default="standard")
    init.add_argument("--interactive", action="store_true")
    init.set_defaults(func=cmd_init)

    new = sub.add_parser("new", help="Create a ticket.")
    _add_common(new)
    new.add_argument("--title", required=True)
    new.add_argument("--type", choices=TYPES, default="feature")
    new.add_argument("--status", choices=STATUSES)
    new.add_argument("--priority", choices=PRIORITIES, default="P2")
    for name in ("severity", "area", "owner", "estimate", "risk", "labels", "depends-on", "blocks", "source", "context", "acceptance", "notes", "validation", "handoff"):
        new.add_argument(f"--{name}", dest=name.replace("-", "_"))
    new.set_defaults(func=cmd_new)

    show = sub.add_parser("show", help="Show one canonical ticket.")
    _add_common(show)
    show.add_argument("ticket_id")
    show.set_defaults(func=cmd_show)

    list_cmd = sub.add_parser("list", help="List tickets.")
    _add_common(list_cmd)
    list_cmd.add_argument("--status", choices=STATUSES)
    list_cmd.add_argument("--type", choices=TYPES)
    list_cmd.add_argument("--area")
    list_cmd.set_defaults(func=cmd_list)

    next_cmd = sub.add_parser("next", help="Select the highest-priority actionable ready ticket.")
    _add_common(next_cmd)
    next_cmd.set_defaults(func=cmd_next)

    context = sub.add_parser("context", help="Return a compact session or ticket working packet.")
    _add_common(context)
    context.add_argument("ticket_id", nargs="?")
    context.add_argument("--next", action="store_true", help="Return the next actionable ready ticket packet.")
    context.set_defaults(func=cmd_context)

    edit = sub.add_parser("edit", help="Edit ticket metadata or narrative fields.")
    _add_common(edit)
    edit.add_argument("ticket_id")
    for name in ("title", "type", "priority", "severity", "area", "owner", "estimate", "risk", "labels", "source", "context", "acceptance", "notes", "validation", "handoff"):
        edit.add_argument(f"--{name}")
    edit.add_argument("--external-id", action="append", help="Set provider=id metadata; may be repeated.")
    edit.add_argument("--remove-external-id", action="append", help="Remove one provider id; may be repeated.")
    edit.set_defaults(func=cmd_edit)

    comment = sub.add_parser("comment", help="Append a compact activity entry.")
    _add_common(comment)
    comment.add_argument("ticket_id")
    comment.add_argument("message")
    comment.set_defaults(func=cmd_comment)

    move = sub.add_parser("move", help="Move a ticket through the workflow.")
    _add_common(move)
    _add_override(move)
    move.add_argument("ticket_id")
    move.add_argument("status", choices=STATUSES)
    move.set_defaults(func=cmd_move)

    validate = sub.add_parser("validate", help="Record validation evidence.")
    _add_common(validate)
    validate.add_argument("ticket_id")
    validate.add_argument("--result", choices=["passed", "failed", "skipped"], required=True)
    validate.add_argument("--command")
    validate.add_argument("--notes")
    validate.set_defaults(func=cmd_validate)

    close = sub.add_parser("close", help="Close a ticket with a resolution.")
    _add_common(close)
    _add_override(close)
    close.add_argument("ticket_id")
    close.add_argument("--resolution", required=True)
    close.add_argument("--wont-do", action="store_true")
    close.set_defaults(func=cmd_close)

    reopen = sub.add_parser("reopen", help="Reopen a closed ticket.")
    _add_common(reopen)
    reopen.add_argument("ticket_id")
    reopen.add_argument("--status", choices=["inbox", "backlog", "ready"], default="backlog")
    reopen.add_argument("--reason", required=True)
    reopen.set_defaults(func=cmd_reopen)

    for name, func in (("link", cmd_link), ("unlink", cmd_unlink)):
        relation = sub.add_parser(name, help=f"{name.title()} ticket dependencies.")
        _add_common(relation)
        relation.add_argument("ticket_id")
        relation.add_argument("relationship", choices=["depends-on", "blocks"])
        relation.add_argument("target_id")
        relation.set_defaults(func=func)

    render = sub.add_parser("render", help="Regenerate derived registry and views.")
    _add_common(render)
    render.set_defaults(func=cmd_render)

    sync = sub.add_parser("sync", help="Legacy alias for render.")
    _add_common(sync)
    sync.set_defaults(func=cmd_render)

    doctor = sub.add_parser("doctor", help="Validate canonical state without mutating it.")
    _add_common(doctor)
    doctor.set_defaults(func=cmd_doctor)

    migrate = sub.add_parser("migrate", help="Migrate an existing ticket schema safely.")
    _add_common(migrate)
    migrate.add_argument("--dry-run", action="store_true")
    migrate.set_defaults(func=cmd_migrate)

    sprint = sub.add_parser("sprint", help="Manage lightweight sprints.")
    sprint_sub = sprint.add_subparsers(dest="sprint_command", required=True)
    sprint_start = sprint_sub.add_parser("start")
    _add_common(sprint_start)
    sprint_start.add_argument("--name", required=True)
    sprint_start.add_argument("--goal", required=True)
    sprint_start.add_argument("--tickets", default="")
    sprint_start.add_argument("--start")
    sprint_start.add_argument("--end")
    sprint_start.add_argument("--risks")
    sprint_start.add_argument("--validation")
    sprint_start.add_argument("--force", action="store_true")
    sprint_start.set_defaults(func=cmd_sprint_start)
    sprint_add = sprint_sub.add_parser("add")
    _add_common(sprint_add)
    sprint_add.add_argument("--tickets", required=True)
    sprint_add.set_defaults(func=cmd_sprint_add)
    sprint_status = sprint_sub.add_parser("status")
    _add_common(sprint_status)
    sprint_status.set_defaults(func=cmd_sprint_status)
    sprint_close = sprint_sub.add_parser("close")
    _add_common(sprint_close)
    sprint_close.add_argument("--summary", required=True)
    sprint_close.add_argument("--carryover", default="")
    sprint_close.add_argument("--carryover-note")
    sprint_close.set_defaults(func=cmd_sprint_close)

    tracker = sub.add_parser("tracker-setup", help="Configure optional connector guidance; no automatic sync.")
    _add_common(tracker)
    tracker.add_argument("--provider", choices=TRACKER_PROVIDERS, required=True)
    tracker.add_argument("--mode", choices=TRACKER_MODES, default="hybrid")
    tracker.add_argument("--external-project", default="")
    tracker.add_argument("--connector", default="")
    tracker.set_defaults(func=cmd_tracker_setup)

    operating = sub.add_parser("operating-init", help="Legacy-compatible operating-document installer.")
    _add_common(operating)
    operating.add_argument("--mode", choices=["fast", "deep"], default="fast")
    operating.add_argument("--force", action="store_true")
    operating.set_defaults(func=cmd_operating_init)

    sync_hooks = sub.add_parser("sync-hooks", help="Legacy alias for tracker-setup.")
    _add_common(sync_hooks)
    sync_hooks.add_argument("--provider", choices=TRACKER_PROVIDERS, required=True)
    sync_hooks.add_argument("--mode", choices=["local-first", "hybrid", "external-first"], default="hybrid")
    sync_hooks.add_argument("--external-project", default="")
    sync_hooks.add_argument("--mcp-server", default="")
    sync_hooks.set_defaults(func=cmd_sync_hooks)

    linear = sub.add_parser("linear-setup", help="Legacy Linear tracker-setup alias.")
    _add_common(linear)
    linear.add_argument("--mode", choices=["repo-primary", "hybrid", "linear-primary"], default="repo-primary")
    linear.add_argument("--team", default="")
    linear.add_argument("--project", default="")
    linear.add_argument("--labels", default="")
    linear.add_argument("--work-lanes", default="")
    linear.add_argument("--changelog-title", default="")
    linear.add_argument("--mcp-server", default="")
    linear.set_defaults(func=cmd_linear_setup)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args.func(args)
    except (StoreError, OperatingError) as exc:
        parser.exit(1, f"Error: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
