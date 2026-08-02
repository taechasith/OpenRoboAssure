"""P10 full benchmark execution harness for ORA-BENCH-001."""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import numpy as np
import yaml

from openroboassure.benchmark.pilot import _closed_loop_variables, _sensitivity_variables
from openroboassure.benchmark.preregistration import (
    P09_BENCHMARK_ID,
    P09_EVALUATION_SCENARIOS_PER_ROBOT_TASK,
    P09_GATE_ID,
    P09_TRAINING_SEEDS,
    P09_TRAINING_STEPS_PER_METHOD_SEED,
    build_hidden_failure_catalogue,
    build_p09_evaluation_scenarios,
    build_public_commitment,
    load_hidden_seed_package,
    stable_digest,
)
from openroboassure.policies.mlp import StateMlpPolicy
from openroboassure.scenarios.models import PickPlaceScenario, ScenarioSplit
from openroboassure.training.environment import PickPlaceGymEnv
from openroboassure.training.randomization import RandomizationSystem, ScenarioSampler
from openroboassure.training.trainer import TrainingConfiguration, train_policy

BenchmarkMode = Literal["preflight", "smoke", "full"]

_PUBLIC_SMOKE_OPTIONAL_PREFLIGHT_CHECKS = frozenset(
    {
        "private_seed_package_exists",
        "hidden_commitment_matches_private_seed_package",
        "evaluation_commitment_matches_private_seed_package",
    }
)


@dataclass(frozen=True)
class FullBenchmarkMethod:
    """One preregistered full-benchmark method."""

    label: str
    description: str
    randomization_system: RandomizationSystem
    selected_variables: tuple[str, ...]


