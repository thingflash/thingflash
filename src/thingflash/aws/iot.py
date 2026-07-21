from __future__ import annotations

import boto3
from botocore.exceptions import (
    ClientError,
    EndpointConnectionError,
    NoCredentialsError,
)

from thingflash.aws.session import AWSUnavailableError, make_client


def describe_endpoint(
    session: boto3.session.Session, *, endpoint_type: str = "iot:Data-ATS"
) -> str:
    """Return the account's IoT data endpoint address.

    Raises :class:`AWSUnavailableError` when offline or credential-less so
    callers can degrade to a warning.
    """
    client = make_client("iot", session=session)
    try:
        resp = client.describe_endpoint(endpointType=endpoint_type)
    except NoCredentialsError as exc:
        raise AWSUnavailableError(
            "No AWS credentials found.",
            hint="Run `aws configure` or set AWS_PROFILE.",
        ) from exc
    except EndpointConnectionError as exc:
        raise AWSUnavailableError(
            "Could not reach AWS IoT (offline?).",
            hint="Check your network connection and try again.",
        ) from exc
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code", "")
        if code in {"InvalidClientTokenId", "ExpiredToken", "AccessDenied"}:
            raise AWSUnavailableError(
                f"AWS rejected the credentials ({code}).",
                hint="Refresh or reconfigure your credentials.",
            ) from exc
        raise
    return str(resp["endpointAddress"])
