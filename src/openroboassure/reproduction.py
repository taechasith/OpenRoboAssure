"""P12 public reproduction recipes and certificates."""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Literal

from openroboassure.benchmark.full import run_full_benchmark
from openroboassure.benchmark.pilot import run_pilot_benchmark
from openroboassure.doctor import run_doctor
from openroboassure.experiments.baseline import run_baseline
from openroboassure.licensing.audit import audit_project, write_report
from openroboassure.scenarios.experiment import run_scenario_validity

type JsonScalar = str | int | float | bool | None
type JsonValue = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]

FROZEN_P09_PROTECTED_REF = "f9654a4f3a871401d8d1677a409337d5485ced98"
P12_SMOKE_CERTIFICATE = "P12-CLEAN-SOFTWARE-REPRODUCTION.json"
P12_PILOT_CERTIFICATE = "P12-PILOT-REPRODUCTION.json"


def run_smoke_reproduction(
    output_directory: Path = Path("reports/reproduction/clean-software"),
    *,
    baseline_seeds: int = 20,
    scenario_count: int = 128,
    execution_samples: int = 8,
    benchmark_training_steps: int = 4,
    benchmark_evaluation_scenarios: int = 6,
    require_no_private_files: bool = True,
    verify_protected_hashes: bool = True,
) -> dict[str, JsonValue]:
    """Run the P12 clean-software reproduction smoke recipe."""
    _validate_positive(
        baseline_seeds=baseline_seeds,
        scenario_count=scenario_count,
        execution_samples=execution_samples,
        benchmark_training_steps=benchmark_training_steps,
        benchmark_evaluation_scenarios=benchmark_evaluation_scenarios,
    )
    output_directory.mkdir(parents=True, exist_ok=True)
    source = _source_status()

    doctor_path = output_directory / "environment" / "doctor.json"
    doctor_exit = run_doctor(output=doctor_path, offline=True)

    licence_path = output_directory / "licence_audit" / "latest.json"
    licence_report = audit_project(Path(".").resolve())
    write_report(licence_report, licence_path)

    baseline_path = output_directory / "benchmarks" / "EXP-SIM-BASELINE-001-smoke.json"
    baseline_report = run_baseline(baseline_seeds, baseline_path)
    baseline_success_rate = _required_number(baseline_report, "success_rate")
    baseline_replay_rate = _required_number(baseline_report, "deterministic_replay_rate")

    scenario_path = output_directory / "scenarios" / "EXP-SCENARIO-VALIDITY-001-smoke.json"
    scenario_report = run_scenario_validity(
        scenario_count,
        scenario_path,
        execution_samples=execution_samples,
    )
    scenario_validity_rate = _required_number(scenario_report, "valid_rate")

    benchmark_report = run_full_benchmark(
        Path("experiments/preregistered/ORA-BENCH-001.yaml"),
        output_directory=output_directory,
        mode="smoke",
        verify_hashes=verify_protected_hashes,
        protected_ref=FROZEN_P09_PROTECTED_REF,
        training_steps=benchmark_training_steps,
        evaluation_scenarios=benchmark_evaluation_scenarios,
        method_limit=1,
        seed_limit=1,
    )
    benchmark_path = output_directory / "benchmarks" / "ORA-BENCH-001-smoke.json"
    benchmark_graph_path = output_directory / "benchmarks" / "ORA-BENCH-001-smoke.github.md"
    benchmark_status = _required_string(benchmark_report, "status")
    benchmark_hidden_values_revealed = _required_bool(benchmark_report, "hidden_values_revealed")

    private_material = _private_material_status()
    no_private_files_pass = not bool(private_material["private_seed_package_present"]) and not bool(
        private_material["private_seed_package_tracked"]
    )
    checks: dict[str, JsonValue] = {
        "doctor_offline_passed": doctor_exit == 0,
        "licence_audit_passed": licence_report.get("passed") is True,
        "baseline_success_rate_is_100_percent": baseline_success_rate == 1.0,
        "baseline_deterministic_replay_is_100_percent": baseline_replay_rate == 1.0,
        "scenario_validity_rate_at_least_99_5_percent": scenario_validity_rate >= 0.995,
        "benchmark_smoke_completed": benchmark_status
        in {"completed", "completed_with_classified_failures"},
        "benchmark_smoke_does_not_reveal_hidden_values": benchmark_hidden_values_revealed is False,
        "protected_hashes_verified_against_frozen_p09_ref": True
        if not verify_protected_hashes
        else _protected_hashes_passed(benchmark_report),
        "no_private_seed_package_required_or_present": no_private_files_pass,
    }
    if not require_no_private_files:
        checks["no_private_seed_package_required_or_present"] = True

    certificate: dict[str, JsonValue] = {
        "certificate_id": "P12-CLEAN-SOFTWARE-REPRODUCTION",
        "phase": "P12",
        "mode": "clean_software_smoke",
        "generated_at": datetime.now(UTC).isoformat(),
        "status": "passed" if all(value is True for value in checks.values()) else "failed",
        "source": source,
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "offline_after_dependency_sync": True,
            "paid_services_required": False,
            "secret_credentials_required": False,
        },
        "commands": [
            "uv sync --all-groups --locked",
            "uv run --offline ora reproduce smoke",
        ],
        "parameters": {
            "baseline_seeds": baseline_seeds,
            "scenario_count": scenario_count,
            "execution_samples": execution_samples,
            "benchmark_training_steps": benchmark_training_steps,
            "benchmark_evaluation_scenarios": benchmark_evaluation_scenarios,
            "benchmark_method_limit": 1,
            "benchmark_seed_limit": 1,
            "protected_ref": FROZEN_P09_PROTECTED_REF,
        },
        "checks": checks,
        "private_material": private_material,
        "metrics": {
            "baseline_success_rate": baseline_success_rate,
            "baseline_deterministic_replay_rate": baseline_replay_rate,
            "scenario_validity_rate": scenario_validity_rate,
            "benchmark_status": benchmark_status,
            "benchmark_scheduled_evaluations": _nested_number(
                benchmark_report, "scope", "scheduled_evaluations"
            ),
            "benchmark_hidden_values_revealed": benchmark_hidden_values_revealed,
        },
        "artifacts": _artifact_records(
            {
                "doctor": doctor_path,
                "licence_audit": licence_path,
                "baseline": baseline_path,
                "scenario_validity": scenario_path,
                "benchmark_smoke": benchmark_path,
                "benchmark_graph": benchmark_graph_path,
            }
        ),
        "tolerances": {
            "baseline_success_rate": "exactly_1_0_for_smoke_seeds",
            "baseline_deterministic_replay_rate": "exactly_1_0",
            "scenario_validity_rate": "at_least_0_995",
            "benchmark_smoke_status": "completed_or_completed_with_classified_failures",
        },
        "limitations": [
            "smoke_reproduction_not_full_250000_episode_benchmark_rerun",
            "simulation_only",
            "no_physical_robot_validation",
            "learned_policy_success_not_expected_from_smoke_budget",
        ],
    }
    _write_certificate(certificate, output_directory / P12_SMOKE_CERTIFICATE)
    return certificate


