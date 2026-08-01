"""P09 preregistration commitments for the conservative full benchmark."""

from __future__ import annotations

import hashlib
import json
import math
import secrets
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path

import yaml

from openroboassure.experiments.seeds import MAX_SEED
from openroboassure.scenarios.compiler import SamplingMethod, ScenarioCompiler
from openroboassure.scenarios.models import PickPlaceScenario, ScenarioFamily, ScenarioSplit

P09_BENCHMARK_ID = "ORA-BENCH-001"
P09_GATE_ID = "GATE-P09-PREREGISTRATION"
P09_METHODS = ("A", "B", "C", "D", "E")
P09_TRAINING_SEEDS = (11, 22, 33, 44, 55)
P09_ROBOTS = ("ORA-4A",)
P09_TASKS = ("pick_place_v1",)
P09_EVALUATION_SCENARIOS_PER_ROBOT_TASK = 10_000
P09_TRAINING_STEPS_PER_METHOD_SEED = 100_000
P09_EVALUATION_FAMILIES = (
    ScenarioFamily.S1_IN_DISTRIBUTION,
    ScenarioFamily.S2_BOUNDARY,
    ScenarioFamily.S3_UNSEEN_COMBINATIONS,
    ScenarioFamily.S4_OUT_OF_DISTRIBUTION,
    ScenarioFamily.S5_ADVERSARIAL,
    ScenarioFamily.S6_FAULT_INJECTION,
)

_FORBIDDEN_PUBLIC_KEYS = frozenset(
    {
        "entries",
        "evaluation_root_seed",
        "hidden_catalogue_salt",
        "hidden_labels",
        "parameter_hash",
        "parameter_hashes",
        "scenario_hash",
        "scenario_hashes",
    }
)


def stable_digest(payload: object) -> str:
    """Return a canonical SHA-256 digest for JSON-compatible payloads."""
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def new_hidden_seed_package(*, generated_at: str | None = None) -> dict[str, object]:
    """Create hidden material that must remain outside committed repository files."""
    return {
        "benchmark_id": P09_BENCHMARK_ID,
        "schema_version": 1,
        "generated_at": generated_at or datetime.now(UTC).isoformat(),
        "evaluation_root_seed": secrets.randbelow(MAX_SEED + 1),
        "hidden_catalogue_salt": secrets.token_hex(32),
    }


def load_hidden_seed_package(path: Path) -> dict[str, object]:
    """Load the private P09 hidden seed package."""
    with path.open(encoding="utf-8") as handle:
        package = json.load(handle)
    if not isinstance(package, dict):
        raise TypeError("Hidden seed package must be a JSON object")
    return dict(package)


