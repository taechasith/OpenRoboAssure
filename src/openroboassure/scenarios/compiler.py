"""Deterministic constrained sampling and scenario compilation."""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from enum import StrEnum
from functools import cache
from math import gcd, sqrt

from openroboassure.scenarios.models import PickPlaceScenario, ScenarioFamily, ScenarioSplit
from openroboassure.scenarios.ontology import (
    CORE_PICK_PLACE_REGISTRY,
    ParameterKind,
    ParameterSpec,
    UncertaintyRegistry,
)
from openroboassure.scenarios.validation import validate_scenario

_MASK_64 = (1 << 64) - 1
_UNIT_DENOMINATOR = float(1 << 53)
_HALTON_BASES = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53)


class SamplingMethod(StrEnum):
    """Supported reproducible sampling methods."""

    LATIN_HYPERCUBE = "latin_hypercube"
    HALTON = "halton"


class ScenarioCompiler:
    """Compile human-approved uncertainty values into valid task scenarios."""

    def __init__(self, registry: UncertaintyRegistry = CORE_PICK_PLACE_REGISTRY) -> None:
        self.registry = registry

    def compile_one(
        self,
        index: int,
        *,
        population_size: int,
        root_seed: int,
        family: ScenarioFamily = ScenarioFamily.S1_IN_DISTRIBUTION,
        split: ScenarioSplit = ScenarioSplit.TRAIN,
        method: SamplingMethod = SamplingMethod.LATIN_HYPERCUBE,
    ) -> PickPlaceScenario:
        """Compile one stable scenario at a known position in a sample population."""
        if index < 0:
            raise ValueError("Scenario index must be non-negative")
        if population_size <= 0:
            raise ValueError("Scenario population_size must be positive")
        if index >= population_size:
            raise ValueError("Scenario index must be smaller than population_size")

        values = {
            parameter.name: self._sample_parameter(
                parameter, index, population_size, root_seed, family, split, method
            )
            for parameter in self.registry.parameters
        }
        self._apply_family_overrides(
            values, index, population_size, root_seed, family, split, method
        )
        self._apply_correlations(values)
        half_extent = float(values["object_half_extent_m"])
        scenario = PickPlaceScenario(
            index=index,
            seed=_scenario_seed(root_seed, index, split),
            family=family,
            split=split,
            object_mass_kg=float(values["object_mass_kg"]),
            surface_friction=float(values["surface_friction"]),
            object_half_extent_m=half_extent,
            object_position=(
                float(values["object_x_m"]),
                float(values["object_y_m"]),
                half_extent,
            ),
            target_radius_m=float(values["target_radius_m"]),
            target_position=(
                float(values["target_x_m"]),
                float(values["target_y_m"]),
                0.001,
            ),
            action_latency_steps=int(values["action_latency_steps"]),
            action_noise_fraction=float(values["action_noise_fraction"]),
            joint_encoder_bias_rad=float(values["joint_encoder_bias_rad"]),
            joint_encoder_noise_rad=float(values["joint_encoder_noise_rad"]),
            object_state_noise_m=float(values["object_state_noise_m"]),
            frame_delay_steps=int(values["frame_delay_steps"]),
            observation_dropout_probability=float(values["observation_dropout_probability"]),
            vertical_gravity_scale=float(values["vertical_gravity_scale"]),
        )
        validation = validate_scenario(scenario)
        if not validation.valid:
            raise ValueError(f"Compiler produced invalid scenario: {', '.join(validation.reasons)}")
        return scenario

    def generate(
        self,
        count: int,
        *,
        root_seed: int,
        family: ScenarioFamily = ScenarioFamily.S1_IN_DISTRIBUTION,
        split: ScenarioSplit = ScenarioSplit.TRAIN,
        method: SamplingMethod = SamplingMethod.LATIN_HYPERCUBE,
    ) -> Iterator[PickPlaceScenario]:
        """Yield a streaming deterministic population without retaining it in memory."""
        if count <= 0:
            raise ValueError("Scenario count must be positive")
        for index in range(count):
            yield self.compile_one(
                index,
                population_size=count,
                root_seed=root_seed,
                family=family,
                split=split,
                method=method,
            )

    @staticmethod
    def deduplicate(scenarios: Iterable[PickPlaceScenario]) -> list[PickPlaceScenario]:
        """Remove repeated physical/task parameter configurations while preserving order."""
        unique: list[PickPlaceScenario] = []
        seen: set[str] = set()
        for scenario in scenarios:
            if scenario.parameter_hash not in seen:
                unique.append(scenario)
                seen.add(scenario.parameter_hash)
        return unique

    @staticmethod
    def assert_split_disjoint(
        training: Iterable[PickPlaceScenario], evaluation: Iterable[PickPlaceScenario]
    ) -> None:
        """Reject parameter reuse between training and evaluation partitions."""
        train_hashes = {scenario.parameter_hash for scenario in training}
        evaluation_hashes = {scenario.parameter_hash for scenario in evaluation}
        overlap = train_hashes & evaluation_hashes
        if overlap:
            raise ValueError(
                f"Training/evaluation scenario leakage detected: {len(overlap)} overlaps"
            )

    def _sample_parameter(
        self,
        parameter: ParameterSpec,
        index: int,
        population_size: int,
        root_seed: int,
        family: ScenarioFamily,
        split: ScenarioSplit,
        method: SamplingMethod,
    ) -> float:
        if family is ScenarioFamily.S0_NOMINAL:
            return parameter.nominal
        bounds = parameter.training_bounds
        if family is ScenarioFamily.S2_BOUNDARY:
            bounds = parameter.global_bounds
            unit = 0.005 if (index + _dimension_id(parameter.name)) % 2 == 0 else 0.995
        elif family is ScenarioFamily.S4_OUT_OF_DISTRIBUTION and self._is_ood_parameter(
            parameter.name, index
        ):
            bounds = parameter.global_bounds
            unit = 0.025 if index % 2 == 0 else 0.975
        else:
            unit = _sample_unit(
                index, population_size, root_seed, _dimension_id(parameter.name), split, method
            )
        return _scale(unit, bounds, parameter.kind)

    @staticmethod
    def _is_ood_parameter(name: str, index: int) -> bool:
        return _dimension_id(name) % 4 == index % 4

    def _apply_family_overrides(
        self,
        values: dict[str, float],
        index: int,
        population_size: int,
        root_seed: int,
        family: ScenarioFamily,
        split: ScenarioSplit,
        method: SamplingMethod,
    ) -> None:
        if family is ScenarioFamily.S3_UNSEEN_COMBINATIONS:
            values["object_mass_kg"] = _scale(
                0.80,
                self.registry.parameter("object_mass_kg").global_bounds,
                ParameterKind.CONTINUOUS,
            )
            values["surface_friction"] = _scale(
                0.20,
                self.registry.parameter("surface_friction").global_bounds,
                ParameterKind.CONTINUOUS,
            )
            values["action_latency_steps"] = 3 + index % 2
            values["object_x_m"] = _scale(
                0.15,
                self.registry.parameter("object_x_m").global_bounds,
                ParameterKind.CONTINUOUS,
            )
        elif family is ScenarioFamily.S6_FAULT_INJECTION:
            values["frame_delay_steps"] = 3 + index % 2
            values["observation_dropout_probability"] = _scale(
                _sample_unit(index, population_size, root_seed, 97, split, method),
                (0.05, 0.10),
                ParameterKind.CONTINUOUS,
            )
            values["action_latency_steps"] = 3 + index % 2

    def _apply_correlations(self, values: dict[str, float]) -> None:
        """Apply the approved size-to-target-clearance conditional correlation."""
        if ("object_half_extent_m", "target_radius_m") not in self.registry.correlations:
            return
        required_radius = sqrt(2.0) * values["object_half_extent_m"] + 0.010
        upper = self.registry.parameter("target_radius_m").global_bounds[1]
        values["target_radius_m"] = min(upper, max(values["target_radius_m"], required_radius))


