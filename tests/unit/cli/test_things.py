import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from thingflash.cli.main import app
from thingflash.core import registry

runner = CliRunner()


def test_list_json_is_pure_json(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(registry, "list_things", lambda: [])
    result = runner.invoke(app, ["things", "list", "--output", "json"])
    assert result.exit_code == 0
    assert json.loads(result.stdout) == []


def test_delete_without_tty_and_yes_exits_3() -> None:
    result = runner.invoke(app, ["things", "delete", "cam-1"])
    assert result.exit_code == 3


def test_create_then_list_roundtrip(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(registry, "REGISTRY_PATH", tmp_path / "registry.json")

    created = runner.invoke(app, ["things", "create", "cam-1"])
    assert created.exit_code == 0

    listed = runner.invoke(app, ["things", "list", "--output", "json"])
    assert listed.exit_code == 0
    names = [t["name"] for t in json.loads(listed.stdout)]
    assert names == ["cam-1"]


def test_create_rejects_invalid_name(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(registry, "REGISTRY_PATH", tmp_path / "registry.json")
    result = runner.invoke(app, ["things", "create", "bad name!"])
    assert result.exit_code == 1
