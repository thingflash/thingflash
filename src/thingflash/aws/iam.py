from __future__ import annotations

import boto3
from botocore.exceptions import (
    ClientError,
    EndpointConnectionError,
    NoCredentialsError,
)

from thingflash.aws.session import (
    AWSUnavailableError,
    SimulateNotAllowedError,
    make_client,
)

# Evaluation decisions that mean the action is permitted.
_ALLOWED_DECISIONS = {"allowed"}


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
