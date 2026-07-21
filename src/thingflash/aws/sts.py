from __future__ import annotations

from dataclasses import dataclass

import boto3
from botocore.exceptions import (
    ClientError,
    EndpointConnectionError,
    NoCredentialsError,
)

from thingflash.aws.session import AWSUnavailableError, make_client

# STS error codes that mean "credentials present but not usable".
_AUTH_ERROR_CODES = {
    "InvalidClientTokenId",
    "ExpiredToken",
    "AccessDenied",
    "SignatureDoesNotMatch",
    "AuthFailure",
    "UnrecognizedClientException",
}


@dataclass
class Identity:
    account: str
    arn: str
    user_id: str


def get_caller_identity(session: boto3.session.Session) -> Identity:
    """Return the caller's :class:`Identity` via ``sts:GetCallerIdentity``.

    Raises :class:`AWSUnavailableError` when offline or when credentials are
    missing/invalid, so callers can degrade to a warning instead of crashing.
    """
    client = make_client("sts", session=session)
    try:
        resp = client.get_caller_identity()
    except NoCredentialsError as exc:
        raise AWSUnavailableError(
            "No AWS credentials found.",
            hint="Run `aws configure` or set AWS_PROFILE / AWS_ACCESS_KEY_ID.",
        ) from exc
    except EndpointConnectionError as exc:
        raise AWSUnavailableError(
            "Could not reach AWS (offline?).",
            hint="Check your network connection and try again.",
        ) from exc
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code", "")
        if code in _AUTH_ERROR_CODES:
            raise AWSUnavailableError(
                f"AWS rejected the credentials ({code}).",
                hint="Refresh or reconfigure your credentials.",
            ) from exc
        raise
    return Identity(
        account=resp["Account"],
        arn=resp["Arn"],
        user_id=resp["UserId"],
    )
