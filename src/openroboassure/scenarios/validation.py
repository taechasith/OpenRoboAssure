"""Hard and soft validity checks for procedural Pick-and-Place scenarios."""

from __future__ import annotations

from dataclasses import dataclass
from math import hypot, sqrt

from openroboassure.scenarios.models import PickPlaceScenario
from openroboassure.scenarios.ontology import CORE_PARAMETERS_BY_NAME
from openroboassure.simulators.action_conversion import JOINT_HIGH, JOINT_LOW
from openroboassure.simulators.task_geometry import INITIAL_CONFIGURATION, TABLE_HALF_EXTENTS

_CONTAINMENT_MARGIN_M = 0.010
_OBJECT_TARGET_CLEARANCE_M = 0.010
_END_EFFECTOR_RADIUS_M = 0.022


@dataclass(frozen=True)
class ScenarioValidation:
    """Result of hard constraints plus a normalized soft-margin score."""

    valid: bool
    reasons: tuple[str, ...]
    soft_margin_score: float


def validate_scenario(scenario: PickPlaceScenario) -> ScenarioValidation:
    """Check approved bounds, reachability, containment, and collision-free reset."""
    reasons: list[str] = []
    _check_bounds(scenario, reasons)
    _check_geometry(scenario, reasons)
    _check_reachability(scenario, reasons)
    _check_collision_free_initialization(scenario, reasons)
    return ScenarioValidation(not reasons, tuple(reasons), _soft_margin_score(scenario))


def _check_bounds(scenario: PickPlaceScenario, reasons: list[str]) -> None:
    values = {
        "object_mass_kg": scenario.object_mass_kg,
        "surface_friction": scenario.surface_friction,
        "object_half_extent_m": scenario.object_half_extent_m,
        "target_radius_m": scenario.target_radius_m,
        "action_latency_steps": float(scenario.action_latency_steps),
        "action_noise_fraction": scenario.action_noise_fraction,
        "joint_encoder_bias_rad": scenario.joint_encoder_bias_rad,
        "joint_encoder_noise_rad": scenario.joint_encoder_noise_rad,
        "object_state_noise_m": scenario.object_state_noise_m,
        "frame_delay_steps": float(scenario.frame_delay_steps),
        "observation_dropout_probability": scenario.observation_dropout_probability,
        "vertical_gravity_scale": scenario.vertical_gravity_scale,
    }
    for name, value in values.items():
        parameter = CORE_PARAMETERS_BY_NAME[name]
        low, high = parameter.global_bounds
        if not low <= value <= high:
            reasons.append(f"{name}_out_of_bounds")


def _check_geometry(scenario: PickPlaceScenario, reasons: list[str]) -> None:
    object_x, object_y, object_z = scenario.object_position
    target_x, target_y, _ = scenario.target_position
    half_extent = scenario.object_half_extent_m
    if abs(object_z - half_extent) > 1e-12:
        reasons.append("object_not_resting_on_table")
    if abs(object_x) + half_extent > float(TABLE_HALF_EXTENTS[0]) - _CONTAINMENT_MARGIN_M:
        reasons.append("object_outside_table_x")
    if abs(object_y) + half_extent > float(TABLE_HALF_EXTENTS[1]) - _CONTAINMENT_MARGIN_M:
        reasons.append("object_outside_table_y")
    if (
        abs(target_x) + scenario.target_radius_m
        > float(TABLE_HALF_EXTENTS[0]) - _CONTAINMENT_MARGIN_M
    ):
        reasons.append("target_outside_table_x")
    if (
        abs(target_y) + scenario.target_radius_m
        > float(TABLE_HALF_EXTENTS[1]) - _CONTAINMENT_MARGIN_M
    ):
        reasons.append("target_outside_table_y")
    target_clearance = scenario.target_radius_m - sqrt(2.0) * half_extent
    if target_clearance < _OBJECT_TARGET_CLEARANCE_M:
        reasons.append("target_clearance_too_small")


def _check_reachability(scenario: PickPlaceScenario, reasons: list[str]) -> None:
    for label, position in (
        ("object", scenario.object_position),
        ("target", scenario.target_position),
    ):
        if not JOINT_LOW[0] <= position[0] <= JOINT_HIGH[0]:
            reasons.append(f"{label}_outside_reach_x")
        if not JOINT_LOW[1] <= position[1] <= JOINT_HIGH[1]:
            reasons.append(f"{label}_outside_reach_y")


def _check_collision_free_initialization(scenario: PickPlaceScenario, reasons: list[str]) -> None:
    end_effector_x, end_effector_y = (
        float(INITIAL_CONFIGURATION[0]),
        float(INITIAL_CONFIGURATION[1]),
    )
    object_x, object_y, _ = scenario.object_position
    distance = hypot(object_x - end_effector_x, object_y - end_effector_y)
    required_distance = (
        scenario.object_half_extent_m + _END_EFFECTOR_RADIUS_M + _CONTAINMENT_MARGIN_M
    )
    if distance < required_distance:
        reasons.append("initial_end_effector_object_collision")


def _soft_margin_score(scenario: PickPlaceScenario) -> float:
    table_x_margin = float(TABLE_HALF_EXTENTS[0]) - abs(scenario.object_position[0])
    table_y_margin = float(TABLE_HALF_EXTENTS[1]) - abs(scenario.object_position[1])
    target_clearance = scenario.target_radius_m - sqrt(2.0) * scenario.object_half_extent_m
    normalized = min(
        table_x_margin / 0.10,
        table_y_margin / 0.10,
        target_clearance / 0.020,
    )
    return max(0.0, min(1.0, normalized))
