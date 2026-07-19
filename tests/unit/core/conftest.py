from collections.abc import Callable

import pytest

from thingflash.core.manifest import Manifest

ManifestFactory = Callable[..., Manifest]


@pytest.fixture
def make_manifest() -> ManifestFactory:
    def _make(
        *,
        name: str = "proj",
        region: str = "us-east-1",
        thing_type: str = "sensor",
        groups: list[str] | None = None,
        mode: str = "least-privilege",
        topics: dict[str, str] | None = None,
    ) -> Manifest:
        return Manifest(
            apiVersion="thingflash.com/v1",
            kind="IoTProject",
            metadata={"name": name},
            aws={"region": region},
            fleet={
                "thingType": thing_type,
                "groups": groups or ["default"],
                "policies": {"mode": mode},
            },
            mqtt={"topics": topics or {}},
        )

    return _make
