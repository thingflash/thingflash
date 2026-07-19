from pathlib import Path

import pytest

from thingflash.core import scaffold
from thingflash.core.errors import AlreadyExistsError, ValidationError
from thingflash.core.scaffold import ProjectConfig


def test_render_manifest_contains_values() -> None:
    text = scaffold.render_manifest(
        ProjectConfig(name="greenhouse", region="ap-northeast-2", thing_type="esp32-sensor")
    )
    assert "name: greenhouse" in text
    assert "region: ap-northeast-2" in text
    assert "thingType: esp32-sensor" in text
    # literal braces in MQTT topics must survive templating
    assert "devices/{thingName}/telemetry" in text


def test_init_project_creates_files(tmp_path: Path) -> None:
    result = scaffold.init_project(ProjectConfig(name="proj", region="us-east-1"), root=tmp_path)
    assert (tmp_path / "thingflash.yaml").exists()
    assert (tmp_path / ".thingflash" / "state.json").exists()
    assert ".thingflash/" in (tmp_path / ".gitignore").read_text()
    assert str(tmp_path / "thingflash.yaml") in result.created


def test_init_existing_manifest_without_force_raises(tmp_path: Path) -> None:
    cfg = ProjectConfig(name="proj")
    scaffold.init_project(cfg, root=tmp_path)
    with pytest.raises(AlreadyExistsError):
        scaffold.init_project(cfg, root=tmp_path)


def test_init_force_overwrites_and_gitignore_is_idempotent(tmp_path: Path) -> None:
    cfg = ProjectConfig(name="proj")
    scaffold.init_project(cfg, root=tmp_path)
    result = scaffold.init_project(cfg, root=tmp_path, force=True)
    assert str(tmp_path / "thingflash.yaml") in result.updated
    assert str(tmp_path / ".gitignore") in result.skipped


def test_gitignore_append_preserves_existing(tmp_path: Path) -> None:
    (tmp_path / ".gitignore").write_text("*.log\n")
    scaffold.init_project(ProjectConfig(name="proj"), root=tmp_path)
    content = (tmp_path / ".gitignore").read_text()
    assert "*.log" in content
    assert ".thingflash/" in content


@pytest.mark.parametrize(
    "cfg",
    [
        ProjectConfig(name="bad name!"),
        ProjectConfig(name="ok", region="not-a-region"),
        ProjectConfig(name="ok", environment="prod"),
        ProjectConfig(name="ok", thing_type="bad type!"),
    ],
)
def test_init_validation_errors(cfg: ProjectConfig, tmp_path: Path) -> None:
    with pytest.raises(ValidationError):
        scaffold.init_project(cfg, root=tmp_path)
