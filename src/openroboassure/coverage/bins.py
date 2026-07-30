"""One-way and pairwise scenario coverage bins."""

from __future__ import annotations

from itertools import combinations

from openroboassure.scenarios.models import PickPlaceScenario, ScenarioFamily, ScenarioSplit
from openroboassure.scenarios.ontology import (
    CORE_PICK_PLACE_REGISTRY,
    ParameterKind,
    ParameterSpec,
)
from openroboassure.scenarios.parameters import scenario_parameter_values
from openroboassure.training.randomization import scenario_from_parameter_values

DEFAULT_CONTINUOUS_BINS = 4


def summarize_coverage(
    scenarios: list[PickPlaceScenario],
    *,
    continuous_bins: int = DEFAULT_CONTINUOUS_BINS,
    max_gap_queue: int = 24,
) -> dict[str, object]:
    """Summarize one-way, pairwise, and scenario-family coverage."""
    if continuous_bins <= 0:
        raise ValueError("continuous_bins must be positive")
    if not scenarios:
        raise ValueError("At least one scenario is required for coverage")
    one_way_seen: dict[str, set[int]] = {
        parameter.name: set() for parameter in CORE_PICK_PLACE_REGISTRY.parameters
    }
    pairwise_seen: dict[tuple[str, str], set[tuple[int, int]]] = {
        (left.name, right.name): set()
        for left, right in combinations(CORE_PICK_PLACE_REGISTRY.parameters, 2)
    }
    family_seen = {family.value: 0 for family in ScenarioFamily}
    for scenario in scenarios:
        values = scenario_parameter_values(scenario)
        bins = {
            parameter.name: parameter_bin(parameter, values[parameter.name], continuous_bins)
            for parameter in CORE_PICK_PLACE_REGISTRY.parameters
        }
        for name, bin_index in bins.items():
            one_way_seen[name].add(bin_index)
        for left, right in combinations(CORE_PICK_PLACE_REGISTRY.parameters, 2):
            pairwise_seen[(left.name, right.name)].add((bins[left.name], bins[right.name]))
        family_seen[scenario.family.value] += 1
    one_way_rows = [
        _one_way_row(parameter, one_way_seen[parameter.name], continuous_bins)
        for parameter in CORE_PICK_PLACE_REGISTRY.parameters
    ]
    pairwise_rows = [
        _pairwise_row(left, right, seen, continuous_bins)
        for (left_name, right_name), seen in sorted(pairwise_seen.items())
        for left in [CORE_PICK_PLACE_REGISTRY.parameter(left_name)]
        for right in [CORE_PICK_PLACE_REGISTRY.parameter(right_name)]
    ]
    family_rows = [
        {
            "family": family,
            "scenario_count": count,
            "covered": count > 0,
        }
        for family, count in sorted(family_seen.items())
    ]
    one_way_score = _ratio_sum(one_way_rows, "covered_bins", "total_bins")
    pairwise_score = _ratio_sum(pairwise_rows, "covered_interactions", "total_interactions")
    family_score = sum(1 for count in family_seen.values() if count > 0) / len(family_seen)
    gap_queue = _gap_queue(one_way_rows, pairwise_rows, max_gap_queue)
    return {
        "scenario_count": len(scenarios),
        "continuous_bins": continuous_bins,
        "one_way_parameter_coverage": one_way_rows,
        "pairwise_interaction_coverage": pairwise_rows,
        "scenario_family_coverage": family_rows,
        "coverage_scores": {
            "one_way": one_way_score,
            "pairwise": pairwise_score,
            "scenario_family": family_score,
            "combined": (one_way_score + pairwise_score + family_score) / 3.0,
        },
        "coverage_gap_queue": gap_queue,
    }


def parameter_bin(parameter: ParameterSpec, value: float, continuous_bins: int) -> int:
    """Map one approved parameter value to a stable coverage bin."""
    low, high = parameter.global_bounds
    if parameter.kind is ParameterKind.DISCRETE:
        return int(max(low, min(high, round(value))) - low)
    unit = (value - low) / (high - low)
    return min(continuous_bins - 1, max(0, int(unit * continuous_bins)))


def generate_gap_targeted_scenarios(
    gap_queue: list[dict[str, object]],
    *,
    limit: int = 8,
    seed: int = 20260730,
    continuous_bins: int = DEFAULT_CONTINUOUS_BINS,
) -> list[PickPlaceScenario]:
    """Generate valid scenarios that target the highest-priority coverage gaps."""
    scenarios: list[PickPlaceScenario] = []
    for index, gap in enumerate(gap_queue[:limit]):
        values = _nominal_values()
        parameters = gap["parameters"]
        bins = gap["bins"]
        if not isinstance(parameters, list) or not isinstance(bins, list):
            raise TypeError("Coverage gap parameters and bins must be lists")
        for raw_name, raw_bin in zip(parameters, bins, strict=True):
            name = str(raw_name)
            values[name] = _value_for_bin(
                CORE_PICK_PLACE_REGISTRY.parameter(name),
                int(raw_bin),
                continuous_bins,
            )
        scenarios.append(
            scenario_from_parameter_values(
                values,
                index=index,
                seed=seed + index,
                family=ScenarioFamily.S5_ADVERSARIAL,
                split=ScenarioSplit.TRAIN,
            )
        )
    return scenarios


