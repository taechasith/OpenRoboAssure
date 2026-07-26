from __future__ import annotations

import numpy as np
import pytest

from openroboassure.simulators.action_conversion import ACTION_LIMITS, canonical_action_delta
from openroboassure.simulators.mujoco_adapter import MujocoORA4AAdapter
from openroboassure.simulators.pybullet_adapter import PyBulletORA4AAdapter


def test_action_conversion_clips_and_rejects_invalid_shape() -> None:
    assert np.array_equal(canonical_action_delta(np.ones(4)), ACTION_LIMITS)
    with pytest.raises(ValueError, match="shape"):
        canonical_action_delta(np.zeros(3))


def test_ora4a_static_task_geometry_is_equivalent_across_simulators() -> None:
    mujoco_adapter = MujocoORA4AAdapter()
    pybullet_adapter = PyBulletORA4AAdapter()
    try:
        mujoco_initial = mujoco_adapter.reset(17)
        pybullet_initial = pybullet_adapter.reset(17)
        np.testing.assert_allclose(
            mujoco_initial.end_effector_position, pybullet_initial.end_effector_position, atol=1e-12
        )
        np.testing.assert_allclose(
            mujoco_initial.object_position, pybullet_initial.object_position, atol=1e-12
        )
        for action in (
            np.array([0.007, -0.006, 0.004, 0.02]),
            np.array([-0.003, 0.004, 0.0, -0.01]),
        ):
            mujoco_state = mujoco_adapter.step(action).state
            pybullet_state = pybullet_adapter.step(action).state
            np.testing.assert_allclose(
                mujoco_state.end_effector_position, pybullet_state.end_effector_position, atol=1e-12
            )
            np.testing.assert_allclose(
                mujoco_state.object_position, pybullet_state.object_position, atol=1e-12
            )
        assert np.array_equal(mujoco_adapter.target_position, pybullet_adapter.target_position)
    finally:
        pybullet_adapter.close()
