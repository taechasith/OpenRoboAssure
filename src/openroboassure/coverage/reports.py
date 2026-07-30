"""Coverage report generation for P07."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from openroboassure.coverage.bins import generate_gap_targeted_scenarios, summarize_coverage
from openroboassure.scenarios.compiler import ScenarioCompiler
from openroboassure.scenarios.models import PickPlaceScenario, ScenarioFamily, ScenarioSplit
from openroboassure.training.randomization import scenario_from_parameter_values


def run_coverage_report(
    output: Path,
    *,
    scenario_count: int = 128,
    seed: int = 20260730,
    counterexamples_path: Path | None = None,
) -> dict[str, object]:
    """Generate the P07 scenario coverage report and gap queue."""
    if scenario_count < len(ScenarioFamily):
        raise ValueError("scenario_count must cover each declared scenario family at least once")
    scenarios = _default_population(scenario_count, seed)
    counterexample_scenarios = (
        _counterexample_scenarios(counterexamples_path) if counterexamples_path is not None else []
    )
    scenarios = ScenarioCompiler.deduplicate([*scenarios, *counterexample_scenarios])
    summary = summarize_coverage(scenarios)
    gap_queue = summary["coverage_gap_queue"]
    if not isinstance(gap_queue, list) or not all(isinstance(item, dict) for item in gap_queue):
        raise TypeError("Coverage gap queue is malformed")
    gap_scenarios = generate_gap_targeted_scenarios(gap_queue)
    report: dict[str, object] = {
        "experiment_id": "EXP-COVERAGE-001",
        "scope": "P07 one-way parameter-bin, pairwise interaction, and family coverage",
        "base_scenario_count": scenario_count,
        "counterexample_scenario_count": len(counterexample_scenarios),
        "deduplicated_scenario_count": len(scenarios),
        "summary": summary,
        "gap_targeted_scenarios": [scenario.to_dict() for scenario in gap_scenarios],
        "report_hash": "",
    }
    report["report_hash"] = _hash_mapping(report)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def _default_population(count: int, seed: int) -> list[PickPlaceScenario]:
    compiler = ScenarioCompiler()
    families = tuple(ScenarioFamily)
    per_family = count // len(families)
    remainder = count % len(families)
    scenarios: list[PickPlaceScenario] = []
    for family_index, family in enumerate(families):
        family_count = per_family + int(family_index < remainder)
        scenarios.extend(
            compiler.generate(
                family_count,
                root_seed=seed + family_index,
                family=family,
                split=ScenarioSplit.TRAIN,
            )
        )
    return scenarios


def _counterexample_scenarios(path: Path) -> list[PickPlaceScenario]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    raw_counterexamples = payload.get("counterexamples")
    if not isinstance(raw_counterexamples, list):
        raise ValueError("Counterexample report is missing counterexamples")
    scenarios: list[PickPlaceScenario] = []
    for index, counterexample in enumerate(raw_counterexamples):
        if not isinstance(counterexample, dict):
            raise TypeError("Counterexample entry must be a mapping")
        raw_values = counterexample.get("parameter_values")
        if not isinstance(raw_values, dict):
            raise TypeError("Counterexample parameter_values must be a mapping")
        values = {
            str(key): float(value)
            for key, value in raw_values.items()
            if isinstance(value, int | float)
        }
        scenarios.append(
            scenario_from_parameter_values(
                values,
                index=index,
                seed=20260730 + index,
                family=ScenarioFamily.S5_ADVERSARIAL,
                split=ScenarioSplit.TRAIN,
            )
        )
    return scenarios


def _hash_mapping(value: dict[str, object]) -> str:
    text = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
