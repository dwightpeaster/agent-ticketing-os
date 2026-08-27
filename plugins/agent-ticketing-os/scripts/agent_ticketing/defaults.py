"""Generic configuration and repository detection."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import SCHEMA_VERSION, SYSTEM_VERSION
from .constants import PRIORITIES, STATUSES, TYPES
from .util import load_json, now


IGNORED_AREAS = {
    "node_modules",
    "vendor",
    "dist",
    "build",
    "coverage",
    "target",
    "venv",
    ".venv",
    "docs",
    "tests",
}


def _repo_directories(root: Path) -> list[str]:
    if not root.exists():
        return []
    return sorted(
        path.name
        for path in root.iterdir()
        if path.is_dir() and not path.name.startswith(".") and path.name not in IGNORED_AREAS
    )


def detect_repo(root: Path) -> dict[str, Any]:
    files = {path.name for path in root.iterdir()} if root.exists() else set()
    directories = _repo_directories(root)
    kind = "generic"
    commands: list[str] = []

    if "package.json" in files:
        kind = "node"
        package = load_json(root / "package.json", {})
        scripts = package.get("scripts", {}) if isinstance(package, dict) else {}
        runner = "pnpm" if "pnpm-lock.yaml" in files else "yarn" if "yarn.lock" in files else "npm run"
        for script in ("test", "lint", "typecheck", "build"):
            if script in scripts:
                commands.append(f"{runner} {script}" if runner != "yarn" else f"yarn {script}")
    if "pyproject.toml" in files or "setup.py" in files or "requirements.txt" in files:
        kind = "python" if kind == "generic" else "mixed"
        commands.append("python3 -m pytest")
    if "Cargo.toml" in files:
        kind = "rust" if kind == "generic" else "mixed"
        commands.extend(["cargo test", "cargo clippy --all-targets --all-features"])
    if "go.mod" in files:
        kind = "go" if kind == "generic" else "mixed"
        commands.append("go test ./...")
    if "composer.json" in files:
        kind = "php" if kind == "generic" else "mixed"
        commands.append("composer test")
    if any(name.endswith(".sln") for name in files):
        kind = "dotnet" if kind == "generic" else "mixed"
        commands.append("dotnet test")

    areas = directories[:10]
    for standard in ("tests", "docs", "repo"):
        if standard not in areas:
            areas.append(standard)
    if areas == ["tests", "docs", "repo"]:
        areas = ["app", "api", "data", "tests", "docs", "repo"]
    return {"kind": kind, "validation_commands": list(dict.fromkeys(commands)), "areas": areas}


def default_config(root: Path, profile: str = "standard") -> dict[str, Any]:
    detected = detect_repo(root)
    normalized = profile
    if profile == "generic":
        normalized = "standard"
    if profile == "strict":
        normalized = "guarded"
    guarded = normalized == "guarded"
    created = now()
    return {
        "schema_version": SCHEMA_VERSION,
        "system_version": SYSTEM_VERSION,
        "created": created,
        "updated": created,
        "project": {
            "name": root.name,
            "mission": "Keep repository work clear, reviewable, and easy to resume.",
            "repo_kind": detected["kind"],
        },
        "ticketing": {
            "prefix": "T",
            "layout": "split-board" if guarded else "local-ticket-files",
            "default_status": "inbox",
            "default_priority": "P2",
            "statuses": STATUSES,
            "types": TYPES,
            "priorities": PRIORITIES,
            "areas": detected["areas"],
        },
        "workflow": {
            "policy": "guarded" if guarded else "standard",
            "require_ticket_for_meaningful_changes": True,
            "require_close_command_for_closed_status": True,
            "allow_override_with_reason": True,
        },
        "operating": {
            "profile": "compact",
            "docs_root": "docs/agent-workflow",
            "managed_agent_instructions": True,
        },
        "validation": {
            "commands": detected["validation_commands"],
            "definition_of_done": [
                "Acceptance criteria are satisfied or gaps are documented",
                "Validation evidence or a skipped-validation reason is recorded",
                "Ticket activity and handoff notes are current",
                "Deferred work has a follow-up ticket",
            ],
        },
        "trackers": {},
    }
