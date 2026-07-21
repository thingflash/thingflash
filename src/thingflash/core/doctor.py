from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

import boto3

from thingflash.aws import iam, permissions, sts
from thingflash.aws.session import (
    AWSConfigError,
    AWSUnavailableError,
    SimulateNotAllowedError,
    build_session,
)
from thingflash.core.constants import (
    DEFAULT_REGION,
    FAIL,
    MANIFEST_FILENAME,
    OK,
    STATE_DIRNAME,
    WARN,
)
from thingflash.core.manifest import Manifest, load_manifest

_MAX_DENIED_SHOWN = 5


@dataclass
class Check:
    name: str
    status: str
    detail: str
    hint: str | None = None


@dataclass
class _AwsTarget:
    profile: str | None
    region: str | None


def run_checks(
    root: Path | None = None,
    *,
    profile: str | None = None,
    region: str | None = None,
    skip_aws: bool = False,
) -> list[Check]:
    root = root or Path.cwd()
    manifest, manifest_check = _check_manifest(root)
    checks = [_check_python(), manifest_check, _check_state_dir(root)]

    if skip_aws:
        checks.append(Check("aws", WARN, "AWS checks skipped (--skip-aws)."))
        return checks

    target = _resolve_aws_target(manifest, profile, region)
    identity_check, session, identity = _check_aws_identity(target)
    checks.append(identity_check)
    checks.append(_check_aws_permissions(session, identity))
    return checks


def has_failures(checks: list[Check]) -> bool:
    return any(c.status == FAIL for c in checks)


def _check_python() -> Check:
    version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    return Check("python", OK, f"Python {version}")


def _check_manifest(root: Path) -> tuple[Manifest | None, Check]:
    path = root / MANIFEST_FILENAME
    if not path.exists():
        return None, Check(
            "manifest", FAIL, f"{MANIFEST_FILENAME} not found", hint="Run `thingflash init`."
        )
    try:
        manifest = load_manifest(path)
    except Exception as exc:  # noqa: BLE001 - surfaced as a doctor finding, not a crash
        return None, Check("manifest", FAIL, "manifest is invalid", hint=str(exc))
    return manifest, Check(
        "manifest", OK, f"{MANIFEST_FILENAME} valid (project: {manifest.metadata.name})"
    )


def _check_state_dir(root: Path) -> Check:
    path = root / STATE_DIRNAME
    if path.is_dir():
        return Check("state", OK, f"{STATE_DIRNAME}/ present")
    return Check(
        "state", WARN, f"{STATE_DIRNAME}/ missing", hint="It is created by `thingflash init`."
    )


def _resolve_aws_target(
    manifest: Manifest | None, cli_profile: str | None, cli_region: str | None
) -> _AwsTarget:
    """Resolve profile/region with precedence: CLI > manifest > env > default."""
    profile = (
        cli_profile
        or (manifest.aws.profile if manifest else None)
        or os.environ.get("AWS_PROFILE")
    )
    region = (
        cli_region
        or (manifest.aws.region if manifest else None)
        or os.environ.get("AWS_REGION")
        or os.environ.get("AWS_DEFAULT_REGION")
        or DEFAULT_REGION
    )
    return _AwsTarget(profile=profile, region=region)


def _check_aws_identity(
    target: _AwsTarget,
) -> tuple[Check, boto3.session.Session | None, sts.Identity | None]:
    try:
        session = build_session(profile=target.profile, region=target.region)
        identity = sts.get_caller_identity(session)
    except (AWSUnavailableError, AWSConfigError) as exc:
        return Check("aws-identity", WARN, exc.message, hint=exc.hint), None, None
    detail = f"account {identity.account} ({_short_arn(identity.arn)}) in {target.region}"
    return Check("aws-identity", OK, detail), session, identity


def _check_aws_permissions(
    session: boto3.session.Session | None, identity: sts.Identity | None
) -> Check:
    if session is None or identity is None:
        return Check(
            "aws-permissions",
            WARN,
            "skipped: no verified AWS identity",
            hint="Resolve the aws-identity warning first.",
        )
    try:
        results = iam.simulate(session, identity.arn, permissions.REQUIRED_ACTIONS)
    except (SimulateNotAllowedError, AWSUnavailableError) as exc:
        return Check("aws-permissions", WARN, exc.message, hint=exc.hint)

    if not results:
        return Check(
            "aws-permissions",
            WARN,
            "no simulation results returned",
            hint="Verify the required permissions manually.",
        )

    denied = sorted(action for action, allowed in results.items() if not allowed)
    if denied:
        preview = ", ".join(denied[:_MAX_DENIED_SHOWN])
        extra = len(denied) - _MAX_DENIED_SHOWN
        suffix = f" (+{extra} more)" if extra > 0 else ""
        return Check(
            "aws-permissions",
            FAIL,
            f"{len(denied)} required action(s) denied: {preview}{suffix}",
            hint="Attach the missing permissions to your IAM identity.",
        )
    return Check("aws-permissions", OK, f"all {len(results)} required actions allowed")


def _short_arn(arn: str) -> str:
    """Return the resource portion of an ARN (e.g. ``user/alice``)."""
    return arn.rsplit(":", 1)[-1]
