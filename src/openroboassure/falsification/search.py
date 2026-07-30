"""Constrained falsification search for policy counterexamples."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

import numpy as np
import numpy.typing as npt

from openroboassure.policies.mlp import StateMlpPolicy
from openroboassure.policies.scripted import ScriptedPickPlacePolicy
from openroboassure.scenarios.models import PickPlaceScenario, ScenarioFamily, ScenarioSplit
from openroboassure.scenarios.ontology import CORE_PICK_PLACE_REGISTRY, ParameterKind
from openroboassure.training.environment import PickPlaceGymEnv
from openroboassure.training.randomization import scenario_from_parameter_values


class PolicyController(Protocol):
    """Minimal policy contract used by falsification and replay."""

    def act(self, observation: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]: ...

    def reset(self) -> None: ...


class SearchBackend(Protocol):
    """VerifAI-style black-box search boundary used by the P07 implementation."""

    name: str

    def suggest(self, trial_index: int) -> dict[str, float]: ...

    def observe(
        self, trial_index: int, values: dict[str, float], objective: float, failed: bool
    ) -> None: ...


@dataclass(frozen=True)
class EpisodeOutcome:
    """Policy outcome on one concrete scenario."""

    success: bool
    dropped: bool
    steps: int
    collision_count: int
    final_goal_distance_m: float
    robustness: float

    def to_dict(self) -> dict[str, object]:
        """Return a stable JSON-compatible representation."""
        return {
            "success": self.success,
            "dropped": self.dropped,
            "steps": self.steps,
            "collision_count": self.collision_count,
            "final_goal_distance_m": self.final_goal_distance_m,
            "robustness": self.robustness,
        }


@dataclass(frozen=True)
class TrialRecord:
    """One falsification trial and its predicate result."""

    trial_index: int
    scenario: PickPlaceScenario
    parameter_values: dict[str, float]
    outcome: EpisodeOutcome
    predicate_hits: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        """Return a stable JSON-compatible representation."""
        return {
            "trial_index": self.trial_index,
            "scenario": self.scenario.to_dict(),
            "scenario_hash": self.scenario.scenario_hash,
            "parameter_values": self.parameter_values,
            "outcome": self.outcome.to_dict(),
            "predicate_hits": list(self.predicate_hits),
        }


@dataclass
class CompatibleBlackBoxSearch:
    """Small deterministic search backend with a VerifAI-compatible API shape."""

    seed: int
    name: str = "internal_verifai_compatible_black_box_v1"
    _best_values: dict[str, float] | None = field(default=None, init=False)
    _best_objective: float | None = field(default=None, init=False)

    def suggest(self, trial_index: int) -> dict[str, float]:
        """Return one constrained scenario parameter proposal."""
        if trial_index == 0:
            return _adversarial_seed_values()
        rng = np.random.default_rng(np.random.SeedSequence([self.seed, trial_index, 0xFA15]))
        if self._best_values is not None and trial_index % 3 != 0:
            return _mutate_values(self._best_values, rng)
        return _random_values(rng)

    def observe(
        self, trial_index: int, values: dict[str, float], objective: float, failed: bool
    ) -> None:
        """Update local best state after a trial is evaluated."""
        del trial_index, failed
        if self._best_objective is None or objective < self._best_objective:
            self._best_objective = objective
            self._best_values = dict(values)


class _MlpPolicyController:
    def __init__(self, model_path: Path) -> None:
        self._policy = StateMlpPolicy.load(model_path)

    def act(self, observation: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
        return self._policy.act(observation)

    def reset(self) -> None:
        return None


def run_falsification_search(
    output: Path,
    *,
    trials: int = 96,
    seed: int = 20260730,
    policy_path: Path | None = None,
) -> dict[str, object]:
    """Search valid P05 scenarios for policy failure predicates."""
    if trials <= 0:
        raise ValueError("trials must be positive")
    backend = CompatibleBlackBoxSearch(seed)
    controller = _policy_controller(policy_path)
    records: list[TrialRecord] = []
    for trial_index in range(trials):
        values = backend.suggest(trial_index)
        scenario = scenario_from_parameter_values(
            values,
            index=trial_index,
            seed=_trial_seed(seed, trial_index),
            family=ScenarioFamily.S5_ADVERSARIAL,
            split=ScenarioSplit.EVALUATION,
        )
        outcome = evaluate_scenario(scenario, controller)
        predicates = failure_predicates(outcome)
        backend.observe(trial_index, values, outcome.robustness, bool(predicates))
        records.append(TrialRecord(trial_index, scenario, values, outcome, predicates))
    counterexamples = [
        _counterexample_record(index, record)
        for index, record in enumerate(
            sorted(
                [record for record in records if record.predicate_hits],
                key=lambda item: item.outcome.robustness,
            )[:10],
            start=1,
        )
    ]
    _write_counterexample_files(output.parent, counterexamples)
    first_failure = next(
        (record.trial_index for record in records if record.predicate_hits),
        None,
    )
    report: dict[str, object] = {
        "experiment_id": "EXP-FALSIFICATION-001",
        "scope": "P07 constrained counterexample search over approved P05 scenario values",
        "backend": backend.name,
        "external_verifai_dependency": "not_used_internal_compatible_api",
        "policy": "scripted_reference" if policy_path is None else policy_path.as_posix(),
        "trials": trials,
        "failure_predicates": [
            "task_failure",
            "dropped_object",
            "timeout",
            "collision",
            "goal_distance_above_target_radius",
        ],
        "first_failure_trial": first_failure,
        "counterexample_count": len(counterexamples),
        "failure_rate": sum(1 for record in records if record.predicate_hits) / trials,
        "counterexamples": counterexamples,
        "all_trial_summary": [
            {
                "trial_index": record.trial_index,
                "scenario_hash": record.scenario.scenario_hash,
                "robustness": record.outcome.robustness,
                "predicate_hits": list(record.predicate_hits),
            }
            for record in records
        ],
        "report_hash": "",
    }
    report["report_hash"] = _hash_mapping(report)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def evaluate_scenario(
    scenario: PickPlaceScenario, controller: PolicyController | None = None
) -> EpisodeOutcome:
    """Evaluate one policy controller on one scenario."""
    policy = controller if controller is not None else ScriptedPickPlacePolicy()
    policy.reset()
    environment = PickPlaceGymEnv()
    collisions = 0
    info: dict[str, object] = {}
    try:
        observation, _ = environment.reset(seed=scenario.seed, options={"scenario": scenario})
        for _ in range(environment.max_episode_steps):
            observation, _, terminated, truncated, info = environment.step(policy.act(observation))
            collisions += _integer_metric(info["collision_count"])
            if terminated or truncated:
                break
        final_goal_distance = float(np.linalg.norm(observation[3:6] - observation[6:9]))
        success = bool(info.get("success", False))
        dropped = bool(info.get("dropped", False))
        steps = _integer_metric(info.get("steps", environment.max_episode_steps))
        robustness = _robustness(success, dropped, final_goal_distance, scenario.target_radius_m)
        return EpisodeOutcome(success, dropped, steps, collisions, final_goal_distance, robustness)
    finally:
        environment.close()


def failure_predicates(outcome: EpisodeOutcome) -> tuple[str, ...]:
    """Evaluate the declared P07 failure predicates."""
    hits: list[str] = []
    if not outcome.success:
        hits.append("task_failure")
    if outcome.dropped:
        hits.append("dropped_object")
    if not outcome.success and outcome.steps >= 90:
        hits.append("timeout")
    if outcome.collision_count > 0:
        hits.append("collision")
    if outcome.final_goal_distance_m > 0.06:
        hits.append("goal_distance_above_target_radius")
    return tuple(hits)


def _policy_controller(policy_path: Path | None) -> PolicyController:
    if policy_path is None:
        return ScriptedPickPlacePolicy()
    return _MlpPolicyController(policy_path)


def _counterexample_record(index: int, record: TrialRecord) -> dict[str, object]:
    return {
        "counterexample_id": f"CE-{index:06d}",
        **record.to_dict(),
    }


def _write_counterexample_files(directory: Path, records: list[dict[str, object]]) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for record in records:
        counterexample_id = str(record["counterexample_id"])
        path = directory / f"{counterexample_id}.json"
        path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _adversarial_seed_values() -> dict[str, float]:
    values = _nominal_values()
    values.update(
        {
            "object_mass_kg": 0.50,
            "surface_friction": 0.20,
            "object_half_extent_m": 0.024,
            "object_x_m": -0.18,
            "object_y_m": -0.14,
            "target_radius_m": 0.044,
            "target_x_m": 0.20,
            "target_y_m": 0.15,
            "action_latency_steps": 4.0,
            "action_noise_fraction": 0.25,
            "joint_encoder_noise_rad": 0.03,
            "object_state_noise_m": 0.005,
            "frame_delay_steps": 4.0,
            "observation_dropout_probability": 0.10,
            "vertical_gravity_scale": 1.02,
        }
    )
    return values


def _random_values(rng: np.random.Generator) -> dict[str, float]:
    values: dict[str, float] = {}
    for parameter in CORE_PICK_PLACE_REGISTRY.parameters:
        low, high = parameter.global_bounds
        if parameter.kind is ParameterKind.DISCRETE:
            values[parameter.name] = float(rng.integers(int(low), int(high) + 1))
        else:
            values[parameter.name] = float(rng.uniform(low, high))
    return values


def _mutate_values(values: dict[str, float], rng: np.random.Generator) -> dict[str, float]:
    mutated = dict(values)
    parameters = list(CORE_PICK_PLACE_REGISTRY.parameters)
    for raw_index in rng.choice(len(parameters), size=3, replace=False):
        parameter = parameters[int(raw_index)]
        low, high = parameter.global_bounds
        if parameter.kind is ParameterKind.DISCRETE:
            mutated[parameter.name] = float(rng.integers(int(low), int(high) + 1))
        else:
            width = high - low
            mutated[parameter.name] = float(
                np.clip(mutated[parameter.name] + rng.normal(0.0, 0.20 * width), low, high)
            )
    return mutated


def _nominal_values() -> dict[str, float]:
    return {parameter.name: parameter.nominal for parameter in CORE_PICK_PLACE_REGISTRY.parameters}


def _trial_seed(seed: int, trial_index: int) -> int:
    return int(
        np.random.default_rng(np.random.SeedSequence([seed, trial_index])).integers(
            0, np.iinfo(np.int64).max
        )
    )


def _robustness(
    success: bool, dropped: bool, final_goal_distance_m: float, target_radius_m: float
) -> float:
    margin = target_radius_m - final_goal_distance_m
    if success:
        return 1.0 + margin
    if dropped:
        return -2.0 + margin
    return -1.0 + margin


def _integer_metric(value: object) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    raise TypeError(f"Expected integer metric, received {type(value).__name__}")


def _hash_mapping(value: dict[str, object]) -> str:
    text = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
