"""Helpers for converting scenarios to approved parameter mappings."""

from __future__ import annotations

from openroboassure.scenarios.models import PickPlaceScenario


def scenario_parameter_values(scenario: PickPlaceScenario) -> dict[str, float]:
    """Return a scenario as the flat P05 uncertainty-parameter mapping."""
    return {
        "object_mass_kg": scenario.object_mass_kg,
        "surface_friction": scenario.surface_friction,
        "object_half_extent_m": scenario.object_half_extent_m,
        "object_x_m": scenario.object_position[0],
        "object_y_m": scenario.object_position[1],
        "target_radius_m": scenario.target_radius_m,
        "target_x_m": scenario.target_position[0],
        "target_y_m": scenario.target_position[1],
        "action_latency_steps": float(scenario.action_latency_steps),
        "action_noise_fraction": scenario.action_noise_fraction,
        "joint_encoder_bias_rad": scenario.joint_encoder_bias_rad,
        "joint_encoder_noise_rad": scenario.joint_encoder_noise_rad,
        "object_state_noise_m": scenario.object_state_noise_m,
        "frame_delay_steps": float(scenario.frame_delay_steps),
        "observation_dropout_probability": scenario.observation_dropout_probability,
        "vertical_gravity_scale": scenario.vertical_gravity_scale,
    }
