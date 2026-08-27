"""Install concise, agent-readable workflow documents without clobbering user content."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from . import SYSTEM_VERSION
from .util import atomic_write, load_json, now, write_json


ASSET_ROOT = Path(__file__).resolve().parents[2] / "assets"
MANAGED_START = "<!-- agent-ticketing-os:start -->"
MANAGED_END = "<!-- agent-ticketing-os:end -->"

COMPACT_DOCS = [
    "TICKET_STANDARDS.md",
    "BRANCH_WORKFLOW.md",
    "IMPLEMENTATION_WORKFLOW.md",
    "COMMIT_WORKFLOW.md",
    "DEFINITION_OF_DONE.md",
    "REVIEW_AND_HANDOFF.md",
]

EXTENDED_DOCS = [
    "QA_GUIDE.md",
    "RELEASE_RUNBOOK.md",
    "SECURITY_WORKFLOW.md",
    "WRITING_STANDARDS.md",
    "REPOSITORY_MAP.md",
]


class OperatingError(RuntimeError):
    """Raised when generated operating guidance cannot be updated safely."""


def _digest(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _managed_instructions() -> str:
    return f"""{MANAGED_START}
## Agent Ticketing OS

This repository uses Agent Ticketing OS. Canonical tickets are the source of truth for agent work.

### Always

- Start or resume with the installed ticket engine's `context` command. Use `context --next` when no ticket is active.
- Do not begin meaningful implementation without an active ticket unless the user explicitly waives that requirement.
- Keep one coherent outcome per ticket. Do not silently expand scope; create linked follow-up tickets for separate discoveries.
- Use the ticket engine for state changes. `.tickets/tickets/*.md` files are canonical; boards and registries are generated views.
- Before editing, inspect the current branch and working tree. Preserve unrelated user changes and existing repository instructions.
- Inspect nearby code and prefer established repository patterns before introducing abstractions or dependencies.
- Never store secrets, credentials, tokens, private customer data, or sensitive URLs in tickets or workflow documents.
- Do not mark work complete without recorded validation evidence or a documented reason validation could not run.
- Update affected tests, documentation, configuration examples, and setup instructions when behavior changes.
- External trackers are disabled unless repository configuration or the user explicitly enables one. No synchronization is automatic.

### Load By Phase

- Triage or ticket restructuring: `docs/agent-workflow/TICKET_STANDARDS.md`.
- Branch or pull-request work: `docs/agent-workflow/BRANCH_WORKFLOW.md`.
- Implementation, new abstractions, dependencies, or deletion: `docs/agent-workflow/IMPLEMENTATION_WORKFLOW.md`.
- Staging or committing: `docs/agent-workflow/COMMIT_WORKFLOW.md`.
- Review, closure, or handoff: `docs/agent-workflow/DEFINITION_OF_DONE.md` and `docs/agent-workflow/REVIEW_AND_HANDOFF.md`.

### Handoff

Before final handoff, run the ticket engine's `doctor` command and record the ticket status, outcome, important files, validation results, remaining risks, and next recommended action.
{MANAGED_END}"""


def _merge_managed_block(path: Path, block: str) -> str:
    if not path.exists():
        return f"# Agent Instructions\n\n{block}\n"
    current = path.read_text(encoding="utf-8")
    if (MANAGED_START in current) != (MANAGED_END in current):
        raise OperatingError(f"Refusing to edit {path}: Agent Ticketing OS managed markers are incomplete")
    if MANAGED_START in current and MANAGED_END in current:
        before, remainder = current.split(MANAGED_START, 1)
        _old, after = remainder.split(MANAGED_END, 1)
        return f"{before.rstrip()}\n\n{block}{after.rstrip()}\n"
    return f"{current.rstrip()}\n\n{block}\n"


def _asset_content(name: str, project: str) -> str:
    path = ASSET_ROOT / "operating" / name
    if not path.exists():
        raise RuntimeError(f"Missing operating asset: {path}")
    return path.read_text(encoding="utf-8").replace("{{PROJECT}}", project).rstrip() + "\n"


def install_ticket_templates(store: Any) -> dict[str, int]:
    source = ASSET_ROOT / "ticket-templates"
    destination = store.directory / "templates"
    created = 0
    preserved = 0
    for asset in sorted(source.glob("*.md")):
        target = destination / asset.name
        if target.is_symlink():
            raise OperatingError(f"Refusing symbolic-link ticket template: {target}")
        if target.exists():
            preserved += 1
            continue
        atomic_write(target, asset.read_text(encoding="utf-8").rstrip() + "\n")
        created += 1
    return {"created": created, "preserved": preserved}


def install_operating_docs(store: Any, profile: str = "compact") -> dict[str, Any]:
    config = store.load_config()
    project = str(config.get("project", {}).get("name", store.root.name))
    docs_root = (store.root / str(config.get("operating", {}).get("docs_root", "docs/agent-workflow"))).resolve()
    try:
        docs_root.relative_to(store.root)
    except ValueError as exc:
        raise OperatingError(f"Refusing operating docs path outside the repository: {docs_root}") from exc
    marker_path = store.directory / "operating.json"
    if marker_path.is_symlink():
        raise OperatingError(f"Refusing symbolic-link operating marker: {marker_path}")
    marker = load_json(marker_path, {"files": {}})
    old_hashes = marker.get("files", {}) if isinstance(marker, dict) else {}
    new_hashes = dict(old_hashes)
    report: dict[str, Any] = {"created": [], "updated": [], "preserved": []}
    names = [*COMPACT_DOCS, *(EXTENDED_DOCS if profile == "extended" else [])]

    for name in names:
        content = _asset_content(name, project)
        path = docs_root / name
        if path.is_symlink():
            raise OperatingError(f"Refusing symbolic-link operating document: {path}")
        relative = str(path.relative_to(store.root))
        previous_hash = old_hashes.get(relative)
        if not path.exists():
            atomic_write(path, content)
            report["created"].append(relative)
            new_hashes[relative] = _digest(content)
            continue
        current = path.read_text(encoding="utf-8")
        if previous_hash and _digest(current) == previous_hash:
            if atomic_write(path, content):
                report["updated"].append(relative)
            new_hashes[relative] = _digest(content)
        elif current == content:
            new_hashes[relative] = _digest(content)
        else:
            report["preserved"].append(relative)

    block = _managed_instructions()
    for name in ("AGENTS.md", "CLAUDE.md"):
        path = store.root / name
        if path.is_symlink():
            raise OperatingError(f"Refusing symbolic-link agent instructions: {path}")
        existed = path.exists()
        merged = _merge_managed_block(path, block)
        if atomic_write(path, merged):
            report["updated" if existed else "created"].append(name)

    templates = install_ticket_templates(store)
    report["templates"] = templates
    config_changed = (
        config.get("operating", {}).get("profile") != profile
        or config.get("system_version") != SYSTEM_VERSION
    )
    if config_changed:
        config["operating"]["profile"] = profile
        config["system_version"] = SYSTEM_VERSION
        config["updated"] = now()
        write_json(store.config_path, config)
    marker_changed = marker.get("profile") != profile or old_hashes != new_hashes
    material_changed = bool(report["created"] or report["updated"] or templates["created"])
    if marker_changed or material_changed or not marker_path.exists():
        marker = {
            "profile": profile,
            "files": new_hashes,
            "updated": config.get("updated", marker.get("updated", now())),
        }
        write_json(marker_path, marker)
    return report
