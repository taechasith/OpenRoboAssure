"""The four approved P06 randomization systems over the P05 ontology."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from math import sqrt

import numpy as np

from openroboassure.scenarios.models import PickPlaceScenario, ScenarioFamily, ScenarioSplit
from openroboassure.scenarios.ontology import CORE_PICK_PLACE_REGISTRY, ParameterKind, ParameterSpec
from openroboassure.scenarios.validation import validate_scenario


class RandomizationSystem(StrEnum):
    """The human-approved baseline definitions."""

    A_NO_RANDOMIZATION = "A"
    B_BROAD_UNIFORM = "B"
    C_AUTOMATIC_CURRICULUM = "C"
    D_SENSITIVITY_GUIDED = "D"


@dataclass(frozen=True)
class ScenarioSampler:
    """Reproducibly draw only valid P05 scenarios for one approved system."""

    system: RandomizationSystem
    root_seed: int
    selected_variables: tuple[str, ...] = ()

    def sample(
        self, index: int, *, progress: float = 1.0, split: ScenarioSplit = ScenarioSplit.TRAIN
    ) -> PickPlaceScenario:
        """Produce one scenario without cross-system changes to the ontology."""
        if index < 0:
            raise ValueError("Scenario index must be non-negative")
        if not 0.0 <= progress <= 1.0:
            raise ValueError("Curriculum progress must be within [0, 1]")
        if self.system is RandomizationSystem.D_SENSITIVITY_GUIDED and not self.selected_variables:
            raise ValueError("System D requires Morris/Sobol selected variables")
        rng = np.random.default_rng(
            np.random.SeedSequence([self.root_seed, index, int(split == ScenarioSplit.EVALUATION)])
        )
        values = {
            parameter.name: self._sample_parameter(parameter, rng, progress)
            for parameter in CORE_PICK_PLACE_REGISTRY.parameters
        }
        return scenario_from_parameter_values(
            values,
            index=index,
            seed=int(rng.integers(0, np.iinfo(np.int64).max)),
            family=self._family,
            split=split,
        )

    @property
    def _family(self) -> ScenarioFamily:
        return (
            ScenarioFamily.S0_NOMINAL
            if self.system is RandomizationSystem.A_NO_RANDOMIZATION
            else ScenarioFamily.S1_IN_DISTRIBUTION
        )

    def _sample_parameter(
        self, parameter: ParameterSpec, rng: np.random.Generator, progress: float
    ) -> float:
        if self.system is RandomizationSystem.A_NO_RANDOMIZATION:
            return parameter.nominal
        if (
            self.system is RandomizationSystem.D_SENSITIVITY_GUIDED
            and parameter.name not in self.selected_variables
        ):
            return parameter.nominal
        low, high = parameter.training_bounds
        if self.system is RandomizationSystem.C_AUTOMATIC_CURRICULUM:
            low = parameter.nominal + (low - parameter.nominal) * progress
            high = parameter.nominal + (high - parameter.nominal) * progress
        if parameter.kind is ParameterKind.DISCRETE:
            return float(rng.integers(int(low), int(high) + 1))
        return float(rng.uniform(low, high))

    @staticmethod
    def _apply_required_correlation(values: dict[str, float]) -> None:
        required_radius = sqrt(2.0) * values["object_half_extent_m"] + 0.010
        maximum_radius = CORE_PICK_PLACE_REGISTRY.parameter("target_radius_m").global_bounds[1]
        values["target_radius_m"] = min(
            maximum_radius, max(values["target_radius_m"], required_radius)
        )


def scenario_from_parameter_values(
    values: dict[str, float],
    *,
    index: int,
    seed: int,
    family: ScenarioFamily,
    split: ScenarioSplit,
) -> PickPlaceScenario:
    """Compile independently selected P05 values into one valid scenario."""
    required = {parameter.name for parameter in CORE_PICK_PLACE_REGISTRY.parameters}
    if values.keys() != required:
        raise ValueError("Scenario values must provide every P05 parameter exactly once")
    normalized = dict(values)
    ScenarioSampler._apply_required_correlation(normalized)
    half_extent = float(normalized["object_half_extent_m"])
    scenario = PickPlaceScenario(
        index=index,
        seed=seed,
        family=family,
        split=split,
        object_mass_kg=float(normalized["object_mass_kg"]),
        surface_friction=float(normalized["surface_friction"]),
        object_half_extent_m=half_extent,
        object_position=(
            float(normalized["object_x_m"]),
            float(normalized["object_y_m"]),
            half_extent,
        ),
        target_radius_m=float(normalized["target_radius_m"]),
        target_position=(float(normalized["target_x_m"]), float(normalized["target_y_m"]), 0.001),
        action_latency_steps=int(normalized["action_latency_steps"]),
        action_noise_fraction=float(normalized["action_noise_fraction"]),
        joint_encoder_bias_rad=float(normalized["joint_encoder_bias_rad"]),
        joint_encoder_noise_rad=float(normalized["joint_encoder_noise_rad"]),
        object_state_noise_m=float(normalized["object_state_noise_m"]),
        frame_delay_steps=int(normalized["frame_delay_steps"]),
        observation_dropout_probability=float(normalized["observation_dropout_probability"]),
        vertical_gravity_scale=float(normalized["vertical_gravity_scale"]),
    )
    validation = validate_scenario(scenario)
    if not validation.valid:
        raise ValueError(f"Randomization produced an invalid scenario: {validation.reasons}")
    return scenario
