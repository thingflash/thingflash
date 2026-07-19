from __future__ import annotations

import re
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from thingflash.core.errors import ManifestValidationError
from thingflash.core.scaffold import ENVIRONMENTS, MANIFEST_FILENAME

API_VERSION = "thingflash.com/v1"
KIND = "IoTProject"
RESERVED_SECTIONS = ("provisioning", "jobs", "schedules")

_REGION_RE = re.compile(r"^[a-z]{2}-[a-z]+-\d$")


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Metadata(_Base):
    name: str
    environment: str = "development"

    @field_validator("environment")
    @classmethod
    def _check_environment(cls, value: str) -> str:
        if value not in ENVIRONMENTS:
            raise ValueError(f"must be one of {', '.join(ENVIRONMENTS)}")
        return value


class AWS(_Base):
    region: str
    profile: str = "default"

    @field_validator("region")
    @classmethod
    def _check_region(cls, value: str) -> str:
        if not _REGION_RE.match(value):
            raise ValueError("must be an AWS region id, e.g. us-east-1")
        return value


class Policies(_Base):
    mode: str = "least-privilege"


class Fleet(_Base):
    thingType: str  # noqa: N815 - matches the manifest YAML key
    groups: list[str] = Field(default_factory=lambda: ["default"])
    policies: Policies = Field(default_factory=Policies)


class MQTT(_Base):
    topics: dict[str, str] = Field(default_factory=dict)


class Manifest(_Base):
    apiVersion: str  # noqa: N815 - matches the manifest YAML key
    kind: str
    metadata: Metadata
    aws: AWS
    fleet: Fleet
    mqtt: MQTT = Field(default_factory=MQTT)

    @field_validator("apiVersion")
    @classmethod
    def _check_api_version(cls, value: str) -> str:
        if value != API_VERSION:
            raise ValueError(f"unsupported apiVersion, expected {API_VERSION}")
        return value

    @field_validator("kind")
    @classmethod
    def _check_kind(cls, value: str) -> str:
        if value != KIND:
            raise ValueError(f"unsupported kind, expected {KIND}")
        return value


def load_manifest(path: Path | None = None) -> Manifest:
    """Load and validate the manifest at ``path`` (default: ./thingflash.yaml)."""
    path = path or Path(MANIFEST_FILENAME)
    if not path.exists():
        raise ManifestValidationError(
            f"No manifest found at {path}.",
            code="NO_MANIFEST",
            hint="Run `thingflash init` to create one.",
        )

    try:
        raw = yaml.safe_load(path.read_text())
    except yaml.YAMLError as exc:
        raise ManifestValidationError(
            f"Could not parse {path}: {exc}",
            code="MANIFEST_PARSE_ERROR",
            hint="Check the YAML syntax.",
        ) from exc

    if not isinstance(raw, dict):
        raise ManifestValidationError(
            f"{path} must contain a YAML mapping.",
            code="MANIFEST_INVALID",
        )

    for section in RESERVED_SECTIONS:
        if section in raw:
            raise ManifestValidationError(
                f"The '{section}' section is supported in a future release.",
                code="MANIFEST_RESERVED_SECTION",
                hint="Remove it for now.",
            )

    try:
        return Manifest(**raw)
    except ValidationError as exc:
        raise ManifestValidationError(
            f"{path} is invalid:\n{_format_errors(exc)}",
            code="MANIFEST_INVALID",
            hint="See docs/manifest-reference.md for the schema.",
        ) from exc


def _format_errors(exc: ValidationError) -> str:
    lines = []
    for err in exc.errors():
        loc = ".".join(str(p) for p in err["loc"]) or "(root)"
        lines.append(f"  - {loc}: {err['msg']}")
    return "\n".join(lines)
