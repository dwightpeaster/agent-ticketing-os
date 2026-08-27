"""Canonical Markdown ticket storage with locking and migration support."""

from __future__ import annotations

import contextlib
import os
import re
import shutil
from pathlib import Path
from typing import Any, Iterator

from . import SCHEMA_VERSION, SYSTEM_VERSION
from .defaults import default_config
from .constants import CLOSED_STATUSES
from .model import TicketFormatError, normalize_ticket, parse_ticket, readiness_problems, render_ticket, summary, validate_ticket
from .util import atomic_write, load_json, now, slugify, write_if_missing, write_json


class StoreError(RuntimeError):
    """Raised when local ticket state is unavailable or unsafe to modify."""


class TicketStore:
    def __init__(self, root: Path):
        self.root = root.expanduser().resolve()
        self.directory = self.root / ".tickets"
        self.config_path = self.directory / "config.json"
        self.registry_path = self.directory / "REGISTRY.json"
        self.ticket_directory = self.directory / "tickets"

    def ensure_initialized(self) -> None:
        self._ensure_local_directory(self.directory, ".tickets")
        if self.config_path.is_symlink():
            raise StoreError("Refusing symbolic-link ticket configuration: .tickets/config.json")
        if not self.config_path.exists():
            raise StoreError("No .tickets/config.json found. Run the Agent Ticketing OS installer.")

    def _ensure_local_directory(self, path: Path, label: str) -> None:
        if path.is_symlink():
            raise StoreError(f"Refusing symbolic-link ticket directory: {label}")
        try:
            path.resolve().relative_to(self.root)
        except ValueError as exc:
            raise StoreError(f"Refusing ticket directory outside the repository: {label}") from exc

    @contextlib.contextmanager
    def lock(self) -> Iterator[None]:
        self._ensure_local_directory(self.directory, ".tickets")
        self.directory.mkdir(parents=True, exist_ok=True)
        lock_path = self.directory / ".lock"
        with lock_path.open("a+", encoding="utf-8") as handle:
            try:
                import fcntl
            except ImportError:
                import msvcrt

                if lock_path.stat().st_size == 0:
                    handle.write("0")
                    handle.flush()
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
                try:
                    yield
                finally:
                    handle.seek(0)
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
                try:
                    yield
                finally:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    def load_config(self) -> dict[str, Any]:
        self.ensure_initialized()
        config = load_json(self.config_path, {})
        if not isinstance(config, dict):
            raise StoreError(".tickets/config.json must contain a JSON object")
        version = int(config.get("schema_version", 1))
        if version > SCHEMA_VERSION:
            raise StoreError(
                f"Ticket schema {version} is newer than this installation supports ({SCHEMA_VERSION})."
            )
        return config

    def initialize(self, profile: str = "standard") -> dict[str, Any]:
        if self.config_path.exists():
            raise StoreError(".tickets/config.json already exists; run install to upgrade or repair it.")
        self.root.mkdir(parents=True, exist_ok=True)
        for relative in ("tickets", "reports", "sprints", "trackers", "backups"):
            (self.directory / relative).mkdir(parents=True, exist_ok=True)
        write_if_missing(self.directory / ".gitignore", ".lock\n.*.tmp\nbackups/\n")
        config = default_config(self.root, profile)
        write_json(self.config_path, config)
        self.render_all()
        return config

    def _safe_path(self, path: Path) -> Path:
        self._ensure_local_directory(self.ticket_directory, ".tickets/tickets")
        if path.is_symlink():
            raise StoreError(f"Refusing symbolic-link ticket file: {path}")
        resolved = path.resolve()
        try:
            resolved.relative_to(self.ticket_directory.resolve())
        except ValueError as exc:
            raise StoreError(f"Refusing to access a ticket outside .tickets/tickets: {path}") from exc
        return resolved

    def ticket_paths(self) -> list[Path]:
        if not self.ticket_directory.exists():
            return []
        self._ensure_local_directory(self.ticket_directory, ".tickets/tickets")
        candidates = sorted(self.ticket_directory.glob("*.md"))
        symlinks = [path for path in candidates if path.is_symlink()]
        if symlinks:
            names = ", ".join(str(path.relative_to(self.root)) for path in symlinks)
            raise StoreError(f"Refusing symbolic-link ticket files: {names}")
        return [path for path in candidates if path.is_file()]

    def load_tickets(self) -> list[dict[str, Any]]:
        tickets: list[dict[str, Any]] = []
        seen: set[str] = set()
        errors: list[str] = []
        for path in self.ticket_paths():
            try:
                ticket, _legacy = parse_ticket(path)
            except TicketFormatError as exc:
                errors.append(f"{path.relative_to(self.root)}: {exc}")
                continue
            ticket_id = str(ticket.get("id", ""))
            if ticket_id in seen:
                errors.append(f"duplicate ticket id: {ticket_id}")
            seen.add(ticket_id)
            ticket["_path"] = path
            errors.extend(validate_ticket(ticket))
            tickets.append(ticket)
        if errors:
            raise StoreError("Invalid ticket state:\n- " + "\n- ".join(errors))
        return tickets

    def find(self, ticket_id: str, tickets: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        for ticket in tickets if tickets is not None else self.load_tickets():
            if ticket.get("id") == ticket_id:
                return ticket
        raise StoreError(f"Ticket not found: {ticket_id}")

    def next_id(self, config: dict[str, Any], tickets: list[dict[str, Any]]) -> str:
        prefix = str(config.get("ticketing", {}).get("prefix", "T")).upper()
        pattern = re.compile(rf"^{re.escape(prefix)}-(\d+)$")
        numbers = [int(match.group(1)) for ticket in tickets if (match := pattern.match(str(ticket.get("id", ""))))]
        return f"{prefix}-{(max(numbers, default=0) + 1):04d}"

    def create(self, fields: dict[str, Any]) -> dict[str, Any]:
        config = self.load_config()
        tickets = self.load_tickets()
        created = now()
        ticket = normalize_ticket(
            {
                "id": self.next_id(config, tickets),
                "title": fields["title"].strip(),
                "type": fields.get("type", "feature"),
                "status": fields.get("status") or config["ticketing"].get("default_status", "inbox"),
                "priority": fields.get("priority") or config["ticketing"].get("default_priority", "P2"),
                "severity": fields.get("severity", ""),
                "area": fields.get("area") or "repo",
                "owner": fields.get("owner") or "agent",
                "estimate": fields.get("estimate", ""),
                "risk": fields.get("risk") or "medium",
                "labels": fields.get("labels", []),
                "depends_on": fields.get("depends_on", []),
                "blocks": fields.get("blocks", []),
                "source": fields.get("source") or "agent",
                "external_ids": {},
                "created": created,
                "updated": created,
                "body": {
                    "context": fields.get("context") or "Context to be expanded.",
                    "acceptance": fields.get("acceptance") or "- [ ] Acceptance criteria to be confirmed.",
                    "notes": fields.get("notes") or "Implementation notes to be added.",
                    "validation": fields.get("validation") or "- [ ] Validation plan to be confirmed.",
                    "evidence": "Not recorded.",
                    "handoff": fields.get("handoff") or "No handoff notes yet.",
                    "closure": "Open.",
                },
                "activity": [f"{created} created by ticketctl."],
            }
        )
        errors = validate_ticket(ticket)
        if ticket["status"] in CLOSED_STATUSES:
            errors.append(f"{ticket['id']}: create open work first and use close for closed statuses")
        if (
            config.get("workflow", {}).get("policy") == "guarded"
            and ticket["status"] in {"ready", "in_progress", "review"}
        ):
            errors.extend(f"{ticket['id']}: {problem}" for problem in readiness_problems(ticket))
        if errors:
            raise StoreError("Cannot create ticket:\n- " + "\n- ".join(errors))
        path = self.ticket_directory / f"{ticket['id']}-{slugify(ticket['title'])}.md"
        ticket["_path"] = path
        atomic_write(path, render_ticket(ticket))
        self.render_all()
        return ticket

    def save_ticket(self, ticket: dict[str, Any]) -> bool:
        path = ticket.get("_path")
        if not isinstance(path, Path):
            path = self.ticket_directory / f"{ticket['id']}-{slugify(ticket['title'])}.md"
        path = self._safe_path(path)
        ticket["_path"] = path
        errors = validate_ticket(ticket)
        if errors:
            raise StoreError("Cannot save ticket:\n- " + "\n- ".join(errors))
        return atomic_write(path, render_ticket(ticket))

    def render_all(self) -> dict[str, int]:
        from .render import render_views

        if self.registry_path.is_symlink():
            raise StoreError("Refusing symbolic-link generated registry: .tickets/REGISTRY.json")
        config = self.load_config()
        tickets = self.load_tickets()
        changed = render_views(self, config, tickets)
        registry = {
            "schema_version": SCHEMA_VERSION,
            "system_version": SYSTEM_VERSION,
            "generated_from": "canonical Markdown ticket files",
            "generated_at": max(
                [str(ticket.get("updated", "")) for ticket in tickets] + [str(config.get("updated", config.get("created", "")))]
            ),
            "next_number": int(self.next_id(config, tickets).split("-", 1)[1]),
            "tickets": [
                summary(ticket, str(ticket["_path"].relative_to(self.root)))
                for ticket in sorted(tickets, key=lambda item: str(item.get("id", "")))
            ],
        }
        if write_json(self.registry_path, registry):
            changed["registry"] = 1
        return changed

    def _backup_v1(self) -> Path:
        stamp = now().replace(":", "").replace("+", "-")
        backup = self.directory / "backups" / f"schema-v1-{stamp}"
        counter = 1
        while backup.exists():
            backup = self.directory / "backups" / f"schema-v1-{stamp}-{counter}"
            counter += 1
        backup.mkdir(parents=True)
        for path in (self.config_path, self.registry_path):
            if path.exists():
                shutil.copy2(path, backup / path.name)
        if self.ticket_directory.exists():
            shutil.copytree(self.ticket_directory, backup / "tickets")
        return backup

    def migration_report(self) -> dict[str, Any]:
        config = load_json(self.config_path, {})
        version = int(config.get("schema_version", 1)) if isinstance(config, dict) else 1
        return {
            "from_schema": version,
            "to_schema": SCHEMA_VERSION,
            "ticket_files": len(self.ticket_paths()),
            "needs_migration": version < SCHEMA_VERSION,
        }

    def migrate(self, dry_run: bool = False) -> dict[str, Any]:
        self.ensure_initialized()
        old_config = load_json(self.config_path, {})
        old_version = int(old_config.get("schema_version", 1))
        report = self.migration_report()
        if old_version == SCHEMA_VERSION:
            report["status"] = "current"
            return report
        if old_version > SCHEMA_VERSION:
            raise StoreError(f"Cannot downgrade schema {old_version} to {SCHEMA_VERSION}.")
        if dry_run:
            report["status"] = "dry-run"
            return report

        write_if_missing(self.directory / ".gitignore", ".lock\n.*.tmp\nbackups/\n")
        backup = self._backup_v1()
        legacy_registry = load_json(self.registry_path, {"tickets": []})
        registry_by_id = {
            str(item.get("id")): item
            for item in legacy_registry.get("tickets", [])
            if isinstance(item, dict) and item.get("id")
        }
        migrated: list[dict[str, Any]] = []
        seen: set[str] = set()
        for path in self.ticket_paths():
            try:
                ticket, _legacy = parse_ticket(path)
            except TicketFormatError as exc:
                raise StoreError(
                    f"Cannot migrate {path.relative_to(self.root)} safely: {exc}. "
                    f"The schema-1 backup is available at {backup.relative_to(self.root)}."
                ) from exc
            ticket["_path"] = path
            migrated.append(ticket)
            seen.add(str(ticket.get("id")))
        for ticket_id, item in registry_by_id.items():
            if ticket_id in seen:
                continue
            ticket = normalize_ticket(item)
            relative = item.get("file")
            path = self._safe_path(self.root / relative) if relative else self.ticket_directory / f"{ticket_id}-{slugify(ticket['title'])}.md"
            ticket["_path"] = path
            migrated.append(ticket)

        old_profile = str(old_config.get("project", {}).get("profile", "generic"))
        profile = "guarded" if old_profile == "strict" or old_config.get("ticketing", {}).get("layout") == "split-board" else "standard"
        base_config = default_config(self.root, profile)
        config = default_config(self.root, profile)
        config["created"] = old_config.get("created", legacy_registry.get("created", config["created"]))
        for section in ("project", "ticketing", "validation"):
            if isinstance(old_config.get(section), dict):
                config[section].update(old_config[section])
        config["project"].pop("profile", None)
        legacy_missions = {
            "Track repo work clearly enough that any agent can continue it.",
            "Track work with one readable working board, a deferred backlog, one-line completed archives, and strict agent handoffs.",
        }
        if config["project"].get("mission") in legacy_missions:
            config["project"]["mission"] = base_config["project"]["mission"]
        legacy_area_sets = {
            tuple(["app", "components", "api", "data", "tests", "docs", "repo"]),
            tuple(["dashboard", "customers", "leads", "calls", "inventory", "navigation", "components", "hooks", "types", "repo"]),
            tuple(["backend", "mobile", "dashboard", "public", "notifications", "security", "deployment", "docs", "repo"]),
        }
        if tuple(config["ticketing"].get("areas", [])) in legacy_area_sets:
            config["ticketing"]["areas"] = base_config["ticketing"]["areas"]
        if config["ticketing"].get("default_status") == "ready":
            config["ticketing"]["default_status"] = "inbox"
        config["ticketing"].pop("phase_ranges", None)
        config["ticketing"].pop("readiness_gate", None)
        config["ticketing"].pop("locations", None)
        config["ticketing"].pop("display_statuses", None)
        old_done = config.get("validation", {}).get("definition_of_done", [])
        if old_done and (
            old_done[0] in {"Acceptance criteria satisfied", "The change maps to one active ticket"}
        ):
            config["validation"]["definition_of_done"] = base_config["validation"]["definition_of_done"]
        config["schema_version"] = SCHEMA_VERSION
        config["system_version"] = SYSTEM_VERSION
        config["updated"] = now()
        legacy_trackers = old_config.get("sync", {})
        if isinstance(legacy_trackers, dict):
            mode_map = {"local-first": "local-primary", "external-first": "external-primary"}
            for provider, legacy in legacy_trackers.items():
                if not isinstance(legacy, dict):
                    continue
                config["trackers"][provider] = {
                    "provider": provider,
                    "mode": mode_map.get(str(legacy.get("mode", "hybrid")), str(legacy.get("mode", "hybrid"))),
                    "external_project": legacy.get("external_project", legacy.get("project", "")),
                    "connector": legacy.get("mcp_server", provider),
                    "enabled": bool(legacy.get("enabled", True)),
                    "automatic_sync": False,
                    "updated": config["updated"],
                }
        config["migration"] = {
            "from_schema": old_version,
            "backup": str(backup.relative_to(self.root)),
            "migrated_at": config["updated"],
        }
        write_json(self.config_path, config)
        write_if_missing(self.directory / ".gitignore", ".lock\n.*.tmp\nbackups/\n")
        for ticket in migrated:
            self.save_ticket(ticket)
        self.render_all()
        report.update({"status": "migrated", "backup": str(backup.relative_to(self.root)), "tickets": len(migrated)})
        return report