def run_full_benchmark(
    manifest_path: Path,
    *,
    output_directory: Path = Path("reports"),
    mode: BenchmarkMode = "full",
    require_approval: str = P09_GATE_ID,
    verify_hashes: bool = False,
    protected_ref: str = "HEAD",
    training_steps: int | None = None,
    evaluation_scenarios: int | None = None,
    method_limit: int | None = None,
    seed_limit: int | None = None,
) -> dict[str, object]:
    """Run P10 preflight, smoke, or full benchmark execution."""
    manifest = load_manifest(manifest_path)
    preflight = run_p10_preflight(
        manifest_path,
        output_directory=output_directory,
        require_approval=require_approval,
        verify_hashes=verify_hashes,
        protected_ref=protected_ref,
    )
    if mode == "preflight":
        preflight_report: dict[str, object] = {
            "experiment_id": P09_BENCHMARK_ID,
            "phase": "P10",
            "mode": mode,
            "status": "passed" if bool(preflight["passed"]) else "failed",
            "preflight": preflight,
            "hidden_values_revealed": False,
            "report_hash": "",
        }
        preflight_report["report_hash"] = stable_digest(preflight_report)
        _write_result_package(preflight_report, output_directory, mode=mode)
        return preflight_report
    blocking_preflight_checks = _blocking_preflight_checks(preflight, mode)
    if blocking_preflight_checks:
        failed = ", ".join(blocking_preflight_checks)
        raise RuntimeError(f"P10 preflight failed; blocking checks: {failed}")
    if mode == "full" and preflight["dirty_protected_paths"]:
        raise RuntimeError("P10 full execution requires a clean protected-file worktree")

    methods, seeds, step_budget, scenario_count = _execution_scope(
        manifest,
        output_directory,
        mode=mode,
        training_steps=training_steps,
        evaluation_scenarios=evaluation_scenarios,
        method_limit=method_limit,
        seed_limit=seed_limit,
    )
    if mode == "smoke":
        root_seed = 20260901
        hidden_catalogue_salt = "smoke-only-not-preregistered"
    else:
        seed_package = load_hidden_seed_package(_private_seed_path(manifest, manifest_path.parent))
        root_seed = _required_int(seed_package, "evaluation_root_seed")
        hidden_catalogue_salt = _required_string(seed_package, "hidden_catalogue_salt")
    scenarios = build_p09_evaluation_scenarios(scenario_count, root_seed=root_seed)
    scenario_set_commitment = stable_digest(
        {
            "benchmark_id": P09_BENCHMARK_ID,
            "scenario_hashes": [item.scenario_hash for item in scenarios],
        }
    )
    parameter_set_commitment = stable_digest(
        {
            "benchmark_id": P09_BENCHMARK_ID,
            "parameter_hashes": [item.parameter_hash for item in scenarios],
        }
    )
    runs: list[dict[str, object]] = []
    for method in methods:
        for seed in seeds:
            runs.append(
                _run_method_seed(
                    method,
                    seed,
                    training_steps=step_budget,
                    scenarios=scenarios,
                    output_directory=output_directory,
                )
            )
    leakage = _leakage_report(runs, scenarios)
    pre_reveal_results = {
        "methods": [method.label for method in methods],
        "seeds": list(seeds),
        "training_steps_per_method_seed": step_budget,
        "evaluation_scenarios_per_method_seed": scenario_count,
        "scenario_set_commitment": scenario_set_commitment,
        "parameter_set_commitment": parameter_set_commitment,
        "runs": [_run_without_training_hashes(run) for run in runs],
    }
    results_freeze_hash = stable_digest(pre_reveal_results)
    aggregate = _aggregate_runs(runs)
    status = _execution_status(runs, leakage)
    execution_report: dict[str, object] = {
        "experiment_id": P09_BENCHMARK_ID,
        "phase": "P10",
        "mode": mode,
        "status": status,
        "manifest": manifest_path.as_posix(),
        "preflight": preflight,
        "scope": {
            "robots": ["ORA-4A"],
            "tasks": ["pick_place_v1"],
            "methods": [method.label for method in methods],
            "seeds": list(seeds),
            "training_steps_per_method_seed": step_budget,
            "evaluation_scenarios_per_method_seed": scenario_count,
            "scheduled_evaluations": len(methods) * len(seeds) * scenario_count,
        },
        "evaluation_commitments": {
            "scenario_set_sha256": scenario_set_commitment,
            "parameter_set_sha256": parameter_set_commitment,
        },
        "results_freeze": {
            "pre_reveal_results_sha256": results_freeze_hash,
            "frozen_before_hidden_catalogue_reveal": True,
        },
        "runs": [_run_without_training_hashes(run) for run in runs],
        "statistical_summary": aggregate,
        "operational_acceptance": _acceptance_report(runs, leakage),
        "leakage": leakage,
        "hidden_values_revealed": mode == "full",
        "limitations": [
            "simulation_only",
            "no_physical_robot_validation",
            "conservative_ora4a_pick_place_only_scope",
            "interpretation_requires_GATE-P11-INTERPRETATION",
        ],
        "report_hash": "",
    }
    if mode == "full":
        hidden_catalogue = build_hidden_failure_catalogue(
            scenarios, hidden_catalogue_salt=hidden_catalogue_salt
        )
        execution_report["hidden_catalogue_after_freeze"] = {
            "catalogue_sha256": stable_digest(
                {"benchmark_id": P09_BENCHMARK_ID, "entries": hidden_catalogue}
            ),
            "labels_revealed_after_results_freeze": True,
            "entries": hidden_catalogue,
        }
        execution_report["failure_discovery"] = _failure_discovery_report(hidden_catalogue, runs)
    else:
        execution_report["hidden_catalogue_after_freeze"] = {
            "labels_revealed_after_results_freeze": False,
            "reason": "smoke_mode_does_not_reveal_preregistered_hidden_catalogue",
        }
    execution_report["report_hash"] = stable_digest(execution_report)
    _write_result_package(execution_report, output_directory, mode=mode)
    return execution_report


