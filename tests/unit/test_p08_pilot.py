"""P08 conservative pilot benchmark contract tests."""

from __future__ import annotations

from pathlib import Path

from openroboassure.benchmark.pilot import (
    P08_METHODS,
    P08_SEEDS,
    build_hidden_catalogue,
    build_pilot_evaluation_scenarios,
    run_pilot_benchmark,
)


def test_pilot_evaluation_catalogue_is_frozen_and_labelled() -> None:
    first = build_pilot_evaluation_scenarios(12, root_seed=20260801)
    second = build_pilot_evaluation_scenarios(12, root_seed=20260801)

    assert first == second
    assert len({scenario.scenario_hash for scenario in first}) == 12

    hidden = build_hidden_catalogue(first)

    assert len(hidden) == 12
    assert all("hidden_labels" in entry for entry in hidden)


def test_small_pilot_runs_all_methods_and_classifies_outcomes(tmp_path: Path) -> None:
    report = run_pilot_benchmark(
        tmp_path,
        training_steps=4,
        evaluation_scenarios_per_config=6,
        protected_ref="HEAD",
    )

    acceptance = report["operational_acceptance"]
    preregistration = report["preregistration"]
    assert isinstance(acceptance, dict)
    assert isinstance(preregistration, dict)
    assert preregistration["total_scheduled_evaluations"] == len(P08_METHODS) * len(P08_SEEDS) * 6
    assert acceptance["classified_job_rate"] == 1.0
    assert "hidden_catalogue_after_freeze" in report
    assert (tmp_path / "benchmarks" / "ORA-PILOT-001.json").exists()
