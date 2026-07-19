from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

from thingflash.core.errors import AlreadyExistsError, NotFoundError, ValidationError

REGISTRY_PATH = Path(".thingflash") / "registry.json"

_THING_NAME_RE = re.compile(r"^[a-zA-Z0-9:_-]{1,128}$")


@dataclass
class Thing:
    """A registered Thing (device)."""

    name: str
    thing_type: str | None = None
    cert_expiry: str | None = None


def _validate_name(name: str) -> None:
    if not _THING_NAME_RE.match(name):
        raise ValidationError(
            f"Invalid Thing name: {name!r}",
            code="INVALID_NAME",
            hint="Use 1-128 characters from a-z, A-Z, 0-9, colon, underscore, or hyphen.",
        )


def _load() -> dict[str, Thing]:
    if not REGISTRY_PATH.exists():
        return {}
    raw = json.loads(REGISTRY_PATH.read_text())
    return {name: Thing(**data) for name, data in raw.items()}


def _save(things: dict[str, Thing]) -> None:
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY_PATH.write_text(
        json.dumps({name: asdict(thing) for name, thing in things.items()}, indent=2)
    )


def list_things() -> list[Thing]:
    """Return all registered Things, ordered by name."""
    things = _load()
    return [things[name] for name in sorted(things)]


def create_thing(name: str, thing_type: str | None = None) -> Thing:
    """Register a Thing. Idempotent: creating an existing Thing is an error only
    when the requested type conflicts."""
    _validate_name(name)
    things = _load()
    existing = things.get(name)
    if existing is not None:
        if thing_type is not None and existing.thing_type != thing_type:
            raise AlreadyExistsError(
                f"Thing {name!r} already exists with a different type.",
                hint="Delete it first or use the existing type.",
            )
        return existing
    thing = Thing(name=name, thing_type=thing_type)
    things[name] = thing
    _save(things)
    return thing


def delete_thing(name: str) -> None:
    """Remove a Thing from the registry."""
    things = _load()
    if name not in things:
        raise NotFoundError(
            f"Thing {name!r} is not registered.",
            hint="Run `thingflash things list` to see registered Things.",
        )
    del things[name]
    _save(things)