def write_hidden_seed_package(path: Path, *, generated_at: str | None = None) -> dict[str, object]:
    """Write a private seed package without returning hidden values to stdout."""
    package = new_hidden_seed_package(generated_at=generated_at)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(package, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return package


def build_p09_evaluation_scenarios(
    count: int = P09_EVALUATION_SCENARIOS_PER_ROBOT_TASK,
    *,
    root_seed: int,
) -> list[PickPlaceScenario]:
    """Build the hidden P09 evaluation catalogue for the approved conservative scope."""
    if count <= 0:
        raise ValueError("P09 evaluation scenario count must be positive")
    compiler = ScenarioCompiler()
    per_family = count // len(P09_EVALUATION_FAMILIES)
    remainder = count % len(P09_EVALUATION_FAMILIES)
    scenarios: list[PickPlaceScenario] = []
    for family_index, family in enumerate(P09_EVALUATION_FAMILIES):
        family_count = per_family + int(family_index < remainder)
        scenarios.extend(
            compiler.generate(
                family_count,
                root_seed=root_seed + family_index,
                family=family,
                split=ScenarioSplit.EVALUATION,
                method=SamplingMethod.LATIN_HYPERCUBE,
            )
        )
    if len(scenarios) != count:
        raise AssertionError("P09 evaluation scenario count changed")
    return scenarios


def build_hidden_failure_catalogue(
    scenarios: list[PickPlaceScenario], *, hidden_catalogue_salt: str
) -> list[dict[str, object]]:
    """Build hidden failure labels for isolated evaluation-time reveal."""
    if not hidden_catalogue_salt:
        raise ValueError("Hidden catalogue salt must be non-empty")
    catalogue: list[dict[str, object]] = []
    for scenario in scenarios:
        labels = [scenario.family.value]
        transfer_distance = math.dist(scenario.object_position, scenario.target_position)
        if scenario.action_latency_steps >= 3 or scenario.frame_delay_steps >= 3:
            labels.append("high_delay")
        if scenario.observation_dropout_probability >= 0.05:
            labels.append("high_observation_dropout")
        if scenario.object_mass_kg >= 0.35 and scenario.surface_friction <= 0.40:
            labels.append("heavy_low_friction")
        if transfer_distance >= 0.30:
            labels.append("long_transfer")
        sorted_labels = sorted(labels)
        failure_id = stable_digest(
            {
                "hidden_catalogue_salt": hidden_catalogue_salt,
                "hidden_labels": sorted_labels,
                "scenario_hash": scenario.scenario_hash,
            }
        )
        catalogue.append(
            {
                "failure_id": failure_id,
                "hidden_labels": sorted_labels,
                "scenario_hash": scenario.scenario_hash,
            }
        )
    return catalogue


def build_public_commitment(
    seed_package: Mapping[str, object],
    *,
    scenario_count: int = P09_EVALUATION_SCENARIOS_PER_ROBOT_TASK,
) -> dict[str, object]:
    """Return public P09 commitments without exposing hidden seed or catalogue values."""
    root_seed = _required_int(seed_package, "evaluation_root_seed")
    hidden_salt = _required_string(seed_package, "hidden_catalogue_salt")
    scenarios = build_p09_evaluation_scenarios(scenario_count, root_seed=root_seed)
    scenario_hashes = [scenario.scenario_hash for scenario in scenarios]
    parameter_hashes = [scenario.parameter_hash for scenario in scenarios]
    catalogue = build_hidden_failure_catalogue(scenarios, hidden_catalogue_salt=hidden_salt)
    public = {
        "benchmark_id": P09_BENCHMARK_ID,
        "gate": P09_GATE_ID,
        "schema_version": 1,
        "hidden_material_status": "withheld_until_results_freeze",
        "scope": {
            "robots": list(P09_ROBOTS),
            "tasks": list(P09_TASKS),
            "methods": list(P09_METHODS),
            "training_seeds": len(P09_TRAINING_SEEDS),
            "evaluation_scenarios_per_robot_task": scenario_count,
        },
        "commitments": {
            "hidden_seed_package_sha256": stable_digest(
                {
                    "benchmark_id": seed_package.get("benchmark_id"),
                    "evaluation_root_seed": root_seed,
                    "hidden_catalogue_salt": hidden_salt,
                    "schema_version": seed_package.get("schema_version"),
                }
            ),
            "evaluation_scenario_set_sha256": stable_digest(
                {
                    "benchmark_id": P09_BENCHMARK_ID,
                    "scenario_hashes": scenario_hashes,
                }
            ),
            "evaluation_parameter_set_sha256": stable_digest(
                {
                    "benchmark_id": P09_BENCHMARK_ID,
                    "parameter_hashes": parameter_hashes,
                }
            ),
            "hidden_failure_catalogue_sha256": stable_digest(
                {
                    "benchmark_id": P09_BENCHMARK_ID,
                    "entries": catalogue,
                }
            ),
        },
        "isolation": {
            "contains_hidden_seed_values": False,
            "contains_scenario_hashes": False,
            "contains_parameter_hashes": False,
            "contains_hidden_failure_labels": False,
            "private_seed_package_committed": False,
        },
    }
    assert_public_commitment(public)
    return public


def write_public_commitment(commitment: Mapping[str, object], path: Path) -> None:
    """Write the public P09 commitment YAML."""
    assert_public_commitment(commitment)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(dict(commitment), sort_keys=False), encoding="utf-8")


def assert_public_commitment(payload: Mapping[str, object]) -> None:
    """Reject public payloads that expose hidden seeds, hashes, labels, or entries."""
    leaked = sorted(_find_forbidden_public_keys(payload))
    if leaked:
        raise ValueError(f"Public P09 commitment leaks hidden fields: {', '.join(leaked)}")


def _find_forbidden_public_keys(value: object) -> set[str]:
    if isinstance(value, Mapping):
        found = {str(key) for key in value if str(key) in _FORBIDDEN_PUBLIC_KEYS}
        for child in value.values():
            found.update(_find_forbidden_public_keys(child))
        return found
    if isinstance(value, list):
        found_values: set[str] = set()
        for child in value:
            found_values.update(_find_forbidden_public_keys(child))
        return found_values
    return set()


def _required_int(mapping: Mapping[str, object], key: str) -> int:
    value = mapping[key]
    if not isinstance(value, int):
        raise TypeError(f"{key} must be an integer")
    if not 0 <= value <= MAX_SEED:
        raise ValueError(f"{key} must be between 0 and {MAX_SEED}")
    return value


def _required_string(mapping: Mapping[str, object], key: str) -> str:
    value = mapping[key]
    if not isinstance(value, str):
        raise TypeError(f"{key} must be a string")
    if not value:
        raise ValueError(f"{key} must be non-empty")
    return value
