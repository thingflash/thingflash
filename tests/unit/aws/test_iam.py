import boto3
import pytest
from botocore.stub import Stubber

from thingflash.aws import iam, permissions
from thingflash.aws.session import IamWriteNotAllowedError, SimulateNotAllowedError
from thingflash.aws.sts import Principal

_ARN = "arn:aws:iam::123456789012:user/alice"
_ACCOUNT = "123456789012"
_POLICY_ARN = f"arn:aws:iam::{_ACCOUNT}:policy/{permissions.POLICY_NAME}"


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


def test_ensure_policy_creates_and_returns_arn(monkeypatch: pytest.MonkeyPatch) -> None:
    client, stubber = _stubbed_client()
    stubber.add_response(
        "create_policy",
        {"Policy": {"Arn": _POLICY_ARN}},
    )
    monkeypatch.setattr(iam, "make_client", lambda service, **k: client)
    document = permissions.build_policy_document()
    with stubber:
        arn = iam.ensure_policy(None, permissions.POLICY_NAME, document, account=_ACCOUNT)  # type: ignore[arg-type]
    assert arn == _POLICY_ARN
    stubber.assert_no_pending_responses()


def test_ensure_policy_already_exists_is_idempotent(monkeypatch: pytest.MonkeyPatch) -> None:
    client, stubber = _stubbed_client()
    stubber.add_client_error(
        "create_policy",
        service_error_code="EntityAlreadyExists",
        service_message="already exists",
    )
    monkeypatch.setattr(iam, "make_client", lambda service, **k: client)
    document = permissions.build_policy_document()
    with stubber:
        arn = iam.ensure_policy(None, permissions.POLICY_NAME, document, account=_ACCOUNT)  # type: ignore[arg-type]
    assert arn == _POLICY_ARN


def test_ensure_policy_access_denied_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    client, stubber = _stubbed_client()
    stubber.add_client_error(
        "create_policy",
        service_error_code="AccessDenied",
        service_message="not allowed",
    )
    monkeypatch.setattr(iam, "make_client", lambda service, **k: client)
    document = permissions.build_policy_document()
    with stubber, pytest.raises(IamWriteNotAllowedError):
        iam.ensure_policy(None, permissions.POLICY_NAME, document, account=_ACCOUNT)  # type: ignore[arg-type]


def test_attach_policy_user(monkeypatch: pytest.MonkeyPatch) -> None:
    client, stubber = _stubbed_client()
    stubber.add_response(
        "attach_user_policy",
        {},
        {"UserName": "alice", "PolicyArn": _POLICY_ARN},
    )
    monkeypatch.setattr(iam, "make_client", lambda service, **k: client)
    with stubber:
        iam.attach_policy(None, Principal("user", "alice"), _POLICY_ARN)  # type: ignore[arg-type]
    stubber.assert_no_pending_responses()


def test_attach_policy_role(monkeypatch: pytest.MonkeyPatch) -> None:
    client, stubber = _stubbed_client()
    stubber.add_response(
        "attach_role_policy",
        {},
        {"RoleName": "DeployRole", "PolicyArn": _POLICY_ARN},
    )
    monkeypatch.setattr(iam, "make_client", lambda service, **k: client)
    with stubber:
        iam.attach_policy(None, Principal("role", "DeployRole"), _POLICY_ARN)  # type: ignore[arg-type]
    stubber.assert_no_pending_responses()


def test_attach_policy_access_denied_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    client, stubber = _stubbed_client()
    stubber.add_client_error(
        "attach_user_policy",
        service_error_code="AccessDenied",
        service_message="not allowed",
    )
    monkeypatch.setattr(iam, "make_client", lambda service, **k: client)
    with stubber, pytest.raises(IamWriteNotAllowedError):
        iam.attach_policy(None, Principal("user", "alice"), _POLICY_ARN)  # type: ignore[arg-type]
