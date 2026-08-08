from pathlib import Path

import pytest

from thingflash.aws.session import (
    AWSConfigError,
    AWSUnavailableError,
    IamWriteNotAllowedError,
    SimulateNotAllowedError,
)
from thingflash.aws.sts import Identity, Principal
from thingflash.core import doctor, scaffold
from thingflash.core.scaffold import ProjectConfig

_ARN = "arn:aws:iam::123456789012:user/alice"


def _init(root: Path) -> None:
    scaffold.init_project(ProjectConfig(name="proj", region="us-east-1"), root=root)


def _fake_identity(_session: object) -> Identity:
    return Identity(account="123456789012", arn=_ARN, user_id="AIDAEXAMPLE")


def test_doctor_flags_missing_manifest(tmp_path: Path) -> None:
    checks = {c.name: c for c in doctor.run_checks(tmp_path, skip_aws=True)}
    assert checks["manifest"].status == doctor.FAIL
    assert doctor.has_failures(doctor.run_checks(tmp_path, skip_aws=True))


def test_doctor_local_only_passes(tmp_path: Path) -> None:
    _init(tmp_path)
    checks = {c.name: c.status for c in doctor.run_checks(tmp_path, skip_aws=True)}
    assert checks["manifest"] == doctor.OK
    assert checks["state"] == doctor.OK
    assert checks["aws"] == doctor.WARN  # skipped
    assert not doctor.has_failures(doctor.run_checks(tmp_path, skip_aws=True))


def test_doctor_aws_all_allowed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _init(tmp_path)
    monkeypatch.setattr(doctor.sts, "get_caller_identity", _fake_identity)
    monkeypatch.setattr(
        doctor.iam, "simulate", lambda s, arn, actions, **k: {a: True for a in actions}
    )
    checks = {c.name: c for c in doctor.run_checks(tmp_path)}
    assert checks["aws-identity"].status == doctor.OK
    assert "123456789012" in checks["aws-identity"].detail
    assert checks["aws-permissions"].status == doctor.OK
    assert not doctor.has_failures(list(checks.values()))


def test_doctor_aws_denied_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _init(tmp_path)
    monkeypatch.setattr(doctor.sts, "get_caller_identity", _fake_identity)

    def fake_simulate(_s: object, _arn: str, actions: list[str], **_k: object) -> dict[str, bool]:
        return {a: a != "iam:CreateRole" for a in actions}

    monkeypatch.setattr(doctor.iam, "simulate", fake_simulate)
    checks = {c.name: c for c in doctor.run_checks(tmp_path)}
    assert checks["aws-permissions"].status == doctor.FAIL
    assert "iam:CreateRole" in checks["aws-permissions"].detail
    assert doctor.has_failures(list(checks.values()))


def test_doctor_aws_cannot_self_check_warns(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _init(tmp_path)
    monkeypatch.setattr(doctor.sts, "get_caller_identity", _fake_identity)

    def raise_denied(*_a: object, **_k: object) -> dict[str, bool]:
        raise SimulateNotAllowedError("cannot self-check", hint="grant simulate")

    monkeypatch.setattr(doctor.iam, "simulate", raise_denied)
    checks = {c.name: c for c in doctor.run_checks(tmp_path)}
    assert checks["aws-permissions"].status == doctor.WARN
    assert not doctor.has_failures(list(checks.values()))


def test_doctor_offline_warns_not_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _init(tmp_path)

    def raise_unavailable(_session: object) -> Identity:
        raise AWSUnavailableError("offline", hint="check network")

    monkeypatch.setattr(doctor.sts, "get_caller_identity", raise_unavailable)
    checks = {c.name: c for c in doctor.run_checks(tmp_path)}
    assert checks["aws-identity"].status == doctor.WARN
    assert checks["aws-permissions"].status == doctor.WARN
    assert not doctor.has_failures(list(checks.values()))


def test_permissions_denied_detects_failed_check() -> None:
    denied = [doctor.Check("aws-permissions", doctor.FAIL, "2 denied")]
    allowed = [doctor.Check("aws-permissions", doctor.OK, "all allowed")]
    assert doctor.permissions_denied(denied)
    assert not doctor.permissions_denied(allowed)


def _patch_fix_env(monkeypatch: pytest.MonkeyPatch) -> dict[str, object]:
    """Stub session/identity so fix_permissions never touches real AWS."""
    monkeypatch.setattr(doctor, "build_session", lambda **k: object())
    monkeypatch.setattr(doctor.sts, "get_caller_identity", _fake_identity)
    calls: dict[str, object] = {}

    def fake_ensure(session: object, name: str, doc: object, *, account: str) -> str:
        calls["ensure"] = (name, account)
        return f"arn:aws:iam::{account}:policy/{name}"

    def fake_attach(session: object, principal: Principal, policy_arn: str) -> None:
        calls["attach"] = (principal.type, principal.name, policy_arn)

    monkeypatch.setattr(doctor.iam, "ensure_policy", fake_ensure)
    monkeypatch.setattr(doctor.iam, "attach_policy", fake_attach)
    return calls


def test_fix_permissions_creates_and_attaches(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _init(tmp_path)
    calls = _patch_fix_env(monkeypatch)
    result = doctor.fix_permissions(tmp_path)
    assert result.principal_type == "user"
    assert result.principal_name == "alice"
    assert result.policy_name == doctor.permissions.POLICY_NAME
    assert result.policy_arn.endswith(doctor.permissions.POLICY_NAME)
    assert calls["attach"] == ("user", "alice", result.policy_arn)


def test_fix_permissions_unsupported_identity_raises(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _init(tmp_path)
    _patch_fix_env(monkeypatch)

    def root_identity(_session: object) -> Identity:
        return Identity(account="123456789012", arn="arn:aws:iam::123456789012:root", user_id="X")

    monkeypatch.setattr(doctor.sts, "get_caller_identity", root_identity)
    with pytest.raises(AWSConfigError):
        doctor.fix_permissions(tmp_path)


def test_fix_permissions_propagates_write_denied(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _init(tmp_path)
    _patch_fix_env(monkeypatch)

    def deny(*_a: object, **_k: object) -> str:
        raise IamWriteNotAllowedError("denied", hint="ask an admin")

    monkeypatch.setattr(doctor.iam, "ensure_policy", deny)
    with pytest.raises(IamWriteNotAllowedError):
        doctor.fix_permissions(tmp_path)