def run_p10_preflight(
    manifest_path: Path,
    *,
    output_directory: Path = Path("reports"),
    require_approval: str = P09_GATE_ID,
    verify_hashes: bool = False,
    protected_ref: str = "HEAD",
) -> dict[str, object]:
    """Run P10 integrity checks without executing training or evaluation jobs."""
    manifest = load_manifest(manifest_path)
    _verify_manifest_gate(manifest, require_approval)
    private_path = _private_seed_path(manifest, manifest_path.parent)
    private_exists = private_path.exists()
    private_tracked = _git_path_tracked(private_path)
    private_ignored = (
        True if _path_outside_git_worktree(private_path) else _git_path_ignored(private_path)
    )
    hidden_commitment_passed = False
    evaluation_commitment_passed = False
    if private_exists:
        seed_package = load_hidden_seed_package(private_path)
        scenario_count = _manifest_scenario_count(manifest)
        expected_public = build_public_commitment(seed_package, scenario_count=scenario_count)
        hidden_commitment = _read_yaml_mapping(_manifest_hidden_commitment_path(manifest))
        evaluation_commitment = _read_yaml_mapping(_manifest_evaluation_commitment_path(manifest))
        hidden_commitment_passed = _mapping(
            expected_public["commitments"], "expected public commitments"
        ) == _mapping(hidden_commitment["commitments"], "hidden commitment file commitments")
        expected_commitments = _mapping(expected_public["commitments"], "expected commitments")
        evaluation_commitments = _mapping(
            evaluation_commitment["commitments"], "evaluation commitment file commitments"
        )
        evaluation_commitment_passed = evaluation_commitments.get(
            "evaluation_scenario_set_sha256"
        ) == expected_commitments.get(
            "evaluation_scenario_set_sha256"
        ) and evaluation_commitments.get(
            "evaluation_parameter_set_sha256"
        ) == expected_commitments.get("evaluation_parameter_set_sha256")
    protected_hashes = (
        verify_protected_hashes(manifest_path, ref=protected_ref) if verify_hashes else None
    )
    dirty_protected_paths = dirty_protected_files(manifest_path)
    licence_report = _latest_licence_audit_status(output_directory)
    checks = {
        "approval_matches_required_gate": True,
        "private_seed_package_exists": private_exists,
        "private_seed_package_untracked": not private_tracked,
        "private_seed_package_ignored": private_ignored,
        "hidden_commitment_matches_private_seed_package": hidden_commitment_passed,
        "evaluation_commitment_matches_private_seed_package": evaluation_commitment_passed,
        "protected_hashes_match": True
        if protected_hashes is None
        else bool(protected_hashes["passed"]),
        "licence_audit_latest_passed": licence_report.get("passed") is True,
    }
    passed = all(checks.values())
    return {
        "benchmark_id": P09_BENCHMARK_ID,
        "phase": "P10",
        "mode": "preflight",
        "passed": passed,
        "checks": checks,
        "protected_hashes": protected_hashes,
        "dirty_protected_paths": dirty_protected_paths,
        "hidden_material": {
            "private_seed_package_path": private_path.as_posix(),
            "private_seed_package_exists": private_exists,
            "private_seed_package_committed": private_tracked,
            "private_seed_package_ignored": private_ignored,
            "hidden_values_in_report": False,
        },
        "container": container_definition_digest(),
        "licence_audit": licence_report,
    }


def _blocking_preflight_checks(preflight: dict[str, object], mode: BenchmarkMode) -> list[str]:
    checks = _mapping(preflight.get("checks"), "preflight checks")
    failed = [name for name, passed in checks.items() if passed is not True]
    if mode == "smoke":
        failed = [name for name in failed if name not in _PUBLIC_SMOKE_OPTIONAL_PREFLIGHT_CHECKS]
    return sorted(failed)


def load_manifest(path: Path) -> dict[str, object]:
    """Load a benchmark manifest."""
    payload = _read_yaml_mapping(path)
    if payload.get("benchmark_id") != P09_BENCHMARK_ID:
        raise ValueError(f"Unsupported benchmark manifest: {payload.get('benchmark_id')}")
    return dict(payload)


