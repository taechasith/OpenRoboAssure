"""A state-only scripted policy under the P06 common policy contract."""

from __future__ import annotations

import numpy as np
import numpy.typing as npt


class ScriptedPickPlacePolicy:
    """Waypoint controller used as a deterministic, non-learned reference."""

    def __init__(self) -> None:
        self._stage = 0

    def reset(self) -> None:
        """Discard episode-local waypoint state."""
        self._stage = 0

    def act(self, observation: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
        """Return normalized XYZ-plus-grasp command from canonical state only."""
        end_effector = observation[:3]
        object_position = observation[3:6]
        target_position = observation[6:9]
        held = bool(observation[9] >= 0.5)
        if held and self._stage < 2:
            self._stage = 2
        if self._stage == 0:
            desired = object_position + np.array([0.0, 0.0, 0.13])
            if np.linalg.norm(end_effector - desired) < 0.012:
                self._stage = 1
        elif self._stage == 1:
            desired = object_position + np.array([0.0, 0.0, 0.04])
            if np.linalg.norm(end_effector - desired) < 0.018:
                self._stage = 2
        elif self._stage == 2:
            desired = np.array([object_position[0], object_position[1], 0.20])
            if np.linalg.norm(end_effector - desired) < 0.015:
                self._stage = 3
        elif self._stage == 3:
            desired = target_position + np.array([0.0, 0.0, 0.18])
            if np.linalg.norm(end_effector - desired) < 0.015:
                self._stage = 4
        else:
            desired = target_position + np.array([0.0, 0.0, 0.04])
            if np.linalg.norm(end_effector - desired) < 0.015:
                self._stage = 5
        action = np.zeros(4, dtype=np.float64)
        action[:3] = np.clip((desired - end_effector) / 0.012, -1.0, 1.0)
        action[3] = -1.0 if self._stage == 5 else 1.0
        return action
