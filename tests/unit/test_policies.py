"""P06 policy, randomization, and common-environment contract tests."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from openroboassure.policies.mlp import StateMlpPolicy
from openroboassure.policies.scripted import ScriptedPickPlacePolicy
from openroboassure.training.environment import PickPlaceGymEnv
from openroboassure.training.randomization import RandomizationSystem, ScenarioSampler
from openroboassure.training.sensitivity import select_variables


@pytest.mark.parametrize(
    ("system", "variables"),
    [
        (RandomizationSystem.A_NO_RANDOMIZATION, ()),
        (RandomizationSystem.B_BROAD_UNIFORM, ()),
        (RandomizationSystem.C_AUTOMATIC_CURRICULUM, ()),
        (
            RandomizationSystem.D_SENSITIVITY_GUIDED,
            ("object_mass_kg", "surface_friction", "action_latency_steps"),
        ),
    ],
)
def test_all_p06_samplers_are_deterministic_and_valid(
    system: RandomizationSystem, variables: tuple[str, ...]
) -> None:
    first = ScenarioSampler(system, 22, variables).sample(4, progress=0.5)
    second = ScenarioSampler(system, 22, variables).sample(4, progress=0.5)

    assert first == second
    assert first.scenario_hash == second.scenario_hash


def test_scripted_policy_uses_the_common_gymnasium_action_contract() -> None:
    environment = PickPlaceGymEnv()
    scenario = ScenarioSampler(RandomizationSystem.A_NO_RANDOMIZATION, 11).sample(0)
    observation, _ = environment.reset(seed=11, options={"scenario": scenario})
    policy = ScriptedPickPlacePolicy()
    info: dict[str, object] = {}
    try:
        for _ in range(environment.max_episode_steps):
            observation, _, terminated, truncated, info = environment.step(policy.act(observation))
            if terminated or truncated:
                break
    finally:
        environment.close()

    assert info["success"] is True
    assert info["dropped"] is False


def test_mlp_serialization_preserves_deterministic_actions(tmp_path: Path) -> None:
    policy = StateMlpPolicy(11)
    observation = np.array([-0.1, -0.1, 0.1, -0.1, -0.1, 0.02, 0.16, 0.1, 0.001, 0.0])
    expected = policy.act(observation)
    path = tmp_path / "policy.npz"

    digest = policy.save(path)
    restored = StateMlpPolicy.load(path)

    assert len(digest) == 64
    np.testing.assert_allclose(restored.act(observation), expected)


def test_morris_selection_applies_gate_threshold_and_sobol_cap() -> None:
    rows: list[dict[str, float | str]] = [
        {"parameter": f"parameter_{index}", "mu_star": float(10 - index)} for index in range(8)
    ]

    selection = select_variables(rows)

    assert selection.threshold == 0.5
    assert selection.selected_variables == tuple(f"parameter_{index}" for index in range(6))
