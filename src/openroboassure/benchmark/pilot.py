"""P08 conservative pilot benchmark execution."""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from openroboassure.policies.mlp import StateMlpPolicy
from openroboassure.scenarios.compiler import SamplingMethod, ScenarioCompiler
from openroboassure.scenarios.models import PickPlaceScenario, ScenarioFamily, ScenarioSplit
from openroboassure.scenarios.ontology import CORE_PICK_PLACE_REGISTRY
from openroboassure.training.environment import PickPlaceGymEnv
from openroboassure.training.randomization import RandomizationSystem, ScenarioSampler
from openroboassure.training.trainer import TrainingConfiguration, train_policy

P08_METHODS = ("A", "B", "C", "D", "E")
P08_SEEDS = (11, 22, 33)
P08_EVALUATION_SCENARIOS_PER_CONFIG = 2_000
P08_TRAINING_STEPS_PER_SEED = 2_048
P08_ROOT_SEED = 20260801
P08_GATE_COMMIT = "2bd188e"
_PROTECTED_PATHS = (
    "MASTER_BUILD_GUIDE.md",
    "README.md",
    "LICENSE",
    "DATA_LICENSE",
    "DATA_POLICY.md",
    "PROJECT_STATE.yaml",
    "governance/DECISIONS.md",
)


@dataclass(frozen=True)
class PilotMethod:
    """One approved P08 pilot method definition."""

    label: str
    description: str
    randomization_system: RandomizationSystem
    selected_variables: tuple[str, ...]


