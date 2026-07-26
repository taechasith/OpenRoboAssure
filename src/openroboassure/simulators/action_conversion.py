"""Canonical task-space action conversion shared by all simulator adapters."""

from __future__ import annotations

import numpy as np

from openroboassure.contracts import FloatArray

ACTION_LIMITS = np.array([0.012, 0.012, 0.012, 0.12], dtype=np.float64)
JOINT_LOW = np.array([-0.25, -0.20, 0.02, -3.14], dtype=np.float64)
JOINT_HIGH = np.array([0.25, 0.20, 0.25, 3.14], dtype=np.float64)


def canonical_action_delta(action: FloatArray) -> FloatArray:
    """Validate and clip one canonical ``[x, y, z, yaw]`` task-space action."""
    values = np.asarray(action, dtype=np.float64)
    if values.shape != (4,):
        raise ValueError("Canonical action must have shape (4,) for x, y, z, and yaw")
    return np.clip(values, -ACTION_LIMITS, ACTION_LIMITS)


def apply_canonical_action(current: FloatArray, action: FloatArray) -> FloatArray:
    """Apply a bounded canonical action to a four-axis kinematic configuration."""
    values = np.asarray(current, dtype=np.float64)
    if values.shape != (4,):
        raise ValueError("Current four-axis configuration must have shape (4,)")
    return np.clip(values + canonical_action_delta(action), JOINT_LOW, JOINT_HIGH)
