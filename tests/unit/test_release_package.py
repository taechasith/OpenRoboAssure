"""P13 release package checks."""

from __future__ import annotations

import json
from pathlib import Path

import yaml


def test_p13_release_manifest_references_existing_files() -> None:
    manifest_path = Path("reports/release/v1.0.0-manifest.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest["release"] == "v1.0.0-candidate"
    assert manifest["status"] == "release_candidate_pending_GATE-P13-RELEASE"
    package_items = manifest["package_items"]
    assert isinstance(package_items, dict)

    for paths in package_items.values():
        assert isinstance(paths, list)
        for raw_path in paths:
            path = Path(raw_path)
            assert path.exists(), raw_path


def test_p13_citation_and_seed_ledger_parse() -> None:
    citation = yaml.safe_load(Path("CITATION.cff").read_text(encoding="utf-8"))
    seed_ledger = yaml.safe_load(
        Path("benchmarks/evaluation_sets/public_seed_ledger.yaml").read_text(encoding="utf-8")
    )

    assert citation["version"] == "1.0.0"
    assert citation["license"] == "Apache-2.0"
    assert seed_ledger["release"] == "v1.0.0-candidate"
    entries = seed_ledger["entries"]
    assert isinstance(entries, list)
    assert {entry["id"] for entry in entries} >= {
        "p08_pilot",
        "p10_full_benchmark_commitments",
        "p12_clean_smoke_reproduction",
    }


def test_p13_claims_remain_conservative() -> None:
    manifest = json.loads(Path("reports/release/v1.0.0-manifest.json").read_text(encoding="utf-8"))

    allowed = set(manifest["allowed_claims"])
    prohibited = set(manifest["prohibited_claims"])
    assert "valid_negative_result_for_ora4a_pick_place_simulation_scope" in allowed
    assert "real_world_validated" in prohibited
    assert "guaranteed_robust_learned_policies" in prohibited
    assert allowed.isdisjoint(prohibited)
