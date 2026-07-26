"""Simulator adapter protocol."""

from __future__ import annotations

from typing import Protocol

from openroboassure.contracts import CanonicalState, FloatArray, StepResult


class SimulatorAdapter(Protocol):
    """Common contract for deterministic simulator backends."""

    def reset(self, seed: int) -> CanonicalState: ...

    def step(self, action: FloatArray) -> StepResult: ...

    def get_state(self) -> CanonicalState: ...

    def snapshot(self) -> bytes: ...

    def restore(self, snapshot: bytes) -> None: ...
