from pathlib import Path

import pytest

from thingflash.core import scaffold
from thingflash.core.errors import ManifestValidationError
from thingflash.core.manifest import load_manifest
from thingflash.core.scaffold import ProjectConfig


def _write(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "thingflash.yaml"
    path.write_text(text)
    return path


def _valid_text(**kwargs: str) -> str:
    return scaffold.render_manifest(
        ProjectConfig(name="greenhouse", region="ap-northeast-2", **kwargs)
    )


def test_load_valid_manifest(tmp_path: Path) -> None:
    manifest = load_manifest(_write(tmp_path, _valid_text(thing_type="esp32-sensor")))
    assert manifest.metadata.name == "greenhouse"
    assert manifest.aws.region == "ap-northeast-2"
    assert manifest.fleet.thingType == "esp32-sensor"
    assert manifest.fleet.policies.mode == "least-privilege"


def test_missing_manifest_raises(tmp_path: Path) -> None:
    with pytest.raises(ManifestValidationError) as exc:
        load_manifest(tmp_path / "nope.yaml")
    assert exc.value.code == "NO_MANIFEST"


def test_unknown_field_rejected(tmp_path: Path) -> None:
    text = _valid_text() + "\nunexpected: true\n"
    with pytest.raises(ManifestValidationError):
        load_manifest(_write(tmp_path, text))


def test_reserved_section_rejected(tmp_path: Path) -> None:
    text = _valid_text() + "\njobs:\n  foo: bar\n"
    with pytest.raises(ManifestValidationError) as exc:
        load_manifest(_write(tmp_path, text))
    assert exc.value.code == "MANIFEST_RESERVED_SECTION"


def test_bad_region_rejected(tmp_path: Path) -> None:
    text = _valid_text().replace("region: ap-northeast-2", "region: not-a-region")
    with pytest.raises(ManifestValidationError):
        load_manifest(_write(tmp_path, text))
