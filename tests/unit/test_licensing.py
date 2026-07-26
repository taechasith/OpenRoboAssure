from __future__ import annotations

from pathlib import Path

import yaml

from openroboassure.licensing.audit import _policy, audit_manifest, classify_licence


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


def test_policy_accepts_only_documented_exception_scopes(tmp_path: Path) -> None:
    dependencies = tmp_path / "dependencies"
    dependencies.mkdir()
    (dependencies / "approved_licenses.yaml").write_text("licenses: [MIT]\n", encoding="utf-8")
    (dependencies / "blocked_licenses.yaml").write_text(
        "patterns: []\nblocked_terms: []\n", encoding="utf-8"
    )
    (dependencies / "license_exceptions.yaml").write_text(
        "exceptions:\n"
        "  - package: dev-tool\n    spdx_license: MPL-2.0\n    scope: development_only\n"
        "  - package: runtime-tool\n    spdx_license: BSD\n    scope: runtime_dependency_only\n"
        "  - package: ignored-tool\n    spdx_license: MIT\n    scope: unsupported_scope\n",
        encoding="utf-8",
    )

    assert _policy(tmp_path)[3] == {"dev-tool": "MPL-2.0", "runtime-tool": "BSD"}
