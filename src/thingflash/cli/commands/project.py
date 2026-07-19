"""Top-level project commands: init/doctor/validate/plan/apply/status/destroy.

These attach directly to the root app via ``register``. Commands stay thin:
gather input -> call core -> render. All AWS work is faked (local state) for now.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

import typer

from thingflash.cli import output
from thingflash.cli.common import ExitCode, ManifestOption, OutputFormat, OutputOption, YesOption
from thingflash.core import doctor, executor, scaffold, state
from thingflash.core.errors import ManifestValidationError
from thingflash.core.manifest import Manifest, load_manifest
from thingflash.core.scaffold import ProjectConfig


def register(app: typer.Typer) -> None:
    """Attach project-level commands to the root Typer app."""
    app.command("init", help="Scaffold a new ThingFlash project in the current directory.")(init)
    app.command("doctor", help="Check your environment and report problems.")(doctor_cmd)
    app.command("validate", help="Validate the manifest.")(validate_cmd)
    app.command("plan", help="Show what apply would change (no changes made).")(plan_cmd)
    app.command("apply", help="Apply the manifest (fake: records to local state).")(apply_cmd)
    app.command("status", help="Show currently deployed resources.")(status_cmd)
    app.command("destroy", help="Tear down deployed resources.")(destroy_cmd)


def init(
    name: str | None = typer.Option(None, "--name", help="Project name."),
    region: str | None = typer.Option(None, "--region", help="AWS region, e.g. ap-northeast-2."),
    thing_type: str | None = typer.Option(None, "--thing-type", help="Default Thing type."),
    environment: str | None = typer.Option(
        None, "--environment", "-e", help="development | staging | production."
    ),
    profile: str = typer.Option(
        scaffold.DEFAULT_PROFILE, "--profile", help="AWS credentials profile."
    ),
    force: bool = typer.Option(False, "--force", help="Overwrite an existing thingflash.yaml."),
    yes: bool = YesOption,
    out: OutputFormat = OutputOption,
) -> None:
    """Create thingflash.yaml + .thingflash/ and git-ignore the state directory."""
    interactive = not yes and sys.stdin.isatty()

    if name is None:
        name = (
            typer.prompt("Project name", default=_default_name())
            if interactive
            else _default_name()
        )
    if region is None:
        default_region = os.environ.get("AWS_REGION") or os.environ.get(
            "AWS_DEFAULT_REGION", scaffold.DEFAULT_REGION
        )
        region = (
            typer.prompt("AWS region", default=default_region) if interactive else default_region
        )
    if thing_type is None:
        thing_type = (
            typer.prompt("Default Thing type", default=scaffold.DEFAULT_THING_TYPE)
            if interactive
            else scaffold.DEFAULT_THING_TYPE
        )
    if environment is None:
        environment = (
            typer.prompt("Environment", default=scaffold.DEFAULT_ENVIRONMENT)
            if interactive
            else scaffold.DEFAULT_ENVIRONMENT
        )

    config = ProjectConfig(
        name=name,
        region=region,
        thing_type=thing_type,
        environment=environment,
        profile=profile,
    )
    result = scaffold.init_project(config, force=force)
    output.render_init_result(result, out)


def doctor_cmd(out: OutputFormat = OutputOption) -> None:
    """Check the local environment."""
    checks = doctor.run_checks()
    output.render_doctor(checks, out)
    if doctor.has_failures(checks):
        raise typer.Exit(ExitCode.ERROR)


def validate_cmd(
    manifest_path: Path = ManifestOption,
    out: OutputFormat = OutputOption,
) -> None:
    """Validate the manifest schema and values."""
    manifest = _load_or_exit(manifest_path)
    output.render_validate(manifest, out)


def plan_cmd(
    manifest_path: Path = ManifestOption,
    out: OutputFormat = OutputOption,
) -> None:
    """Preview the changes apply would make."""
    manifest = _load_or_exit(manifest_path)
    plan = executor.plan(manifest)
    output.render_plan(plan, out)


def apply_cmd(
    manifest_path: Path = ManifestOption,
    yes: bool = YesOption,
    out: OutputFormat = OutputOption,
) -> None:
    """Apply the manifest (records desired resources to local state)."""
    manifest = _load_or_exit(manifest_path)
    plan = executor.plan(manifest)
    if out == OutputFormat.table:
        output.render_plan(plan, out)
    if plan.has_changes:
        output.confirm_or_exit("Apply these changes?", yes=yes)
    result = executor.apply(manifest)
    output.render_apply(result, out)


def status_cmd(out: OutputFormat = OutputOption) -> None:
    """Show what is currently deployed."""
    output.render_status(state.load_applied(), out)


def destroy_cmd(
    manifest_path: Path = ManifestOption,
    force: bool = typer.Option(False, "--force", help="Also remove data resources (S3/DynamoDB)."),
    yes: bool = YesOption,
    out: OutputFormat = OutputOption,
) -> None:
    """Tear down deployed resources."""
    applied = state.load_applied()
    if out == OutputFormat.table:
        output.render_destroy_preview(applied, out)
    if applied:
        output.confirm_or_exit("Destroy all deployed resources?", yes=yes)
    removed = executor.destroy()
    output.render_destroy(removed, out)


def _load_or_exit(path: Path) -> Manifest:
    try:
        return load_manifest(path)
    except ManifestValidationError as exc:
        output.error(exc)
        raise typer.Exit(ExitCode.VALIDATION_FAILED) from exc


def _default_name() -> str:
    raw = Path.cwd().name
    cleaned = re.sub(r"[^a-zA-Z0-9_-]", "-", raw).strip("-_")
    return cleaned or "thingflash-project"
