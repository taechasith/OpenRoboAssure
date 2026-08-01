"""P09 preregistration contract tests."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from analysis.statistical_plan import bootstrap_mean_ci, holm_adjust, lower_tail_cvar, success_rate
from openroboassure.benchmark.preregistration import (
    P09_BENCHMARK_ID,
    P09_METHODS,
    P09_TRAINING_SEEDS,
    assert_public_commitment,
    build_p09_evaluation_scenarios,
    build_public_commitment,
)


def test_p09_hidden_commitment_does_not_expose_catalogue_values() -> None:
    package = {
        "benchmark_id": P09_BENCHMARK_ID,
        "schema_version": 1,
        "evaluation_root_seed": 20260901,
        "hidden_catalogue_salt": "fixture-hidden-salt",
    }

    commitment = build_public_commitment(package, scenario_count=18)

    assert commitment["benchmark_id"] == P09_BENCHMARK_ID
    assert commitment["hidden_material_status"] == "withheld_until_results_freeze"
    commitments = commitment["commitments"]
    assert isinstance(commitments, dict)
    assert set(commitments) == {
        "hidden_seed_package_sha256",
        "evaluation_scenario_set_sha256",
        "evaluation_parameter_set_sha256",
        "hidden_failure_catalogue_sha256",
    }
    serialized = yaml.safe_dump(commitment)
    assert "fixture-hidden-salt" not in serialized
    assert "evaluation_root_seed" not in serialized
    assert "hidden_labels:" not in serialized
    assert "scenario_hash:" not in serialized


def test_p09_evaluation_catalogue_is_deterministic_and_unique() -> None:
    first = build_p09_evaluation_scenarios(24, root_seed=20260901)
    second = build_p09_evaluation_scenarios(24, root_seed=20260901)

    assert first == second
    assert len({scenario.scenario_hash for scenario in first}) == 24


def test_public_commitment_rejects_hidden_fields() -> None:
    with pytest.raises(ValueError, match="scenario_hash"):
        assert_public_commitment({"scenario_hash": "abc"})


def test_p09_manifest_is_conservative_and_preregistered() -> None:
    manifest_path = Path("experiments/preregistered/ORA-BENCH-001.yaml")
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))

    assert manifest["benchmark_id"] == P09_BENCHMARK_ID
    assert manifest["gate"] == "GATE-P09-PREREGISTRATION"
    assert manifest["status"] == "preregistered_pending_full_evaluation"
    assert manifest["scope"]["robots"] == ["ORA-4A"]
    assert manifest["scope"]["tasks"] == ["pick_place_v1"]
    assert manifest["methods"]["included"] == list(P09_METHODS)
    assert manifest["training"]["seeds"] == list(P09_TRAINING_SEEDS)
    assert manifest["evaluation"]["hidden_scenarios_per_robot_task"] == 10_000
    assert manifest["evaluation"]["total_scheduled_evaluations"] == 250_000
    assert manifest["integrity"]["full_evaluation_results_exist_before_approval"] is False


def test_frozen_statistical_plan_helpers_are_deterministic() -> None:
    assert success_rate([True, False, 1, 0]) == 0.5
    assert bootstrap_mean_ci([0.0, 1.0, 1.0], iterations=200, seed=1) == bootstrap_mean_ci(
        [0.0, 1.0, 1.0], iterations=200, seed=1
    )
    assert holm_adjust({"a": 0.01, "b": 0.04, "c": 0.03}) == {
        "a": 0.03,
        "b": 0.06,
        "c": 0.06,
    }
    assert lower_tail_cvar([0.2, 0.8, 0.4, 0.1], alpha=0.5) == 0.15000000000000002
