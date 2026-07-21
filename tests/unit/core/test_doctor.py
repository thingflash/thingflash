from pathlib import Path

import pytest

from thingflash.aws.session import AWSUnavailableError, SimulateNotAllowedError
from thingflash.aws.sts import Identity
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
