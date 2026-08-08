from __future__ import annotations

import json

import boto3
from botocore.exceptions import (
    ClientError,
    EndpointConnectionError,
    NoCredentialsError,
)

from thingflash.aws.session import (
    AWSUnavailableError,
    IamWriteNotAllowedError,
    SimulateNotAllowedError,
    make_client,
)
from thingflash.aws.sts import Principal

_ALLOWED_DECISIONS = {"allowed"}
_WRITE_DENIED_CODES = {"AccessDenied", "AccessDeniedException"}


def simulate(
    session: boto3.session.Session,
    source_arn: str,
    actions: list[str],
    *,
    resource_arns: list[str] | None = None,
) -> dict[str, bool]:
    """Simulate whether ``source_arn`` may perform ``actions``.

    Returns a mapping of action name -> allowed (bool). Uses
    ``iam:SimulatePrincipalPolicy`` with pagination so large action lists are
    handled in one logical call.

    Raises :class:`SimulateNotAllowedError` if the caller itself lacks
    permission to run the simulation, and :class:`AWSUnavailableError` when
    offline or credential-less.
    """
    client = make_client("iam", session=session)
    resource_arns = resource_arns or ["*"]
    results: dict[str, bool] = {}
    try:
        paginator = client.get_paginator("simulate_principal_policy")
        for page in paginator.paginate(
            PolicySourceArn=source_arn,
            ActionNames=actions,
            ResourceArns=resource_arns,
        ):
            for evaluation in page.get("EvaluationResults", []):
                name = evaluation["EvalActionName"]
                decision = evaluation["EvalDecision"]
                results[name] = decision in _ALLOWED_DECISIONS
    except NoCredentialsError as exc:
        raise AWSUnavailableError(
            "No AWS credentials found.",
            hint="Run `aws configure` or set AWS_PROFILE.",
        ) from exc
    except EndpointConnectionError as exc:
        raise AWSUnavailableError(
            "Could not reach AWS IAM (offline?).",
            hint="Check your network connection and try again.",
        ) from exc
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code", "")
        if code in {"AccessDenied", "AccessDeniedException"}:
            raise SimulateNotAllowedError(
                "Permission is not allowed: caller lacks iam:SimulatePrincipalPolicy.",
                hint="Grant iam:SimulatePrincipalPolicy, or verify permissions manually.",
            ) from exc
        raise
    return results


def ensure_policy(
    session: boto3.session.Session,
    name: str,
    document: dict[str, object],
    *,
    account: str,
) -> str:
    """Create the managed policy ``name`` and return its ARN.

    If a policy with that name already exists it is left untouched and its ARN
    is returned, so re-running ``doctor --fix`` is idempotent.

    Raises :class:`IamWriteNotAllowedError` if the caller lacks IAM write
    permissions, and :class:`AWSUnavailableError` when offline or credential-less.
    """
    client = make_client("iam", session=session)
    arn = f"arn:aws:iam::{account}:policy/{name}"
    try:
        resp = client.create_policy(PolicyName=name, PolicyDocument=json.dumps(document))
        return str(resp["Policy"]["Arn"])
    except NoCredentialsError as exc:
        raise _offline_error() from exc
    except EndpointConnectionError as exc:
        raise _offline_error() from exc
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code", "")
        if code == "EntityAlreadyExists":
            return arn
        if code in _WRITE_DENIED_CODES:
            raise _write_denied_error("iam:CreatePolicy") from exc
        raise


def attach_policy(
    session: boto3.session.Session, principal: Principal, policy_arn: str
) -> None:
    """Attach ``policy_arn`` to the user or role ``principal``.

    Attaching an already-attached policy is a no-op on the AWS side, so this is
    safe to re-run. Raises the same errors as :func:`ensure_policy`.
    """
    client = make_client("iam", session=session)
    try:
        if principal.type == "user":
            client.attach_user_policy(UserName=principal.name, PolicyArn=policy_arn)
        else:
            client.attach_role_policy(RoleName=principal.name, PolicyArn=policy_arn)
    except NoCredentialsError as exc:
        raise _offline_error() from exc
    except EndpointConnectionError as exc:
        raise _offline_error() from exc
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code", "")
        if code in _WRITE_DENIED_CODES:
            action = "iam:AttachUserPolicy" if principal.type == "user" else "iam:AttachRolePolicy"
            raise _write_denied_error(action) from exc
        raise


def _offline_error() -> AWSUnavailableError:
    return AWSUnavailableError(
        "Could not reach AWS IAM (offline?).",
        hint="Check your network connection and try again.",
    )


def _write_denied_error(action: str) -> IamWriteNotAllowedError:
    return IamWriteNotAllowedError(
        f"Not allowed to modify IAM: caller lacks {action}.",
        hint="Ask an administrator to attach the ThingFlash policy "
        "(see `thingflash permissions`).",
    )
