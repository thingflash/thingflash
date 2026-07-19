from collections.abc import Callable

from thingflash.core import planner
from thingflash.core.manifest import Manifest
from thingflash.core.planner import Resource

ManifestFactory = Callable[..., Manifest]


def test_desired_resources_count(make_manifest: ManifestFactory) -> None:
    manifest = make_manifest(groups=["default", "cameras"])
    resources = planner.desired_resources(manifest)
    types = [r.type for r in resources]
    assert types.count("IoT::ThingGroup") == 2
    assert "IoT::ThingType" in types
    assert "IoT::Policy" in types


def test_build_plan_all_create_from_empty(make_manifest: ManifestFactory) -> None:
    plan = planner.build_plan(make_manifest(), current=[])
    assert plan.has_changes
    assert all(a.op == planner.CREATE for a in plan.actions)


def test_build_plan_is_noop_when_current_matches(make_manifest: ManifestFactory) -> None:
    manifest = make_manifest()
    desired = planner.desired_resources(manifest)
    plan = planner.build_plan(manifest, current=desired)
    assert not plan.has_changes
    assert all(a.op == planner.NOOP for a in plan.actions)


def test_build_plan_deletes_stray_resource(make_manifest: ManifestFactory) -> None:
    manifest = make_manifest()
    current = planner.desired_resources(manifest) + [Resource("IoT::Policy", "orphan")]
    plan = planner.build_plan(manifest, current=current)
    assert any(a.op == planner.DELETE and a.name == "orphan" for a in plan.actions)


def test_security_warnings(make_manifest: ManifestFactory) -> None:
    manifest = make_manifest(mode="allow-all", topics={"telemetry": "devices/+/telemetry"})
    warnings = planner.security_warnings(manifest)
    assert any("Wildcard" in w for w in warnings)
    assert any("least-privilege" in w for w in warnings)