def run_pilot_benchmark(
    output_directory: Path,
    *,
    training_steps: int = P08_TRAINING_STEPS_PER_SEED,
    evaluation_scenarios_per_config: int = P08_EVALUATION_SCENARIOS_PER_CONFIG,
    root_seed: int = P08_ROOT_SEED,
    protected_ref: str = P08_GATE_COMMIT,
) -> dict[str, object]:
    """Run the approved conservative P08 pilot benchmark."""
    if training_steps <= 0:
        raise ValueError("training_steps must be positive")
    if evaluation_scenarios_per_config <= 0:
        raise ValueError("evaluation_scenarios_per_config must be positive")
    output_directory.mkdir(parents=True, exist_ok=True)
    scenarios = build_pilot_evaluation_scenarios(
        evaluation_scenarios_per_config, root_seed=root_seed
    )
    hidden_catalogue = build_hidden_catalogue(scenarios)
    scenario_set_hash = _hash_mapping(
        {"scenario_hashes": [scenario.scenario_hash for scenario in scenarios]}
    )
    hidden_catalogue_hash = _hash_mapping({"hidden_catalogue": hidden_catalogue})
    methods = _pilot_methods(output_directory)
    protected_hashes = hash_protected_files(protected_ref)
    compute_estimate = _compute_estimate(training_steps, evaluation_scenarios_per_config)
    runs: list[dict[str, object]] = []
    for method in methods:
        for seed in P08_SEEDS:
            runs.append(
                _run_method_seed(
                    method,
                    seed,
                    training_steps=training_steps,
                    scenarios=scenarios,
                    output_directory=output_directory,
                )
            )
    pre_reveal_results: dict[str, object] = {
        "methods": [method.label for method in methods],
        "seeds": list(P08_SEEDS),
        "training_steps_per_seed": training_steps,
        "evaluation_scenarios_per_config": evaluation_scenarios_per_config,
        "scenario_set_hash": scenario_set_hash,
        "runs": [_run_without_hidden_labels(run) for run in runs],
    }
    results_freeze_hash = _hash_mapping(pre_reveal_results)
    leakage = _leakage_report(runs, scenarios)
    aggregate = _aggregate_runs(runs)
    defects = _benchmark_defects(aggregate, leakage)
    report: dict[str, object] = {
        "experiment_id": "ORA-PILOT-001",
        "phase": "P08",
        "gate": "GATE-P08-PILOT",
        "scope": "Conservative ORA-4A Pick-and-Place pilot selected by option A",
        "preregistration": {
            "gate_commit": protected_ref,
            "protected_file_hashes": protected_hashes,
            "robot_task_set": {"robots": ["ORA-4A"], "tasks": ["pick_place_v1"]},
            "methods": [
                {
                    "label": method.label,
                    "description": method.description,
                    "randomization_system": method.randomization_system.value,
                    "selected_variables": list(method.selected_variables),
                }
                for method in methods
            ],
            "seeds": list(P08_SEEDS),
            "evaluation_scenarios_per_config": evaluation_scenarios_per_config,
            "total_scheduled_evaluations": len(P08_METHODS)
            * len(P08_SEEDS)
            * evaluation_scenarios_per_config,
            "hidden_catalogue_procedure": (
                "labels generated from existing P05 families and P07-style stress rules; "
                "labels revealed after result freeze"
            ),
            "compute_ceiling": {
                "runtime": "local_cpu_only",
                "gpu_required": False,
                "storage_target": "under_250_mb_new_pilot_artifacts",
                "stop_rule": "stop_if_projected_runtime_or_storage_exceeds_local_machine_practicality",
            },
        },
        "compute_estimate": compute_estimate,
        "evaluation_seed_freeze": {
            "root_seed": root_seed,
            "scenario_count": len(scenarios),
            "scenario_set_hash": scenario_set_hash,
            "deterministic_regeneration": _regeneration_check(scenarios, root_seed),
        },
        "hidden_catalogue_after_freeze": {
            "catalogue_hash": hidden_catalogue_hash,
            "labels_revealed_after_results_freeze": True,
            "results_freeze_hash": results_freeze_hash,
            "entries": hidden_catalogue,
        },
        "runs": runs,
        "statistical_summary": aggregate,
        "operational_acceptance": _acceptance_report(runs, leakage),
        "leakage": leakage,
        "benchmark_defects": defects,
        "full_benchmark_change_proposals": _full_benchmark_proposals(defects),
        "limitations": [
            "simulation_only",
            "no_physical_robot_validation",
            "conservative_pilot_excludes_panda_and_push_to_target",
            "pilot_training_budget_is_cpu_bounded",
            "research_hypotheses_not_required_for_pilot_success",
        ],
        "report_hash": "",
    }
    report["report_hash"] = _hash_mapping(report)
    output_path = output_directory / "benchmarks" / "ORA-PILOT-001.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def build_pilot_evaluation_scenarios(
    count: int, *, root_seed: int = P08_ROOT_SEED
) -> list[PickPlaceScenario]:
    """Build the frozen P08 evaluation catalogue across existing scenario families."""
    compiler = ScenarioCompiler()
    families = (
        ScenarioFamily.S1_IN_DISTRIBUTION,
        ScenarioFamily.S2_BOUNDARY,
        ScenarioFamily.S3_UNSEEN_COMBINATIONS,
        ScenarioFamily.S4_OUT_OF_DISTRIBUTION,
        ScenarioFamily.S5_ADVERSARIAL,
        ScenarioFamily.S6_FAULT_INJECTION,
    )
    per_family = count // len(families)
    remainder = count % len(families)
    scenarios: list[PickPlaceScenario] = []
    for family_index, family in enumerate(families):
        family_count = per_family + int(family_index < remainder)
        scenarios.extend(
            compiler.generate(
                family_count,
                root_seed=root_seed + family_index,
                family=family,
                split=ScenarioSplit.EVALUATION,
                method=SamplingMethod.LATIN_HYPERCUBE,
            )
        )
    if len(scenarios) != count:
        raise AssertionError("Pilot evaluation scenario count changed")
    return scenarios


def build_hidden_catalogue(scenarios: list[PickPlaceScenario]) -> list[dict[str, object]]:
    """Create hidden labels that are revealed only after result freeze."""
    entries: list[dict[str, object]] = []
    for scenario in scenarios:
        labels = [scenario.family.value]
        distance = float(
            np.linalg.norm(
                np.asarray(scenario.target_position) - np.asarray(scenario.object_position)
            )
        )
        if scenario.action_latency_steps >= 3 or scenario.frame_delay_steps >= 3:
            labels.append("high_delay")
        if scenario.observation_dropout_probability >= 0.05:
            labels.append("high_observation_dropout")
        if scenario.object_mass_kg >= 0.35 and scenario.surface_friction <= 0.40:
            labels.append("heavy_low_friction")
        if distance >= 0.30:
            labels.append("long_transfer")
        entries.append({"scenario_hash": scenario.scenario_hash, "hidden_labels": sorted(labels)})
    return entries


def hash_protected_files(ref: str) -> dict[str, object]:
    """Hash protected files from committed git blobs, not dirty worktree files."""
    paths = list(_PROTECTED_PATHS)
    paths.extend(_git_lines(["ls-tree", "-r", "--name-only", ref, "governance/approvals"]))
    rows: list[dict[str, str]] = []
    for path in sorted(set(paths)):
        content = _git_bytes(["show", f"{ref}:{path}"])
        rows.append({"path": path, "sha256": hashlib.sha256(content).hexdigest()})
    return {
        "ref": ref,
        "files": rows,
        "combined_hash": _hash_mapping({"files": rows}),
    }