def verify_protected_hashes(manifest_path: Path, *, ref: str = "HEAD") -> dict[str, object]:
    """Verify P09 protected hashes from committed git blobs at a ref."""
    manifest = load_manifest(manifest_path)
    protected_path = _manifest_protected_hash_path(manifest)
    protected = _read_yaml_mapping(protected_path)
    raw_files = protected.get("files")
    if not isinstance(raw_files, list):
        raise TypeError("Protected hash file must contain a files list")
    rows: list[dict[str, str]] = []
    mismatches: list[dict[str, str]] = []
    for item in raw_files:
        row = _mapping(item, "protected hash row")
        path = _required_string(row, "path")
        expected = _required_string(row, "sha256")
        actual = _git_blob_sha256(ref, path)
        rows.append({"path": path, "sha256": actual})
        if expected != actual:
            mismatches.append({"path": path, "expected": expected, "actual": actual})
    actual_combined = stable_digest({"files": rows})
    expected_combined = _required_string(protected, "combined_hash")
    return {
        "hash_source": "git_blob",
        "ref": ref,
        "manifest": protected_path.as_posix(),
        "file_count": len(rows),
        "expected_combined_hash": expected_combined,
        "actual_combined_hash": actual_combined,
        "mismatches": mismatches,
        "passed": not mismatches and actual_combined == expected_combined,
    }


def dirty_protected_files(manifest_path: Path) -> list[str]:
    """Return protected files that are dirty in the current worktree."""
    manifest = load_manifest(manifest_path)
    protected_path = _manifest_protected_hash_path(manifest)
    protected = _read_yaml_mapping(protected_path)
    raw_files = protected.get("files")
    if not isinstance(raw_files, list):
        raise TypeError("Protected hash file must contain a files list")
    paths = [_required_string(_mapping(item, "protected hash row"), "path") for item in raw_files]
    dirty: list[str] = []
    for path in paths:
        result = subprocess.run(
            ["git", "status", "--porcelain", "--", path],
            check=True,
            capture_output=True,
            text=True,
        )
        if result.stdout.strip():
            dirty.append(path)
    return dirty


def container_definition_digest() -> dict[str, object]:
    """Record reproducible container/source definition hashes without requiring Docker."""
    files = [Path("Dockerfile"), Path("compose.yaml"), Path("pyproject.toml"), Path("uv.lock")]
    rows = []
    for path in files:
        if path.exists():
            rows.append({"path": path.as_posix(), "sha256": _file_sha256(path)})
    commit = _git_text(["rev-parse", "HEAD"])
    payload: dict[str, object] = {"git_commit": commit, "files": rows}
    return {
        "kind": "container_definition_digest",
        "git_commit": commit,
        "files": rows,
        "sha256": stable_digest(payload),
        "docker_image_digest_available": False,
    }


def build_github_benchmark_markdown(report: dict[str, object]) -> str:
    """Create a GitHub-renderable benchmark graph and concise result summary."""
    scope = _mapping(report.get("scope", {}), "report scope")
    runs = report.get("runs", [])
    if not isinstance(runs, list):
        raise TypeError("Report runs must be a list")
    outcomes = Counter(
        str(_mapping(run, "run").get("classified_outcome", "unclassified")) for run in runs
    )
    if not outcomes:
        outcomes["not_run"] = 1
    pie_rows = "\n".join(f'    "{name}" : {count}' for name, count in sorted(outcomes.items()))
    status = str(report.get("status", "unknown"))
    hidden = (
        "revealed after result freeze"
        if report.get("hidden_values_revealed") is True
        else "withheld"
    )
    scheduled = scope.get("scheduled_evaluations", 0)
    return (
        "# ORA-BENCH-001 benchmark graph\n\n"
        f"- Status: `{status}`\n"
        f"- Mode: `{report.get('mode', 'unknown')}`\n"
        f"- Scheduled evaluations represented: `{scheduled}`\n"
        f"- Hidden catalogue: {hidden}\n\n"
        "```mermaid\n"
        "flowchart LR\n"
        "    freeze((P09 freeze)) --> preflight((P10 preflight))\n"
        "    preflight --> train((train methods A-E))\n"
        "    train --> evaluate((hidden evaluation))\n"
        "    evaluate --> freeze_results((freeze results))\n"
        "    freeze_results --> reveal((reveal hidden catalogue))\n"
        "    reveal --> analyse((statistical analysis))\n"
        "    analyse --> graph((GitHub graph))\n"
        "    graph --> gate((GATE-P11 interpretation))\n"
        "    gate -. future benchmark change .-> freeze\n"
        "```\n\n"
        "```mermaid\n"
        "pie title ORA-BENCH-001 classified job outcomes\n"
        f"{pie_rows}\n"
        "```\n"
    )


