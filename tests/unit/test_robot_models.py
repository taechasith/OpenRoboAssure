from __future__ import annotations

import numpy as np
import pytest

from openroboassure.simulators.discrepancy import measure_ora4a_discrepancy
from openroboassure.simulators.mujoco_robot_adapter import MujocoKinematicRobotAdapter


@pytest.mark.parametrize("robot_id", ["panda", "ur5e"])
def test_imported_model_runs_and_respects_joint_limits(robot_id: str) -> None:
    adapter = MujocoKinematicRobotAdapter(robot_id)  # type: ignore[arg-type]
    initial = adapter.reset()
    moved = adapter.step(np.array([0.004, -0.003, 0.002, 0.0]))

    assert np.isfinite(initial.end_effector_position).all()
    assert np.isfinite(moved.end_effector_position).all()
    assert adapter.joint_limits_respected()


def test_kinematic_discrepancy_report_declares_its_limitations() -> None:
    report = measure_ora4a_discrepancy(seed=11)

    end_effector_error = report["max_end_effector_position_error_m"]
    object_error = report["max_object_position_error_m"]
    assert report["samples"] == 5
    assert isinstance(end_effector_error, float)
    assert isinstance(object_error, float)
    assert end_effector_error <= 0.005
    assert object_error <= 0.001
    assert report["dynamic_equivalence"] == "not_claimed_kinematic_smoke_only"
