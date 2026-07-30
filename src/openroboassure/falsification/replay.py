"""Counterexample replay across deterministic seeds."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from openroboassure.falsification.search import evaluate_scenario, failure_predicates
from openroboassure.scenarios.models import ScenarioFamily, ScenarioSplit
from openroboassure.training.randomization import scenario_from_parameter_values

REPLAY_SEEDS = (101, 202, 303)


def replay_search_report(input_report: Path, output: Path) -> dict[str, object]:
    """Replay counterexamples from a saved falsification search report."""
    payload = json.loads(input_report.read_text(encoding="utf-8"))
    counterexamples = payload.get("counterexamples")
    if not isinstance(counterexamples, list):
        raise ValueError("Falsification report is missing a counterexamples list")
    return replay_counterexamples(counterexamples, output)


def replay_counterexamples(
    counterexamples: list[object],
    output: Path,
    *,
    seeds: tuple[int, ...] = REPLAY_SEEDS,
) -> dict[str, object]:
    """Replay preserved counterexamples under new seeds without hiding failures."""
    rows: list[dict[str, object]] = []
    for counterexample in counterexamples:
        if not isinstance(counterexample, dict):
            raise TypeError("Counterexample record must be a mapping")
        counterexample_id = str(counterexample["counterexample_id"])
        values = _parameter_values(counterexample["parameter_values"])
        for index, seed in enumerate(seeds):
            scenario = scenario_from_parameter_values(
                values,
                index=index,
                seed=seed,
                family=ScenarioFamily.S5_ADVERSARIAL,
                split=ScenarioSplit.EVALUATION,
            )
            outcome = evaluate_scenario(scenario)
            predicates = failure_predicates(outcome)
            rows.append(
                {
                    "counterexample_id": counterexample_id,
                    "seed": seed,
                    "scenario_hash": scenario.scenario_hash,
                    "predicate_hits": list(predicates),
                    "outcome": outcome.to_dict(),
                }
            )
    failures = sum(1 for row in rows if row["predicate_hits"])
    report: dict[str, object] = {
        "experiment_id": "EXP-FALSIFICATION-REPLAY-001",
        "scope": "P07 replay of preserved counterexamples across deterministic seeds",
        "counterexample_count": len(counterexamples),
        "replay_seeds": list(seeds),
        "replay_count": len(rows),
        "replayed_failure_rate": failures / len(rows) if rows else 0.0,
        "rows": rows,
        "report_hash": "",
    }
    report["report_hash"] = _hash_mapping(report)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def _parameter_values(payload: object) -> dict[str, float]:
    if not isinstance(payload, dict):
        raise TypeError("Counterexample parameter_values must be a mapping")
    values: dict[str, float] = {}
    for key, value in payload.items():
        if not isinstance(key, str) or not isinstance(value, int | float):
            raise TypeError("Counterexample parameter values must be numeric")
        values[key] = float(value)
    return values


def _hash_mapping(value: dict[str, object]) -> str:
    text = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
