"""Tests for clean-clone and retained-artifact registry validation."""

import copy
import json
from pathlib import Path

from scripts import validate_registry_schemas


def test_absent_retained_ocr_artifact_is_ledger_validated(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(validate_registry_schemas, "REPO_ROOT", tmp_path)
    errors: list[str] = []
    validate_registry_schemas.check_retained_digest(
        errors,
        "$.sha256",
        "build/document_ocr/missing.md",
        "0" * 64,
    )
    assert errors == []


def test_absent_repository_artifact_is_rejected(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(validate_registry_schemas, "REPO_ROOT", tmp_path)
    errors: list[str] = []
    validate_registry_schemas.check_retained_digest(
        errors,
        "$.sha256",
        "data/registry/missing.json",
        "0" * 64,
    )
    assert errors == ["$.sha256: missing repository file 'data/registry/missing.json'"]


def test_live_decomposition_matches_mineru_manifest():
    registry_root = validate_registry_schemas.REGISTRY_DIR
    decomposition = json.loads(
        (registry_root / "document_decomposition_audit.json").read_text(encoding="ascii")
    )
    run_manifest = json.loads(
        (registry_root / "aligned_research_mineru_run.json").read_text(encoding="ascii")
    )
    assert (
        validate_registry_schemas.validate_decomposition_manifest_contract(
            decomposition, run_manifest
        )
        == []
    )


def test_decomposition_manifest_drift_is_rejected():
    registry_root = validate_registry_schemas.REGISTRY_DIR
    decomposition = json.loads(
        (registry_root / "document_decomposition_audit.json").read_text(encoding="ascii")
    )
    run_manifest = json.loads(
        (registry_root / "aligned_research_mineru_run.json").read_text(encoding="ascii")
    )
    drifted = copy.deepcopy(decomposition)
    drifted["documents"][0]["markdown_sha256"] = "0" * 64
    errors = validate_registry_schemas.validate_decomposition_manifest_contract(
        drifted, run_manifest
    )
    assert any("markdown_sha256: manifest mismatch" in error for error in errors)