def _scale(unit: float, bounds: tuple[float, float], kind: ParameterKind) -> float:
    low, high = bounds
    if kind is ParameterKind.DISCRETE:
        return float(int(low + min(int(unit * (int(high - low) + 1)), int(high - low))))
    return low + unit * (high - low)


def _sample_unit(
    index: int,
    population_size: int,
    root_seed: int,
    dimension: int,
    split: ScenarioSplit,
    method: SamplingMethod,
) -> float:
    if method is SamplingMethod.LATIN_HYPERCUBE:
        return _latin_hypercube_unit(index, population_size, root_seed, dimension, split)
    if method is SamplingMethod.HALTON:
        return _halton_unit(index, _split_namespace_seed(root_seed, split), dimension)
    raise ValueError(f"Unsupported scenario sampling method: {method}")


def _latin_hypercube_unit(
    index: int, count: int, root_seed: int, dimension: int, split: ScenarioSplit
) -> float:
    if count == 1:
        return 0.25 if split is ScenarioSplit.TRAIN else 0.75
    multiplier = _coprime_multiplier(count, root_seed, dimension)
    offset = _latin_offset(count, root_seed, dimension)
    stratum = (multiplier * index + offset) % count
    jitter = _unit_float(_mix64(root_seed ^ index ^ (dimension << 17)))
    subbin = 0 if split is ScenarioSplit.TRAIN else 1
    return (2 * stratum + subbin + jitter) / (2 * count)


