from __future__ import annotations

import json
from pathlib import Path

from thingflash.core.planner import Resource
from thingflash.core.scaffold import STATE_DIRNAME

APPLIED_FILENAME = "applied.json"


def _applied_path(root: Path) -> Path:
    return root / STATE_DIRNAME / APPLIED_FILENAME


def load_applied(root: Path | None = None) -> list[Resource]:
    """Return the resources currently recorded as applied."""
    root = root or Path.cwd()
    path = _applied_path(root)
    if not path.exists():
        return []
    raw = json.loads(path.read_text())
    return [Resource(type=item["type"], name=item["name"]) for item in raw]


def save_applied(resources: list[Resource], root: Path | None = None) -> None:
    """Persist the applied resource set."""
    root = root or Path.cwd()
    path = _applied_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [{"type": r.type, "name": r.name} for r in resources]
    path.write_text(json.dumps(payload, indent=2))
