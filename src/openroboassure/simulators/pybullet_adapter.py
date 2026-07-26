"""Deterministic PyBullet implementation of the procedural ORA-4A task."""

from __future__ import annotations

import numpy as np
import pybullet

from openroboassure.contracts import CanonicalState, FloatArray, StepResult
from openroboassure.scenarios.models import PickPlaceScenario
from openroboassure.simulators.action_conversion import apply_canonical_action
from openroboassure.simulators.task_geometry import (
    END_EFFECTOR_Z_OFFSET,
    HELD_OBJECT_OFFSET,
    INITIAL_CONFIGURATION,
    OBJECT_HALF_EXTENTS,
    TABLE_HALF_EXTENTS,
    TARGET_POSITION,
    TARGET_RADIUS,
    sample_object_position,
)


class PyBulletORA4AAdapter:
    """PyBullet counterpart to the kinematic MuJoCo ORA-4A smoke adapter."""

    def __init__(self) -> None:
        self.client_id = pybullet.connect(pybullet.DIRECT)
        self._set_defaults()
        self._build_scene()

    def _set_defaults(self) -> None:
        self.configuration = INITIAL_CONFIGURATION.copy()
        self.object_position = np.zeros(3, dtype=np.float64)
        self.target_position = TARGET_POSITION.copy()
        self.target_radius_m = TARGET_RADIUS
        self.object_half_extent_m = float(OBJECT_HALF_EXTENTS[2])
        self.object_mass_kg = 0.05
        self.surface_friction = 0.70
        self.vertical_gravity_scale = 1.0
        self.held = False

    def _body(
        self,
        collision_shape: int,
        visual_shape: int,
        position: FloatArray,
        *,
        mass: float = 0.0,
    ) -> int:
        return int(
            pybullet.createMultiBody(
                baseMass=mass,
                baseCollisionShapeIndex=collision_shape,
                baseVisualShapeIndex=visual_shape,
                basePosition=position.tolist(),
                physicsClientId=self.client_id,
            )
        )

    def _build_scene(self) -> None:
        pybullet.resetSimulation(physicsClientId=self.client_id)
        pybullet.setGravity(
            0.0, 0.0, -9.81 * self.vertical_gravity_scale, physicsClientId=self.client_id
        )
        table_collision = pybullet.createCollisionShape(
            pybullet.GEOM_BOX,
            halfExtents=TABLE_HALF_EXTENTS.tolist(),
            physicsClientId=self.client_id,
        )
        table_visual = pybullet.createVisualShape(
            pybullet.GEOM_BOX,
            halfExtents=TABLE_HALF_EXTENTS.tolist(),
            rgbaColor=[0.2, 0.2, 0.2, 1.0],
            physicsClientId=self.client_id,
        )
        self.table_body = self._body(
            table_collision, table_visual, np.array([0.0, 0.0, -0.025], dtype=np.float64)
        )
        ee_collision = pybullet.createCollisionShape(
            pybullet.GEOM_SPHERE, radius=0.022, physicsClientId=self.client_id
        )
        ee_visual = pybullet.createVisualShape(
            pybullet.GEOM_SPHERE,
            radius=0.022,
            rgbaColor=[0.9, 0.9, 0.9, 1.0],
            physicsClientId=self.client_id,
        )
        self.end_effector_body = self._body(ee_collision, ee_visual, self._end_effector_position())
        object_collision = pybullet.createCollisionShape(
            pybullet.GEOM_BOX,
            halfExtents=[self.object_half_extent_m] * 3,
            physicsClientId=self.client_id,
        )
        object_visual = pybullet.createVisualShape(
            pybullet.GEOM_BOX,
            halfExtents=OBJECT_HALF_EXTENTS.tolist(),
            rgbaColor=[0.95, 0.35, 0.1, 1.0],
            physicsClientId=self.client_id,
        )
        self.object_body = self._body(
            object_collision, object_visual, self.object_position, mass=self.object_mass_kg
        )
        target_visual = pybullet.createVisualShape(
            pybullet.GEOM_CYLINDER,
            radius=float(self.target_radius_m),
            length=0.004,
            rgbaColor=[0.1, 0.8, 0.25, 0.45],
            physicsClientId=self.client_id,
        )
        self.target_body = self._body(
            -1,
            target_visual,
            np.array([self.target_position[0], self.target_position[1], 0.002]),
        )
        for body in (self.table_body, self.object_body):
            pybullet.changeDynamics(
                body,
                -1,
                lateralFriction=self.surface_friction,
                physicsClientId=self.client_id,
            )

    def _end_effector_position(self) -> FloatArray:
        return np.asarray(
            self.configuration[:3] + np.array([0.0, 0.0, END_EFFECTOR_Z_OFFSET]), dtype=np.float64
        )

    def _sync_bodies(self) -> None:
        pybullet.resetBasePositionAndOrientation(
            self.end_effector_body,
            self._end_effector_position().tolist(),
            pybullet.getQuaternionFromEuler([0.0, 0.0, float(self.configuration[3])]),
            physicsClientId=self.client_id,
        )
        pybullet.resetBasePositionAndOrientation(
            self.object_body,
            self.object_position.tolist(),
            [0.0, 0.0, 0.0, 1.0],
            physicsClientId=self.client_id,
        )

    def reset(self, seed: int) -> CanonicalState:
        self._set_defaults()
        self.object_position = sample_object_position(seed)
        self._build_scene()
        self._sync_bodies()
        return self.get_state()

    def reset_scenario(self, scenario: PickPlaceScenario) -> CanonicalState:
        """Apply an approved procedural scenario and reset into its initial state."""
        self._set_defaults()
        self.object_position = np.asarray(scenario.object_position, dtype=np.float64)
        self.target_position = np.asarray(scenario.target_position, dtype=np.float64)
        self.target_radius_m = scenario.target_radius_m
        self.object_half_extent_m = scenario.object_half_extent_m
        self.object_mass_kg = scenario.object_mass_kg
        self.surface_friction = scenario.surface_friction
        self.vertical_gravity_scale = scenario.vertical_gravity_scale
        self._build_scene()
        self._sync_bodies()
        return self.get_state()

    def get_state(self) -> CanonicalState:
        return CanonicalState(
            self._end_effector_position().copy(), self.object_position.copy(), self.held
        )

    def step(self, action: FloatArray) -> StepResult:
        self.configuration = apply_canonical_action(self.configuration, action)
        if self.held:
            self.object_position = self._end_effector_position() - HELD_OBJECT_OFFSET
        self._sync_bodies()
        return StepResult(self.get_state(), collision_count=0)

    def set_grasp(self, held: bool) -> None:
        if self.held and not held:
            self.object_position[2] = self.object_half_extent_m
        self.held = held
        self._sync_bodies()

    def snapshot(self) -> bytes:
        return np.concatenate(
            (self.configuration, self.object_position, [float(self.held)])
        ).tobytes()

    def restore(self, snapshot: bytes) -> None:
        values = np.frombuffer(snapshot, dtype=np.float64)
        if values.shape != (8,):
            raise ValueError("Invalid ORA-4A PyBullet snapshot")
        self.configuration = values[:4].copy()
        self.object_position = values[4:7].copy()
        self.held = bool(values[7])
        self._sync_bodies()

    def close(self) -> None:
        """Release the private direct-mode PyBullet connection."""
        if pybullet.isConnected(physicsClientId=self.client_id):
            pybullet.disconnect(physicsClientId=self.client_id)
