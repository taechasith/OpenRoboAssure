"""A procedural four-axis MuJoCo adapter for the initial ORA task."""

from __future__ import annotations

import mujoco
import numpy as np

from openroboassure.contracts import CanonicalState, FloatArray, StepResult
from openroboassure.scenarios.models import PickPlaceScenario
from openroboassure.simulators.action_conversion import apply_canonical_action
from openroboassure.simulators.task_geometry import (
    END_EFFECTOR_Z_OFFSET,
    HELD_OBJECT_OFFSET,
    INITIAL_CONFIGURATION,
    OBJECT_HALF_EXTENTS,
    TARGET_POSITION,
    sample_object_position,
)

ORA_4A_XML = """
<mujoco model="ora_4a_pick_place">
  <option timestep="0.01" gravity="0 0 -9.81"/>
  <worldbody>
    <geom name="table" type="box" pos="0 0 -0.025" size="0.45 0.35 0.025" rgba="0.2 0.2 0.2 1"/>
    <body name="ora_4a_carriage" pos="0 0 0.10">
      <joint name="ora_x" type="slide" axis="1 0 0" range="-0.25 0.25"/>
      <joint name="ora_y" type="slide" axis="0 1 0" range="-0.20 0.20"/>
      <joint name="ora_z" type="slide" axis="0 0 1" range="0.02 0.25"/>
      <joint name="ora_yaw" type="hinge" axis="0 0 1" range="-3.14 3.14"/>
      <geom type="cylinder" size="0.025 0.08" rgba="0.15 0.35 0.85 1"/>
      <body name="end_effector" pos="0 0 -0.08">
        <geom type="sphere" size="0.022" rgba="0.9 0.9 0.9 1"/>
      </body>
    </body>
    <body name="object" pos="-0.12 -0.08 0.025">
      <freejoint/>
      <geom name="object_geom" type="box" size="0.02 0.02 0.02" mass="0.05" rgba="0.95 0.35 0.1 1"/>
    </body>
    <site name="target" type="cylinder" pos="0.16 0.10 0.001" size="0.045 0.002" rgba="0.1 0.8 0.25 0.45"/>
  </worldbody>
  <actuator>
    <position joint="ora_x" kp="400"/>
    <position joint="ora_y" kp="400"/>
    <position joint="ora_z" kp="400"/>
    <position joint="ora_yaw" kp="100"/>
  </actuator>
</mujoco>
"""


