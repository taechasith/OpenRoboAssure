"""Evidence generation for declared ORA-4A cross-simulator discrepancies."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from openroboassure.simulators.mujoco_adapter import MujocoORA4AAdapter
from openroboassure.simulators.pybullet_adapter import PyBulletORA4AAdapter

EXCITATION_ACTIONS = (
    np.array([0.007, -0.006, 0.004, 0.02]),
    np.array([-0.003, 0.004, 0.002, -0.01]),
    np.array([0.010, 0.005, -0.003, 0.03]),
    np.array([-0.006, -0.004, 0.005, -0.02]),
)


def measure_ora4a_discrepancy(seed: int = 0) -> dict[str, object]:
    """Measure only observable ORA-4A state differences under fixed excitation."""
    mujoco_adapter = MujocoORA4AAdapter()
    pybullet_adapter = PyBulletORA4AAdapter()
    try:
        mujoco_state = mujoco_adapter.reset(seed)
        pybullet_state = pybullet_adapter.reset(seed)
        ee_errors = [
            float(
                np.linalg.norm(
                    mujoco_state.end_effector_position - pybullet_state.end_effector_position
                )
            )
        ]
        object_errors = [
            float(np.linalg.norm(mujoco_state.object_position - pybullet_state.object_position))
        ]
        for action in EXCITATION_ACTIONS:
            mujoco_state = mujoco_adapter.step(action).state
            pybullet_state = pybullet_adapter.step(action).state
            ee_errors.append(
                float(
                    np.linalg.norm(
                        mujoco_state.end_effector_position - pybullet_state.end_effector_position
                    )
                )
            )
            object_errors.append(
                float(np.linalg.norm(mujoco_state.object_position - pybullet_state.object_position))
            )
        return {
            "experiment_id": "EXP-SIM-DISCREPANCY-001",
            "robot": "ora_4a",
            "task": "pick_place_v1",
            "seed": seed,
            "samples": len(ee_errors),
            "max_end_effector_position_error_m": max(ee_errors),
            "max_object_position_error_m": max(object_errors),
            "dynamic_equivalence": "not_claimed_kinematic_smoke_only",
        }
    finally:
        pybullet_adapter.close()


def write_discrepancy_report(report: dict[str, object], output: Path) -> None:
    """Write a machine-readable discrepancy report without hiding any measured value."""
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