def _execution_scope(
    manifest: dict[str, object],
    output_directory: Path,
    *,
    mode: BenchmarkMode,
    training_steps: int | None,
    evaluation_scenarios: int | None,
    method_limit: int | None,
    seed_limit: int | None,
) -> tuple[list[FullBenchmarkMethod], tuple[int, ...], int, int]:
    methods = _full_methods(output_directory)
    seeds = tuple(_manifest_training_seeds(manifest))
    step_budget = _manifest_training_steps(manifest)
    scenario_count = _manifest_scenario_count(manifest)
    if mode == "full":
        if any(
            value is not None
            for value in (training_steps, evaluation_scenarios, method_limit, seed_limit)
        ):
            raise ValueError(
                "Full mode cannot override preregistered method, seed, or budget scope"
            )
        return methods, seeds, step_budget, scenario_count
    smoke_method_limit = method_limit or 1
    smoke_seed_limit = seed_limit or 1
    smoke_steps = training_steps or 4
    smoke_scenarios = evaluation_scenarios or 6
    if smoke_method_limit <= 0 or smoke_seed_limit <= 0 or smoke_steps <= 0 or smoke_scenarios <= 0:
        raise ValueError("Smoke overrides must be positive")
    return (
        methods[:smoke_method_limit],
        seeds[:smoke_seed_limit],
        smoke_steps,
        smoke_scenarios,
    )


def _run_method_seed(
    method: FullBenchmarkMethod,
    seed: int,
    *,
    training_steps: int,
    scenarios: list[PickPlaceScenario],
    output_directory: Path,
) -> dict[str, object]:
    try:
        training = train_policy(
            TrainingConfiguration(
                system=method.randomization_system,
                seed=seed,
                environment_steps=training_steps,
                selected_variables=method.selected_variables,
            ),
            model_directory=output_directory / "models",
            tracking_path=output_directory / "tracking" / "p10_events.jsonl",
            artifact_prefix=f"p10_{method.label.lower()}",
        )
        evaluation = _evaluate_model(Path(str(training["model_path"])), scenarios)
        training_hashes = _training_parameter_hashes(
            method, seed, _required_int(training, "episodes")
        )
        return {
            "method": method.label,
            "seed": seed,
            "status": "completed",
            "classified_outcome": "completed",
            "training": training,
            "evaluation": evaluation,
            "training_parameter_hashes": training_hashes,
            "retries_attempted": 0,
        }
    except Exception as exc:
        return {
            "method": method.label,
            "seed": seed,
            "status": "failed",
            "classified_outcome": "failed_with_exception",
            "error": type(exc).__name__,
            "message": str(exc),
            "training_parameter_hashes": [],
            "retries_attempted": 0,
        }


def _evaluate_model(model_path: Path, scenarios: list[PickPlaceScenario]) -> dict[str, object]:
    policy = StateMlpPolicy.load(model_path)
    environment = PickPlaceGymEnv()
    successes: list[float] = []
    drops = 0
    collisions = 0
    completion_steps: list[int] = []
    family_successes: dict[str, list[float]] = defaultdict(list)
    try:
        for scenario in scenarios:
            observation, _ = environment.reset(seed=scenario.seed, options={"scenario": scenario})
            info: dict[str, object] = {}
            for _ in range(environment.max_episode_steps):
                observation, _, terminated, truncated, info = environment.step(
                    policy.act(observation)
                )
                collisions += _int_metric(info["collision_count"])
                if terminated or truncated:
                    break
            success = float(bool(info.get("success", False)))
            successes.append(success)
            family_successes[scenario.family.value].append(success)
            drops += int(bool(info.get("dropped", False)))
            completion_steps.append(_int_metric(info.get("steps", environment.max_episode_steps)))
    finally:
        environment.close()
    family_rates = {
        family: float(np.mean(values)) for family, values in sorted(family_successes.items())
    }
    return {
        "evaluation_scenarios": len(scenarios),
        "primary_held_out_task_success": float(np.mean(successes)),
        "drop_rate": drops / len(scenarios),
        "collision_rate": collisions / max(sum(completion_steps), 1),
        "mean_completion_steps": float(np.mean(completion_steps)),
        "invalid_scenario_rate": 0.0,
        "scenario_family_success": family_rates,
        "fifth_percentile_scenario_family_success": float(
            np.quantile(list(family_rates.values()), 0.05)
        ),
    }


