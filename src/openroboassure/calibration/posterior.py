"""Approximate posterior fitting for source-to-hidden-target calibration."""

from __future__ import annotations

from dataclasses import dataclass
from math import exp

import numpy as np


@dataclass(frozen=True)
class CandidateScore:
    """One source-parameter candidate and its target-trajectory discrepancy."""

    candidate_id: str
    values: dict[str, float]
    observation_sse: float
    observation_rmse: float
    outcome_mismatch_rate: float


def posterior_weights(scores: list[CandidateScore], *, observation_sigma_m: float) -> list[float]:
    """Compute normalized Gaussian-error weights over uniformly sampled candidates."""
    if observation_sigma_m <= 0.0:
        raise ValueError("observation_sigma_m must be positive")
    if not scores:
        raise ValueError("At least one candidate is required")
    log_likelihoods = [
        -0.5 * score.observation_sse / (observation_sigma_m * observation_sigma_m)
        for score in scores
    ]
    offset = max(log_likelihoods)
    weights = [exp(value - offset) for value in log_likelihoods]
    total = sum(weights)
    if total <= 0.0:
        raise ValueError("Posterior weights underflowed to zero")
    return [weight / total for weight in weights]


def summarize_posterior(
    scores: list[CandidateScore],
    weights: list[float],
    variable_names: tuple[str, ...],
) -> dict[str, object]:
    """Summarize weighted candidate samples with equal-tailed intervals."""
    if len(scores) != len(weights):
        raise ValueError("Candidate scores and weights must have the same length")
    summaries: dict[str, object] = {}
    for name in variable_names:
        values = np.asarray([score.values[name] for score in scores], dtype=np.float64)
        normalized_weights = np.asarray(weights, dtype=np.float64)
        mean = float(np.sum(values * normalized_weights))
        variance = float(np.sum(((values - mean) ** 2) * normalized_weights))
        summaries[name] = {
            "mean": mean,
            "standard_deviation": float(np.sqrt(max(variance, 0.0))),
            "credible_interval_90": [
                _weighted_quantile(values, normalized_weights, 0.05),
                _weighted_quantile(values, normalized_weights, 0.95),
            ],
        }
    return summaries


def posterior_coverage(
    posterior: dict[str, object], true_values: dict[str, float]
) -> dict[str, object]:
    """Reveal-stage check of whether hidden values fall in posterior intervals."""
    rows: list[dict[str, object]] = []
    covered = 0
    for name, true_value in sorted(true_values.items()):
        entry = posterior[name]
        if not isinstance(entry, dict):
            raise TypeError("Posterior entry must be a mapping")
        interval = entry["credible_interval_90"]
        if (
            not isinstance(interval, list)
            or len(interval) != 2
            or not all(isinstance(value, float) for value in interval)
        ):
            raise TypeError("Posterior credible interval is malformed")
        low, high = interval
        is_covered = low <= true_value <= high
        rows.append(
            {
                "parameter": name,
                "true_value_after_freeze": true_value,
                "interval_low": low,
                "interval_high": high,
                "covered": is_covered,
            }
        )
        covered += int(is_covered)
    return {
        "covered_parameters": covered,
        "total_parameters": len(true_values),
        "coverage_rate": covered / len(true_values),
        "rows": rows,
    }


def _weighted_quantile(values: np.ndarray, weights: np.ndarray, quantile: float) -> float:
    if not 0.0 <= quantile <= 1.0:
        raise ValueError("quantile must be in [0, 1]")
    order = np.argsort(values)
    sorted_values = values[order]
    sorted_weights = weights[order]
    cumulative = np.cumsum(sorted_weights)
    return float(sorted_values[np.searchsorted(cumulative, quantile, side="left")])
