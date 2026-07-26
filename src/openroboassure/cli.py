"""Command-line interface for OpenRoboAssure."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from openroboassure.doctor import run_doctor
from openroboassure.experiments.baseline import run_baseline
from openroboassure.licensing.audit import add_asset, audit_project, write_report
from openroboassure.scenarios.compiler import SamplingMethod, ScenarioCompiler
from openroboassure.scenarios.experiment import run_scenario_validity, write_scenarios
from openroboassure.scenarios.models import ScenarioFamily, ScenarioSplit
from openroboassure.simulators.discrepancy import (
    measure_ora4a_discrepancy,
    write_discrepancy_report,
)
from openroboassure.training.randomization import RandomizationSystem
from openroboassure.training.sensitivity import run_sensitivity_experiment
from openroboassure.training.trainer import (
    TrainingConfiguration,
    build_evaluation_scenarios,
    evaluate_policy,
    run_cpu_standard_campaign,
    train_policy,
)


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level command parser."""
    parser = argparse.ArgumentParser(prog="ora", description="OpenRoboAssure command-line tools")
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor = subparsers.add_parser("doctor", help="write a local environment report")
    doctor.add_argument(
        "--offline",
        action="store_true",
        help="assert that the report is generated without network access",
    )
    baseline = subparsers.add_parser("baseline", help="run the first scripted simulation baseline")
    baseline.add_argument("--seeds", type=int, default=20)
    baseline.add_argument(
        "--output", type=Path, default=Path("reports/benchmarks/EXP-SIM-BASELINE-001.json")
    )
    simulator = subparsers.add_parser("simulator", help="run simulator comparison tools")
    simulator_commands = simulator.add_subparsers(dest="simulator_command", required=True)
    discrepancy = simulator_commands.add_parser(
        "discrepancy", help="measure deterministic ORA-4A cross-simulator discrepancies"
    )
    discrepancy.add_argument("--seed", type=int, default=0)
    discrepancy.add_argument(
        "--output", type=Path, default=Path("reports/discrepancy/EXP-SIM-DISCREPANCY-001.json")
    )
    scenario = subparsers.add_parser("scenario", help="generate and validate procedural scenarios")
    scenario_commands = scenario.add_subparsers(dest="scenario_command", required=True)
    generate = scenario_commands.add_parser(
        "generate", help="write a deterministic scenario population as JSON"
    )
    generate.add_argument("--count", type=int, default=20)
    generate.add_argument("--seed", type=int, default=20260726)
    generate.add_argument(
        "--family",
        choices=[family.value for family in ScenarioFamily],
        default=ScenarioFamily.S1_IN_DISTRIBUTION.value,
    )
    generate.add_argument(
        "--split",
        choices=[split.value for split in ScenarioSplit],
        default=ScenarioSplit.TRAIN.value,
    )
    generate.add_argument(
        "--method",
        choices=[method.value for method in SamplingMethod],
        default=SamplingMethod.LATIN_HYPERCUBE.value,
    )
    generate.add_argument("--output", type=Path, default=Path("reports/scenarios/generated.json"))
    validate = scenario_commands.add_parser(
        "validate", help="run the streamed EXP-SCENARIO-VALIDITY-001 evidence experiment"
    )
    validate.add_argument("--count", type=int, default=1_000_000)
    validate.add_argument("--seed", type=int, default=20260726)
    validate.add_argument("--execution-samples", type=int, default=256)
    validate.add_argument(
        "--output", type=Path, default=Path("reports/scenarios/EXP-SCENARIO-VALIDITY-001.json")
    )
    licence = subparsers.add_parser("licence", help="audit dependency and asset licences")
    licence_commands = licence.add_subparsers(dest="licence_command", required=True)
    audit = licence_commands.add_parser(
        "audit", help="write a strict machine-readable licence report"
    )
    audit.add_argument("--project-root", type=Path, default=Path("."))
    audit.add_argument("--output", type=Path, default=Path("reports/licence_audit/latest.json"))
    asset = subparsers.add_parser("asset", help="register an imported asset")
    asset_commands = asset.add_subparsers(dest="asset_command", required=True)
    add = asset_commands.add_parser("add", help="add an asset record with provenance")
    for name in (
        "asset_id",
        "name",
        "kind",
        "source_repository",
        "source_commit",
        "source_subdirectory",
        "spdx_license",
        "sha256",
        "retrieval_method",
    ):
        add.add_argument(f"--{name.replace('_', '-')}", required=True)
    add.add_argument("--manifest", type=Path, default=Path("assets/manifest.yaml"))
    add.add_argument("--review-status", choices=["pending", "approved"], default="pending")
    add.add_argument("--reviewed-by", default="unreviewed")
    add.add_argument("--review-date", default="unreviewed")
    add.add_argument(
        "--notes", default="Registered by ora asset add; requires review before benchmark use."
    )
    add.add_argument("--redistributed", action="store_true")
    policy = subparsers.add_parser("policy", help="train and evaluate P06 state-only policies")
    policy_commands = policy.add_subparsers(dest="policy_command", required=True)
    train = policy_commands.add_parser("train", help="train one reproducible P06 policy seed")
    train.add_argument(
        "--system", choices=[item.value for item in RandomizationSystem], required=True
    )
    train.add_argument("--seed", type=int, required=True)
    train.add_argument("--steps", type=int, default=100_000)
    train.add_argument("--selected-variable", action="append", default=[])
    train.add_argument("--model-directory", type=Path, default=Path("reports/policies/models"))
    train.add_argument("--tracking", type=Path, default=Path("reports/policies/tracking.jsonl"))
    evaluate = policy_commands.add_parser(
        "evaluate", help="evaluate one policy on 200 held-out scenarios"
    )
    evaluate.add_argument("--model", type=Path, required=True)
    evaluate.add_argument(
        "--output", type=Path, default=Path("reports/policies/EXP-POLICY-EVALUATION.json")
    )
    campaign = policy_commands.add_parser(
        "campaign", help="run the approved P06 four-system CPU-standard campaign"
    )
    campaign.add_argument("--output-directory", type=Path, default=Path("reports"))
    sensitivity = subparsers.add_parser("sensitivity", help="run P06 SALib sensitivity evidence")
    sensitivity_commands = sensitivity.add_subparsers(dest="sensitivity_command", required=True)
    for command_name in ("morris", "sobol", "run"):
        command = sensitivity_commands.add_parser(
            command_name, help="run the linked Morris and Sobol EXP-SENS-001 evidence"
        )
        command.add_argument("--seed", type=int, default=202606)
        command.add_argument(
            "--output", type=Path, default=Path("reports/sensitivity/EXP-SENS-001.json")
        )
    doctor.add_argument(
        "--output",
        type=Path,
        default=Path("reports/environment/latest.json"),
        help="path for the JSON environment report",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run an ORA command and return its process status."""
    args = build_parser().parse_args(argv)
    if args.command == "doctor":
        return run_doctor(output=args.output, offline=args.offline)
    if args.command == "baseline":
        report = run_baseline(args.seeds, args.output)
        print(f"Baseline success rate: {report['success_rate']:.1%}")
        return 0
    if args.command == "simulator" and args.simulator_command == "discrepancy":
        report = measure_ora4a_discrepancy(args.seed)
        write_discrepancy_report(report, args.output)
        print(
            f"Maximum end-effector discrepancy: {report['max_end_effector_position_error_m']:.6f} m"
        )
        return 0
    if args.command == "scenario" and args.scenario_command == "generate":
        compiler = ScenarioCompiler()
        count = write_scenarios(
            compiler.generate(
                args.count,
                root_seed=args.seed,
                family=ScenarioFamily(args.family),
                split=ScenarioSplit(args.split),
                method=SamplingMethod(args.method),
            ),
            args.output,
        )
        print(f"Wrote {count} scenarios to {args.output}")
        return 0
    if args.command == "scenario" and args.scenario_command == "validate":
        report = run_scenario_validity(
            args.count,
            args.output,
            root_seed=args.seed,
            execution_samples=args.execution_samples,
        )
        valid_rate = report["valid_rate"]
        generated_scenarios = report["generated_scenarios"]
        if not isinstance(valid_rate, float) or not isinstance(generated_scenarios, int):
            raise AssertionError("Scenario validity report has invalid summary types")
        print(
            "Scenario validity rate: "
            f"{valid_rate:.1%} over {generated_scenarios} generated scenarios"
        )
        return 0 if valid_rate >= 0.995 else 1
    if args.command == "licence" and args.licence_command == "audit":
        report = audit_project(args.project_root.resolve())
        write_report(report, args.output)
        print(f"OpenRoboAssure licence audit report: {args.output}")
        return 0 if report["passed"] is True else 1
    if args.command == "asset" and args.asset_command == "add":
        fields = (
            "asset_id",
            "name",
            "kind",
            "source_repository",
            "source_commit",
            "source_subdirectory",
            "spdx_license",
            "sha256",
            "retrieval_method",
            "review_status",
            "reviewed_by",
            "review_date",
            "notes",
        )
        record = {field: getattr(args, field) for field in fields}
        record["redistributed"] = args.redistributed
        add_asset(args.manifest, record)
        print(f"Registered asset in {args.manifest}")
        return 0
    if args.command == "policy" and args.policy_command == "train":
        result = train_policy(
            TrainingConfiguration(
                system=RandomizationSystem(args.system),
                seed=args.seed,
                environment_steps=args.steps,
                selected_variables=tuple(args.selected_variable),
            ),
            model_directory=args.model_directory,
            tracking_path=args.tracking,
        )
        print(
            f"Trained {result['system']} seed {result['seed']} for {result['environment_steps']} steps"
        )
        return 0
    if args.command == "policy" and args.policy_command == "evaluate":
        report = evaluate_policy(args.model, build_evaluation_scenarios())
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(f"Held-out task success: {report['primary_held_out_task_success']:.1%}")
        return 0
    if args.command == "policy" and args.policy_command == "campaign":
        report = run_cpu_standard_campaign(args.output_directory)
        aggregate = report["aggregate"]
        if not isinstance(aggregate, dict):
            raise AssertionError("P06 campaign aggregate is malformed")
        print(f"P06 campaign completed with {len(aggregate)} systems")
        return 0
    if args.command == "sensitivity":
        report = run_sensitivity_experiment(args.output, seed=args.seed)
        variables = report["system_d_variables"]
        if not isinstance(variables, list) or not all(isinstance(item, str) for item in variables):
            raise AssertionError("Sensitivity report did not contain System D variables")
        print(f"System D variables: {', '.join(str(item) for item in variables)}")
        return 0
    raise AssertionError(f"Unhandled command: {args.command}")
