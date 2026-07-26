from __future__ import annotations

from openroboassure.experiments.baseline import run_scripted_episode
from openroboassure.simulators.mujoco_adapter import MujocoORA4AAdapter
from openroboassure.simulators.pybullet_adapter import PyBulletORA4AAdapter


def test_same_seed_reproduces_initial_state() -> None:
    first = MujocoORA4AAdapter()
    second = MujocoORA4AAdapter()
    assert first.reset(7).object_position.tolist() == second.reset(7).object_position.tolist()


def test_scripted_policy_succeeds_nominally() -> None:
    result = run_scripted_episode(3)
    assert result.success
    assert result.failure_reason is None


def test_scripted_policy_smoke_succeeds_in_pybullet() -> None:
    result = run_scripted_episode(3, PyBulletORA4AAdapter)
    assert result.success
    assert result.failure_reason is None
