"""Tests for normalized clean-reproduction comparisons."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from jsonschema import Draft202012Validator
from scripts.verify_clean_reproduction import (
    normalized_result,
    parse_sha256_manifest,
    validate_report_schema,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_normalization_removes_only_execution_provenance():
    primary = {
        "source_commit": "a" * 40,
        "aggregate_decision": "not_supported",
        "primary_contrasts": [{"effect_estimate": -0.02}],
        "evidence_archive": {
            "relpath": "data/evidence/primary.tar",
            "sha256": "1" * 64,
        },
    }
    reproduction = deepcopy(primary)
    reproduction["source_commit"] = "b" * 40
    reproduction["evidence_archive"]["relpath"] = "data/reproduction/replay.tar"
    assert normalized_result(primary) == normalized_result(reproduction)


def test_normalization_preserves_scientific_differences():
    primary = {
        "source_commit": "a" * 40,
        "aggregate_decision": "not_supported",
        "evidence_archive": {"relpath": "primary.tar", "sha256": "1" * 64},
    }
    reproduction = deepcopy(primary)
    reproduction["aggregate_decision"] = "supported"
    assert normalized_result(primary) != normalized_result(reproduction)


def test_checksum_manifest_accepts_existing_utf8_repository_paths():
    content = b"a" * 64 + b"  /workspace/source_materials/frameworks/\xc3\x86ther.txt\n"
    records = parse_sha256_manifest(content, "/workspace/")
    assert records == {"source_materials/frameworks/\u00c6ther.txt": "a" * 64}


def test_clean_report_schema_accepts_safe_committed_path_names():
    schema = json.loads(
        (REPO_ROOT / "schemas/registry/clean_reproduction_verification.schema.json")
        .read_text(encoding="ascii")
    )
    validator = Draft202012Validator(schema["$defs"]["relpath"])
    assert validator.is_valid("source_materials/frameworks/draft reply to pais.txt")
    assert validator.is_valid("source_materials/frameworks/\u00c6ther-Crystalline.txt")
    assert not validator.is_valid("/tmp/outside.json")
    assert not validator.is_valid("data/../outside.json")


def test_retained_clean_report_satisfies_its_committed_schema():
    report = json.loads(
        (REPO_ROOT / "data/reproduction/verification_report.json").read_text(encoding="ascii")
    )
    validate_report_schema(report)