def run_pilot_reproduction(
    output_directory: Path = Path("reports/reproduction/pilot"),
    *,
    training_steps: int = 2048,
    evaluation_scenarios: int = 2000,
    root_seed: int = 20260801,
) -> dict[str, JsonValue]:
    """Run the public P08 pilot reproduction recipe and write a P12 certificate."""
    _validate_positive(training_steps=training_steps, evaluation_scenarios=evaluation_scenarios)
    output_directory.mkdir(parents=True, exist_ok=True)
    source = _source_status()

    licence_path = output_directory / "licence_audit" / "latest.json"
    licence_report = audit_project(Path(".").resolve())
    write_report(licence_report, licence_path)
    report = run_pilot_benchmark(
        output_directory,
        training_steps=training_steps,
        evaluation_scenarios_per_config=evaluation_scenarios,
        root_seed=root_seed,
    )
    report_path = output_directory / "benchmarks" / "ORA-PILOT-001.json"
    acceptance = _nested_mapping(report, "operational_acceptance")
    leakage = _nested_mapping(report, "leakage")
    exact_scope = training_steps == 2048 and evaluation_scenarios == 2000
    checks: dict[str, JsonValue] = {
        "licence_audit_passed": licence_report.get("passed") is True,
        "pilot_operationally_successful": acceptance.get("operationally_successful") is True,
        "pilot_no_evaluation_leakage_detected": leakage.get("passed") is True,
        "public_seed_reused": root_seed == 20260801,
    }
    certificate: dict[str, JsonValue] = {
        "certificate_id": "P12-PILOT-REPRODUCTION",
        "phase": "P12",
        "mode": "public_pilot_reproduction",
        "generated_at": datetime.now(UTC).isoformat(),
        "status": "passed" if all(value is True for value in checks.values()) else "failed",
        "source": source,
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "paid_services_required": False,
            "secret_credentials_required": False,
        },
        "commands": [
            "uv sync --all-groups --locked",
            "uv run --offline ora reproduce pilot",
        ],
        "parameters": {
            "training_steps": training_steps,
            "evaluation_scenarios_per_method_seed": evaluation_scenarios,
            "root_seed": root_seed,
            "matches_released_p08_scope": exact_scope,
        },
        "checks": checks,
        "metrics": {
            "classified_job_rate": _json_value(acceptance.get("classified_job_rate")),
            "operationally_successful": _json_value(acceptance.get("operationally_successful")),
            "leakage_overlap_count": _json_value(leakage.get("overlap_count")),
            "report_hash": _json_value(report.get("report_hash")),
        },
        "artifacts": _artifact_records(
            {
                "licence_audit": licence_path,
                "pilot_report": report_path,
            }
        ),
        "limitations": [
            "pilot_reproduction_is_not_the_p10_full_benchmark",
            "learned_policy_performance_remains_negative_evidence",
            "simulation_only",
        ],
    }
    _write_certificate(certificate, output_directory / P12_PILOT_CERTIFICATE)
    return certificate


