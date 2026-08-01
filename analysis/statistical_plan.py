"""Frozen P09 statistical analysis plan for ORA-BENCH-001."""

from __future__ import annotations

import random
from collections.abc import Mapping, Sequence

PLAN_ID = "ORA-BENCH-001-P09-STATISTICAL-PLAN"
PRIMARY_OUTCOME = "primary_held_out_task_success"
SECONDARY_OUTCOMES = (
    "drop_rate",
    "collision_rate",
    "mean_completion_steps",
    "fifth_percentile_scenario_family_success",
    "failure_discovery_rate",
)
PLANNED_METHODS = ("A", "B", "C", "D", "E")
PLANNED_PAIRWISE_COMPARISONS = (
    ("E", "A"),
    ("E", "B"),
    ("E", "C"),
    ("E", "D"),
    ("D", "A"),
    ("D", "B"),
    ("D", "C"),
)
BOOTSTRAP_ITERATIONS = 10_000
CONFIDENCE_LEVEL = 0.95
MULTIPLE_COMPARISON_CORRECTION = "holm"


def success_rate(outcomes: Sequence[bool | int | float]) -> float:
    """Calculate the preregistered binary success rate."""
    if not outcomes:
        raise ValueError("At least one outcome is required")
    normalized = [1.0 if bool(outcome) else 0.0 for outcome in outcomes]
    return sum(normalized) / len(normalized)


def bootstrap_mean_ci(
    values: Sequence[float],
    *,
    iterations: int = BOOTSTRAP_ITERATIONS,
    confidence_level: float = CONFIDENCE_LEVEL,
    seed: int = 20260901,
) -> tuple[float, float]:
    """Return a deterministic percentile bootstrap confidence interval for a mean."""
    if not values:
        raise ValueError("At least one value is required")
    if iterations <= 0:
        raise ValueError("Bootstrap iterations must be positive")
    if not 0.0 < confidence_level < 1.0:
        raise ValueError("Confidence level must be between 0 and 1")
    rng = random.Random(seed)
    n = len(values)
    means = []
    for _ in range(iterations):
        sample = [values[rng.randrange(n)] for _ in range(n)]
        means.append(sum(sample) / n)
    means.sort()
    alpha = 1.0 - confidence_level
    lower_index = max(0, int((alpha / 2.0) * iterations))
    upper_index = min(iterations - 1, int((1.0 - alpha / 2.0) * iterations))
    return means[lower_index], means[upper_index]


def holm_adjust(p_values: Mapping[str, float]) -> dict[str, float]:
    """Apply Holm's step-down adjustment to planned comparison p-values."""
    if not p_values:
        raise ValueError("At least one p-value is required")
    ordered = sorted(p_values.items(), key=lambda item: item[1])
    adjusted_by_key: dict[str, float] = {}
    running_max = 0.0
    m = len(ordered)
    for rank, (key, p_value) in enumerate(ordered):
        if not 0.0 <= p_value <= 1.0:
            raise ValueError("p-values must be in [0, 1]")
        adjusted = min(1.0, (m - rank) * p_value)
        running_max = max(running_max, adjusted)
        adjusted_by_key[key] = running_max
    return {key: adjusted_by_key[key] for key in p_values}


def lower_tail_cvar(values: Sequence[float], *, alpha: float = 0.05) -> float:
    """Calculate lower-tail CVaR for worst-case success-style metrics."""
    if not values:
        raise ValueError("At least one value is required")
    if not 0.0 < alpha <= 1.0:
        raise ValueError("alpha must be in (0, 1]")
    ordered = sorted(values)
    tail_count = max(1, int(len(ordered) * alpha))
    tail = ordered[:tail_count]
    return sum(tail) / len(tail)
