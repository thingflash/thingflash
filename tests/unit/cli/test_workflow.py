import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from thingflash.cli.main import app

runner = CliRunner()


def _init(tmp_path: Path) -> None:
    result = runner.invoke(app, ["init", "--name", "proj", "--region", "us-east-1", "--yes"])
    assert result.exit_code == 0


def test_full_fake_workflow(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    _init(tmp_path)

    assert runner.invoke(app, ["validate"]).exit_code == 0

    plan = runner.invoke(app, ["plan", "-o", "json"])
    assert plan.exit_code == 0
    assert any(a["op"] == "create" for a in json.loads(plan.stdout)["actions"])

    apply = runner.invoke(app, ["apply", "--yes", "-o", "json"])
    assert apply.exit_code == 0

    status = runner.invoke(app, ["status", "-o", "json"])
    assert json.loads(status.stdout)  # non-empty

    # applying again is a no-op
    plan2 = runner.invoke(app, ["plan", "-o", "json"])
    assert not any(a["op"] == "create" for a in json.loads(plan2.stdout)["actions"])

    destroy = runner.invoke(app, ["destroy", "--yes", "-o", "json"])
    assert destroy.exit_code == 0
    assert json.loads(runner.invoke(app, ["status", "-o", "json"]).stdout) == []


def test_validate_missing_manifest_exits_2(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    assert runner.invoke(app, ["validate"]).exit_code == 2


def test_doctor_missing_manifest_exits_1(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    assert runner.invoke(app, ["doctor"]).exit_code == 1


def test_apply_without_tty_or_yes_exits_3(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    _init(tmp_path)
    assert runner.invoke(app, ["apply"]).exit_code == 3
