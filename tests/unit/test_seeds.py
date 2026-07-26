from __future__ import annotations

import random

import pytest

from openroboassure.experiments.seeds import MAX_SEED, SeedPlan, apply_seed


def test_seed_derivation_is_stable_and_namespaced() -> None:
    plan = SeedPlan(42)

    assert plan.derive("scenario", 0) == SeedPlan(42).derive("scenario", 0)
    assert plan.derive("scenario", 0) != plan.derive("scenario", 1)
    assert plan.derive("scenario", 0) != plan.derive("policy", 0)


def test_apply_seed_replays_python_randomness() -> None:
    apply_seed(123)
    first = random.random()
    apply_seed(123)

    assert random.random() == first


@pytest.mark.parametrize("seed", [-1, MAX_SEED + 1])
def test_seed_plan_rejects_out_of_range_root_seed(seed: int) -> None:
    with pytest.raises(ValueError, match="Seed must be"):
        SeedPlan(seed)
