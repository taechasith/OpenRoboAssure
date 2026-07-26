"""Command-line interface for OpenRoboAssure."""

from __future__ import annotations

import argparse
from pathlib import Path

from openroboassure.doctor import run_doctor
from openroboassure.experiments.baseline import run_baseline
from openroboassure.licensing.audit import add_asset, audit_project, write_report


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
    raise AssertionError(f"Unhandled command: {args.command}")
