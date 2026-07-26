"""Gymnasium-compatible state-only ORA-4A Pick-and-Place task wrapper."""

from __future__ import annotations

from collections import deque
from typing import Any

import gymnasium as gym
import numpy as np
import numpy.typing as npt

from openroboassure.scenarios.models import PickPlaceScenario
from openroboassure.simulators.action_conversion import ACTION_LIMITS
from openroboassure.simulators.mujoco_adapter import MujocoORA4AAdapter

_OBSERVATION_SIZE = 10
_MAX_ACTION = np.ones(4, dtype=np.float32)


class PickPlaceGymEnv(gym.Env[npt.NDArray[np.float64], npt.NDArray[np.float64]]):
    """Gymnasium API that applies the approved P05 disturbances at run time.

    The policy action is normalized ``[x, y, z, grasp]``. The first three
    channels share the existing canonical motion limits; grasp is gated by
    physical proximity rather than allowing remote attachment.
    """

    metadata = {"render_modes": []}

    def __init__(self, max_episode_steps: int = 90) -> None:
        super().__init__()
        self.action_space = gym.spaces.Box(-_MAX_ACTION, _MAX_ACTION, dtype=np.float32)
        self.observation_space = gym.spaces.Box(
            low=np.full(_OBSERVATION_SIZE, -np.inf, dtype=np.float64),
            high=np.full(_OBSERVATION_SIZE, np.inf, dtype=np.float64),
            dtype=np.float64,
        )
        self.adapter = MujocoORA4AAdapter()
        self.max_episode_steps = max_episode_steps
        self._rng = np.random.default_rng(0)
        self._scenario: PickPlaceScenario | None = None
        self._action_queue: deque[npt.NDArray[np.float64]] = deque()
        self._observation_queue: deque[npt.NDArray[np.float64]] = deque()
        self._last_observation = np.zeros(_OBSERVATION_SIZE, dtype=np.float64)
        self._steps = 0
        self._had_grasp = False
        self._released = False
        self._previous_distance = 0.0

    def reset(
        self, *, seed: int | None = None, options: dict[str, Any] | None = None
    ) -> tuple[npt.NDArray[np.float64], dict[str, Any]]:
        """Reset to a supplied valid scenario and return its canonical observation."""
        super().reset(seed=seed)
        if seed is not None:
            self._rng = np.random.default_rng(seed)
        if options is None or not isinstance(options.get("scenario"), PickPlaceScenario):
            raise ValueError(
                "PickPlaceGymEnv.reset requires options={'scenario': PickPlaceScenario}"
            )
        self._scenario = options["scenario"]
        state = self.adapter.reset_scenario(self._scenario)
        self._action_queue = deque(
            [np.zeros(4, dtype=np.float64) for _ in range(self._scenario.action_latency_steps)]
        )
        raw_observation = self._observe(
            state.end_effector_position, state.object_position, state.held
        )
        self._observation_queue = deque(
            [raw_observation.copy() for _ in range(self._scenario.frame_delay_steps + 1)],
            maxlen=self._scenario.frame_delay_steps + 1,
        )
        self._last_observation = raw_observation.copy()
        self._steps = 0
        self._had_grasp = False
        self._released = False
        self._previous_distance = self._active_distance(raw_observation)
        return self._delayed_observation(), {"scenario_hash": self._scenario.scenario_hash}

    def step(
        self, action: npt.NDArray[np.float64]
    ) -> tuple[npt.NDArray[np.float64], float, bool, bool, dict[str, Any]]:
        """Advance one common action and return reward plus transparent outcomes."""
        scenario = self._require_scenario()
        normalized = np.asarray(action, dtype=np.float64)
        if normalized.shape != (4,):
            raise ValueError("Policy action must have four normalized channels")
        normalized = np.clip(normalized, -1.0, 1.0)
        self._action_queue.append(normalized)
        executed = self._action_queue.popleft()
        motion = np.zeros(4, dtype=np.float64)
        motion[:3] = executed[:3] * ACTION_LIMITS[:3]
        noise_limit = scenario.action_noise_fraction * ACTION_LIMITS[:3]
        motion[:3] += self._rng.uniform(-noise_limit, noise_limit)
        state_before = self.adapter.get_state()
        proximity = float(
            np.linalg.norm(state_before.end_effector_position - state_before.object_position)
        )
        invalid_grasp = False
        if executed[3] > 0.0 and not state_before.held:
            if proximity <= 0.045:
                self.adapter.set_grasp(True)
                self._had_grasp = True
            else:
                invalid_grasp = True
        elif executed[3] <= 0.0 and state_before.held:
            self.adapter.set_grasp(False)
            self._released = True
        result = self.adapter.step(motion)
        self._steps += 1
        raw_observation = self._observe(
            result.state.end_effector_position, result.state.object_position, result.state.held
        )
        self._observation_queue.append(raw_observation)
        observation = self._delayed_observation()
        current_distance = self._active_distance(raw_observation)
        reward = 25.0 * (self._previous_distance - current_distance) - 0.01
        self._previous_distance = current_distance
        if result.state.held and not state_before.held:
            reward += 1.0
        if invalid_grasp:
            reward -= 0.05
        success = self._is_success(result.state.object_position)
        dropped = self._released and not success
        terminated = success or dropped
        truncated = self._steps >= self.max_episode_steps and not terminated
        if success:
            reward += 20.0
        info: dict[str, Any] = {
            "success": success,
            "dropped": dropped,
            "collision_count": result.collision_count,
            "invalid_grasp": invalid_grasp,
            "scenario_hash": scenario.scenario_hash,
            "steps": self._steps,
        }
        return observation, float(reward), terminated, truncated, info

    def close(self) -> None:
        """Release adapter resources when an experiment completes."""
        close = getattr(self.adapter, "close", None)
        if callable(close):
            close()
        super().close()

    def _require_scenario(self) -> PickPlaceScenario:
        if self._scenario is None:
            raise RuntimeError("Environment must be reset before stepping")
        return self._scenario

    def _observe(
        self,
        end_effector_position: npt.NDArray[np.float64],
        object_position: npt.NDArray[np.float64],
        held: bool,
    ) -> npt.NDArray[np.float64]:
        scenario = self._require_scenario()
        joint_bias_m = scenario.joint_encoder_bias_rad * ACTION_LIMITS[0] / 0.03
        joint_noise_m = scenario.joint_encoder_noise_rad * ACTION_LIMITS[0] / 0.03
        end_effector = (
            end_effector_position + joint_bias_m + self._rng.normal(0.0, joint_noise_m, 3)
        )
        observed_object = object_position + self._rng.normal(0.0, scenario.object_state_noise_m, 3)
        return np.concatenate(
            (end_effector, observed_object, self.adapter.target_position, [float(held)])
        ).astype(np.float64)

    def _delayed_observation(self) -> npt.NDArray[np.float64]:
        scenario = self._require_scenario()
        candidate = self._observation_queue[0].copy()
        if self._rng.random() < scenario.observation_dropout_probability:
            return self._last_observation.copy()
        self._last_observation = candidate.copy()
        return candidate

    def _active_distance(self, observation: npt.NDArray[np.float64]) -> float:
        if observation[9] >= 0.5:
            return float(np.linalg.norm(observation[3:6] - observation[6:9]))
        return float(np.linalg.norm(observation[:3] - observation[3:6]))

    def _is_success(self, object_position: npt.NDArray[np.float64]) -> bool:
        if not self._released or not self._had_grasp:
            return False
        lateral_distance = np.linalg.norm(object_position[:2] - self.adapter.target_position[:2])
        return bool(
            lateral_distance <= self.adapter.object_half_extent_m and object_position[2] <= 0.05
        )
