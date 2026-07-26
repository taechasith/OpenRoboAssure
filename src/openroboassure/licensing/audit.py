"""Strict, local licence auditing for dependencies and imported assets."""

from __future__ import annotations

import fnmatch
import json
import re
from dataclasses import asdict, dataclass
from importlib.metadata import distributions
from pathlib import Path
from typing import Literal

import yaml

Status = Literal["approved", "blocked", "unknown"]
REQUIRED_ASSET_FIELDS = {
    "asset_id",
    "name",
    "kind",
    "source_repository",
    "source_commit",
    "source_subdirectory",
    "spdx_license",
    "redistributed",
    "retrieval_method",
    "sha256",
    "review_status",
    "reviewed_by",
    "review_date",
    "notes",
}


@dataclass(frozen=True)
class Finding:
    source: str
    identifier: str
    status: Status
    licence: str | None
    message: str


def _load(path: Path) -> dict[str, object]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected a mapping in {path}")
    return {str(key): item for key, item in value.items()}


def _policy(root: Path) -> tuple[set[str], list[str], list[str], dict[str, str]]:
    approved = _load(root / "dependencies" / "approved_licenses.yaml").get("licenses", [])
    blocked = _load(root / "dependencies" / "blocked_licenses.yaml")
    if not isinstance(approved, list):
        raise ValueError("Approved licences must be a list")
    patterns_value = blocked.get("patterns", [])
    terms_value = blocked.get("blocked_terms", [])
    if not isinstance(patterns_value, list) or not isinstance(terms_value, list):
        raise ValueError("Blocked licence policy values must be lists")
    exceptions = _load(root / "dependencies" / "license_exceptions.yaml").get("exceptions", [])
    if not isinstance(exceptions, list):
        raise ValueError("Licence exceptions must be a list")
    approved_exceptions = {
        str(item["package"]).lower(): str(item["spdx_license"])
        for item in exceptions
        if isinstance(item, dict) and item.get("scope") == "development_only"
    }
    return (
        {str(item) for item in approved},
        [str(item) for item in patterns_value],
        [str(item) for item in terms_value],
        approved_exceptions,
    )


def classify_licence(
    value: str | None, approved: set[str], blocked: list[str], terms: list[str]
) -> Status:
    if not value or not value.strip():
        return "unknown"
    lowered = value.lower()
    if any(term.lower() in lowered for term in terms):
        return "blocked"
    parts = [
        part for part in re.findall(r"[A-Za-z0-9.+-]+", value) if part not in {"AND", "OR", "WITH"}
    ]
    if any(
        any(fnmatch.fnmatchcase(part.lower(), pattern.lower()) for pattern in blocked)
        for part in parts
    ):
        return "blocked"
    return "approved" if parts and all(part in approved for part in parts) else "unknown"


def _metadata_licence(metadata: object) -> str | None:
    get = getattr(metadata, "get")  # noqa: B009
    expression = get("License-Expression")
    if expression:
        return str(expression)
    value = str(get("License", "")).strip()
    aliases = {"MIT": "MIT", "PSF-2.0": "PSF-2.0", "BSD": "BSD"}
    if value in aliases:
        return aliases[value]
    if "Apache License" in value:
        return "Apache-2.0"
    classifiers = getattr(metadata, "get_all")("Classifier", []) or []  # noqa: B009
    if any("MIT License" in item for item in classifiers):
        return "MIT"
    if any("MPL 2.0" in item for item in classifiers):
        return "MPL-2.0"
    if any("BSD License" in item for item in classifiers):
        return "BSD"
    return value or None


def _resolved_bsd_licence(distribution: object, licence: str | None) -> str | None:
    if licence != "BSD":
        return licence
    files = getattr(distribution, "files", None)
    locate_file = getattr(distribution, "locate_file")  # noqa: B009
    for entry in files or []:
        if not entry.name.lower().startswith(("license", "copying")):
            continue
        text = Path(locate_file(entry)).read_text(encoding="utf-8", errors="ignore")
        if "Neither the name" in text or "names of the contributors" in text:
            return "BSD-3-Clause"
    return licence


