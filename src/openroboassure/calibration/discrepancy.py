"""Trajectory discrepancy metrics for hidden-target calibration."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class TrajectoryStep:
    """One observable transition sample available to calibration code."""

    step: int
    action: tuple[float, float, float, float]
    observation: tuple[float, ...]
    reward: float
    terminated: bool
    truncated: bool
    success: bool

    def to_dict(self) -> dict[str, object]:
        """Return a stable JSON-compatible representation."""
        return {
            "step": self.step,
            "action": list(self.action),
            "observation": list(self.observation),
            "reward": self.reward,
            "terminated": self.terminated,
            "truncated": self.truncated,
            "success": self.success,
        }


@dataclass(frozen=True)
class CalibrationTrajectory:
    """A limited target trajectory with actions, observations, and outcomes."""

    program: str
    seed: int
    scenario_hash: str
    steps: tuple[TrajectoryStep, ...]

    def to_dict(self) -> dict[str, object]:
        """Return a stable JSON-compatible representation."""
        return {
            "program": self.program,
            "seed": self.seed,
            "scenario_hash": self.scenario_hash,
            "steps": [step.to_dict() for step in self.steps],
            "sample_count": len(self.steps),
            "final_success": self.steps[-1].success if self.steps else False,
        }


def observation_sse(
    target: tuple[CalibrationTrajectory, ...], source: tuple[CalibrationTrajectory, ...]
) -> float:
    """Return sum-squared observable-state error across matched trajectories."""
    if len(target) != len(source):
        raise ValueError("Target and source trajectory counts must match")
    total = 0.0
    for target_trajectory, source_trajectory in zip(target, source, strict=True):
        if target_trajectory.program != source_trajectory.program:
            raise ValueError("Trajectory programs must match")
        count = min(len(target_trajectory.steps), len(source_trajectory.steps))
        if count == 0:
            continue
        target_observations = np.asarray(
            [step.observation for step in target_trajectory.steps[:count]], dtype=np.float64
        )
        source_observations = np.asarray(
            [step.observation for step in source_trajectory.steps[:count]], dtype=np.float64
        )
        difference = target_observations - source_observations
        total += float(np.sum(difference * difference))
    return total


def observation_rmse(
    target: tuple[CalibrationTrajectory, ...], source: tuple[CalibrationTrajectory, ...]
) -> float:
    """Return root-mean-square observable-state error across matched trajectories."""
    samples = sum(
        min(len(target_trajectory.steps), len(source_trajectory.steps))
        for target_trajectory, source_trajectory in zip(target, source, strict=True)
    )
    if samples == 0:
        raise ValueError("Cannot compare empty calibration trajectories")
    dimensions = len(target[0].steps[0].observation)
    return float(np.sqrt(observation_sse(target, source) / (samples * dimensions)))


def outcome_mismatch_rate(
    target: tuple[CalibrationTrajectory, ...], source: tuple[CalibrationTrajectory, ...]
) -> float:
    """Return the fraction of programs with a mismatched final success outcome."""
    if len(target) != len(source):
        raise ValueError("Target and source trajectory counts must match")
    mismatches = 0
    for target_trajectory, source_trajectory in zip(target, source, strict=True):
        target_success = target_trajectory.steps[-1].success if target_trajectory.steps else False
        source_success = source_trajectory.steps[-1].success if source_trajectory.steps else False
        mismatches += int(target_success != source_success)
    return mismatches / len(target)


def trajectory_digest(trajectories: tuple[CalibrationTrajectory, ...]) -> str:
    """Hash only observable target trajectory payloads."""
    payload = [trajectory.to_dict() for trajectory in trajectories]
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
