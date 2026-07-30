"""P07 calibration, falsification, coverage, and loop contract tests."""

from __future__ import annotations

from pathlib import Path

from openroboassure.calibration.hidden_target import run_hidden_target_calibration
from openroboassure.coverage.reports import run_coverage_report
from openroboassure.falsification.replay import replay_counterexamples
from openroboassure.falsification.search import run_falsification_search


def test_hidden_target_calibration_freezes_predictions_before_reveal(tmp_path: Path) -> None:
    output = tmp_path / "calibration.json"

    report = run_hidden_target_calibration(output, candidate_count=12)

    target_handling = report["target_handling"]
    discrepancy = report["discrepancy"]
    assert isinstance(target_handling, dict)
    assert isinstance(discrepancy, dict)
    assert target_handling["hidden_values_available_to_method"] is False
    assert len(str(target_handling["prediction_freeze_hash"])) == 64
    assert "true_hidden_parameters_after_freeze" in report
    assert discrepancy["status"] in {"improved", "negative_result_preserved"}
    assert output.exists()


def test_falsification_preserves_and_replays_counterexamples(tmp_path: Path) -> None:
    search_output = tmp_path / "counterexamples" / "search.json"
    replay_output = tmp_path / "counterexamples" / "replay.json"

    search_report = run_falsification_search(search_output, trials=4)
    counterexamples = search_report["counterexamples"]
    assert isinstance(counterexamples, list)
    counterexample_count = search_report["counterexample_count"]
    assert isinstance(counterexample_count, int)
    assert counterexample_count >= 1
    assert (search_output.parent / "CE-000001.json").exists()

    replay_report = replay_counterexamples(counterexamples[:1], replay_output, seeds=(1, 2))

    assert replay_report["counterexample_count"] == 1
    assert replay_report["replay_count"] == 2
    assert replay_output.exists()


def test_coverage_report_measures_gaps_and_targets_them(tmp_path: Path) -> None:
    output = tmp_path / "coverage.json"

    report = run_coverage_report(output, scenario_count=16)

    summary = report["summary"]
    assert isinstance(summary, dict)
    scores = summary["coverage_scores"]
    gap_queue = summary["coverage_gap_queue"]
    assert isinstance(scores, dict)
    assert isinstance(gap_queue, list)
    combined = scores["combined"]
    gap_targeted = report["gap_targeted_scenarios"]
    assert isinstance(combined, float)
    assert isinstance(gap_targeted, list)
    assert 0.0 < combined <= 1.0
    assert len(gap_targeted) > 0
    assert output.exists()
