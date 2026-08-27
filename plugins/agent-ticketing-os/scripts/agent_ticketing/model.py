"""Ticket parsing, validation, and rendering."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .constants import BODY_SECTIONS, PLACEHOLDER_MARKERS, PRIORITIES, STATUSES, TYPES
from .util import csv_items, is_placeholder


class TicketFormatError(ValueError):
    """Raised when a canonical ticket cannot be parsed safely."""


def _parse_frontmatter(text: str) -> tuple[dict[str, Any], str, bool]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise TicketFormatError("ticket must begin with a --- metadata delimiter")
    try:
        closing = next(index for index, line in enumerate(lines[1:], 1) if line.strip() == "---")
    except StopIteration as exc:
        raise TicketFormatError("ticket metadata is missing its closing --- delimiter") from exc
    raw = "\n".join(lines[1:closing]).strip()
    if not raw:
        raise TicketFormatError("ticket metadata is empty")
    try:
        metadata = json.loads(raw)
        if not isinstance(metadata, dict):
            raise TicketFormatError("ticket metadata must be a JSON object")
        return metadata, "\n".join(lines[closing + 1 :]).lstrip(), False
    except json.JSONDecodeError:
        metadata: dict[str, Any] = {}
        for line in lines[1:closing]:
            if not line.strip():
                continue
            if ":" not in line:
                raise TicketFormatError(f"invalid legacy metadata line: {line}")
            key, value = line.split(":", 1)
            metadata[key.strip()] = value.strip()
        return metadata, "\n".join(lines[closing + 1 :]).lstrip(), True


def _parse_sections(body_text: str) -> dict[str, Any]:
    section_lookup = {heading: key for key, heading in BODY_SECTIONS}
    matches = list(re.finditer(r"(?m)^## ([^\n]+)\s*$", body_text))
    sections: dict[str, Any] = {}
    for index, match in enumerate(matches):
        heading = match.group(1).strip()
        key = section_lookup.get(heading)
        if not key:
            raise TicketFormatError(
                f"unsupported level-two section '{heading}'; use a level-three subsection inside a canonical section"
            )
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body_text)
        value = body_text[match.end() : end].strip()
        if key == "activity":
            sections[key] = [
                line[2:].strip()
                for line in value.splitlines()
                if line.startswith("- ") and line[2:].strip() not in {"No activity yet.", "None"}
            ]
        else:
            sections[key] = value
    return sections


def normalize_ticket(ticket: dict[str, Any]) -> dict[str, Any]:
    result = dict(ticket)
    for key in ("labels", "depends_on", "blocks"):
        value = result.get(key, [])
        if isinstance(value, str):
            result[key] = csv_items(value)
        elif isinstance(value, list):
            result[key] = list(dict.fromkeys(str(item).strip() for item in value if str(item).strip()))
        else:
            result[key] = []
    external_ids = result.get("external_ids", {})
    result["external_ids"] = external_ids if isinstance(external_ids, dict) else {}
    for key, default in {
        "severity": "",
        "owner": "agent",
        "estimate": "",
        "risk": "medium",
        "source": "agent",
    }.items():
        if result.get(key) is None:
            result[key] = default
        else:
            result.setdefault(key, default)
    result.setdefault("activity", [])
    result.setdefault("body", {})
    body = dict(result["body"])
    body.setdefault("context", "Context to be expanded.")
    body.setdefault("acceptance", "- [ ] Acceptance criteria to be confirmed.")
    body.setdefault("notes", "Implementation notes to be added.")
    body.setdefault("validation", "- [ ] Validation plan to be confirmed.")
    body.setdefault("evidence", "Not recorded.")
    body.setdefault("handoff", "No handoff notes yet.")
    body.setdefault("closure", "Open.")
    result["body"] = body
    return result


def parse_ticket(path: Path) -> tuple[dict[str, Any], bool]:
    metadata, body_text, legacy = _parse_frontmatter(path.read_text(encoding="utf-8"))
    sections = _parse_sections(body_text)
    title_match = re.search(r"(?m)^#\s+(?:[A-Z]+-\d+:\s*)?(.+?)\s*$", body_text)
    if not metadata.get("title") and title_match:
        metadata["title"] = title_match.group(1).strip()
    metadata["body"] = {key: value for key, value in sections.items() if key != "activity"}
    metadata["activity"] = sections.get("activity", [])
    return normalize_ticket(metadata), legacy


def metadata_for(ticket: dict[str, Any]) -> dict[str, Any]:
    required = [
        "id",
        "title",
        "type",
        "status",
        "priority",
        "area",
        "created",
        "updated",
    ]
    metadata = {key: ticket.get(key, "") for key in required}
    for key in ("severity", "estimate"):
        if ticket.get(key):
            metadata[key] = ticket[key]
    for key in ("labels", "depends_on", "blocks", "external_ids"):
        if ticket.get(key):
            metadata[key] = ticket[key]
    for key, default in (("owner", "agent"), ("risk", "medium"), ("source", "agent")):
        if ticket.get(key) not in {None, "", default}:
            metadata[key] = ticket[key]
    return metadata


def render_ticket(ticket: dict[str, Any]) -> str:
    ticket = normalize_ticket(ticket)
    metadata = json.dumps(metadata_for(ticket), indent=2, sort_keys=True)
    body = ticket["body"]
    activity = ticket.get("activity", [])
    activity_text = "\n".join(f"- {item}" for item in activity) or "- No activity yet."
    return (
        f"---\n{metadata}\n---\n\n"
        f"# {ticket['id']}: {ticket['title']}\n\n"
        f"## Context\n\n{body['context']}\n\n"
        f"## Acceptance Criteria\n\n{body['acceptance']}\n\n"
        f"## Implementation Notes\n\n{body['notes']}\n\n"
        f"## Validation Plan\n\n{body['validation']}\n\n"
        f"## Validation Evidence\n\n{body['evidence']}\n\n"
        f"## Agent Handoff\n\n{body['handoff']}\n\n"
        f"## Activity Log\n\n{activity_text}\n\n"
        f"## Closure\n\n{body['closure']}\n"
    )


def validate_ticket(ticket: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    ticket_id = ticket.get("id", "<unknown>")
    if not re.fullmatch(r"[A-Z][A-Z0-9]*-\d{4,}", str(ticket.get("id", ""))):
        errors.append(f"{ticket_id}: invalid id")
    if not str(ticket.get("title", "")).strip():
        errors.append(f"{ticket_id}: title is required")
    elif "\n" in str(ticket.get("title")):
        errors.append(f"{ticket_id}: title must be one line")
    if ticket.get("status") not in STATUSES:
        errors.append(f"{ticket_id}: invalid status {ticket.get('status')}")
    if ticket.get("type") not in TYPES:
        errors.append(f"{ticket_id}: invalid type {ticket.get('type')}")
    if ticket.get("priority") not in PRIORITIES:
        errors.append(f"{ticket_id}: invalid priority {ticket.get('priority')}")
    if not str(ticket.get("area", "")).strip():
        errors.append(f"{ticket_id}: area is required")
    elif "\n" in str(ticket.get("area")):
        errors.append(f"{ticket_id}: area must be one line")
    return errors


def readiness_problems(ticket: dict[str, Any]) -> list[str]:
    body = ticket.get("body", {})
    problems: list[str] = []
    for key in ("context", "acceptance", "validation"):
        value = str(body.get(key, ""))
        if is_placeholder(value, PLACEHOLDER_MARKERS[key]):
            problems.append(f"{key.replace('_', ' ')} is missing or still a placeholder")
    if not str(ticket.get("area", "")).strip():
        problems.append("area is missing")
    return problems


def closure_problems(ticket: dict[str, Any]) -> list[str]:
    problems = readiness_problems(ticket)
    acceptance = str(ticket.get("body", {}).get("acceptance", ""))
    if re.search(r"(?m)^\s*(?:[-*+]|\d+\.)\s+\[\s\]", acceptance):
        problems.append("acceptance criteria remain unchecked")
    evidence = str(ticket.get("body", {}).get("evidence", ""))
    if is_placeholder(evidence, PLACEHOLDER_MARKERS["evidence"]):
        problems.append("validation evidence is missing")
    elif "[PASSED]" not in evidence and "[SKIPPED]" not in evidence:
        problems.append("validation has no passed result or documented skip")
    return problems


def summary(ticket: dict[str, Any], relative_path: str) -> dict[str, Any]:
    data = metadata_for(ticket)
    data["file"] = relative_path
    return data