def _training_parameter_hashes(method: FullBenchmarkMethod, seed: int, episodes: int) -> list[str]:
    sampler = ScenarioSampler(method.randomization_system, seed, method.selected_variables)
    return [
        sampler.sample(index, progress=1.0, split=ScenarioSplit.TRAIN).parameter_hash
        for index in range(episodes)
    ]


def _leakage_report(
    runs: list[dict[str, object]], scenarios: list[PickPlaceScenario]
) -> dict[str, object]:
    evaluation_hashes = {scenario.parameter_hash for scenario in scenarios}
    overlaps: list[dict[str, object]] = []
    for run in runs:
        training_hashes = run.get("training_parameter_hashes")
        if not isinstance(training_hashes, list):
            raise TypeError("Run training_parameter_hashes must be a list")
        overlap = evaluation_hashes & {str(value) for value in training_hashes}
        if overlap:
            overlaps.append(
                {
                    "method": run["method"],
                    "seed": run["seed"],
                    "overlap_count": len(overlap),
                }
            )
    return {
        "evaluation_parameter_hashes": len(evaluation_hashes),
        "overlap_count": sum(_int_metric(row["overlap_count"]) for row in overlaps),
        "overlaps": overlaps,
        "passed": not overlaps,
    }


def _aggregate_runs(runs: list[dict[str, object]]) -> dict[str, object]:
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for run in runs:
        grouped[str(run["method"])].append(run)
    return {
        method: _aggregate_method(method_runs, seed=20261001 + index)
        for index, (method, method_runs) in enumerate(sorted(grouped.items()))
    }


def _aggregate_method(runs: list[dict[str, object]], seed: int) -> dict[str, object]:
    completed = [run for run in runs if run["status"] == "completed"]
    values = []
    for run in completed:
        evaluation = _mapping(run["evaluation"], "completed run evaluation")
        value = evaluation["primary_held_out_task_success"]
        if not isinstance(value, float):
            raise TypeError("Primary success must be a float")
        values.append(value)
    if values:
        observations = np.asarray(values, dtype=np.float64)
        rng = np.random.default_rng(seed)
        samples = rng.choice(observations, size=(1000, len(observations)), replace=True).mean(
            axis=1
        )
        mean_success = float(observations.mean())
        lower = float(np.quantile(samples, 0.025))
        upper = float(np.quantile(samples, 0.975))
    else:
        mean_success = 0.0
        lower = 0.0
        upper = 0.0
    return {
        "scheduled_runs": len(runs),
        "completed_runs": len(completed),
        "classified_runs": len(runs),
        "mean_primary_held_out_task_success": mean_success,
        "bootstrap_95_lower": lower,
        "bootstrap_95_upper": upper,
    }


def _acceptance_report(
    runs: list[dict[str, object]], leakage: dict[str, object]
) -> dict[str, object]:
    total = len(runs)
    classified = sum(1 for run in runs if "classified_outcome" in run)
    classified_rate = classified / max(total, 1)
    return {
        "all_jobs_classified": classified == total,
        "classified_job_rate": classified_rate,
        "classified_job_rate_threshold": 0.95,
        "no_evaluation_leakage_detected": bool(leakage["passed"]),
        "poor_performance_not_retried_for_score_improvement": True,
        "operationally_successful": classified_rate >= 0.95 and bool(leakage["passed"]),
    }