def _one_way_row(
    parameter: ParameterSpec, seen: set[int], continuous_bins: int
) -> dict[str, object]:
    total = _total_bins(parameter, continuous_bins)
    missing = [index for index in range(total) if index not in seen]
    return {
        "parameter": parameter.name,
        "category": parameter.category,
        "covered_bins": len(seen),
        "total_bins": total,
        "coverage": len(seen) / total,
        "missing_bins": missing,
    }


def _pairwise_row(
    left: ParameterSpec, right: ParameterSpec, seen: set[tuple[int, int]], continuous_bins: int
) -> dict[str, object]:
    left_total = _total_bins(left, continuous_bins)
    right_total = _total_bins(right, continuous_bins)
    total = left_total * right_total
    missing: list[list[int]] = []
    for left_index in range(left_total):
        for right_index in range(right_total):
            if (left_index, right_index) not in seen and len(missing) < 8:
                missing.append([left_index, right_index])
    return {
        "parameters": [left.name, right.name],
        "categories": [left.category, right.category],
        "covered_interactions": len(seen),
        "total_interactions": total,
        "coverage": len(seen) / total,
        "sample_missing_bins": missing,
    }


def _gap_queue(
    one_way_rows: list[dict[str, object]],
    pairwise_rows: list[dict[str, object]],
    limit: int,
) -> list[dict[str, object]]:
    gaps: list[dict[str, object]] = []
    for row in one_way_rows:
        missing = row["missing_bins"]
        if not isinstance(missing, list):
            raise TypeError("One-way missing bins must be a list")
        for raw_bin_index in missing:
            if not isinstance(raw_bin_index, int):
                raise TypeError("One-way missing bin must be an integer")
            coverage = _as_float(row["coverage"])
            gaps.append(
                {
                    "gap_id": f"one_way:{row['parameter']}:bin_{raw_bin_index}",
                    "kind": "one_way",
                    "parameters": [str(row["parameter"])],
                    "bins": [raw_bin_index],
                    "priority": 1.0 - coverage,
                }
            )
    for row in pairwise_rows:
        missing = row["sample_missing_bins"]
        parameters = row["parameters"]
        if not isinstance(missing, list) or not isinstance(parameters, list):
            raise TypeError("Pairwise missing bins and parameters must be lists")
        for pair in missing[:2]:
            if (
                not isinstance(pair, list)
                or len(pair) != 2
                or not all(isinstance(value, int) for value in pair)
            ):
                raise TypeError("Pairwise missing bin must be a two-item list")
            left_bin, right_bin = pair
            coverage = _as_float(row["coverage"])
            gaps.append(
                {
                    "gap_id": (
                        f"pairwise:{parameters[0]}:bin_{left_bin}__{parameters[1]}:bin_{right_bin}"
                    ),
                    "kind": "pairwise",
                    "parameters": [str(parameters[0]), str(parameters[1])],
                    "bins": [left_bin, right_bin],
                    "priority": 1.0 - coverage,
                }
            )
    return sorted(gaps, key=lambda item: _as_float(item["priority"]), reverse=True)[:limit]


def _value_for_bin(parameter: ParameterSpec, bin_index: int, continuous_bins: int) -> float:
    low, high = parameter.global_bounds
    if parameter.kind is ParameterKind.DISCRETE:
        return float(low + bin_index)
    width = (high - low) / continuous_bins
    return low + (bin_index + 0.5) * width


def _total_bins(parameter: ParameterSpec, continuous_bins: int) -> int:
    if parameter.kind is ParameterKind.DISCRETE:
        low, high = parameter.global_bounds
        return int(high - low + 1)
    return continuous_bins


def _ratio_sum(rows: list[dict[str, object]], covered_key: str, total_key: str) -> float:
    covered = sum(_as_int(row[covered_key]) for row in rows)
    total = sum(_as_int(row[total_key]) for row in rows)
    return covered / total


def _nominal_values() -> dict[str, float]:
    return {parameter.name: parameter.nominal for parameter in CORE_PICK_PLACE_REGISTRY.parameters}


def _as_float(value: object) -> float:
    if isinstance(value, int | float):
        return float(value)
    raise TypeError(f"Expected numeric value, received {type(value).__name__}")


def _as_int(value: object) -> int:
    if isinstance(value, int):
        return value
    raise TypeError(f"Expected integer value, received {type(value).__name__}")
