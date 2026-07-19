from __future__ import annotations

from dataclasses import dataclass, field

from thingflash.core.manifest import Manifest

CREATE = "create"
UPDATE = "update"
DELETE = "delete"
NOOP = "noop"

_OP_PREFIX = {CREATE: "+", UPDATE: "~", DELETE: "-", NOOP: " "}


@dataclass(frozen=True)
class Resource:
    """A single managed resource (fake stand-in for a CloudFormation/IoT resource)."""

    type: str
    name: str


@dataclass
class Action:
    op: str
    resource_type: str
    name: str

    @property
    def prefix(self) -> str:
        return _OP_PREFIX.get(self.op, "?")


@dataclass
class Plan:
    actions: list[Action] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def changes(self) -> list[Action]:
        return [a for a in self.actions if a.op != NOOP]

    @property
    def has_changes(self) -> bool:
        return bool(self.changes)


def desired_resources(manifest: Manifest) -> list[Resource]:
    """Derive the set of resources the manifest asks for."""
    name = manifest.metadata.name
    resources = [Resource("IoT::ThingType", manifest.fleet.thingType)]
    resources += [Resource("IoT::ThingGroup", group) for group in manifest.fleet.groups]
    resources.append(Resource("IoT::Policy", f"{name}-device-policy"))
    return resources


def security_warnings(manifest: Manifest) -> list[str]:
    """Emit plan warnings for insecure choices (wildcards, weak policy mode)."""
    warnings: list[str] = []
    for topic in manifest.mqtt.topics.values():
        if "+" in topic or "#" in topic:
            warnings.append(f"Wildcard MQTT topic grants broad access: {topic}")
    if manifest.fleet.policies.mode != "least-privilege":
        warnings.append(
            f"IoT policy mode is '{manifest.fleet.policies.mode}', not least-privilege."
        )
    return warnings


def build_plan(manifest: Manifest, current: list[Resource]) -> Plan:
    """Diff desired vs current resources into an ordered plan."""
    desired = desired_resources(manifest)
    current_set = set(current)
    desired_set = set(desired)

    actions: list[Action] = []
    for resource in desired:
        op = NOOP if resource in current_set else CREATE
        actions.append(Action(op, resource.type, resource.name))
    for resource in current:
        if resource not in desired_set:
            actions.append(Action(DELETE, resource.type, resource.name))

    return Plan(actions=actions, warnings=security_warnings(manifest))
