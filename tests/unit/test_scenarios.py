from __future__ import annotations

import json
from pathlib import Path

import pytest

from openroboassure.scenarios.compiler import SamplingMethod, ScenarioCompiler
from openroboassure.scenarios.experiment import run_scenario_validity
from openroboassure.scenarios.models import ScenarioFamily, ScenarioSplit
from openroboassure.scenarios.validation import validate_scenario


def test_latin_hypercube_population_is_valid_deterministic_and_deduplicated() -> None:
    compiler = ScenarioCompiler()
    first = list(
        compiler.generate(
            64,
            root_seed=81,
            family=ScenarioFamily.S1_IN_DISTRIBUTION,
            split=ScenarioSplit.TRAIN,
        )
    )
    second = list(
        compiler.generate(
            64,
            root_seed=81,
            family=ScenarioFamily.S1_IN_DISTRIBUTION,
            split=ScenarioSplit.TRAIN,
        )
    )

    assert first == second
    assert all(validate_scenario(scenario).valid for scenario in first)
    assert len({scenario.object_mass_kg for scenario in first}) == len(first)
    assert ScenarioCompiler.deduplicate([first[0], first[0], first[1]]) == first[:2]


def test_halton_sampling_and_each_family_compile_to_valid_scenarios() -> None:
    compiler = ScenarioCompiler()

    halton = compiler.compile_one(
        2,
        population_size=16,
        root_seed=17,
        method=SamplingMethod.HALTON,
        split=ScenarioSplit.EVALUATION,
    )
    assert validate_scenario(halton).valid
    for family in ScenarioFamily:
        scenario = compiler.compile_one(
            3,
            population_size=16,
            root_seed=17,
            family=family,
            split=ScenarioSplit.EVALUATION,
        )
        assert validate_scenario(scenario).valid


def test_train_and_evaluation_parameter_hashes_are_disjoint() -> None:
    compiler = ScenarioCompiler()
    training = list(compiler.generate(128, root_seed=101, split=ScenarioSplit.TRAIN))
    evaluation = list(compiler.generate(128, root_seed=101, split=ScenarioSplit.EVALUATION))

    ScenarioCompiler.assert_split_disjoint(training, evaluation)
    with pytest.raises(ValueError, match="leakage"):
        ScenarioCompiler.assert_split_disjoint(training, training)


def test_validity_experiment_writes_machine_readable_report(tmp_path: Path) -> None:
    output = tmp_path / "EXP-SCENARIO-VALIDITY-001.json"

    report = run_scenario_validity(128, output, root_seed=91, execution_samples=8)

    saved = json.loads(output.read_text(encoding="utf-8"))
    assert report["generated_scenarios"] == 128
    assert report["valid_rate"] == 1.0
    assert saved["simulator_execution"]["execution_rate"] == 1.0
    assert saved["train_evaluation_parameter_hash_overlap"] == 0
