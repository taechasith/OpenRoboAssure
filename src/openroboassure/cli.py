"""Command-line interface for OpenRoboAssure."""

from __future__ import annotations

import argparse
from pathlib import Path

from openroboassure.doctor import run_doctor


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
    raise AssertionError(f"Unhandled command: {args.command}")
