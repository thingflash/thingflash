from pathlib import Path

import pytest

from thingflash.core import doctor, scaffold
from thingflash.core.scaffold import ProjectConfig


@pytest.mark.e2e
def test_doctor_against_real_aws(tmp_path: Path) -> None:
    """Smoke test that runs the real AWS checks. Excluded by default.

    Run with real credentials via: ``pytest -m e2e``.
    """
    scaffold.init_project(ProjectConfig(name="proj", region="us-east-1"), root=tmp_path)
    checks = {c.name: c for c in doctor.run_checks(tmp_path)}
    assert "aws-identity" in checks
    assert "aws-permissions" in checks
    # We don't assert a specific status: it depends on the caller's real setup.
    assert checks["aws-identity"].status in {doctor.OK, doctor.WARN, doctor.FAIL}
