"""P10 full benchmark harness tests."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from openroboassure.benchmark.full import (
    build_github_benchmark_markdown,
    run_full_benchmark,
    run_p10_preflight,
    verify_protected_hashes,
)
from openroboassure.benchmark.preregistration import (
    P09_BENCHMARK_ID,
    build_public_commitment,
    write_hidden_seed_package,
    write_public_commitment,
)

FROZEN_P09_PROTECTED_REF = "f9654a4f3a871401d8d1677a409337d5485ced98"


def test_protected_hashes_verify_from_committed_p09_files() -> None:
    report = verify_protected_hashes(
        Path("experiments/preregistered/ORA-BENCH-001.yaml"),
        ref=FROZEN_P09_PROTECTED_REF,
    )

    assert report["passed"] is True
    assert report["mismatches"] == []


def test_preflight_keeps_hidden_values_out_of_report(tmp_path: Path) -> None:
    manifest, private_package = _write_fixture_manifest(tmp_path)

    report = run_p10_preflight(
        manifest,
        output_directory=tmp_path / "reports",
        verify_hashes=False,
    )
    serialized = yaml.safe_dump(report)

    assert report["passed"] is True
    assert private_package.read_text(encoding="utf-8").splitlines()[3].strip() not in serialized
    assert "fixture-hidden-salt" not in serialized
    hidden_material = report["hidden_material"]
    assert isinstance(hidden_material, dict)
    assert hidden_material["hidden_values_in_report"] is False


def test_smoke_run_writes_labelled_report_and_github_circle_graph(tmp_path: Path) -> None:
    manifest, _ = _write_fixture_manifest(tmp_path)

    report = run_full_benchmark(
        manifest,
        output_directory=tmp_path / "reports",
        mode="smoke",
        verify_hashes=False,
        training_steps=4,
        evaluation_scenarios=6,
        method_limit=1,
        seed_limit=1,
    )

    assert report["mode"] == "smoke"
    assert report["hidden_values_revealed"] is False
    assert (tmp_path / "reports" / "benchmarks" / "ORA-BENCH-001-smoke.json").exists()
    graph = tmp_path / "reports" / "benchmarks" / "ORA-BENCH-001-smoke.github.md"
    assert graph.exists()
    text = graph.read_text(encoding="utf-8")
    assert "flowchart LR" in text
    assert "pie title ORA-BENCH-001 classified job outcomes" in text


def test_github_graph_handles_preflight_without_runs() -> None:
    markdown = build_github_benchmark_markdown(
        {
            "mode": "preflight",
            "status": "passed",
            "scope": {"scheduled_evaluations": 0},
            "runs": [],
            "hidden_values_revealed": False,
        }
    )

    assert "not_run" in markdown
    assert "GATE-P11 interpretation" in markdown


def _write_fixture_manifest(tmp_path: Path) -> tuple[Path, Path]:
    private_package = tmp_path / "private" / "p09" / "ORA-BENCH-001-sealed-seed-package.json"
    package = write_hidden_seed_package(private_package, generated_at="2026-08-02T00:00:00+07:00")
    package["evaluation_root_seed"] = 20260901
    package["hidden_catalogue_salt"] = "fixture-hidden-salt"
    private_package.write_text(
        json.dumps(package, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    audit_path = tmp_path / "reports" / "licence_audit" / "latest.json"
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path.write_text(
        json.dumps({"passed": True, "approved": 1, "blocked": 0, "unknown": 0}) + "\n",
        encoding="utf-8",
    )
    hidden_commitment = tmp_path / "benchmarks" / "hidden_catalogue" / "commitment.yaml"
    evaluation_commitment = tmp_path / "benchmarks" / "evaluation_sets" / "commitment.yaml"
    commitment = build_public_commitment(package)
    write_public_commitment(commitment, hidden_commitment)
    commitments = commitment["commitments"]
    assert isinstance(commitments, dict)
    evaluation_commitment.parent.mkdir(parents=True, exist_ok=True)
    evaluation_commitment.write_text(
        yaml.safe_dump(
            {
                "benchmark_id": P09_BENCHMARK_ID,
                "gate": "GATE-P09-PREREGISTRATION",
                "schema_version": 1,
                "commitments": {
                    "evaluation_scenario_set_sha256": commitments["evaluation_scenario_set_sha256"],
                    "evaluation_parameter_set_sha256": commitments[
                        "evaluation_parameter_set_sha256"
                    ],
                },
            }
        ),
        encoding="utf-8",
    )
    manifest = tmp_path / "experiments" / "preregistered" / "ORA-BENCH-001.yaml"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(
        yaml.safe_dump(
            {
                "benchmark_id": P09_BENCHMARK_ID,
                "gate": "GATE-P09-PREREGISTRATION",
                "training": {
                    "seeds": [11, 22, 33, 44, 55],
                    "environment_steps_per_method_seed": 100000,
                },
                "evaluation": {
                    "hidden_scenarios_per_robot_task": 10000,
                    "hidden_material": {
                        "public_commitment": hidden_commitment.as_posix(),
                        "evaluation_set_commitment": evaluation_commitment.as_posix(),
                        "private_seed_package": private_package.as_posix(),
                    },
                },
                "integrity": {
                    "protected_hashes": "benchmarks/specs/ORA-BENCH-001-protected-hashes.yaml"
                },
            }
        ),
        encoding="utf-8",
    )
    return manifest, private_package
