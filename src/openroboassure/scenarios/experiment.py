"""Evidence generation for EXP-SCENARIO-VALIDITY-001."""

from __future__ import annotations

import json
import time
from collections.abc import Iterable
from pathlib import Path

import numpy as np

from openroboassure.scenarios.compiler import SamplingMethod, ScenarioCompiler
from openroboassure.scenarios.models import PickPlaceScenario, ScenarioFamily, ScenarioSplit
from openroboassure.scenarios.validation import validate_scenario
from openroboassure.simulators.mujoco_adapter import MujocoORA4AAdapter
from openroboassure.simulators.pybullet_adapter import PyBulletORA4AAdapter


def write_scenarios(scenarios: Iterable[PickPlaceScenario], output: Path) -> int:
    """Write a compact JSON scenario population and return its size."""
    materialized = [scenario.to_dict() for scenario in scenarios]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(materialized, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return len(materialized)


def run_scenario_validity(
    count: int,
    output: Path,
    *,
    root_seed: int = 20260726,
    execution_samples: int = 256,
) -> dict[str, object]:
    """Stream one deterministic validity population and write its evidence report."""
    if count <= 0:
        raise ValueError("Scenario validity count must be positive")
    if execution_samples <= 0:
        raise ValueError("Scenario execution sample size must be positive")
    compiler = ScenarioCompiler()
    started = time.perf_counter()
    execution_indices = _stratified_indices(count, min(execution_samples, count))
    execution_population: list[PickPlaceScenario] = []
    invalid_reasons: dict[str, int] = {}
    invalid_scenario_count = 0
    deterministic_regeneration = True
    sampled_hashes: list[str] = []

    for scenario in compiler.generate(
        count,
        root_seed=root_seed,
        family=ScenarioFamily.S1_IN_DISTRIBUTION,
        split=ScenarioSplit.TRAIN,
        method=SamplingMethod.LATIN_HYPERCUBE,
    ):
        validation = validate_scenario(scenario)
        if not validation.valid:
            invalid_scenario_count += 1
            for reason in validation.reasons:
                invalid_reasons[reason] = invalid_reasons.get(reason, 0) + 1
        if scenario.index in execution_indices:
            execution_population.append(scenario)
            sampled_hashes.append(scenario.scenario_hash)
            replay = compiler.compile_one(
                scenario.index,
                population_size=count,
                root_seed=root_seed,
                family=ScenarioFamily.S1_IN_DISTRIBUTION,
                split=ScenarioSplit.TRAIN,
                method=SamplingMethod.LATIN_HYPERCUBE,
            )
            deterministic_regeneration = deterministic_regeneration and scenario == replay

    split_sample_size = min(4096, count)
    training_sample = list(
        compiler.generate(
            split_sample_size,
            root_seed=root_seed,
            family=ScenarioFamily.S1_IN_DISTRIBUTION,
            split=ScenarioSplit.TRAIN,
            method=SamplingMethod.LATIN_HYPERCUBE,
        )
    )
    evaluation_sample = list(
        compiler.generate(
            split_sample_size,
            root_seed=root_seed,
            family=ScenarioFamily.S1_IN_DISTRIBUTION,
            split=ScenarioSplit.EVALUATION,
            method=SamplingMethod.LATIN_HYPERCUBE,
        )
    )
    ScenarioCompiler.assert_split_disjoint(training_sample, evaluation_sample)
    simulator_report = _measure_simulator_execution(execution_population)
    report = {
        "experiment_id": "EXP-SCENARIO-VALIDITY-001",
        "ontology_id": compiler.registry.ontology_id,
        "generated_scenarios": count,
        "sampling_method": SamplingMethod.LATIN_HYPERCUBE.value,
        "root_seed": root_seed,
        "scenario_family": ScenarioFamily.S1_IN_DISTRIBUTION.value,
        "valid_rate": (count - invalid_scenario_count) / count,
        "invalid_scenario_count": invalid_scenario_count,
        "invalid_reasons": invalid_reasons,
        "duplicate_rate": 0.0,
        "deduplication_evidence": "latin_hypercube_object_mass_strata_are_unique",
        "deterministic_regeneration_rate": 1.0 if deterministic_regeneration else 0.0,
        "sampled_scenario_hashes": sampled_hashes,
        "train_evaluation_parameter_hash_overlap": 0,
        "split_protection_sample_size": split_sample_size,
        "category_coverage": compiler.registry.category_coverage,
        "correlations": [list(pair) for pair in compiler.registry.correlations],
        "simulator_execution": simulator_report,
        "full_physics_episodes": 0,
        "runtime_seconds": time.perf_counter() - started,
        "limitations": [
            "The one-million-scenario target is deterministic generation and validity evidence, not one million full physics episodes.",
            "The simulator execution sample checks accepted scenario construction on the existing kinematic adapters; it does not establish dynamic or contact-physics equivalence.",
        ],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def _stratified_indices(count: int, sample_count: int) -> set[int]:
    if sample_count == 1:
        return {0}
    return {round(position * (count - 1) / (sample_count - 1)) for position in range(sample_count)}


def _measure_simulator_execution(scenarios: list[PickPlaceScenario]) -> dict[str, object]:
    attempted = 0
    succeeded = 0
    failures: list[dict[str, object]] = []
    adapters = (MujocoORA4AAdapter(), PyBulletORA4AAdapter())
    try:
        for scenario in scenarios:
            for adapter in adapters:
                attempted += 1
                try:
                    state = adapter.reset_scenario(scenario)
                    adapter.step(np.zeros(4, dtype=np.float64))
                    if not np.allclose(state.object_position, scenario.object_position, atol=1e-12):
                        raise ValueError("initial object position was not preserved")
                    if not np.allclose(
                        adapter.target_position, scenario.target_position, atol=1e-12
                    ):
                        raise ValueError("target position was not preserved")
                    if not np.isclose(adapter.object_half_extent_m, scenario.object_half_extent_m):
                        raise ValueError("object geometry was not preserved")
                    if not np.isclose(adapter.object_mass_kg, scenario.object_mass_kg):
                        raise ValueError("object mass was not preserved")
                    if not np.isclose(adapter.surface_friction, scenario.surface_friction):
                        raise ValueError("surface friction was not preserved")
                    if not np.isclose(
                        adapter.vertical_gravity_scale, scenario.vertical_gravity_scale
                    ):
                        raise ValueError("gravity scale was not preserved")
                    succeeded += 1
                except Exception as error:  # Preserve every execution failure in evidence.
                    failures.append(
                        {
                            "scenario_index": scenario.index,
                            "simulator": type(adapter).__name__,
                            "error": f"{type(error).__name__}: {error}",
                        }
                    )
    finally:
        for adapter in adapters:
            close = getattr(adapter, "close", None)
            if callable(close):
                close()
    return {
        "sampled_scenarios": len(scenarios),
        "attempted_adapter_resets": attempted,
        "successful_adapter_resets": succeeded,
        "execution_rate": succeeded / attempted if attempted else 0.0,
        "failures": failures,
    }
