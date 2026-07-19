import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from thingflash.cli.main import app

runner = CliRunner()


def test_init_ci_mode_creates_project(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(
        app, ["init", "--name", "my_sensor", "--region", "ap-northeast-2", "--yes"]
    )
    assert result.exit_code == 0
    assert (tmp_path / "thingflash.yaml").exists()
    assert (tmp_path / ".thingflash" / "state.json").exists()
    assert ".thingflash/" in (tmp_path / ".gitignore").read_text()
    manifest = (tmp_path / "thingflash.yaml").read_text()
    assert "name: my_sensor" in manifest
    assert "region: ap-northeast-2" in manifest


def test_init_json_output_is_pure_json(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(
        app, ["init", "--name", "proj", "--region", "us-east-1", "--yes", "-o", "json"]
    )
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["project"] == "proj"
    assert any("thingflash.yaml" in p for p in data["created"])


def test_init_existing_without_force_exits_1(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)
    first = runner.invoke(app, ["init", "--name", "proj", "--region", "us-east-1", "--yes"])
    assert first.exit_code == 0
    second = runner.invoke(app, ["init", "--name", "proj", "--region", "us-east-1", "--yes"])
    assert second.exit_code == 1


def test_init_force_overwrites(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init", "--name", "proj", "--region", "us-east-1", "--yes"])
    result = runner.invoke(
        app, ["init", "--name", "proj2", "--region", "us-east-1", "--yes", "--force"]
    )
    assert result.exit_code == 0
    assert "name: proj2" in (tmp_path / "thingflash.yaml").read_text()
