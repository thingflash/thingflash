from pathlib import Path

import pytest

from thingflash.core import doctor, scaffold
from thingflash.core.scaffold import ProjectConfig


def test_doctor_flags_missing_manifest(tmp_path: Path) -> None:
    checks = {c.name: c for c in doctor.run_checks(tmp_path)}
    assert checks["manifest"].status == doctor.FAIL
    assert doctor.has_failures(doctor.run_checks(tmp_path))


def test_doctor_passes_with_valid_project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    scaffold.init_project(ProjectConfig(name="proj", region="us-east-1"), root=tmp_path)
    monkeypatch.setenv("AWS_PROFILE", "default")
    checks = {c.name: c.status for c in doctor.run_checks(tmp_path)}
    assert checks["manifest"] == doctor.OK
    assert checks["state"] == doctor.OK
    assert not doctor.has_failures(doctor.run_checks(tmp_path))
