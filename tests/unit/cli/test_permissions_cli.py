import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from thingflash.aws import permissions
from thingflash.aws.session import IamWriteNotAllowedError
from thingflash.cli.main import app
from thingflash.core import doctor
from thingflash.core.doctor import PermissionFix

runner = CliRunner()


def test_permissions_json_is_a_valid_policy_document() -> None:
    result = runner.invoke(app, ["permissions", "-o", "json"])
    assert result.exit_code == 0
    document = json.loads(result.stdout)
    assert document["Version"] == "2012-10-17"
    granted = {a for s in document["Statement"] for a in s["Action"]}
    assert set(permissions.REQUIRED_ACTIONS) <= granted
    assert "iam:SimulatePrincipalPolicy" in granted


def test_permissions_table_shows_attach_commands() -> None:
    result = runner.invoke(app, ["permissions"])
    assert result.exit_code == 0
    assert "aws iam create-policy" in result.stdout
    assert permissions.POLICY_NAME in result.stdout


def test_doctor_fix_attaches_when_permissions_denied(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init", "--name", "proj", "--region", "us-east-1", "--yes"])

    def denied_checks(**_k: object) -> list[doctor.Check]:
        return [doctor.Check("aws-permissions", doctor.FAIL, "2 denied")]

    monkeypatch.setattr(doctor, "run_checks", denied_checks)
    monkeypatch.setattr(
        doctor,
        "fix_permissions",
        lambda **k: PermissionFix("user", "alice", permissions.POLICY_NAME, "arn:...:policy/x"),
    )
    result = runner.invoke(app, ["doctor", "--fix", "--yes"])
    assert result.exit_code == 0
    assert "Attached" in result.stdout
    assert "alice" in result.stdout


def test_doctor_fix_reports_write_denied_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init", "--name", "proj", "--region", "us-east-1", "--yes"])

    monkeypatch.setattr(
        doctor,
        "run_checks",
        lambda **k: [doctor.Check("aws-permissions", doctor.FAIL, "2 denied")],
    )

    def deny(**_k: object) -> PermissionFix:
        raise IamWriteNotAllowedError("denied", hint="ask an admin")

    monkeypatch.setattr(doctor, "fix_permissions", deny)
    result = runner.invoke(app, ["doctor", "--fix", "--yes"])
    assert result.exit_code == 1
    assert "AWS_IAM_WRITE_DENIED" in result.stderr
