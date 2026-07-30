"""Equal-budget CPU training, model provenance, and held-out evaluation for P06."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np

from openroboassure.policies.mlp import PolicySpecification, StateMlpPolicy
from openroboassure.scenarios.compiler import SamplingMethod, ScenarioCompiler
from openroboassure.scenarios.models import PickPlaceScenario, ScenarioFamily, ScenarioSplit
from openroboassure.training.environment import PickPlaceGymEnv
from openroboassure.training.randomization import RandomizationSystem, ScenarioSampler
from openroboassure.training.sensitivity import run_sensitivity_experiment

P06_SEEDS = (11, 22, 33, 44, 55)
P06_STEPS_PER_SEED = 100_000
P06_EVALUATION_SCENARIOS = 200


@dataclass(frozen=True)
class TrainingConfiguration:
    """One reproducible P06 training job with no system-specific tuning knobs."""

    system: RandomizationSystem
    seed: int
    environment_steps: int = P06_STEPS_PER_SEED
    selected_variables: tuple[str, ...] = ()
    policy: PolicySpecification = field(default_factory=PolicySpecification)

    def to_dict(self) -> dict[str, object]:
        """Return the complete immutable job configuration."""
        value = asdict(self)
        value["system"] = self.system.value
        value["policy"] = self.policy.to_dict()
        return value


def train_policy(
    configuration: TrainingConfiguration,
    *,
    model_directory: Path,
    tracking_path: Path,
    artifact_prefix: str = "p06",
) -> dict[str, object]:
    """Train an exact-step stochastic policy and persist model/config hashes."""
    if configuration.environment_steps <= 0:
        raise ValueError("Training environment_steps must be positive")
    if not artifact_prefix.replace("_", "").replace("-", "").isalnum():
        raise ValueError("Training artifact_prefix must be filesystem-safe")
    sampler = ScenarioSampler(
        configuration.system, configuration.seed, configuration.selected_variables
    )
    policy = StateMlpPolicy(configuration.seed, configuration.policy)
    environment = PickPlaceGymEnv()
    episodes = 0
    steps = 0
    successes = 0
    drops = 0
    collisions = 0
    returns: list[float] = []
    _write_tracking_event(tracking_path, {"event": "training_started", **configuration.to_dict()})
    try:
        while steps < configuration.environment_steps:
            progress = steps / configuration.environment_steps
            scenario = sampler.sample(episodes, progress=progress)
            observation, _ = environment.reset(seed=scenario.seed, options={"scenario": scenario})
            episode_samples = []
            episode_rewards: list[float] = []
            info: dict[str, object] = {}
            while steps < configuration.environment_steps:
                sample = policy.sample(observation)
                observation, reward, terminated, truncated, info = environment.step(sample.action)
                episode_samples.append(sample)
                episode_rewards.append(reward)
                steps += 1
                collisions += _integer_metric(info["collision_count"])
                if terminated or truncated:
                    break
            returns.append(policy.update(episode_samples, episode_rewards))
            successes += _integer_metric(info.get("success", False))
            drops += _integer_metric(info.get("dropped", False))
            episodes += 1
    finally:
        environment.close()
    model_path = model_directory / (
        f"{artifact_prefix}_{configuration.system.value.lower()}_{configuration.seed}.npz"
    )
    model_hash = policy.save(model_path)
    configuration_hash = _canonical_hash(configuration.to_dict())
    result: dict[str, object] = {
        "schema_version": 1,
        "system": configuration.system.value,
        "seed": configuration.seed,
        "environment_steps": steps,
        "episodes": episodes,
        "training_success_rate": successes / episodes,
        "training_drop_rate": drops / episodes,
        "training_collision_rate": collisions / max(steps, 1),
        "mean_episode_return": float(np.mean(returns)),
        "policy_specification": configuration.policy.to_dict(),
        "configuration_hash": configuration_hash,
        "model_path": model_path.as_posix(),
        "model_hash": model_hash,
    }
    _write_tracking_event(tracking_path, {"event": "training_completed", **result})
    return result


def build_evaluation_scenarios() -> list[PickPlaceScenario]:
    """Build 200 fixed P05 evaluation-split scenarios across five families."""
    compiler = ScenarioCompiler()
    families = (
        ScenarioFamily.S1_IN_DISTRIBUTION,
        ScenarioFamily.S2_BOUNDARY,
        ScenarioFamily.S3_UNSEEN_COMBINATIONS,
        ScenarioFamily.S4_OUT_OF_DISTRIBUTION,
        ScenarioFamily.S6_FAULT_INJECTION,
    )
    per_family = P06_EVALUATION_SCENARIOS // len(families)
    scenarios: list[PickPlaceScenario] = []
    for family_index, family in enumerate(families):
        scenarios.extend(
            compiler.generate(
                per_family,
                root_seed=20260726 + family_index,
                family=family,
                split=ScenarioSplit.EVALUATION,
                method=SamplingMethod.LATIN_HYPERCUBE,
            )
        )
    if len(scenarios) != P06_EVALUATION_SCENARIOS:
        raise AssertionError("P06 evaluation scenario count changed")
    return scenarios


def evaluate_policy(model_path: Path, scenarios: list[PickPlaceScenario]) -> dict[str, object]:
    """Evaluate one saved policy on the immutable common held-out scenario set."""
    if len(scenarios) != P06_EVALUATION_SCENARIOS:
        raise ValueError("P06 evaluation requires exactly 200 held-out scenarios")
    policy = StateMlpPolicy.load(model_path)
    environment = PickPlaceGymEnv()
    successes: list[float] = []
    drops = 0
    collisions = 0
    completion_steps: list[int] = []
    invalid_scenarios = 0
    family_successes: dict[str, list[float]] = defaultdict(list)
    try:
        for scenario in scenarios:
            observation, _ = environment.reset(seed=scenario.seed, options={"scenario": scenario})
            info: dict[str, object] = {}
            for _ in range(environment.max_episode_steps):
                observation, _, terminated, truncated, info = environment.step(
                    policy.act(observation)
                )
                collisions += _integer_metric(info["collision_count"])
                if terminated or truncated:
                    break
            success = float(bool(info.get("success", False)))
            successes.append(success)
            family_successes[scenario.family.value].append(success)
            drops += _integer_metric(info.get("dropped", False))
            completion_steps.append(
                _integer_metric(info.get("steps", environment.max_episode_steps))
            )
    except ValueError:
        invalid_scenarios += 1
        raise
    finally:
        environment.close()
    family_rates = {
        name: float(np.mean(values)) for name, values in sorted(family_successes.items())
    }
    return {
        "evaluation_scenarios": len(scenarios),
        "primary_held_out_task_success": float(np.mean(successes)),
        "drop_rate": drops / len(scenarios),
        "collision_rate": collisions / max(sum(completion_steps), 1),
        "mean_completion_steps": float(np.mean(completion_steps)),
        "invalid_scenario_rate": invalid_scenarios / len(scenarios),
        "scenario_family_success": family_rates,
        "fifth_percentile_scenario_family_success": float(
            np.quantile(list(family_rates.values()), 0.05)
        ),
    }


def assert_equal_budgets(results: list[dict[str, object]]) -> None:
    """Reject a campaign where any baseline received a different step budget."""
    budgets = {_integer_metric(result["environment_steps"]) for result in results}
    expected_runs = len(RandomizationSystem) * len(P06_SEEDS)
    if len(results) != expected_runs or budgets != {P06_STEPS_PER_SEED}:
        raise ValueError(
            "P06 equal-budget check failed: require four systems x five seeds x 100,000 steps"
        )


def run_cpu_standard_campaign(output_directory: Path) -> dict[str, object]:
    """Execute the human-approved four-system, twenty-run CPU P06 campaign."""
    sensitivity = run_sensitivity_experiment(output_directory / "sensitivity" / "EXP-SENS-001.json")
    raw_variables = sensitivity["system_d_variables"]
    if not isinstance(raw_variables, list) or not all(
        isinstance(item, str) for item in raw_variables
    ):
        raise ValueError("Sensitivity report did not contain System D variables")
    selected_variables = tuple(raw_variables)
    scenarios = build_evaluation_scenarios()
    tracking_path = output_directory / "tracking" / "p06_events.jsonl"
    training_results: list[dict[str, object]] = []
    for system in RandomizationSystem:
        for seed in P06_SEEDS:
            configuration = TrainingConfiguration(
                system=system,
                seed=seed,
                selected_variables=(
                    selected_variables if system is RandomizationSystem.D_SENSITIVITY_GUIDED else ()
                ),
            )
            result = train_policy(
                configuration,
                model_directory=output_directory / "models",
                tracking_path=tracking_path,
            )
            evaluation = evaluate_policy(Path(str(result["model_path"])), scenarios)
            training_results.append({**result, "evaluation": evaluation})
    assert_equal_budgets(training_results)
    report: dict[str, object] = {
        "experiment_id": "EXP-POLICY-BASELINES-001",
        "scope": "P06 CPU-standard ORA-4A Pick-and-Place only",
        "training": {
            "systems": [system.value for system in RandomizationSystem],
            "seeds": list(P06_SEEDS),
            "steps_per_seed": P06_STEPS_PER_SEED,
            "total_environment_steps": sum(
                _integer_metric(result["environment_steps"]) for result in training_results
            ),
            "equal_budget_check": "passed",
            "policy_architecture": PolicySpecification().to_dict(),
        },
        "evaluation": {
            "held_out_scenarios_per_policy_seed": P06_EVALUATION_SCENARIOS,
            "total_episodes": len(training_results) * P06_EVALUATION_SCENARIOS,
            "scenario_set_hash": _scenario_set_hash(scenarios),
        },
        "sensitivity_report": (output_directory / "sensitivity" / "EXP-SENS-001.json").as_posix(),
        "system_d_variables": list(selected_variables),
        "runs": training_results,
        "aggregate": _aggregate_results(training_results),
        "report_hash": "",
    }
    report["report_hash"] = _canonical_hash(report)
    output_path = output_directory / "benchmarks" / "EXP-POLICY-BASELINES-001.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    registry_path = output_directory / "models" / "registry.json"
    registry_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "experiment_id": report["experiment_id"],
                "models": [
                    {
                        key: result[key]
                        for key in (
                            "system",
                            "seed",
                            "model_path",
                            "model_hash",
                            "configuration_hash",
                            "policy_specification",
                        )
                    }
                    for result in training_results
                ],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return report


def _canonical_hash(value: dict[str, object]) -> str:
    text = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _write_tracking_event(path: Path, event: dict[str, object]) -> None:
    """Append one local-only JSONL lifecycle event without external tracking services."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")


