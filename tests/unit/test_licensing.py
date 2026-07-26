from __future__ import annotations

from email.message import Message
from pathlib import Path

import pytest
import yaml

import openroboassure.licensing.audit as audit_module
from openroboassure.licensing.audit import (
    _metadata_licence,
    _policy,
    audit_manifest,
    audit_python_packages,
    classify_licence,
)


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
        "local_path": "assets/imported/fixture",
        "entrypoint": "fixture.xml",
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


def test_metadata_normalizes_zlib_spelling() -> None:
    assert _metadata_licence({"License": "zlib"}) == "Zlib"


def test_metadata_resolves_apache_classifier() -> None:
    metadata = Message()
    metadata["Classifier"] = "License :: OSI Approved :: Apache Software License"
    assert _metadata_licence(metadata) == "Apache-2.0"


def test_missing_package_metadata_is_not_approved_by_an_absent_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Metadata(dict[str, str]):
        def get_all(self, name: str, default: list[str]) -> list[str]:
            return default

    class Distribution:
        metadata = Metadata(Name="missing-metadata")
        files: list[object] = []

    monkeypatch.setattr(audit_module, "distributions", lambda: [Distribution()])

    finding = audit_python_packages({"MIT"}, [], [], {})[0]
    assert finding.licence is None
    assert finding.status == "unknown"


def test_asset_manifest_checks_vendored_entrypoint_hash(tmp_path: Path) -> None:
    manifest = tmp_path / "assets" / "manifest.yaml"
    entrypoint = tmp_path / "assets" / "imported" / "fixture" / "fixture.xml"
    entrypoint.parent.mkdir(parents=True)
    entrypoint.write_text("model", encoding="utf-8")
    asset = _asset("MIT")
    asset["redistributed"] = True
    asset["sha256"] = "9372c470eeadd5ecd9c3c74c2b3cb633f8e2f2fad799250a0f70d652b6b825e4"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(yaml.safe_dump({"schema_version": 1, "assets": [asset]}), encoding="utf-8")

    assert audit_manifest(manifest, {"MIT"}, [], [])[0].status == "approved"
    asset["sha256"] = "0" * 64
    manifest.write_text(yaml.safe_dump({"schema_version": 1, "assets": [asset]}), encoding="utf-8")
    assert audit_manifest(manifest, {"MIT"}, [], [])[0].status == "unknown"


def test_repository_vendored_model_manifest_is_complete() -> None:
    root = Path(__file__).resolve().parents[2]
    findings = audit_manifest(
        root / "assets" / "manifest.yaml",
        {"Apache-2.0", "BSD-3-Clause"},
        [],
        [],
    )

    assert {finding.identifier for finding in findings} == {"panda_mjcf", "ur5e_mjcf"}
    assert all(finding.status == "approved" for finding in findings)
