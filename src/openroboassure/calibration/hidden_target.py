"""Hidden-target sim-to-sim calibration experiment for P07."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import numpy.typing as npt

from openroboassure.calibration.discrepancy import (
    CalibrationTrajectory,
    TrajectoryStep,
    observation_rmse,
    observation_sse,
    outcome_mismatch_rate,
    trajectory_digest,
)
from openroboassure.calibration.posterior import (
    CandidateScore,
    posterior_coverage,
    posterior_weights,
    summarize_posterior,
)
from openroboassure.policies.scripted import ScriptedPickPlacePolicy
from openroboassure.scenarios.compiler import ScenarioCompiler
from openroboassure.scenarios.models import PickPlaceScenario, ScenarioFamily, ScenarioSplit
from openroboassure.scenarios.ontology import CORE_PICK_PLACE_REGISTRY, ParameterKind
from openroboassure.scenarios.parameters import scenario_parameter_values
from openroboassure.training.environment import PickPlaceGymEnv
from openroboassure.training.randomization import scenario_from_parameter_values

CALIBRATION_VARIABLES = (
    "object_x_m",
    "object_y_m",
    "target_x_m",
    "target_y_m",
    "action_latency_steps",
    "frame_delay_steps",
)
_OBSERVATION_SIGMA_M = 0.015
_PROGRAMS = ("scripted_pick_place", "axis_sweep")


def run_hidden_target_calibration(
    output: Path,
    *,
    seed: int = 20260730,
    candidate_count: int = 128,
) -> dict[str, object]:
    """Run the P07 hidden-target calibration evidence experiment."""
    if candidate_count < 8:
        raise ValueError("candidate_count must be at least 8")
    hidden_target = _build_hidden_target(seed)
    target_trajectories = collect_target_trajectories(hidden_target, seed=seed)
    nominal = _scenario_from_values(
        _nominal_values(),
        index=0,
        seed=seed,
        family=ScenarioFamily.S0_NOMINAL,
    )
    nominal_trajectories = replay_target_actions(nominal, target_trajectories)
    candidate_scenarios = _candidate_scenarios(seed, candidate_count)
    scores = [
        _score_candidate(candidate, target_trajectories, candidate_id=f"CAND-{index:04d}")
        for index, candidate in enumerate(candidate_scenarios)
    ]
    weights = posterior_weights(scores, observation_sigma_m=_OBSERVATION_SIGMA_M)
    posterior = summarize_posterior(scores, weights, CALIBRATION_VARIABLES)
    best_index = min(range(len(scores)), key=lambda index: scores[index].observation_rmse)
    best_score = scores[best_index]
    best_scenario = candidate_scenarios[best_index]
    true_values = {
        name: scenario_parameter_values(hidden_target)[name] for name in CALIBRATION_VARIABLES
    }
    nominal_rmse = observation_rmse(target_trajectories, nominal_trajectories)
    nominal_mismatch = outcome_mismatch_rate(target_trajectories, nominal_trajectories)
    frozen_prediction: dict[str, object] = {
        "target_trajectory_digest": trajectory_digest(target_trajectories),
        "candidate_count": candidate_count,
        "calibration_variables": list(CALIBRATION_VARIABLES),
        "posterior": posterior,
        "map_estimate": best_score.values,
        "nominal_observation_rmse": nominal_rmse,
        "calibrated_map_observation_rmse": best_score.observation_rmse,
        "nominal_outcome_mismatch_rate": nominal_mismatch,
        "calibrated_map_outcome_mismatch_rate": best_score.outcome_mismatch_rate,
    }
    prediction_freeze_hash = _hash_mapping(frozen_prediction)
    coverage = posterior_coverage(posterior, true_values)
    relative_improvement = (
        (nominal_rmse - best_score.observation_rmse) / nominal_rmse if nominal_rmse > 0.0 else 0.0
    )
    report: dict[str, object] = {
        "experiment_id": "EXP-CALIBRATION-001",
        "scope": "P07 hidden-target sim-to-sim calibration for ORA-4A Pick-and-Place",
        "target_handling": {
            "hidden_values_available_to_method": False,
            "reveal_order": "predictions_frozen_before_true_parameters_are_written",
            "prediction_freeze_hash": prediction_freeze_hash,
        },
        "excitation_policies": list(_PROGRAMS),
        "limited_target_trajectories": {
            "trajectory_count": len(target_trajectories),
            "samples": sum(len(trajectory.steps) for trajectory in target_trajectories),
            "digest": trajectory_digest(target_trajectories),
        },
        "candidate_search": {
            "candidate_count": candidate_count,
            "prior": "uniform over approved P05 training bounds for calibration variables",
            "observation_sigma_m": _OBSERVATION_SIGMA_M,
        },
        "discrepancy": {
            "metric": "observable trajectory RMSE over canonical state observations",
            "nominal_observation_rmse": nominal_rmse,
            "calibrated_map_observation_rmse": best_score.observation_rmse,
            "relative_improvement": relative_improvement,
            "nominal_outcome_mismatch_rate": nominal_mismatch,
            "calibrated_map_outcome_mismatch_rate": best_score.outcome_mismatch_rate,
            "status": "improved" if relative_improvement > 0.0 else "negative_result_preserved",
        },
        "posterior": posterior,
        "map_estimate": {
            "candidate_id": best_score.candidate_id,
            "values": best_score.values,
            "scenario_hash": best_scenario.scenario_hash,
        },
        "true_hidden_parameters_after_freeze": true_values,
        "posterior_coverage_after_reveal": coverage,
        "target_policy_transfer": _target_policy_transfer(hidden_target, seed),
        "report_hash": "",
    }
    report["report_hash"] = _hash_mapping(report)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def collect_target_trajectories(
    scenario: PickPlaceScenario, *, seed: int
) -> tuple[CalibrationTrajectory, ...]:
    """Collect limited target trajectories without returning hidden parameter values."""
    return tuple(
        _rollout_program(scenario, program=program, seed=seed + index)
        for index, program in enumerate(_PROGRAMS)
    )


def replay_target_actions(
    scenario: PickPlaceScenario, target: tuple[CalibrationTrajectory, ...]
) -> tuple[CalibrationTrajectory, ...]:
    """Replay target-provided actions in a source scenario."""
    return tuple(_replay_actions(scenario, trajectory) for trajectory in target)


def _rollout_program(
    scenario: PickPlaceScenario, *, program: str, seed: int
) -> CalibrationTrajectory:
    environment = PickPlaceGymEnv()
    steps: list[TrajectoryStep] = []
    try:
        observation, _ = environment.reset(seed=seed, options={"scenario": scenario})
        policy = ScriptedPickPlacePolicy()
        for step_index in range(environment.max_episode_steps):
            if program == "scripted_pick_place":
                action = policy.act(observation)
            elif program == "axis_sweep":
                action = _axis_sweep_action(step_index)
            else:
                raise ValueError(f"Unsupported calibration program: {program}")
            observation, reward, terminated, truncated, info = environment.step(action)
            steps.append(
                _trajectory_step(
                    step_index, action, observation, reward, terminated, truncated, info
                )
            )
            if terminated or truncated:
                break
    finally:
        environment.close()
    return CalibrationTrajectory(program, seed, scenario.scenario_hash, tuple(steps))


def _replay_actions(
    scenario: PickPlaceScenario, trajectory: CalibrationTrajectory
) -> CalibrationTrajectory:
    environment = PickPlaceGymEnv()
    steps: list[TrajectoryStep] = []
    try:
        environment.reset(seed=trajectory.seed, options={"scenario": scenario})
        for target_step in trajectory.steps:
            action = np.asarray(target_step.action, dtype=np.float64)
            observation, reward, terminated, truncated, info = environment.step(action)
            steps.append(
                _trajectory_step(
                    target_step.step, action, observation, reward, terminated, truncated, info
                )
            )
            if terminated or truncated:
                break
    finally:
        environment.close()
    return CalibrationTrajectory(
        trajectory.program, trajectory.seed, scenario.scenario_hash, tuple(steps)
    )


def _trajectory_step(
    step_index: int,
    action: npt.NDArray[np.float64],
    observation: npt.NDArray[np.float64],
    reward: float,
    terminated: bool,
    truncated: bool,
    info: dict[str, object],
) -> TrajectoryStep:
    action_values = tuple(float(value) for value in action)
    if len(action_values) != 4:
        raise ValueError("Calibration action must have four channels")
    return TrajectoryStep(
        step=step_index,
        action=(action_values[0], action_values[1], action_values[2], action_values[3]),
        observation=tuple(float(value) for value in observation),
        reward=float(reward),
        terminated=terminated,
        truncated=truncated,
        success=bool(info.get("success", False)),
    )


def _score_candidate(
    candidate: PickPlaceScenario,
    target_trajectories: tuple[CalibrationTrajectory, ...],
    *,
    candidate_id: str,
) -> CandidateScore:
    source_trajectories = replay_target_actions(candidate, target_trajectories)
    values = scenario_parameter_values(candidate)
    return CandidateScore(
        candidate_id=candidate_id,
        values={name: values[name] for name in CALIBRATION_VARIABLES},
        observation_sse=observation_sse(target_trajectories, source_trajectories),
        observation_rmse=observation_rmse(target_trajectories, source_trajectories),
        outcome_mismatch_rate=outcome_mismatch_rate(target_trajectories, source_trajectories),
    )


def _build_hidden_target(seed: int) -> PickPlaceScenario:
    compiler = ScenarioCompiler()
    return compiler.compile_one(
        17,
        population_size=64,
        root_seed=seed,
        family=ScenarioFamily.S1_IN_DISTRIBUTION,
        split=ScenarioSplit.TRAIN,
    )


def _candidate_scenarios(seed: int, count: int) -> list[PickPlaceScenario]:
    scenarios = [
        _scenario_from_values(
            _nominal_values(),
            index=0,
            seed=seed,
            family=ScenarioFamily.S0_NOMINAL,
        )
    ]
    for index in range(1, count):
        values = _nominal_values()
        rng = np.random.default_rng(np.random.SeedSequence([seed, index, 0xC411B]))
        for name in CALIBRATION_VARIABLES:
            parameter = CORE_PICK_PLACE_REGISTRY.parameter(name)
            low, high = parameter.training_bounds
            if parameter.kind is ParameterKind.DISCRETE:
                values[name] = float(rng.integers(int(low), int(high) + 1))
            else:
                values[name] = float(rng.uniform(low, high))
        scenarios.append(
            _scenario_from_values(
                values,
                index=index,
                seed=int(rng.integers(0, np.iinfo(np.int64).max)),
                family=ScenarioFamily.S1_IN_DISTRIBUTION,
            )
        )
    return scenarios


def _scenario_from_values(
    values: dict[str, float], *, index: int, seed: int, family: ScenarioFamily
) -> PickPlaceScenario:
    return scenario_from_parameter_values(
        values,
        index=index,
        seed=seed,
        family=family,
        split=ScenarioSplit.TRAIN,
    )


def _nominal_values() -> dict[str, float]:
    return {parameter.name: parameter.nominal for parameter in CORE_PICK_PLACE_REGISTRY.parameters}


def _axis_sweep_action(step_index: int) -> npt.NDArray[np.float64]:
    cycle = step_index % 24
    action = np.zeros(4, dtype=np.float64)
    if cycle < 6:
        action[0] = 1.0
    elif cycle < 12:
        action[1] = 1.0
    elif cycle < 18:
        action[0] = -1.0
    else:
        action[1] = -1.0
    action[2] = 0.5 if step_index % 12 < 6 else -0.5
    action[3] = 1.0
    return action


def _target_policy_transfer(scenario: PickPlaceScenario, seed: int) -> dict[str, object]:
    trajectory = _rollout_program(scenario, program="scripted_pick_place", seed=seed + 99)
    final = trajectory.steps[-1]
    return {
        "policy": "deterministic_scripted_state_only",
        "target_episode_success": final.success,
        "target_episode_steps": len(trajectory.steps),
        "claim": "simulation_only_target_transfer_no_real_world_validation",
    }


def _hash_mapping(value: dict[str, object]) -> str:
    text = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
