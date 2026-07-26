from __future__ import annotations

from pathlib import Path

import yaml

from openroboassure.licensing.audit import audit_manifest, classify_licence


def _asset(licence: str) -> dict[str, object]:
    return {
        "asset_id": "fixture",
        "name": "fixture",
        "kind": "robot_model",
        "source_repository": "https://example.test/repo",
        "source_commit": "abc",
        "source_subdirectory": "model",
        "spdx_license": licence,
        "redistributed": False,
        "retrieval_method": "fixture",
        "sha256": "a" * 64,
        "review_status": "approved",
        "reviewed_by": "tester",
        "review_date": "2026-07-26",
        "notes": "fixture",
    }


def test_licence_classification_rejects_blocked_and_unknown_values() -> None:
    allowed = {"MIT"}
    assert classify_licence("MIT", allowed, ["CC-BY-NC-*"], ["research-only"]) == "approved"
    assert classify_licence("CC-BY-NC-4.0", allowed, ["CC-BY-NC-*"], ["research-only"]) == "blocked"
    assert (
        classify_licence("Proprietary-1.0", allowed, ["CC-BY-NC-*"], ["research-only"]) == "unknown"
    )


def test_asset_manifest_accepts_permissive_and_rejects_restricted(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.yaml"
    manifest.write_text(
        yaml.safe_dump({"schema_version": 1, "assets": [_asset("MIT")]}), encoding="utf-8"
    )
    assert (
        audit_manifest(manifest, {"MIT"}, ["CC-BY-NC-*"], ["research-only"])[0].status == "approved"
    )
    manifest.write_text(
        yaml.safe_dump({"schema_version": 1, "assets": [_asset("CC-BY-NC-4.0")]}), encoding="utf-8"
    )
    assert (
        audit_manifest(manifest, {"MIT"}, ["CC-BY-NC-*"], ["research-only"])[0].status == "blocked"
    )