def _scenario_set_hash(scenarios: list[PickPlaceScenario]) -> str:
    return _canonical_hash({"scenario_hashes": [scenario.scenario_hash for scenario in scenarios]})


def _aggregate_results(results: list[dict[str, object]]) -> dict[str, object]:
    grouped: dict[str, list[float]] = defaultdict(list)
    for result in results:
        evaluation = result["evaluation"]
        if not isinstance(evaluation, dict):
            raise TypeError("Training result must contain an evaluation mapping")
        value = evaluation.get("primary_held_out_task_success")
        if not isinstance(value, float):
            raise TypeError("Evaluation must contain a floating-point primary metric")
        grouped[str(result["system"])].append(value)
    return {
        system: _bootstrap_summary(values, seed=20260726 + index)
        for index, (system, values) in enumerate(sorted(grouped.items()))
    }


def _bootstrap_summary(values: list[float], seed: int) -> dict[str, float | int]:
    observations = np.asarray(values, dtype=np.float64)
    rng = np.random.default_rng(seed)
    samples = rng.choice(observations, size=(1000, len(observations)), replace=True).mean(axis=1)
    return {
        "seed_count": len(values),
        "mean_primary_held_out_task_success": float(observations.mean()),
        "bootstrap_95_lower": float(np.quantile(samples, 0.025)),
        "bootstrap_95_upper": float(np.quantile(samples, 0.975)),
    }


def _integer_metric(value: object) -> int:
    """Narrow externally reported metric values before arithmetic."""
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    raise TypeError(f"Expected an integer metric, received {type(value).__name__}")
