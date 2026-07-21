from __future__ import annotations

from typing import Any

import boto3
from botocore.config import Config
from botocore.exceptions import ProfileNotFound

from thingflash.core.errors import ThingFlashError

# Fail fast rather than block a `doctor` run for the default ~60s when offline.
_CLIENT_CONFIG = Config(
    connect_timeout=3,
    read_timeout=5,
    retries={"max_attempts": 2, "mode": "standard"},
)


class AWSConfigError(ThingFlashError):
    """The requested AWS profile/region could not be used to build a session."""

    code = "AWS_CONFIG_ERROR"


class AWSUnavailableError(ThingFlashError):
    """AWS could not be reached or no usable credentials were found.

    Doctor treats this as a WARN (not a FAIL): it usually means the machine is
    offline or credentials are simply not configured yet.
    """

    code = "AWS_UNAVAILABLE"


class SimulateNotAllowedError(ThingFlashError):
    """The caller lacks ``iam:SimulatePrincipalPolicy`` to self-check permissions."""

    code = "AWS_SIMULATE_DENIED"


def build_session(
    *, profile: str | None = None, region: str | None = None
) -> boto3.session.Session:
    """Build a boto3 session for ``profile``/``region``.

    ``profile``/``region`` of ``None`` (or the sentinel ``"default"`` profile)
    fall back to boto3's normal resolution (env vars, shared config, instance
    role). Raises :class:`AWSConfigError` if the named profile does not exist.
    """
    kwargs: dict[str, Any] = {}
    if profile and profile != "default":
        kwargs["profile_name"] = profile
    if region:
        kwargs["region_name"] = region
    try:
        return boto3.session.Session(**kwargs)
    except ProfileNotFound as exc:
        raise AWSConfigError(
            f"AWS profile '{profile}' not found.",
            hint="Check `aws configure list-profiles` or your manifest's aws.profile.",
        ) from exc


def make_client(
    service: str,
    *,
    session: boto3.session.Session | None = None,
    profile: str | None = None,
    region: str | None = None,
) -> Any:
    """Return a boto3 client for ``service`` with ThingFlash's timeout config."""
    session = session or build_session(profile=profile, region=region)
    # ``service`` is dynamic, so boto3-stubs' per-service Literal overloads don't apply.
    return session.client(service, config=_CLIENT_CONFIG)  # type: ignore[call-overload]