@cache
def _coprime_multiplier(count: int, root_seed: int, dimension: int) -> int:
    candidate = int(_mix64(root_seed ^ (dimension << 24) ^ 0xD1B54A32D192ED03) % count) | 1
    while gcd(candidate, count) != 1:
        candidate = (candidate + 2) % count
        if candidate == 0:
            candidate = 1
    return candidate


@cache
def _latin_offset(count: int, root_seed: int, dimension: int) -> int:
    return int(_mix64(root_seed ^ (dimension << 32) ^ 0x9E3779B97F4A7C15) % count)


def _halton_unit(index: int, root_seed: int, dimension: int) -> float:
    value = index + 1 + int(_mix64(root_seed ^ dimension) % 10_000)
    base = _HALTON_BASES[dimension % len(_HALTON_BASES)]
    denominator = float(base)
    result = 0.0
    while value:
        value, remainder = divmod(value, base)
        result += remainder / denominator
        denominator *= base
    return result


def _scenario_seed(root_seed: int, index: int, split: ScenarioSplit) -> int:
    return int(
        _mix64(_split_namespace_seed(root_seed, split) ^ index ^ 0xA0761D6478BD642F)
        & ((1 << 63) - 1)
    )


def _split_namespace_seed(root_seed: int, split: ScenarioSplit) -> int:
    namespace = 0x6A09E667F3BCC909 if split is ScenarioSplit.TRAIN else 0xBB67AE8584CAA73B
    return _mix64(root_seed ^ namespace)


@cache
def _dimension_id(name: str) -> int:
    value = 0
    for character in name.encode("utf-8"):
        value = _mix64(value ^ character)
    return int(value & 0x7FFFFFFF)


def _unit_float(value: int) -> float:
    return float(value >> 11) / _UNIT_DENOMINATOR


def _mix64(value: int) -> int:
    value = (value + 0x9E3779B97F4A7C15) & _MASK_64
    value = ((value ^ (value >> 30)) * 0xBF58476D1CE4E5B9) & _MASK_64
    value = ((value ^ (value >> 27)) * 0x94D049BB133111EB) & _MASK_64
    return (value ^ (value >> 31)) & _MASK_64
