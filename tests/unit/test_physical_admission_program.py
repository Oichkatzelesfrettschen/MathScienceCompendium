"""Tests for physical-claim admission ordering and evidence requirements."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from scripts.validate_registry_schemas import load_json, semantic_checks, validate_with_jsonschema


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_measurable_packages_have_unique_ranked_hypotheses():
    payload = json.loads(
        (REPO_ROOT / "data/registry/physical_admission_program.json").read_text(encoding="ascii")
    )
    packages = payload["packages"]
    assert [package["rank"] for package in packages] == [1, 2, 3, 4]
    assert len({package["claim_id"] for package in packages}) == 4
    assert len({package["hypothesis_id"] for package in packages}) == 4
    assert all(package["operator_set"] for package in packages)
    assert all(package["locked_controls"] for package in packages)
    assert all(package["blockers"] for package in packages)


def test_admission_state_requires_independent_replication_before_admitted():
    payload = json.loads(
        (REPO_ROOT / "data/registry/physical_admission_program.json").read_text(encoding="ascii")
    )
    states = payload["promotion_states"]
    assert states.index("independently_replicated") < states.index("admitted")
    assert "independent_replication_record" in payload["raw_evidence_contract"]


def test_physical_admission_schema_rejects_unknown_states():
    payload = load_json(REPO_ROOT / "data/registry/physical_admission_program.json")
    schema = load_json(REPO_ROOT / "schemas/registry/physical_admission_program.schema.json")
    mutated = deepcopy(payload)
    mutated["packages"][0]["current_state"] = "invented_state"
    assert validate_with_jsonschema(mutated, schema)


def test_physical_admission_semantics_reject_false_promotion():
    payload = load_json(REPO_ROOT / "data/registry/physical_admission_program.json")
    mutated = deepcopy(payload)
    mutated["packages"][0]["current_state"] = "admitted"
    mutated["packages"][0]["next_required_state"] = "none"
    errors = semantic_checks("physical_admission_program.json", mutated)
    assert any("state_evidence" in error for error in errors)
    assert any("cannot retain blockers" in error for error in errors)


def test_physical_admission_semantics_reject_unknown_cross_references():
    payload = load_json(REPO_ROOT / "data/registry/physical_admission_program.json")
    mutated = deepcopy(payload)
    mutated["packages"][0]["claim_id"] = "missing_claim"
    mutated["packages"][0]["hypothesis_id"] = "hyp_missing"
    errors = semantic_checks("physical_admission_program.json", mutated)
    assert any("unknown canonical claim" in error for error in errors)
    assert any("unknown canonical hypothesis" in error for error in errors)