class MujocoORA4AAdapter:
    """MuJoCo implementation of ORA-4A with deterministic grasp attachment."""

    def __init__(self) -> None:
        self.model = mujoco.MjModel.from_xml_string(ORA_4A_XML)
        self.data = mujoco.MjData(self.model)
        self._object_geom_id = mujoco.mj_name2id(
            self.model, mujoco.mjtObj.mjOBJ_GEOM, "object_geom"
        )
        self._object_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "object")
        self._target_site_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_SITE, "target")
        self._table_geom_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "table")
        self._default_geom_size = self.model.geom_size.copy()
        self._default_geom_friction = self.model.geom_friction.copy()
        self._default_body_mass = self.model.body_mass.copy()
        self._default_site_pos = self.model.site_pos.copy()
        self._default_site_size = self.model.site_size.copy()
        self._default_gravity = self.model.opt.gravity.copy()
        self.held = False
        self.initial_object_position = np.zeros(3, dtype=np.float64)
        self.target_position = TARGET_POSITION.copy()
        self.object_half_extent_m = float(OBJECT_HALF_EXTENTS[2])
        self.object_mass_kg = 0.05
        self.surface_friction = 0.70
        self.vertical_gravity_scale = 1.0

    def reset(self, seed: int) -> CanonicalState:
        self._restore_defaults()
        return self._reset(sample_object_position(seed))

    def reset_scenario(self, scenario: PickPlaceScenario) -> CanonicalState:
        """Apply an approved procedural scenario and reset into its initial state."""
        self._restore_defaults()
        self._apply_scenario(scenario)
        return self._reset(np.asarray(scenario.object_position, dtype=np.float64))

    def _reset(self, object_position: FloatArray) -> CanonicalState:
        mujoco.mj_resetData(self.model, self.data)
        self.data.qpos[:4] = INITIAL_CONFIGURATION
        self.initial_object_position = object_position.copy()
        self.data.qpos[4:7] = self.initial_object_position
        self.data.qpos[7:11] = np.array([1.0, 0.0, 0.0, 0.0])
        self.data.ctrl[:] = self.data.qpos[:4]
        self.held = False
        mujoco.mj_forward(self.model, self.data)
        return self.get_state()

    def _restore_defaults(self) -> None:
        self.model.geom_size[:] = self._default_geom_size
        self.model.geom_friction[:] = self._default_geom_friction
        self.model.body_mass[:] = self._default_body_mass
        self.model.site_pos[:] = self._default_site_pos
        self.model.site_size[:] = self._default_site_size
        self.model.opt.gravity[:] = self._default_gravity
        self.target_position = TARGET_POSITION.copy()
        self.object_half_extent_m = float(OBJECT_HALF_EXTENTS[2])
        self.object_mass_kg = 0.05
        self.surface_friction = 0.70
        self.vertical_gravity_scale = 1.0

    def _apply_scenario(self, scenario: PickPlaceScenario) -> None:
        self.model.geom_size[self._object_geom_id] = np.full(3, scenario.object_half_extent_m)
        self.model.geom_friction[self._object_geom_id] = np.array(
            [scenario.surface_friction, 0.005, 0.0001]
        )
        self.model.geom_friction[self._table_geom_id] = np.array(
            [scenario.surface_friction, 0.005, 0.0001]
        )
        self.model.body_mass[self._object_body_id] = scenario.object_mass_kg
        self.model.site_pos[self._target_site_id] = np.asarray(
            scenario.target_position, dtype=np.float64
        )
        self.model.site_size[self._target_site_id, 0] = scenario.target_radius_m
        self.model.opt.gravity[2] = -9.81 * scenario.vertical_gravity_scale
        self.target_position = np.asarray(scenario.target_position, dtype=np.float64)
        self.object_half_extent_m = scenario.object_half_extent_m
        self.object_mass_kg = scenario.object_mass_kg
        self.surface_friction = scenario.surface_friction
        self.vertical_gravity_scale = scenario.vertical_gravity_scale

    def get_state(self) -> CanonicalState:
        ee = self.data.qpos[:3].copy()
        ee[2] += END_EFFECTOR_Z_OFFSET
        return CanonicalState(ee, self.data.qpos[4:7].copy(), self.held)

    def step(self, action: FloatArray) -> StepResult:
        target = apply_canonical_action(self.data.ctrl.copy(), action)
        self.data.ctrl[:] = target
        self.data.qpos[:4] = target
        self.data.qvel[:4] = 0.0
        mujoco.mj_forward(self.model, self.data)
        if self.held:
            state = self.get_state()
            self.data.qpos[4:7] = state.end_effector_position - HELD_OBJECT_OFFSET
            self.data.qvel[4:10] = 0.0
            mujoco.mj_forward(self.model, self.data)
        return StepResult(self.get_state(), collision_count=0)

    def set_grasp(self, held: bool) -> None:
        if self.held and not held:
            self.data.qpos[6] = self.object_half_extent_m
            self.data.qvel[4:10] = 0.0
            mujoco.mj_forward(self.model, self.data)
        self.held = held

    def snapshot(self) -> bytes:
        return np.concatenate((self.data.qpos, self.data.qvel, [float(self.held)])).tobytes()

    def restore(self, snapshot: bytes) -> None:
        values = np.frombuffer(snapshot, dtype=np.float64)
        nq, nv = self.model.nq, self.model.nv
        self.data.qpos[:] = values[:nq]
        self.data.qvel[:] = values[nq : nq + nv]
        self.held = bool(values[nq + nv])
        mujoco.mj_forward(self.model, self.data)

    def render_rgb(self) -> np.ndarray:
        """Render one optional RGB frame for local diagnostics."""
        with mujoco.Renderer(self.model, height=240, width=320) as renderer:
            renderer.update_scene(self.data)
            return np.array(renderer.render(), dtype=np.uint8)
