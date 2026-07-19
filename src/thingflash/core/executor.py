from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from thingflash.core import planner, state
from thingflash.core.manifest import Manifest
from thingflash.core.planner import Plan, Resource


@dataclass
class ApplyResult:
    plan: Plan
    applied: list[Resource]


def plan(manifest: Manifest, root: Path | None = None) -> Plan:
    """Compute the plan for ``manifest`` against current local state."""
    root = root or Path.cwd()
    return planner.build_plan(manifest, state.load_applied(root))


def apply(manifest: Manifest, root: Path | None = None) -> ApplyResult:
    """Re-plan, then record the desired resources as applied."""
    root = root or Path.cwd()
    current_plan = plan(manifest, root)
    desired = planner.desired_resources(manifest)
    state.save_applied(desired, root)
    return ApplyResult(plan=current_plan, applied=desired)


def destroy(root: Path | None = None) -> list[Resource]:
    """Remove all applied resources. Returns what was removed."""
    root = root or Path.cwd()
    removed = state.load_applied(root)
    state.save_applied([], root)
    return removed
