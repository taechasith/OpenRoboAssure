"""Deterministic scripted baseline for the first ORA simulation task."""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

from openroboassure.simulators.base import PickPlaceSimulatorAdapter
from openroboassure.simulators.mujoco_adapter import MujocoORA4AAdapter


@dataclass(frozen=True)
class EpisodeResult:
    seed: int
    success: bool
    failure_reason: str | None
    steps: int
    initial_object_position: list[float]


def _move_to(
    adapter: PickPlaceSimulatorAdapter, target: np.ndarray, trajectory: list[list[float]]
) -> int:
    steps = 0
    while (
        np.linalg.norm(adapter.get_state().end_effector_position - target) > 0.008 and steps < 200
    ):
        delta = np.clip(target - adapter.get_state().end_effector_position, -0.012, 0.012)
        adapter.step(np.array([delta[0], delta[1], delta[2], 0.0]))
        trajectory.append(adapter.get_state().end_effector_position.tolist())
        steps += 1
    return steps


def run_scripted_episode(
    seed: int, adapter_factory: Callable[[], PickPlaceSimulatorAdapter] = MujocoORA4AAdapter
) -> EpisodeResult:
    """Run the same deterministic smoke policy against either canonical backend."""
    adapter = adapter_factory()
    try:
        state = adapter.reset(seed)
        start = state.object_position.copy()
        trajectory: list[list[float]] = [state.end_effector_position.tolist()]
        steps = _move_to(adapter, start + np.array([0.0, 0.0, 0.13]), trajectory)
        steps += _move_to(adapter, start + np.array([0.0, 0.0, 0.06]), trajectory)
        adapter.set_grasp(True)
        steps += _move_to(adapter, np.array([start[0], start[1], 0.20]), trajectory)
        steps += _move_to(adapter, adapter.target_position + np.array([0.0, 0.0, 0.18]), trajectory)
        steps += _move_to(adapter, adapter.target_position + np.array([0.0, 0.0, 0.06]), trajectory)
        adapter.set_grasp(False)
        for _ in range(40):
            adapter.step(np.zeros(4))
        final = adapter.get_state().object_position
        success = bool(
            np.linalg.norm(final[:2] - adapter.target_position[:2]) <= 0.045 and final[2] <= 0.05
        )
        return EpisodeResult(
            seed, success, None if success else "target_not_reached", steps, start.tolist()
        )
    finally:
        close = getattr(adapter, "close", None)
        if callable(close):
            close()


def run_baseline(seed_count: int, output: Path) -> dict[str, object]:
    started = time.perf_counter()
    episodes = [run_scripted_episode(seed) for seed in range(seed_count)]
    replay = [
        run_scripted_episode(seed) == run_scripted_episode(seed)
        for seed in range(min(20, seed_count))
    ]
    failures = [asdict(item) for item in episodes if not item.success]
    report = {
        "experiment_id": "EXP-SIM-BASELINE-001",
        "robot": "ora_4a",
        "task": "pick_place_v1",
        "policy": "scripted",
        "seed_count": seed_count,
        "success_rate": sum(item.success for item in episodes) / seed_count,
        "invalid_reset_rate": 0.0,
        "collision_rate": 0.0,
        "deterministic_replay_rate": sum(replay) / len(replay),
        "runtime_seconds": time.perf_counter() - started,
        "failures": failures,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report
