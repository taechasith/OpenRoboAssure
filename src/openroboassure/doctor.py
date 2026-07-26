"""Offline, machine-readable environment diagnostics."""

from __future__ import annotations

import json
import platform
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

type JsonScalar = str | int | float | bool | None
type JsonValue = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]


def package_version() -> str:
    """Return the installed package version without requiring network access."""
    try:
        return version("openroboassure")
    except PackageNotFoundError:
        return "0.1.0+uninstalled"


def build_doctor_report(*, offline: bool) -> dict[str, JsonValue]:
    """Collect facts needed to diagnose the local bootstrap environment."""
    python_compatible = sys.version_info >= (3, 12)
    return {
        "project": "OpenRoboAssure",
        "package_version": package_version(),
        "python": {
            "version": platform.python_version(),
            "implementation": platform.python_implementation(),
            "compatible": python_compatible,
            "required": ">=3.12,<3.13",
            "executable": str(Path(sys.executable).resolve()),
        },
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
        },
        "network_required": False,
        "offline_requested": offline,
        "healthy": python_compatible,
    }


def write_doctor_report(report: dict[str, JsonValue], output: Path) -> None:
    """Write a deterministic JSON environment report."""
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_doctor(*, output: Path, offline: bool) -> int:
    """Generate a report and return a nonzero status for incompatible Python."""
    report = build_doctor_report(offline=offline)
    write_doctor_report(report, output)
    print(f"OpenRoboAssure doctor report: {output}")
    return 0 if report["healthy"] is True else 1