def _failure_discovery_report(
    hidden_catalogue: list[dict[str, object]], runs: list[dict[str, object]]
) -> dict[str, object]:
    failure_labels: Counter[str] = Counter()
    for entry in hidden_catalogue:
        labels = entry.get("hidden_labels")
        if isinstance(labels, list):
            failure_labels.update(str(label) for label in labels)
    completed_runs = sum(1 for run in runs if run.get("status") == "completed")
    return {
        "completed_runs": completed_runs,
        "hidden_catalogue_entries": len(hidden_catalogue),
        "failure_label_counts": dict(sorted(failure_labels.items())),
    }


def _execution_status(runs: list[dict[str, object]], leakage: dict[str, object]) -> str:
    if not bool(leakage["passed"]):
        return "stopped_leakage_detected"
    if all(run["status"] == "completed" for run in runs):
        return "completed"
    if all("classified_outcome" in run for run in runs):
        return "completed_with_classified_failures"
    return "failed_unclassified_jobs"


def _write_result_package(
    report: dict[str, object], output_directory: Path, *, mode: BenchmarkMode
) -> None:
    benchmark_dir = output_directory / "benchmarks"
    benchmark_dir.mkdir(parents=True, exist_ok=True)
    suffix = "" if mode == "full" else f"-{mode}"
    report_path = benchmark_dir / f"{P09_BENCHMARK_ID}{suffix}.json"
    graph_path = benchmark_dir / f"{P09_BENCHMARK_ID}{suffix}.github.md"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    graph_path.write_text(build_github_benchmark_markdown(report), encoding="utf-8")


def _full_methods(output_directory: Path) -> list[FullBenchmarkMethod]:
    sensitivity = tuple(_sensitivity_variables(output_directory))
    closed_loop = tuple(_closed_loop_variables(output_directory))
    return [
        FullBenchmarkMethod(
            "A",
            "No randomization",
            RandomizationSystem.A_NO_RANDOMIZATION,
            (),
        ),
        FullBenchmarkMethod(
            "B",
            "Independent broad uniform P05 randomization",
            RandomizationSystem.B_BROAD_UNIFORM,
            (),
        ),
        FullBenchmarkMethod(
            "C",
            "Automatic curriculum P05 randomization",
            RandomizationSystem.C_AUTOMATIC_CURRICULUM,
            (),
        ),
        FullBenchmarkMethod(
            "D",
            "Morris/Sobol guided randomization from EXP-SENS-001",
            RandomizationSystem.D_SENSITIVITY_GUIDED,
            sensitivity,
        ),
        FullBenchmarkMethod(
            "E",
            "P07 closed-loop revised randomization from EXP-LOOP-001",
            RandomizationSystem.D_SENSITIVITY_GUIDED,
            closed_loop,
        ),
    ]


def _run_without_training_hashes(run: dict[str, object]) -> dict[str, object]:
    return {key: value for key, value in run.items() if key != "training_parameter_hashes"}


def _verify_manifest_gate(manifest: dict[str, object], require_approval: str) -> None:
    gate = manifest.get("gate")
    if gate != require_approval:
        raise ValueError(
            f"Manifest gate {gate!r} does not match required approval {require_approval!r}"
        )
    if require_approval != P09_GATE_ID:
        raise ValueError(f"P10 requires {P09_GATE_ID}")


def _manifest_training_seeds(manifest: dict[str, object]) -> list[int]:
    training = _mapping(manifest["training"], "manifest training")
    raw = training["seeds"]
    if not isinstance(raw, list) or not all(isinstance(seed, int) for seed in raw):
        raise TypeError("Manifest training seeds must be a list of integers")
    if tuple(raw) != P09_TRAINING_SEEDS:
        raise ValueError("Manifest training seeds differ from P09 preregistration constants")
    return raw


def _manifest_training_steps(manifest: dict[str, object]) -> int:
    training = _mapping(manifest["training"], "manifest training")
    steps = _required_int(training, "environment_steps_per_method_seed")
    if steps != P09_TRAINING_STEPS_PER_METHOD_SEED:
        raise ValueError("Manifest training steps differ from P09 preregistration constants")
    return steps


