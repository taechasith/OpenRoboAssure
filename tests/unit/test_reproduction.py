"""P12 reproduction command tests."""

from __future__ import annotations

from pathlib import Path

from openroboassure.reproduction import (
    P12_SMOKE_CERTIFICATE,
    certificate_exit_code,
    run_smoke_reproduction,
)


def test_smoke_reproduction_writes_certificate(tmp_path: Path) -> None:
    certificate = run_smoke_reproduction(
        tmp_path / "reports",
        baseline_seeds=2,
        scenario_count=12,
        execution_samples=2,
        benchmark_training_steps=4,
        benchmark_evaluation_scenarios=6,
        require_no_private_files=False,
        verify_protected_hashes=False,
    )

    assert certificate["status"] == "passed"
    assert certificate_exit_code(certificate) == 0
    assert (tmp_path / "reports" / P12_SMOKE_CERTIFICATE).exists()
    checks = certificate["checks"]
    assert isinstance(checks, dict)
    assert checks["benchmark_smoke_does_not_reveal_hidden_values"] is True
    metrics = certificate["metrics"]
    assert isinstance(metrics, dict)
    assert metrics["baseline_success_rate"] == 1.0
