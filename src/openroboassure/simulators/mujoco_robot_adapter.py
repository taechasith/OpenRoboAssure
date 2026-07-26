"""Kinematic MuJoCo probes for the approved imported robot embodiments."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import mujoco
import numpy as np

from openroboassure.contracts import FloatArray
from openroboassure.simulators.action_conversion import canonical_action_delta

RobotId = Literal["panda", "ur5e"]


@dataclass(frozen=True)
class RobotModelSpec:
    """Pinned local entry point and end-effector body for one imported model."""

    entrypoint: str
    end_effector_body: str


@dataclass(frozen=True)
class RobotKinematicState:
    """Inspectable primary-simulator state for an imported robot model."""

    end_effector_position: FloatArray
    joint_positions: FloatArray


MODEL_SPECS: dict[RobotId, RobotModelSpec] = {
    "panda": RobotModelSpec("franka_emika_panda/panda.xml", "hand"),
    "ur5e": RobotModelSpec("universal_robots_ur5e/ur5e.xml", "wrist_3_link"),
}


def _model_path(entrypoint: str) -> Path:
    """Resolve an asset from a source checkout or the release-wheel payload."""
    source_path = (
        Path(__file__).resolve().parents[3]
        / "assets"
        / "imported"
        / "mujoco_menagerie"
        / entrypoint
    )
    if source_path.is_file():
        return source_path
    return Path(__file__).resolve().parents[1] / "assets" / "mujoco_menagerie" / entrypoint


class MujocoKinematicRobotAdapter:
    """Move an approved Panda or UR5e model by damped-Jacobian task-space steps.

    The adapter deliberately exposes kinematic motion only. It is a validated
    primary-simulator model probe, not a grasping controller or a claim of
    cross-simulator dynamic equivalence.
    """

    def __init__(self, robot_id: RobotId) -> None:
        self.robot_id = robot_id
        spec = MODEL_SPECS[robot_id]
        self.model = mujoco.MjModel.from_xml_path(str(_model_path(spec.entrypoint)))
        self.data = mujoco.MjData(self.model)
        self.end_effector_body = mujoco.mj_name2id(
            self.model, mujoco.mjtObj.mjOBJ_BODY, spec.end_effector_body
        )
        if self.end_effector_body < 0:
            raise ValueError(f"Missing end-effector body for {robot_id}")

    def reset(self) -> RobotKinematicState:
        if self.model.nkey:
            mujoco.mj_resetDataKeyframe(self.model, self.data, 0)
        else:
            mujoco.mj_resetData(self.model, self.data)
        mujoco.mj_forward(self.model, self.data)
        return self.get_state()

    def get_state(self) -> RobotKinematicState:
        return RobotKinematicState(
            self.data.xpos[self.end_effector_body].copy(), self.data.qpos.copy()
        )

    def step(self, action: FloatArray) -> RobotKinematicState:
        delta = canonical_action_delta(action)[:3]
        jacobian = np.zeros((3, self.model.nv), dtype=np.float64)
        mujoco.mj_jacBody(self.model, self.data, jacobian, None, self.end_effector_body)
        damping = 1e-4
        joint_delta = jacobian.T @ np.linalg.solve(
            jacobian @ jacobian.T + damping * np.eye(3), delta
        )
        for joint in range(self.model.njnt):
            qpos_address = self.model.jnt_qposadr[joint]
            dof_address = self.model.jnt_dofadr[joint]
            candidate = self.data.qpos[qpos_address] + joint_delta[dof_address]
            if self.model.jnt_limited[joint]:
                low, high = self.model.jnt_range[joint]
                candidate = float(np.clip(candidate, low, high))
            self.data.qpos[qpos_address] = candidate
        self.data.qvel[:] = 0.0
        mujoco.mj_forward(self.model, self.data)
        return self.get_state()

    def joint_limits_respected(self) -> bool:
        """Return whether every limited hinge/slide joint is inside its declared range."""
        for joint in range(self.model.njnt):
            if not self.model.jnt_limited[joint]:
                continue
            qpos = self.data.qpos[self.model.jnt_qposadr[joint]]
            low, high = self.model.jnt_range[joint]
            if qpos < low - 1e-12 or qpos > high + 1e-12:
                return False
        return True
