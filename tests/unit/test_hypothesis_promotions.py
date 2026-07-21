"""Tests for the independent-reproduction manuscript promotion gate."""

from __future__ import annotations

import hashlib
import json
import subprocess
from copy import deepcopy
from typing import TYPE_CHECKING, Any

import scripts.validate_hypothesis_promotions as promotion_validator


if TYPE_CHECKING:
    from pathlib import Path


def write_json(path: Path, payload: dict[str, Any]) -> str:
    """Write deterministic ASCII JSON and return its digest."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="ascii",
    )
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_text(path: Path, content: str) -> str:
    """Write ASCII text and return its digest."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="ascii")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_command(repository: Path, *arguments: str) -> str:
    """Run one local Git command in a temporary validation repository."""
    return subprocess.run(
        ["git", *arguments],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def build_validation_fixture(tmp_path: Path, monkeypatch: Any) -> dict[str, Any]:
    """Create one fully valid negative-result promotion record."""
    preregistration_relpath = "protocol.json"
    preregistration_sha256 = write_json(
        tmp_path / preregistration_relpath,
        {"schema_version": 1, "locked": True},
    )
    environment_relpath = "Dockerfile"
    environment_sha256 = write_text(tmp_path / environment_relpath, "FROM scratch\n")
    primary_relpath = "primary.json"
    primary_sha256 = write_json(
        tmp_path / primary_relpath,
        {"schema_version": 1, "scientific_outcome": "falsified"},
    )
    reproduction_relpath = "reproduction.json"
    reproduction_sha256 = write_json(
        tmp_path / reproduction_relpath,
        {"schema_version": 1, "scientific_outcome": "falsified"},
    )
    environment_report_relpath = "environment_report.json"
    environment_report_sha256 = write_json(
        tmp_path / environment_report_relpath,
        {"schema_version": 1, "outputs": []},
    )
    image_identity_relpath = "image_identity.json"
    image_identity_sha256 = write_json(
        tmp_path / image_identity_relpath,
        {"schema_version": 1, "image_id": "sha256:" + "1" * 64},
    )
    run_log_relpath = "docker_compose_run.log"
    run_log_sha256 = write_text(tmp_path / run_log_relpath, "resumed=0\n")

    git_command(tmp_path, "init", "-q")
    git_command(tmp_path, "config", "user.email", "validation@example.invalid")
    git_command(tmp_path, "config", "user.name", "Validation Fixture")
    git_command(tmp_path, "add", preregistration_relpath)
    git_command(tmp_path, "commit", "-q", "-m", "test: bind protocol")
    source_commit = git_command(tmp_path, "rev-parse", "HEAD")

    image_digest = "sha256:" + "1" * 64
    verification_relpath = "verification_report.json"
    verification_payload = {
        "schema_version": 1,
        "source_commit": source_commit,
        "image_reference": "reproduction-evidence-reproduction:latest",
        "image_digest": image_digest,
        "all_checks_passed": True,
        "environment_report": {
            "relpath": environment_report_relpath,
            "sha256": environment_report_sha256,
        },
        "image_identity": {
            "relpath": image_identity_relpath,
            "sha256": image_identity_sha256,
        },
        "source_identity": [{"relpath": "runner.py", "match": True}],
        "source_tree_contract": {
            "image_file_count": 1,
            "committed_file_count": 1,
            "missing_required_source_paths": [],
            "unexpected_image_paths": [],
            "all_image_files_match_commit": True,
        },
        "input_identity": [{"relpath": "data/registry/lbm_evidence_audit.json", "match": True}],
        "environment_outputs": [
            {"relpath": relpath, "match": True}
            for relpath in sorted(promotion_validator.EXPECTED_REPRODUCTION_OUTPUT_PATHS)
        ],
        "cache_isolation": {
            "relpath": run_log_relpath,
            "sha256": run_log_sha256,
            "match": True,
        },
        "json_comparisons": [
            {"comparison_id": comparison_id, "normalized_json_identical": True}
            for comparison_id in sorted(promotion_validator.EXPECTED_JSON_COMPARISON_IDS)
        ],
        "archive_comparisons": [
            {"comparison_id": comparison_id, "byte_identical": True}
            for comparison_id in sorted(promotion_validator.EXPECTED_ARCHIVE_COMPARISON_IDS)
        ],
    }
    verification_sha256 = write_json(tmp_path / verification_relpath, verification_payload)
    hypothesis_payload = {
        "schema_version": 1,
        "hypotheses": [
            {
                "id": "hyp_negative_result",
                "implementation_status": "implemented_negative",
                "paper_promotion": "promoted",
                "independent_reproduction": {"status": "passed"},
            }
        ],
    }
    hypothesis_path = tmp_path / "hypotheses.json"
    write_json(hypothesis_path, hypothesis_payload)
    manuscript_section_relpath = "papers/sections/result.tex"
    write_text(
        tmp_path / manuscript_section_relpath,
        "\\registeredresult{hyp_negative_result}\n",
    )
    manuscript_path = tmp_path / "manuscript_results.json"
    write_json(
        manuscript_path,
        {
            "schema_version": 1,
            "description": "Test result admission.",
            "records": [
                {
                    "hypothesis_id": "hyp_negative_result",
                    "result_relpath": primary_relpath,
                    "section_relpaths": [manuscript_section_relpath],
                }
            ],
        },
    )
    record = {
        "reproduction_id": "repro_negative_result",
        "hypothesis_id": "hyp_negative_result",
        "runner_id": "clean_runner",
        "reviewed_by": "independent_reviewer",
        "primary_source_commit": source_commit,
        "reproduction_source_commit": source_commit,
        "environment_image_digest": image_digest,
        "environment_definition_relpath": environment_relpath,
        "environment_definition_sha256": environment_sha256,
        "verification_report_relpath": verification_relpath,
        "verification_report_sha256": verification_sha256,
        "preregistration_relpath": preregistration_relpath,
        "preregistration_sha256": preregistration_sha256,
        "primary_result_relpath": primary_relpath,
        "primary_result_sha256": primary_sha256,
        "reproduction_result_relpath": reproduction_relpath,
        "reproduction_result_sha256": reproduction_sha256,
        "primary_outcome": "falsified",
        "reproduction_outcome": "falsified",
        "command": "docker compose run --rm evidence-reproduction",
        "status": "passed",
        "independent_execution": True,
        "primary_cache_reused": False,
        "clean_environment": True,
        "outcome_match": True,
        "evidence_paths": [
            {"relpath": environment_report_relpath, "sha256": environment_report_sha256},
            {"relpath": image_identity_relpath, "sha256": image_identity_sha256},
            {"relpath": run_log_relpath, "sha256": run_log_sha256},
        ],
    }
    reproduction_path = tmp_path / "reproductions.json"
    write_json(reproduction_path, {"schema_version": 1, "records": [record]})
    monkeypatch.setattr(promotion_validator, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(promotion_validator, "HYPOTHESIS_PATH", hypothesis_path)
    monkeypatch.setattr(promotion_validator, "REPRODUCTION_PATH", reproduction_path)
    monkeypatch.setattr(promotion_validator, "MANUSCRIPT_RESULTS_PATH", manuscript_path)
    return {
        "record": record,
        "reproduction_path": reproduction_path,
        "verification_path": tmp_path / verification_relpath,
        "verification_payload": verification_payload,
    }


def test_current_registry_has_no_illegal_promotions():
    assert promotion_validator.validate_promotions() == []


def test_valid_negative_result_promotion_passes(tmp_path, monkeypatch):
    build_validation_fixture(tmp_path, monkeypatch)
    assert promotion_validator.validate_promotions() == []


def test_verification_failure_is_fail_closed(tmp_path, monkeypatch):
    fixture = build_validation_fixture(tmp_path, monkeypatch)
    verification = deepcopy(fixture["verification_payload"])
    verification["archive_comparisons"][0]["byte_identical"] = False
    write_json(fixture["verification_path"], verification)
    errors = promotion_validator.validate_promotions()
    assert any("verification report: digest mismatch" in error for error in errors)
    assert any("clean-reproduction verification did not pass" in error for error in errors)


def test_incomplete_comparison_set_is_fail_closed(tmp_path, monkeypatch):
    fixture = build_validation_fixture(tmp_path, monkeypatch)
    verification = deepcopy(fixture["verification_payload"])
    verification["json_comparisons"].pop()
    write_json(fixture["verification_path"], verification)
    errors = promotion_validator.validate_promotions()
    assert any("verification schema json_comparisons" in error for error in errors)
    assert any("clean-reproduction verification did not pass" in error for error in errors)


def test_truthy_strings_cannot_forge_verification(tmp_path, monkeypatch):
    fixture = build_validation_fixture(tmp_path, monkeypatch)
    verification = deepcopy(fixture["verification_payload"])
    verification["all_checks_passed"] = "true"
    verification["source_identity"][0]["match"] = "true"
    write_json(fixture["verification_path"], verification)
    errors = promotion_validator.validate_promotions()
    assert any("clean-reproduction verification did not pass" in error for error in errors)


def test_runner_reviewer_identity_and_cache_reuse_are_rejected(tmp_path, monkeypatch):
    fixture = build_validation_fixture(tmp_path, monkeypatch)
    record = fixture["record"]
    record["reviewed_by"] = record["runner_id"]
    record["primary_cache_reused"] = True
    write_json(
        fixture["reproduction_path"],
        {"schema_version": 1, "records": [record]},
    )
    errors = promotion_validator.validate_promotions()
    assert any("runner and reviewer must differ" in error for error in errors)
    assert any("reused the primary run cache" in error for error in errors)


def test_traversal_and_symlink_escape_are_rejected(tmp_path, monkeypatch):
    fixture = build_validation_fixture(tmp_path, monkeypatch)
    outside_path = tmp_path.parent / "outside-evidence.txt"
    outside_sha256 = write_text(outside_path, "outside\n")
    record = fixture["record"]
    record["environment_definition_relpath"] = "../outside-evidence.txt"
    record["environment_definition_sha256"] = outside_sha256
    escape_path = tmp_path / "escape.txt"
    escape_path.symlink_to(outside_path)
    record["evidence_paths"].append({"relpath": "escape.txt", "sha256": outside_sha256})
    write_json(
        fixture["reproduction_path"],
        {"schema_version": 1, "records": [record]},
    )
    errors = promotion_validator.validate_promotions()
    assert any("unsafe evidence path ../outside-evidence.txt" in error for error in errors)
    assert any("unsafe evidence path escape.txt" in error for error in errors)
