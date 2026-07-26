"""Serializable scenario contracts for the approved Pick-and-Place ontology."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import StrEnum


class ScenarioFamily(StrEnum):
    """Benchmark scenario families fixed by the master build guide."""

    S0_NOMINAL = "S0_nominal"
    S1_IN_DISTRIBUTION = "S1_in_distribution"
    S2_BOUNDARY = "S2_boundary"
    S3_UNSEEN_COMBINATIONS = "S3_unseen_combinations"
    S4_OUT_OF_DISTRIBUTION = "S4_out_of_distribution"
    S5_ADVERSARIAL = "S5_adversarial"
    S6_FAULT_INJECTION = "S6_fault_injection"
    S7_CROSS_SIMULATOR = "S7_cross_simulator"


class ScenarioSplit(StrEnum):
    """Immutable partition used to prevent training/evaluation leakage."""

    TRAIN = "train"
    EVALUATION = "evaluation"


@dataclass(frozen=True)
class PickPlaceScenario:
    """One complete, serializable procedural Pick-and-Place scenario."""

    index: int
    seed: int
    family: ScenarioFamily
    split: ScenarioSplit
    object_mass_kg: float
    surface_friction: float
    object_half_extent_m: float
    object_position: tuple[float, float, float]
    target_radius_m: float
    target_position: tuple[float, float, float]
    action_latency_steps: int
    action_noise_fraction: float
    joint_encoder_bias_rad: float
    joint_encoder_noise_rad: float
    object_state_noise_m: float
    frame_delay_steps: int
    observation_dropout_probability: float
    vertical_gravity_scale: float

    def to_dict(self) -> dict[str, object]:
        """Return the canonical JSON-compatible representation."""
        return {
            "schema_version": 1,
            "ontology_id": "pick_place_core_v1",
            "index": self.index,
            "seed": self.seed,
            "family": self.family.value,
            "split": self.split.value,
            "object_mass_kg": self.object_mass_kg,
            "surface_friction": self.surface_friction,
            "object_half_extent_m": self.object_half_extent_m,
            "object_position": list(self.object_position),
            "target_radius_m": self.target_radius_m,
            "target_position": list(self.target_position),
            "action_latency_steps": self.action_latency_steps,
            "action_noise_fraction": self.action_noise_fraction,
            "joint_encoder_bias_rad": self.joint_encoder_bias_rad,
            "joint_encoder_noise_rad": self.joint_encoder_noise_rad,
            "object_state_noise_m": self.object_state_noise_m,
            "frame_delay_steps": self.frame_delay_steps,
            "observation_dropout_probability": self.observation_dropout_probability,
            "vertical_gravity_scale": self.vertical_gravity_scale,
        }

    @property
    def scenario_hash(self) -> str:
        """Hash the complete scenario, including its split and deterministic identity."""
        return _digest(self.to_dict())

    @property
    def parameter_hash(self) -> str:
        """Hash only physical/task parameters to detect cross-split leakage."""
        payload = self.to_dict()
        for key in ("index", "seed", "family", "split"):
            del payload[key]
        return _digest(payload)


def _digest(payload: dict[str, object]) -> str:
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