def audit_python_packages(
    approved: set[str], blocked: list[str], terms: list[str], exceptions: dict[str, str]
) -> list[Finding]:
    findings: list[Finding] = []
    for distribution in sorted(
        distributions(), key=lambda item: str(item.metadata["Name"]).lower()
    ):
        name = str(distribution.metadata["Name"])
        licence = _resolved_bsd_licence(distribution, _metadata_licence(distribution.metadata))
        status = classify_licence(licence, approved, blocked, terms)
        if exceptions.get(name.lower()) == licence:
            status = "approved"
        findings.append(
            Finding("python_dependency", name, status, licence, "Package metadata licence")
        )
    return findings


def audit_manifest(
    path: Path, approved: set[str], blocked: list[str], terms: list[str]
) -> list[Finding]:
    document = _load(path)
    assets = document.get("assets", [])
    if not isinstance(assets, list):
        return [Finding("asset_manifest", str(path), "unknown", None, "assets must be a list")]
    findings: list[Finding] = []
    for asset in assets:
        if not isinstance(asset, dict):
            findings.append(
                Finding("asset_manifest", str(path), "unknown", None, "Asset must be a mapping")
            )
            continue
        data = {str(key): value for key, value in asset.items()}
        identifier = str(data.get("asset_id", "<missing asset_id>"))
        missing = REQUIRED_ASSET_FIELDS - data.keys()
        licence = str(data.get("spdx_license", "")) or None
        status = classify_licence(licence, approved, blocked, terms)
        if missing or not re.fullmatch(r"[a-fA-F0-9]{64}", str(data.get("sha256", ""))):
            status = "unknown"
        if data.get("review_status") != "approved":
            status = "unknown"
        findings.append(
            Finding("asset_manifest", identifier, status, licence, "Asset manifest record")
        )
    return findings


def audit_headers(
    root: Path, approved: set[str], blocked: list[str], terms: list[str]
) -> list[Finding]:
    findings: list[Finding] = []
    for directory in (root / "third_party", root / "vendor", root / "assets" / "imported"):
        if not directory.is_dir():
            continue
        for path in directory.rglob("*"):
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")[:4096]
            match = re.search(r"SPDX-License-Identifier:\s*([^\r\n*]+)", text)
            licence = match.group(1).strip() if match else None
            findings.append(
                Finding(
                    "source_header",
                    str(path.relative_to(root)),
                    classify_licence(licence, approved, blocked, terms),
                    licence,
                    "Imported source SPDX header",
                )
            )
    return findings


def audit_project(root: Path, *, include_packages: bool = True) -> dict[str, object]:
    approved, blocked, terms, exceptions = _policy(root)
    findings = audit_manifest(root / "assets" / "manifest.yaml", approved, blocked, terms)
    findings.extend(audit_headers(root, approved, blocked, terms))
    if include_packages:
        findings.extend(audit_python_packages(approved, blocked, terms, exceptions))
    counts = {
        status: sum(item.status == status for item in findings)
        for status in ("approved", "blocked", "unknown")
    }
    return {
        "schema_version": 1,
        "passed": counts["blocked"] == 0 and counts["unknown"] == 0,
        "summary": counts,
        "findings": [asdict(item) for item in findings],
    }


def write_report(report: dict[str, object], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def add_asset(manifest: Path, asset: dict[str, object]) -> None:
    document = _load(manifest)
    assets = document.setdefault("assets", [])
    if not isinstance(assets, list):
        raise ValueError("Manifest assets must be a list")
    if any(isinstance(item, dict) and item.get("asset_id") == asset["asset_id"] for item in assets):
        raise ValueError(f"Asset already exists: {asset['asset_id']}")
    assets.append(asset)
    manifest.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
