"""Small dependency-free helpers."""

from __future__ import annotations

import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return re.sub(r"-+", "-", value).strip("-") or "ticket"


def csv_items(value: str | None) -> list[str]:
    if not value:
        return []
    return list(dict.fromkeys(item.strip() for item in value.split(",") if item.strip()))


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def atomic_write(path: Path, content: str) -> bool:
    """Write only changed content and replace the destination atomically."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_text(encoding="utf-8") == content:
        return False
    target_mode = (path.stat().st_mode & 0o777) if path.exists() else 0o644
    handle = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    )
    temp_path = Path(handle.name)
    try:
        with handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temp_path, target_mode)
        os.replace(temp_path, path)
    finally:
        if temp_path.exists():
            temp_path.unlink()
    return True


def write_json(path: Path, data: Any) -> bool:
    return atomic_write(path, json.dumps(data, indent=2, sort_keys=True) + "\n")


def write_if_missing(path: Path, content: str) -> bool:
    if path.exists():
        return False
    return atomic_write(path, content.rstrip() + "\n")


def is_placeholder(value: str, markers: list[str]) -> bool:
    normalized = " ".join(value.lower().split())
    return not normalized or any(marker in normalized for marker in markers)


def latest_timestamp(values: list[str], fallback: str) -> str:
    candidates = [value for value in values if value]
    return max(candidates) if candidates else fallback