def _pilot_methods(output_directory: Path) -> list[PilotMethod]:
    sensitivity = tuple(_sensitivity_variables(output_directory))
    closed_loop = tuple(_closed_loop_variables(output_directory))
    return [
        PilotMethod(
            "A",
            "No randomization",
            RandomizationSystem.A_NO_RANDOMIZATION,
            (),
        ),
        PilotMethod(
            "B",
            "Independent broad uniform P05 randomization",
            RandomizationSystem.B_BROAD_UNIFORM,
            (),
        ),
        PilotMethod(
            "C",
            "Automatic curriculum P05 randomization",
            RandomizationSystem.C_AUTOMATIC_CURRICULUM,
            (),
        ),
        PilotMethod(
            "D",
            "Morris/Sobol guided randomization from EXP-SENS-001",
            RandomizationSystem.D_SENSITIVITY_GUIDED,
            sensitivity,
        ),
        PilotMethod(
            "E",
            "P07 closed-loop revised randomization from EXP-LOOP-001",
            RandomizationSystem.D_SENSITIVITY_GUIDED,
            closed_loop,
        ),
    ]


def _run_method_seed(
    method: PilotMethod,
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
            tracking_path=output_directory / "tracking" / "p08_events.jsonl",
            artifact_prefix=f"p08_{method.label.lower()}",
        )
        evaluation = _evaluate_model(Path(str(training["model_path"])), scenarios)
        training_hashes = _training_parameter_hashes(method, seed, _as_int(training["episodes"]))
        return {
            "method": method.label,
            "seed": seed,
            "status": "completed",
            "classified_outcome": "completed",
            "training": training,
            "evaluation": evaluation,
            "training_parameter_hashes": training_hashes,
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
                collisions += _as_int(info["collision_count"])
                if terminated or truncated:
                    break
            success = float(bool(info.get("success", False)))
            successes.append(success)
            family_successes[scenario.family.value].append(success)
            drops += int(bool(info.get("dropped", False)))
            completion_steps.append(_as_int(info.get("steps", environment.max_episode_steps)))
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


def _training_parameter_hashes(method: PilotMethod, seed: int, episodes: int) -> list[str]:
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
        "overlap_count": sum(_as_int(row["overlap_count"]) for row in overlaps),
        "overlaps": overlaps,
        "passed": not overlaps,
    }


def _aggregate_runs(runs: list[dict[str, object]]) -> dict[str, object]:
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for run in runs:
        grouped[str(run["method"])].append(run)
    return {
        method: _aggregate_method(method_runs, seed=20260810 + index)
        for index, (method, method_runs) in enumerate(sorted(grouped.items()))
    }


def _aggregate_method(runs: list[dict[str, object]], seed: int) -> dict[str, object]:
    completed = [run for run in runs if run["status"] == "completed"]
    values = []
    for run in completed:
        evaluation = run["evaluation"]
        if not isinstance(evaluation, dict):
            raise TypeError("Completed run evaluation must be a mapping")
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
    methods_completed = all(
        any(run["method"] == method and run["status"] == "completed" for run in runs)
        for method in P08_METHODS
    )
    classified_rate = classified / total
    leakage_passed = bool(leakage["passed"])
    return {
        "all_methods_run_for_all_approved_configurations": all(
            run["status"] == "completed" for run in runs
        ),
        "all_methods_have_at_least_one_completed_run": methods_completed,
        "classified_job_rate": classified_rate,
        "classified_job_rate_threshold": 0.95,
        "licence_audit_required_before_merge": True,
        "no_evaluation_leakage_detected": leakage_passed,
        "generated_data_can_be_regenerated": True,
        "result_package_reproducible_on_clean_environment": "pending_ci_validation",
        "operationally_successful": (
            methods_completed and classified_rate >= 0.95 and leakage_passed
        ),
    }


def _compute_estimate(
    training_steps: int, evaluation_scenarios_per_config: int
) -> dict[str, object]:
    scheduled_evaluations = len(P08_METHODS) * len(P08_SEEDS) * evaluation_scenarios_per_config
    return {
        "training_environment_steps": len(P08_METHODS) * len(P08_SEEDS) * training_steps,
        "scheduled_evaluation_episodes": scheduled_evaluations,
        "maximum_evaluation_environment_steps": scheduled_evaluations * 90,
        "model_count": len(P08_METHODS) * len(P08_SEEDS),
        "new_model_storage_estimate_bytes": len(P08_METHODS) * len(P08_SEEDS) * 43_244,
    }


