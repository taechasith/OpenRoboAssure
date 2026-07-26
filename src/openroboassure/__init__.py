"""OpenRoboAssure's simulation-only assurance tooling."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("openroboassure")
except PackageNotFoundError:
    __version__ = "0.1.0"