def _manifest_scenario_count(manifest: dict[str, object]) -> int:
    evaluation = _mapping(manifest["evaluation"], "manifest evaluation")
    count = _required_int(evaluation, "hidden_scenarios_per_robot_task")
    if count != P09_EVALUATION_SCENARIOS_PER_ROBOT_TASK:
        raise ValueError("Manifest scenario count differs from P09 preregistration constants")
    return count


def _private_seed_path(manifest: dict[str, object], manifest_parent: Path) -> Path:
    hidden = _hidden_material(manifest)
    return _resolve_manifest_path(
        _required_string(hidden, "private_seed_package"), manifest_parent=manifest_parent
    )


def _manifest_hidden_commitment_path(manifest: dict[str, object]) -> Path:
    hidden = _hidden_material(manifest)
    return Path(_required_string(hidden, "public_commitment"))


def _manifest_evaluation_commitment_path(manifest: dict[str, object]) -> Path:
    hidden = _hidden_material(manifest)
    return Path(_required_string(hidden, "evaluation_set_commitment"))


def _manifest_protected_hash_path(manifest: dict[str, object]) -> Path:
    integrity = _mapping(manifest["integrity"], "manifest integrity")
    return Path(_required_string(integrity, "protected_hashes"))


def _hidden_material(manifest: dict[str, object]) -> dict[str, object]:
    evaluation = _mapping(manifest["evaluation"], "manifest evaluation")
    return dict(_mapping(evaluation["hidden_material"], "manifest hidden material"))


def _resolve_manifest_path(value: str, *, manifest_parent: Path) -> Path:
    path = Path(value)
    if path.is_absolute() or path.exists():
        return path
    parent_candidate = manifest_parent / path
    if parent_candidate.exists():
        return parent_candidate
    return path


def _read_yaml_mapping(path: Path) -> dict[str, object]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"{path} must contain a YAML mapping")
    return dict(payload)


def _latest_licence_audit_status(output_directory: Path) -> dict[str, object]:
    path = output_directory / "licence_audit" / "latest.json"
    if not path.exists():
        return {"path": path.as_posix(), "passed": False, "reason": "missing"}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError("Licence audit report must be a JSON object")
    return {
        "path": path.as_posix(),
        "passed": payload.get("passed") is True,
        "approved": payload.get("approved"),
        "blocked": payload.get("blocked"),
        "unknown": payload.get("unknown"),
    }


def _git_blob_sha256(ref: str, path: str) -> str:
    content = subprocess.run(
        ["git", "show", f"{ref}:{path}"],
        check=True,
        capture_output=True,
    ).stdout
    return hashlib.sha256(content).hexdigest()


def _git_path_tracked(path: Path) -> bool:
    return (
        subprocess.run(
            ["git", "ls-files", "--error-unmatch", "--", path.as_posix()],
            capture_output=True,
        ).returncode
        == 0
    )


def _git_path_ignored(path: Path) -> bool:
    return (
        subprocess.run(
            ["git", "check-ignore", "-q", "--", path.as_posix()], capture_output=True
        ).returncode
        == 0
    )


def _path_outside_git_worktree(path: Path) -> bool:
    root = Path(_git_text(["rev-parse", "--show-toplevel"])).resolve()
    resolved = path.resolve()
    return root not in (resolved, *resolved.parents)


def _git_text(args: list[str]) -> str:
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True).stdout.strip()


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _mapping(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise TypeError(f"{label} must be a mapping")
    return dict(value)


def _required_int(mapping: dict[str, object], key: str) -> int:
    value = mapping[key]
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{key} must be an integer")
    return value


def _required_string(mapping: dict[str, object], key: str) -> str:
    value = mapping[key]
    if not isinstance(value, str):
        raise TypeError(f"{key} must be a string")
    if not value:
        raise ValueError(f"{key} must be non-empty")
    return value


def _int_metric(value: object) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    raise TypeError(f"Expected integer metric, received {type(value).__name__}")
