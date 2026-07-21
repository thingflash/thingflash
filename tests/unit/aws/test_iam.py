import boto3
import pytest
from botocore.stub import Stubber

from thingflash.aws import iam
from thingflash.aws.session import SimulateNotAllowedError

_ARN = "arn:aws:iam::123456789012:user/alice"


def _stubbed_client() -> tuple[object, Stubber]:
    client = boto3.client(
        "iam",
        region_name="us-east-1",
        aws_access_key_id="testing",
        aws_secret_access_key="testing",
    )
    return client, Stubber(client)


def test_simulate_maps_decisions_to_bool(monkeypatch: pytest.MonkeyPatch) -> None:
    client, stubber = _stubbed_client()
    stubber.add_response(
        "simulate_principal_policy",
        {
            "EvaluationResults": [
                {
                    "EvalActionName": "iot:CreateThing",
                    "EvalResourceName": "*",
                    "EvalDecision": "allowed",
                },
                {
                    "EvalActionName": "iam:CreateRole",
                    "EvalResourceName": "*",
                    "EvalDecision": "implicitDeny",
                },
            ]
        },
        {
            "PolicySourceArn": _ARN,
            "ActionNames": ["iot:CreateThing", "iam:CreateRole"],
            "ResourceArns": ["*"],
        },
    )
    monkeypatch.setattr(iam, "make_client", lambda service, **k: client)
    with stubber:
        result = iam.simulate(None, _ARN, ["iot:CreateThing", "iam:CreateRole"])  # type: ignore[arg-type]
    assert result == {"iot:CreateThing": True, "iam:CreateRole": False}
    stubber.assert_no_pending_responses()


def test_simulate_access_denied_raises_self_check(monkeypatch: pytest.MonkeyPatch) -> None:
    client, stubber = _stubbed_client()
    stubber.add_client_error(
        "simulate_principal_policy",
        service_error_code="AccessDenied",
        service_message="not allowed",
    )
    monkeypatch.setattr(iam, "make_client", lambda service, **k: client)
    with stubber, pytest.raises(SimulateNotAllowedError):
        iam.simulate(None, _ARN, ["iot:CreateThing"])  # type: ignore[arg-type]
