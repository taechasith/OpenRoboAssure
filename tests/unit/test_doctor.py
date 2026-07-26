from __future__ import annotations

import json
from pathlib import Path

from openroboassure.cli import main
from openroboassure.doctor import build_doctor_report


def test_doctor_report_is_offline_and_python_compatible() -> None:
    report = build_doctor_report(offline=True)

    assert report["network_required"] is False
    assert report["offline_requested"] is True
    assert report["healthy"] is True


def test_doctor_command_writes_machine_readable_report(tmp_path: Path) -> None:
    output = tmp_path / "doctor.json"

    assert main(["doctor", "--offline", "--output", str(output)]) == 0

    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["project"] == "OpenRoboAssure"
    assert report["network_required"] is False
