"""Shared procedural geometry and deterministic reset sampling for Pick-and-Place."""

from __future__ import annotations

import numpy as np

TABLE_HALF_EXTENTS = np.array([0.45, 0.35, 0.025], dtype=np.float64)
OBJECT_HALF_EXTENTS = np.array([0.02, 0.02, 0.02], dtype=np.float64)
TARGET_POSITION = np.array([0.16, 0.10, 0.02], dtype=np.float64)
TARGET_RADIUS = 0.045
INITIAL_CONFIGURATION = np.array([0.0, 0.0, 0.12, 0.0], dtype=np.float64)
END_EFFECTOR_Z_OFFSET = 0.02
HELD_OBJECT_OFFSET = np.array([0.0, 0.0, 0.04], dtype=np.float64)


def sample_object_position(seed: int) -> np.ndarray:
    """Return the shared deterministic object start pose for one episode seed."""
    rng = np.random.default_rng(seed)
    return np.array(
        [rng.uniform(-0.16, -0.06), rng.uniform(-0.12, -0.03), OBJECT_HALF_EXTENTS[2]],
        dtype=np.float64,
    )
