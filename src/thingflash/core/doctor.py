from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

from thingflash.core.manifest import load_manifest
from thingflash.core.scaffold import MANIFEST_FILENAME, STATE_DIRNAME

OK = "ok"
WARN = "warn"
FAIL = "fail"


@dataclass
class Check:
    name: str
    status: str
    detail: str
    hint: str | None = None


def run_checks(root: Path | None = None) -> list[Check]:
    root = root or Path.cwd()
    return [
        _check_python(),
        _check_manifest(root),
        _check_state_dir(root),
        _check_aws_credentials(),
    ]


def has_failures(checks: list[Check]) -> bool:
    return any(c.status == FAIL for c in checks)


def _check_python() -> Check:
    version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    return Check("python", OK, f"Python {version}")


def _check_manifest(root: Path) -> Check:
    path = root / MANIFEST_FILENAME
    if not path.exists():
        return Check(
            "manifest", FAIL, f"{MANIFEST_FILENAME} not found", hint="Run `thingflash init`."
        )
    try:
        manifest = load_manifest(path)
    except Exception as exc:  # noqa: BLE001 - surfaced as a doctor finding, not a crash
        return Check("manifest", FAIL, "manifest is invalid", hint=str(exc))
    return Check("manifest", OK, f"{MANIFEST_FILENAME} valid (project: {manifest.metadata.name})")


def _check_state_dir(root: Path) -> Check:
    path = root / STATE_DIRNAME
    if path.is_dir():
        return Check("state", OK, f"{STATE_DIRNAME}/ present")
    return Check(
        "state", WARN, f"{STATE_DIRNAME}/ missing", hint="It is created by `thingflash init`."
    )


def _check_aws_credentials() -> Check:
    if os.environ.get("AWS_ACCESS_KEY_ID") or os.environ.get("AWS_PROFILE"):
        source = "AWS_ACCESS_KEY_ID" if os.environ.get("AWS_ACCESS_KEY_ID") else "AWS_PROFILE"
        return Check("aws-credentials", OK, f"credentials detected via {source}")
    return Check(
        "aws-credentials",
        WARN,
        "no AWS credentials detected in environment",
        hint="Configure them with `aws configure` or set AWS_PROFILE (not needed while faked).",
    )