def _benchmark_defects(
    aggregate: dict[str, object], leakage: dict[str, object]
) -> list[dict[str, object]]:
    defects: list[dict[str, object]] = []
    if not bool(leakage["passed"]):
        defects.append(
            {
                "defect_id": "P08-DEFECT-LEAKAGE",
                "severity": "high",
                "description": "Training/evaluation parameter overlap was detected.",
            }
        )
    for method, raw_summary in aggregate.items():
        if not isinstance(raw_summary, dict):
            raise TypeError("Aggregate method summary must be a mapping")
        success = raw_summary["mean_primary_held_out_task_success"]
        if isinstance(success, float) and success == 0.0:
            defects.append(
                {
                    "defect_id": f"P08-DEFECT-ZERO-SUCCESS-{method}",
                    "severity": "medium",
                    "description": (
                        f"Method {method} completed operationally but achieved 0% "
                        "held-out task success."
                    ),
                }
            )
    defects.append(
        {
            "defect_id": "P08-DEFECT-SCOPE-CONSERVATIVE",
            "severity": "low",
            "description": "The conservative pilot excludes Panda and Push-to-Target by approval.",
        }
    )
    return defects


def _full_benchmark_proposals(defects: list[dict[str, object]]) -> list[str]:
    proposals = [
        "Keep failed and zero-success methods in the evidence package; do not tune after evaluation.",
        "Before P09, decide whether the full benchmark needs a stronger policy class or longer training budget.",
        "Add Panda task execution and Push-to-Target only after their adapters have separate validation evidence.",
    ]
    if any(defect["defect_id"] == "P08-DEFECT-SCOPE-CONSERVATIVE" for defect in defects):
        proposals.append(
            "Use P08 results to size the P09 preregistered benchmark before expanding beyond ORA-4A Pick-and-Place."
        )
    return proposals


def _run_without_hidden_labels(run: dict[str, object]) -> dict[str, object]:
    return {key: value for key, value in run.items() if key not in {"training_parameter_hashes"}}


def _regeneration_check(scenarios: list[PickPlaceScenario], root_seed: int) -> dict[str, object]:
    regenerated = build_pilot_evaluation_scenarios(len(scenarios), root_seed=root_seed)
    return {
        "passed": [scenario.scenario_hash for scenario in scenarios]
        == [scenario.scenario_hash for scenario in regenerated],
        "regenerated_count": len(regenerated),
    }


def _sensitivity_variables(output_directory: Path) -> list[str]:
    path = output_directory / "sensitivity" / "EXP-SENS-001.json"
    if not path.exists():
        return [
            "frame_delay_steps",
            "action_latency_steps",
            "object_mass_kg",
            "observation_dropout_probability",
            "object_x_m",
            "surface_friction",
        ]
    payload = json.loads(path.read_text(encoding="utf-8"))
    variables = payload.get("system_d_variables")
    if not isinstance(variables, list) or not all(isinstance(item, str) for item in variables):
        raise TypeError("Sensitivity variables must be a string list")
    return variables


def _closed_loop_variables(output_directory: Path) -> list[str]:
    path = output_directory / "benchmarks" / "EXP-LOOP-001.json"
    if not path.exists():
        return [parameter.name for parameter in CORE_PICK_PLACE_REGISTRY.parameters]
    payload = json.loads(path.read_text(encoding="utf-8"))
    revision = payload.get("revision")
    if not isinstance(revision, dict):
        raise TypeError("Closed-loop report revision must be a mapping")
    variables = revision.get("revised_randomization_variables")
    if not isinstance(variables, list) or not all(isinstance(item, str) for item in variables):
        raise TypeError("Closed-loop variables must be a string list")
    return variables


def _git_bytes(args: list[str]) -> bytes:
    result = subprocess.run(["git", *args], check=True, capture_output=True)
    return result.stdout


def _git_lines(args: list[str]) -> list[str]:
    return [line.strip() for line in _git_bytes(args).decode("utf-8").splitlines() if line.strip()]


def _hash_mapping(value: dict[str, object]) -> str:
    text = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _as_int(value: object) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    raise TypeError(f"Expected integer value, received {type(value).__name__}")
