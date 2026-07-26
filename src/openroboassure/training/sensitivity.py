"""SALib-backed Morris and Sobol sensitivity evidence for the approved P06 scope."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import optuna
from SALib.analyze import morris as morris_analyze  # type: ignore[import-untyped]
from SALib.analyze import sobol as sobol_analyze
from SALib.sample import morris as morris_sample  # type: ignore[import-untyped]
from SALib.sample import sobol as sobol_sample

from openroboassure.policies.scripted import ScriptedPickPlacePolicy
from openroboassure.scenarios.models import PickPlaceScenario, ScenarioFamily, ScenarioSplit
from openroboassure.scenarios.ontology import CORE_PICK_PLACE_REGISTRY, ParameterKind
from openroboassure.training.environment import PickPlaceGymEnv
from openroboassure.training.randomization import scenario_from_parameter_values

_MORRIS_TRAJECTORIES = 20
_SOBOL_SAMPLE_SIZE = 512
_SOBOL_MAXIMUM_VARIABLES = 6
_BOOTSTRAP_RESAMPLES = 1000
_MORRIS_FRACTION = 0.05
_SOBOL_LOWER_BOUND = 0.01


@dataclass(frozen=True)
class SensitivitySelection:
    """The reproducible variables System D is permitted to randomize."""

    selected_variables: tuple[str, ...]
    maximum_mu_star: float
    threshold: float


def run_sensitivity_experiment(output: Path, seed: int = 202606) -> dict[str, object]:
    """Run Morris over all sixteen variables, then Sobol over the selected subset."""
    names = [parameter.name for parameter in CORE_PICK_PLACE_REGISTRY.parameters]
    all_problem = _problem(names)
    morris_inputs = morris_sample.sample(
        all_problem, N=_MORRIS_TRAJECTORIES, num_levels=4, seed=seed
    )
    morris_values = _reference_returns(morris_inputs, names, seed)
    morris_raw = morris_analyze.analyze(
        all_problem, morris_inputs, morris_values, num_levels=4, seed=seed
    )
    morris_rows: list[dict[str, float | str]] = []
    for index, name in enumerate(names):
        morris_rows.append(
            {
                "parameter": name,
                "mu": float(morris_raw["mu"][index]),
                "mu_star": float(morris_raw["mu_star"][index]),
                "sigma": float(morris_raw["sigma"][index]),
                "mu_star_conf": float(morris_raw["mu_star_conf"][index]),
            }
        )
    selection = select_variables(morris_rows)
    sobol_problem = _problem(list(selection.selected_variables))
    sobol_inputs = sobol_sample.sample(
        sobol_problem, N=_SOBOL_SAMPLE_SIZE, calc_second_order=False, seed=seed + 1
    )
    sobol_values = _reference_returns(sobol_inputs, list(selection.selected_variables), seed + 1)
    sobol_raw = sobol_analyze.analyze(
        sobol_problem,
        sobol_values,
        calc_second_order=False,
        conf_level=0.95,
        num_resamples=_BOOTSTRAP_RESAMPLES,
        seed=seed + 1,
    )
    sobol_rows: list[dict[str, float | str]] = []
    for index, name in enumerate(selection.selected_variables):
        sobol_rows.append(
            {
                "parameter": name,
                "first_order": float(sobol_raw["S1"][index]),
                "first_order_confidence_half_width": float(sobol_raw["S1_conf"][index]),
                "total_order": float(sobol_raw["ST"][index]),
                "total_order_confidence_half_width": float(sobol_raw["ST_conf"][index]),
                "total_order_confidence_lower": float(
                    sobol_raw["ST"][index] - sobol_raw["ST_conf"][index]
                ),
            }
        )
    retained = [
        str(item["parameter"])
        for item in sobol_rows
        if float(item["total_order_confidence_lower"]) > _SOBOL_LOWER_BOUND
    ]
    final_variables = _at_least_top_three(retained, sobol_rows)
    frozen_search = _verify_frozen_optuna_thresholds(seed)
    report: dict[str, object] = {
        "experiment_id": "EXP-SENS-001",
        "method": "SALib Morris screening followed by SALib Sobol analysis",
        "reference_policy": "deterministic_scripted_state_only",
        "variables_screened": names,
        "morris": {
            "trajectories": _MORRIS_TRAJECTORIES,
            "evaluations": len(morris_inputs),
            "rows": morris_rows,
            "selection": asdict(selection),
        },
        "sobol": {
            "base_sample_size": _SOBOL_SAMPLE_SIZE,
            "second_order": False,
            "bootstrap_resamples": _BOOTSTRAP_RESAMPLES,
            "evaluations": len(sobol_inputs),
            "rows": sobol_rows,
            "retained_variables": final_variables,
            "total_order_lower_bound_rule": _SOBOL_LOWER_BOUND,
        },
        "system_d_variables": final_variables,
        "optuna_gate_invariant": frozen_search,
        "report_hash": "",
    }
    report["report_hash"] = _hash_report(report)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def select_variables(morris_rows: list[dict[str, float | str]]) -> SensitivitySelection:
    """Apply the P06 5%-of-maximum Morris rule with a top-three floor."""
    ranked = sorted(morris_rows, key=lambda item: float(item["mu_star"]), reverse=True)
    maximum = float(ranked[0]["mu_star"])
    threshold = _MORRIS_FRACTION * maximum
    selected = [str(item["parameter"]) for item in ranked if float(item["mu_star"]) >= threshold]
    return SensitivitySelection(tuple(selected[:_SOBOL_MAXIMUM_VARIABLES]), maximum, threshold)


def _problem(names: list[str]) -> dict[str, object]:
    return {"num_vars": len(names), "names": names, "bounds": [[0.0, 1.0] for _ in names]}


def _reference_returns(samples: np.ndarray, varied_names: list[str], seed: int) -> np.ndarray:
    environment = PickPlaceGymEnv()
    try:
        values = [
            _scripted_return(
                environment, _scenario_from_unit_vector(row, varied_names, seed + index)
            )
            for index, row in enumerate(samples)
        ]
    finally:
        environment.close()
    return np.asarray(values, dtype=np.float64)


def _scenario_from_unit_vector(
    vector: np.ndarray, varied_names: list[str], seed: int
) -> PickPlaceScenario:
    values = {
        parameter.name: parameter.nominal for parameter in CORE_PICK_PLACE_REGISTRY.parameters
    }
    for name, unit in zip(varied_names, vector, strict=True):
        parameter = CORE_PICK_PLACE_REGISTRY.parameter(name)
        low, high = parameter.training_bounds
        if parameter.kind is ParameterKind.DISCRETE:
            values[name] = float(int(low + min(int(unit * (int(high - low) + 1)), int(high - low))))
        else:
            values[name] = low + float(unit) * (high - low)
    return scenario_from_parameter_values(
        values,
        index=seed,
        seed=seed,
        family=ScenarioFamily.S1_IN_DISTRIBUTION,
        split=ScenarioSplit.TRAIN,
    )


def _scripted_return(environment: PickPlaceGymEnv, scenario: PickPlaceScenario) -> float:
    observation, _ = environment.reset(seed=scenario.seed, options={"scenario": scenario})
    policy = ScriptedPickPlacePolicy()
    policy.reset()
    total_reward = 0.0
    for _ in range(environment.max_episode_steps):
        observation, reward, terminated, truncated, _ = environment.step(policy.act(observation))
        total_reward += reward
        if terminated or truncated:
            break
    return total_reward


def _at_least_top_three(retained: list[str], rows: list[dict[str, float | str]]) -> list[str]:
    ranked = sorted(rows, key=lambda item: float(item["total_order"]), reverse=True)
    result = list(retained)
    for item in ranked:
        name = str(item["parameter"])
        if len(result) >= 3:
            break
        if name not in result:
            result.append(name)
    return result


def _verify_frozen_optuna_thresholds(seed: int) -> dict[str, float | int]:
    """Record Optuna integration without tuning a gate-fixed campaign parameter."""
    sampler = optuna.samplers.TPESampler(seed=seed)
    study = optuna.create_study(direction="maximize", sampler=sampler)

    def objective(trial: optuna.Trial) -> float:
        morris_fraction = trial.suggest_float("morris_fraction", _MORRIS_FRACTION, _MORRIS_FRACTION)
        sobol_lower_bound = trial.suggest_float(
            "sobol_lower_bound", _SOBOL_LOWER_BOUND, _SOBOL_LOWER_BOUND
        )
        return -(
            abs(morris_fraction - _MORRIS_FRACTION) + abs(sobol_lower_bound - _SOBOL_LOWER_BOUND)
        )

    study.optimize(objective, n_trials=1)
    return {
        "trials": len(study.trials),
        "morris_fraction": float(study.best_params["morris_fraction"]),
        "sobol_lower_bound": float(study.best_params["sobol_lower_bound"]),
    }


def _hash_report(report: dict[str, object]) -> str:
    body = json.dumps(report, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()
