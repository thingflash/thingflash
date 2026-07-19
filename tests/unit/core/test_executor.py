from collections.abc import Callable
from pathlib import Path

from thingflash.core import executor, planner, state
from thingflash.core.manifest import Manifest

ManifestFactory = Callable[..., Manifest]


def test_apply_records_state_and_is_idempotent(
    make_manifest: ManifestFactory, tmp_path: Path
) -> None:
    manifest = make_manifest()

    first = executor.apply(manifest, root=tmp_path)
    assert first.plan.has_changes
    assert set(state.load_applied(tmp_path)) == set(planner.desired_resources(manifest))

    second = executor.apply(manifest, root=tmp_path)
    assert not second.plan.has_changes


def test_plan_reflects_applied_state(make_manifest: ManifestFactory, tmp_path: Path) -> None:
    manifest = make_manifest()
    assert executor.plan(manifest, root=tmp_path).has_changes
    executor.apply(manifest, root=tmp_path)
    assert not executor.plan(manifest, root=tmp_path).has_changes


def test_destroy_clears_state(make_manifest: ManifestFactory, tmp_path: Path) -> None:
    manifest = make_manifest()
    executor.apply(manifest, root=tmp_path)
    removed = executor.destroy(root=tmp_path)
    assert removed
    assert state.load_applied(tmp_path) == []
