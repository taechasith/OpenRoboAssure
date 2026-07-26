"""A procedural four-axis MuJoCo adapter for the initial ORA task."""

from __future__ import annotations

import mujoco
import numpy as np

from openroboassure.contracts import CanonicalState, FloatArray, StepResult

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
      <geom type="box" size="0.02 0.02 0.02" mass="0.05" rgba="0.95 0.35 0.1 1"/>
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

    target_position = np.array([0.16, 0.10, 0.02], dtype=np.float64)

    def __init__(self) -> None:
        self.model = mujoco.MjModel.from_xml_string(ORA_4A_XML)
        self.data = mujoco.MjData(self.model)
        self.held = False
        self.initial_object_position = np.zeros(3, dtype=np.float64)

    def reset(self, seed: int) -> CanonicalState:
        rng = np.random.default_rng(seed)
        mujoco.mj_resetData(self.model, self.data)
        self.data.qpos[:4] = np.array([0.0, 0.0, 0.12, 0.0])
        self.initial_object_position = np.array(
            [rng.uniform(-0.16, -0.06), rng.uniform(-0.12, -0.03), 0.02], dtype=np.float64
        )
        self.data.qpos[4:7] = self.initial_object_position
        self.data.qpos[7:11] = np.array([1.0, 0.0, 0.0, 0.0])
        self.data.ctrl[:] = self.data.qpos[:4]
        self.held = False
        mujoco.mj_forward(self.model, self.data)
        return self.get_state()

    def get_state(self) -> CanonicalState:
        ee = self.data.qpos[:3].copy()
        ee[2] += 0.02
        return CanonicalState(ee, self.data.qpos[4:7].copy(), self.held)

    def step(self, action: FloatArray) -> StepResult:
        target = self.data.ctrl.copy()
        target[:3] = np.clip(target[:3] + action[:3], [-0.25, -0.20, 0.02], [0.25, 0.20, 0.25])
        target[3] = float(np.clip(target[3] + action[3], -3.14, 3.14))
        self.data.ctrl[:] = target
        self.data.qpos[:4] = target
        self.data.qvel[:4] = 0.0
        mujoco.mj_forward(self.model, self.data)
        if self.held:
            state = self.get_state()
            self.data.qpos[4:7] = state.end_effector_position - np.array([0.0, 0.0, 0.04])
            self.data.qvel[4:10] = 0.0
            mujoco.mj_forward(self.model, self.data)
        return StepResult(self.get_state(), collision_count=0)

    def set_grasp(self, held: bool) -> None:
        if self.held and not held:
            self.data.qpos[6] = 0.02
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
