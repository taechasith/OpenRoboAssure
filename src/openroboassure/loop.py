"""System E closed-loop execution for P07."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from openroboassure.calibration.hidden_target import (
    CALIBRATION_VARIABLES,
    run_hidden_target_calibration,
)
from openroboassure.coverage.reports import run_coverage_report
from openroboassure.falsification.replay import replay_counterexamples
from openroboassure.falsification.search import run_falsification_search
from openroboassure.scenarios.ontology import CORE_PICK_PLACE_REGISTRY
from openroboassure.training.randomization import RandomizationSystem
from openroboassure.training.trainer import (
    TrainingConfiguration,
    build_evaluation_scenarios,
    evaluate_policy,
    train_policy,
)

P07_RETRAIN_STEPS = 2_048
P07_SYSTEM_E_SEED = 77


def run_closed_loop(
    output_directory: Path,
    *,
    retrain_steps: int = P07_RETRAIN_STEPS,
    seed: int = 20260730,
) -> dict[str, object]:
    """Run the P07 System E loop end to end and preserve all outcomes."""
    if retrain_steps <= 0:
        raise ValueError("retrain_steps must be positive")
    calibration_path = output_directory / "calibration" / "EXP-CALIBRATION-001.json"
    falsification_path = output_directory / "counterexamples" / "EXP-FALSIFICATION-001.json"
    replay_path = output_directory / "counterexamples" / "EXP-FALSIFICATION-REPLAY-001.json"
    coverage_path = output_directory / "coverage" / "EXP-COVERAGE-001.json"
    loop_path = output_directory / "benchmarks" / "EXP-LOOP-001.json"

    calibration = run_hidden_target_calibration(calibration_path, seed=seed)
    falsification = run_falsification_search(falsification_path, trials=96, seed=seed)
    counterexamples = falsification["counterexamples"]
    if not isinstance(counterexamples, list):
        raise TypeError("Falsification report counterexamples must be a list")
    replay = replay_counterexamples(counterexamples, replay_path)
    coverage = run_coverage_report(
        coverage_path,
        scenario_count=128,
        seed=seed,
        counterexamples_path=falsification_path,
    )
    sensitivity_variables = _sensitivity_variables(output_directory)
    revision = _revise_randomization(
        sensitivity_variables=sensitivity_variables,
        calibration=calibration,
        falsification=falsification,
        coverage=coverage,
    )
    revised_variables = revision["revised_randomization_variables"]
    if not isinstance(revised_variables, list) or not all(
        isinstance(item, str) for item in revised_variables
    ):
        raise TypeError("Revised variables must be a list of strings")

    evaluation_scenarios = build_evaluation_scenarios()
    before = _evaluate_existing_baseline(output_directory, evaluation_scenarios)
    training = train_policy(
        TrainingConfiguration(
            system=RandomizationSystem.D_SENSITIVITY_GUIDED,
            seed=P07_SYSTEM_E_SEED,
            environment_steps=retrain_steps,
            selected_variables=tuple(revised_variables),
        ),
        model_directory=output_directory / "models",
        tracking_path=output_directory / "tracking" / "p07_events.jsonl",
        artifact_prefix="p07_system_e",
    )
    after = evaluate_policy(Path(str(training["model_path"])), evaluation_scenarios)
    comparison = _comparison(before, after)
    report: dict[str, object] = {
        "experiment_id": "EXP-LOOP-001",
        "scope": "P07 System E closed loop: sensitivity, calibration, falsification, coverage, revision, retraining, comparison",
        "inputs": {
            "sensitivity_variables": sensitivity_variables,
            "calibration_report": calibration_path.as_posix(),
            "falsification_report": falsification_path.as_posix(),
            "replay_report": replay_path.as_posix(),
            "coverage_report": coverage_path.as_posix(),
        },
        "revision": revision,
        "retraining": {
            "method": "P06 state-only trainer with revised System E randomization variables",
            "seed": P07_SYSTEM_E_SEED,
            "environment_steps": retrain_steps,
            "model_path": training["model_path"],
            "model_hash": training["model_hash"],
            "note": "CPU-sized P07 loop demonstration, not a replacement for P08 pilot budget",
        },
        "comparison": comparison,
        "negative_results_preserved": _negative_result_notes(comparison, calibration, replay),
        "limitations": [
            "simulation_only",
            "no_physical_robot_validation",
            "uses_internal_verifai_compatible_search_api_not_external_verifai",
            "p07_retraining_budget_is_demonstration_scale",
        ],
        "report_hash": "",
    }
    report["report_hash"] = _hash_mapping(report)
    loop_path.parent.mkdir(parents=True, exist_ok=True)
    loop_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def _sensitivity_variables(output_directory: Path) -> list[str]:
    path = output_directory / "sensitivity" / "EXP-SENS-001.json"
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    variables = payload.get("system_d_variables")
    if not isinstance(variables, list) or not all(isinstance(item, str) for item in variables):
        raise TypeError("Sensitivity report system_d_variables must be a string list")
    return variables


def _revise_randomization(
    *,
    sensitivity_variables: list[str],
    calibration: dict[str, object],
    falsification: dict[str, object],
    coverage: dict[str, object],
) -> dict[str, object]:
    evidence: dict[str, set[str]] = {
        parameter.name: set() for parameter in CORE_PICK_PLACE_REGISTRY.parameters
    }
    for name in sensitivity_variables:
        if name in evidence:
            evidence[name].add("sensitivity")
    for name in CALIBRATION_VARIABLES:
        evidence[name].add("calibration")
    for name in _counterexample_parameters(falsification):
        evidence[name].add("counterexample")
    for name in _coverage_gap_parameters(coverage):
        evidence[name].add("coverage_gap")
    selected = sorted(name for name, reasons in evidence.items() if reasons)
    rows = [
        {
            "parameter": name,
            "category": CORE_PICK_PLACE_REGISTRY.parameter(name).category,
            "evidence": sorted(evidence[name]),
            "change": "include_in_system_e_randomization",
        }
        for name in selected
    ]
    return {
        "revised_randomization_variables": selected,
        "distribution_changes": rows,
        "change_rule": "include any approved P05 variable supported by sensitivity, calibration, counterexample, or coverage-gap evidence",
    }


def _counterexample_parameters(falsification: dict[str, object]) -> set[str]:
    counterexamples = falsification["counterexamples"]
    if not isinstance(counterexamples, list):
        raise TypeError("Falsification counterexamples must be a list")
    names: set[str] = set()
    nominal = {
        parameter.name: parameter.nominal for parameter in CORE_PICK_PLACE_REGISTRY.parameters
    }
    for counterexample in counterexamples[:5]:
        if not isinstance(counterexample, dict):
            raise TypeError("Counterexample record must be a mapping")
        values = counterexample["parameter_values"]
        if not isinstance(values, dict):
            raise TypeError("Counterexample parameter_values must be a mapping")
        deviations = []
        for key, value in values.items():
            if not isinstance(key, str) or not isinstance(value, int | float) or key not in nominal:
                continue
            parameter = CORE_PICK_PLACE_REGISTRY.parameter(key)
            low, high = parameter.global_bounds
            scale = high - low
            deviation = abs(float(value) - nominal[key]) / scale if scale > 0.0 else 0.0
            deviations.append((deviation, key))
        names.update(name for _, name in sorted(deviations, reverse=True)[:3])
    return names


def _coverage_gap_parameters(coverage: dict[str, object]) -> set[str]:
    summary = coverage["summary"]
    if not isinstance(summary, dict):
        raise TypeError("Coverage summary must be a mapping")
    gap_queue = summary["coverage_gap_queue"]
    if not isinstance(gap_queue, list):
        raise TypeError("Coverage gap queue must be a list")
    names: set[str] = set()
    for gap in gap_queue[:8]:
        if not isinstance(gap, dict):
            raise TypeError("Coverage gap must be a mapping")
        parameters = gap["parameters"]
        if not isinstance(parameters, list):
            raise TypeError("Coverage gap parameters must be a list")
        names.update(str(parameter) for parameter in parameters)
    return names


def _evaluate_existing_baseline(
    output_directory: Path, evaluation_scenarios: object
) -> dict[str, object]:
    baseline_path = output_directory / "models" / "p06_d_11.npz"
    if not baseline_path.exists():
        return {
            "available": False,
            "reason": "reports/models/p06_d_11.npz not found",
        }
    if not isinstance(evaluation_scenarios, list):
        raise TypeError("Evaluation scenarios must be a list")
    evaluation = evaluate_policy(baseline_path, evaluation_scenarios)
    return {"available": True, "model_path": baseline_path.as_posix(), "evaluation": evaluation}


def _comparison(before: dict[str, object], after: dict[str, object]) -> dict[str, object]:
    after_success = _primary_success(after)
    if before.get("available") is not True:
        return {
            "before_available": False,
            "after_primary_held_out_task_success": after_success,
            "delta_primary_held_out_task_success": None,
            "status": "comparison_baseline_missing",
        }
    before_evaluation = before["evaluation"]
    if not isinstance(before_evaluation, dict):
        raise TypeError("Baseline evaluation must be a mapping")
    before_success = _primary_success(before_evaluation)
    delta = after_success - before_success
    return {
        "before_available": True,
        "before_model_path": before["model_path"],
        "before_primary_held_out_task_success": before_success,
        "after_primary_held_out_task_success": after_success,
        "delta_primary_held_out_task_success": delta,
        "status": "improved" if delta > 0.0 else "negative_result_preserved",
    }


def _primary_success(evaluation: dict[str, object]) -> float:
    value = evaluation["primary_held_out_task_success"]
    if not isinstance(value, float):
        raise TypeError("Evaluation primary success must be a float")
    return value


def _negative_result_notes(
    comparison: dict[str, object], calibration: dict[str, object], replay: dict[str, object]
) -> list[str]:
    notes: list[str] = []
    if comparison.get("status") == "negative_result_preserved":
        notes.append("closed_loop_retraining_did_not_improve_primary_success")
    discrepancy = calibration["discrepancy"]
    if isinstance(discrepancy, dict) and discrepancy.get("status") == "negative_result_preserved":
        notes.append("calibration_did_not_improve_observation_rmse")
    replay_rate = replay["replayed_failure_rate"]
    if isinstance(replay_rate, float) and replay_rate > 0.0:
        notes.append("counterexamples_remain_replayable_failures")
    return notes


def _hash_mapping(value: dict[str, object]) -> str:
    text = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
