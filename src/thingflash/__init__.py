"""ThingFlash — production-ready AWS IoT infrastructure from a declarative YAML manifest."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("thingflash")
except PackageNotFoundError:  # package is not installed (e.g. running from source)
    __version__ = "0.0.0"

__all__ = ["__version__"]
