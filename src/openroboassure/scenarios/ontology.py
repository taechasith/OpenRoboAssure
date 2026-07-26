"""The human-approved core uncertainty registry for P05."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ParameterKind(StrEnum):
    """Distribution domain for one uncertainty parameter."""

    CONTINUOUS = "continuous"
    DISCRETE = "discrete"


@dataclass(frozen=True)
class ParameterSpec:
    """Range, distribution domain, and nominal value for one variable."""

    name: str
    category: str
    kind: ParameterKind
    global_bounds: tuple[float, float]
    training_bounds: tuple[float, float]
    nominal: float


@dataclass(frozen=True)
class UncertaintyRegistry:
    """Immutable registry used by the scenario compiler and evidence report."""

    ontology_id: str
    parameters: tuple[ParameterSpec, ...]
    correlations: tuple[tuple[str, str], ...]

    def parameter(self, name: str) -> ParameterSpec:
        """Look up a parameter by stable identifier."""
        for parameter in self.parameters:
            if parameter.name == name:
                return parameter
        raise KeyError(f"Unknown scenario parameter: {name}")

    @property
    def category_coverage(self) -> dict[str, list[str]]:
        """Return included variable names grouped by approved category."""
        coverage: dict[str, list[str]] = {}
        for parameter in self.parameters:
            coverage.setdefault(parameter.category, []).append(parameter.name)
        return coverage


CORE_PICK_PLACE_REGISTRY = UncertaintyRegistry(
    ontology_id="pick_place_core_v1",
    parameters=(
        ParameterSpec(
            "object_mass_kg", "physics", ParameterKind.CONTINUOUS, (0.05, 0.50), (0.10, 0.40), 0.05
        ),
        ParameterSpec(
            "surface_friction",
            "physics",
            ParameterKind.CONTINUOUS,
            (0.20, 1.00),
            (0.35, 0.85),
            0.70,
        ),
        ParameterSpec(
            "object_half_extent_m",
            "geometry",
            ParameterKind.CONTINUOUS,
            (0.015, 0.024),
            (0.017, 0.022),
            0.020,
        ),
        ParameterSpec(
            "object_x_m",
            "geometry",
            ParameterKind.CONTINUOUS,
            (-0.18, -0.04),
            (-0.15, -0.08),
            -0.12,
        ),
        ParameterSpec(
            "object_y_m",
            "geometry",
            ParameterKind.CONTINUOUS,
            (-0.14, -0.02),
            (-0.11, -0.05),
            -0.08,
        ),
        ParameterSpec(
            "target_radius_m",
            "geometry",
            ParameterKind.CONTINUOUS,
            (0.044, 0.060),
            (0.047, 0.056),
            0.045,
        ),
        ParameterSpec(
            "target_x_m", "geometry", ParameterKind.CONTINUOUS, (0.10, 0.20), (0.13, 0.19), 0.16
        ),
        ParameterSpec(
            "target_y_m", "geometry", ParameterKind.CONTINUOUS, (0.05, 0.15), (0.07, 0.13), 0.10
        ),
        ParameterSpec("action_latency_steps", "control", ParameterKind.DISCRETE, (0, 4), (0, 2), 0),
        ParameterSpec(
            "action_noise_fraction",
            "control",
            ParameterKind.CONTINUOUS,
            (0.0, 0.25),
            (0.0, 0.15),
            0.0,
        ),
        ParameterSpec(
            "joint_encoder_bias_rad",
            "sensors",
            ParameterKind.CONTINUOUS,
            (-0.03, 0.03),
            (-0.02, 0.02),
            0.0,
        ),
        ParameterSpec(
            "joint_encoder_noise_rad",
            "sensors",
            ParameterKind.CONTINUOUS,
            (0.0, 0.03),
            (0.0, 0.01),
            0.0,
        ),
        ParameterSpec(
            "object_state_noise_m",
            "sensors",
            ParameterKind.CONTINUOUS,
            (0.0, 0.005),
            (0.0, 0.003),
            0.0,
        ),
        ParameterSpec("frame_delay_steps", "sensors", ParameterKind.DISCRETE, (0, 4), (0, 2), 0),
        ParameterSpec(
            "observation_dropout_probability",
            "sensors",
            ParameterKind.CONTINUOUS,
            (0.0, 0.10),
            (0.0, 0.05),
            0.0,
        ),
        ParameterSpec(
            "vertical_gravity_scale",
            "environment",
            ParameterKind.CONTINUOUS,
            (0.98, 1.02),
            (0.99, 1.01),
            1.0,
        ),
    ),
    correlations=(("object_half_extent_m", "target_radius_m"),),
)

CORE_PARAMETERS_BY_NAME = {
    parameter.name: parameter for parameter in CORE_PICK_PLACE_REGISTRY.parameters
}
