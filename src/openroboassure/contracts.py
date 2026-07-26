"""Canonical simulation contracts used by simulator adapters."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

FloatArray = npt.NDArray[np.float64]


@dataclass(frozen=True)
class CanonicalState:
    """State shared across simulator backends."""

    end_effector_position: FloatArray
    object_position: FloatArray
    held: bool


@dataclass(frozen=True)
class StepResult:
    """One simulation transition."""

    state: CanonicalState
    collision_count: int
