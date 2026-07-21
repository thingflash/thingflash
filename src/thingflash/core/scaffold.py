from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from thingflash.core.constants import (
    _MANIFEST_TEMPLATE,
    _NAME_RE,
    _REGION_RE,
    DEFAULT_ENVIRONMENT,
    DEFAULT_PROFILE,
    DEFAULT_REGION,
    DEFAULT_THING_TYPE,
    ENVIRONMENTS,
    GITIGNORE_ENTRY,
    MANIFEST_FILENAME,
    STATE_DIRNAME,
)
from thingflash.core.errors import AlreadyExistsError, ValidationError


@dataclass
class ProjectConfig:
    """Answers collected from `init` prompts or CLI flags."""

    name: str
    region: str = DEFAULT_REGION
    thing_type: str = DEFAULT_THING_TYPE
    environment: str = DEFAULT_ENVIRONMENT
    profile: str = DEFAULT_PROFILE

    def validate(self) -> None:
        if not _NAME_RE.match(self.name):
            raise ValidationError(
                f"Invalid project name: {self.name!r}",
                code="INVALID_NAME",
                hint="Use 1-63 chars: a-z, A-Z, 0-9, _ or -; start alphanumeric.",
            )
        if not _NAME_RE.match(self.thing_type):
            raise ValidationError(
                f"Invalid thing type: {self.thing_type!r}",
                code="INVALID_THING_TYPE",
                hint="Use 1-63 chars: a-z, A-Z, 0-9, _ or -; start alphanumeric.",
            )
        if not _REGION_RE.match(self.region):
            raise ValidationError(
                f"Invalid AWS region: {self.region!r}",
                code="INVALID_REGION",
                hint="Use an AWS region id such as us-east-1 or ap-northeast-2.",
            )
        if self.environment not in ENVIRONMENTS:
            raise ValidationError(
                f"Invalid environment: {self.environment!r}",
                code="INVALID_ENVIRONMENT",
                hint=f"Choose one of: {', '.join(ENVIRONMENTS)}.",
            )


@dataclass
class ScaffoldResult:
    """Summary of what `init` created/updated on disk."""

    project: str
    manifest_path: str
    state_dir: str
    created: list[str] = field(default_factory=list)
    updated: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)


def render_manifest(config: ProjectConfig) -> str:
    """Return the YAML manifest text for ``config``. Pure, no IO."""
    return _MANIFEST_TEMPLATE.format(
        name=config.name,
        environment=config.environment,
        region=config.region,
        profile=config.profile,
        thing_type=config.thing_type,
    )


def init_project(
    config: ProjectConfig,
    *,
    root: Path | None = None,
    force: bool = False,
) -> ScaffoldResult:
    """Scaffold a project under ``root`` (defaults to the current directory)."""
    config.validate()
    root = root or Path.cwd()
    manifest_path = root / MANIFEST_FILENAME
    state_dir = root / STATE_DIRNAME

    result = ScaffoldResult(
        project=config.name,
        manifest_path=str(manifest_path),
        state_dir=str(state_dir),
    )

    _write_manifest(config, manifest_path, force=force, result=result)
    _ensure_state_dir(config, state_dir, result=result)
    _ensure_gitignore(root, result=result)
    return result


def _write_manifest(
    config: ProjectConfig, manifest_path: Path, *, force: bool, result: ScaffoldResult
) -> None:
    existed = manifest_path.exists()
    if existed and not force:
        raise AlreadyExistsError(
            f"{MANIFEST_FILENAME} already exists in this directory.",
            code="PROJECT_EXISTS",
            hint="Edit it directly, or re-run with --force to overwrite.",
        )
    manifest_path.write_text(render_manifest(config))
    (result.updated if existed else result.created).append(str(manifest_path))


def _ensure_state_dir(config: ProjectConfig, state_dir: Path, *, result: ScaffoldResult) -> None:
    if not state_dir.exists():
        state_dir.mkdir(parents=True)
        result.created.append(str(state_dir))
    state_file = state_dir / "state.json"
    existed = state_file.exists()
    state = {"version": 1, "project": config.name, "region": config.region}
    state_file.write_text(json.dumps(state, indent=2))
    (result.updated if existed else result.created).append(str(state_file))


def _ensure_gitignore(root: Path, *, result: ScaffoldResult) -> None:
    gitignore = root / ".gitignore"
    stripped = GITIGNORE_ENTRY.rstrip("/")
    if gitignore.exists():
        lines = [line.strip() for line in gitignore.read_text().splitlines()]
        if GITIGNORE_ENTRY in lines or stripped in lines:
            result.skipped.append(str(gitignore))
            return
        content = gitignore.read_text()
        if content and not content.endswith("\n"):
            content += "\n"
        gitignore.write_text(f"{content}{GITIGNORE_ENTRY}\n")
        result.updated.append(str(gitignore))
    else:
        gitignore.write_text(f"{GITIGNORE_ENTRY}\n")
        result.created.append(str(gitignore))


def to_dict(result: ScaffoldResult) -> dict[str, object]:
    """Serialize a ScaffoldResult (used for JSON output)."""
    return asdict(result)