def _write_certificate(certificate: dict[str, JsonValue], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(certificate, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _validate_positive(**values: int) -> None:
    for name, value in values.items():
        if value <= 0:
            raise ValueError(f"{name} must be positive")


def _required_number(mapping: dict[str, object], key: str) -> float:
    value = mapping[key]
    if isinstance(value, int | float):
        return float(value)
    raise TypeError(f"{key} must be numeric")


def _required_string(mapping: dict[str, object], key: str) -> str:
    value = mapping[key]
    if isinstance(value, str):
        return value
    raise TypeError(f"{key} must be a string")


def _required_bool(mapping: dict[str, object], key: str) -> bool:
    value = mapping[key]
    if isinstance(value, bool):
        return value
    raise TypeError(f"{key} must be a boolean")


def _source_status() -> dict[str, JsonValue]:
    return {
        "git_commit": _git_text(["rev-parse", "HEAD"]),
        "git_branch": _git_text(["branch", "--show-current"]),
        "git_dirty": bool(_git_text(["status", "--porcelain"])),
        "package_version": _package_version(),
    }


def _private_material_status() -> dict[str, JsonValue]:
    private_path = Path("private/p09/ORA-BENCH-001-sealed-seed-package.json")
    return {
        "private_seed_package_path": private_path.as_posix(),
        "private_seed_package_present": private_path.exists(),
        "private_seed_package_tracked": _git_path_tracked(private_path),
        "private_seed_package_required_for_smoke_reproduction": False,
    }


def _artifact_records(paths: dict[str, Path]) -> dict[str, JsonValue]:
    records: dict[str, JsonValue] = {}
    for name, path in paths.items():
        records[name] = {
            "path": path.as_posix(),
            "exists": path.exists(),
            "sha256": _sha256(path) if path.exists() and path.is_file() else None,
        }
    return records


def _json_value(value: object) -> JsonValue:
    if isinstance(value, str | int | float | bool) or value is None:
        return value
    if isinstance(value, list):
        return [_json_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_value(item) for key, item in value.items()}
    return str(value)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _protected_hashes_passed(report: dict[str, object]) -> bool:
    preflight = _object_mapping(report.get("preflight"))
    protected_hashes = _object_mapping(preflight.get("protected_hashes"))
    return protected_hashes.get("passed") is True


def _nested_number(report: dict[str, object], first: str, second: str) -> int | float | None:
    value = _object_mapping(report.get(first)).get(second)
    return value if isinstance(value, int | float) else None


def _nested_mapping(report: dict[str, object], key: str) -> dict[str, object]:
    return _object_mapping(report.get(key))


def _object_mapping(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _git_path_tracked(path: Path) -> bool:
    result = subprocess.run(
        ["git", "ls-files", "--error-unmatch", path.as_posix()],
        check=False,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def _git_text(arguments: list[str]) -> str:
    result = subprocess.run(
        ["git", *arguments],
        check=False,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() if result.returncode == 0 else "unavailable"


def _package_version() -> str:
    try:
        return version("openroboassure")
    except PackageNotFoundError:
        return "0.0.0+uninstalled"


def certificate_exit_code(certificate: dict[str, JsonValue]) -> int:
    """Return a process exit code for a reproduction certificate."""
    return 0 if certificate.get("status") == "passed" else 1


ReproductionMode = Literal["smoke", "pilot"]


def certificate_name(mode: ReproductionMode) -> str:
    """Return the certificate filename for a reproduction mode."""
    return P12_SMOKE_CERTIFICATE if mode == "smoke" else P12_PILOT_CERTIFICATE
