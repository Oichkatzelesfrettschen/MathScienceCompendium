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
    runner_relpath = "runner.py"
    runner_sha256 = write_text(tmp_path / runner_relpath, "VALUE = 1\n")
    environment_relpath = "Dockerfile"
    environment_sha256 = write_text(tmp_path / environment_relpath, "FROM scratch\n")
    primary_relpath = promotion_validator.EXPECTED_JSON_COMPARISONS[
        "triad_selector_audit"
    ][0]
    primary_sha256 = write_json(
        tmp_path / primary_relpath,
        {"schema_version": 1, "scientific_outcome": "falsified"},
    )

    git_command(tmp_path, "init", "-q")
    git_command(tmp_path, "config", "user.email", "validation@example.invalid")
    git_command(tmp_path, "config", "user.name", "Validation Fixture")
    git_command(
        tmp_path,
        "add",
        preregistration_relpath,
        runner_relpath,
        environment_relpath,
        primary_relpath,
    )
    git_command(tmp_path, "commit", "-q", "-m", "test: bind protocol and evidence")
    source_commit = git_command(tmp_path, "rev-parse", "HEAD")

    input_relpath = "data/registry/lbm_evidence_audit.json"
    input_sha256 = write_json(tmp_path / input_relpath, {"schema_version": 1})

    json_payloads = {
        "triad_selector_audit": {
            "schema_version": 1,
            "scientific_outcome": "falsified",
        },
        "beta_plane_production": {
            "schema_version": 1,
            "source_commit": source_commit,
            "aggregate_decision": "not_supported",
            "execution_receipt": promotion_validator.EXPECTED_EXECUTION_RECEIPTS[
                "production"
            ],
        },
        "beta_plane_refinement": {
            "schema_version": 1,
            "source_commit": source_commit,
            "aggregate_decision": "refinement_complete",
            "execution_receipt": promotion_validator.EXPECTED_EXECUTION_RECEIPTS[
                "refinement"
            ],
        },
        "beta_plane_controls": {
            "schema_version": 1,
            "source_commit": source_commit,
            "retained_lbm_null_control": {"audit_sha256": input_sha256},
        },
    }
    json_digests: dict[str, tuple[str, str]] = {}
    for comparison_id, paths in promotion_validator.EXPECTED_JSON_COMPARISONS.items():
        primary_json_relpath, reproduction_json_relpath = paths
        payload = json_payloads[comparison_id]
        primary_digest = write_json(tmp_path / primary_json_relpath, payload)
        reproduction_digest = write_json(tmp_path / reproduction_json_relpath, payload)
        json_digests[comparison_id] = (primary_digest, reproduction_digest)

    archive_digests: dict[str, tuple[str, str]] = {}
    for comparison_id, paths in promotion_validator.EXPECTED_ARCHIVE_COMPARISONS.items():
        primary_archive_relpath, reproduction_archive_relpath = paths
        content = f"{comparison_id}\n"
        primary_digest = write_text(tmp_path / primary_archive_relpath, content)
        reproduction_digest = write_text(tmp_path / reproduction_archive_relpath, content)
        archive_digests[comparison_id] = (primary_digest, reproduction_digest)

    primary_relpath, reproduction_relpath = promotion_validator.EXPECTED_JSON_COMPARISONS[
        "triad_selector_audit"
    ]
    primary_sha256, reproduction_sha256 = json_digests["triad_selector_audit"]

    output_records = []
    for relpath in sorted(promotion_validator.EXPECTED_REPRODUCTION_OUTPUT_PATHS):
        output_path = tmp_path / relpath
        output_records.append(
            {
                "relpath": relpath,
                "sha256": hashlib.sha256(output_path.read_bytes()).hexdigest(),
                "size_bytes": output_path.stat().st_size,
            }
        )
    environment_report_relpath = "environment_report.json"
    environment_report_sha256 = write_json(
        tmp_path / environment_report_relpath,
        {
            "schema_version": 1,
            "source_commit": source_commit,
            "execution_receipts": promotion_validator.EXPECTED_EXECUTION_RECEIPTS,
            "outputs": output_records,
        },
    )
    image_identity_relpath = "image_identity.json"
    image_digest = "sha256:" + "1" * 64
    image_identity_sha256 = write_json(
        tmp_path / image_identity_relpath,
        {
            "schema_version": 1,
            "image_id": image_digest,
            "image_reference": "reproduction-evidence-reproduction:latest",
        },
    )
    run_log_relpath = "docker_compose_run.log"
    run_log_sha256 = write_text(tmp_path / run_log_relpath, "resumed=0\n")
    harness_records = []
    for relpath in sorted(promotion_validator.EXPECTED_VERIFICATION_HARNESS_PATHS):
        digest = write_text(tmp_path / relpath, f"fixture {relpath}\n")
        harness_records.append({"relpath": relpath, "sha256": digest})

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
        "verification_harness": harness_records,
        "source_identity": [
            {
                "relpath": runner_relpath,
                "committed_sha256": runner_sha256,
                "image_sha256": runner_sha256,
                "match": True,
            },
            {
                "relpath": preregistration_relpath,
                "committed_sha256": preregistration_sha256,
                "image_sha256": preregistration_sha256,
                "match": True,
            },
            {
                "relpath": environment_relpath,
                "committed_sha256": environment_sha256,
                "image_sha256": environment_sha256,
                "match": True,
            },
            {
                "relpath": primary_relpath,
                "committed_sha256": primary_sha256,
                "image_sha256": primary_sha256,
                "match": True,
            }
        ],
        "source_tree_contract": {
            "image_file_count": 4,
            "committed_file_count": 4,
            "missing_required_source_paths": [],
            "unexpected_image_paths": [],
            "all_image_files_match_commit": True,
        },
        "input_identity": [
            {
                "relpath": input_relpath,
                "host_sha256": input_sha256,
                "image_sha256": input_sha256,
                "primary_declared_sha256": input_sha256,
                "reproduction_declared_sha256": input_sha256,
                "match": True,
            }
        ],
        "environment_outputs": [
            {
                "relpath": record["relpath"],
                "declared_sha256": record["sha256"],
                "actual_sha256": record["sha256"],
                "declared_size_bytes": record["size_bytes"],
                "actual_size_bytes": record["size_bytes"],
                "match": True,
            }
            for record in output_records
        ],
        "cache_isolation": {
            "relpath": run_log_relpath,
            "sha256": run_log_sha256,
            "execution_receipts": promotion_validator.EXPECTED_EXECUTION_RECEIPTS,
            "expected_execution_receipts": promotion_validator.EXPECTED_EXECUTION_RECEIPTS,
            "match": True,
        },
        "json_comparisons": [
            {
                "comparison_id": comparison_id,
                "primary_relpath": paths[0],
                "reproduction_relpath": paths[1],
                "primary_sha256": json_digests[comparison_id][0],
                "reproduction_sha256": json_digests[comparison_id][1],
                "primary_source_commit": json_payloads[comparison_id].get("source_commit"),
                "reproduction_source_commit": json_payloads[comparison_id].get(
                    "source_commit"
                ),
                "byte_identical": True,
                "normalized_json_identical": True,
            }
            for comparison_id, paths in sorted(
                promotion_validator.EXPECTED_JSON_COMPARISONS.items()
            )
        ],
        "archive_comparisons": [
            {
                "comparison_id": comparison_id,
                "primary_relpath": paths[0],
                "reproduction_relpath": paths[1],
                "primary_sha256": archive_digests[comparison_id][0],
                "reproduction_sha256": archive_digests[comparison_id][1],
                "byte_identical": True,
            }
            for comparison_id, paths in sorted(
                promotion_validator.EXPECTED_ARCHIVE_COMPARISONS.items()
            )
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
        "primary_artifact_commit": source_commit,
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
    monkeypatch.setitem(
        promotion_validator.EXPECTED_RECORD_BINDINGS,
        "hyp_negative_result",
        {
            "comparison_id": "triad_selector_audit",
            "preregistration_relpath": preregistration_relpath,
            "primary_result_relpath": primary_relpath,
            "reproduction_result_relpath": reproduction_relpath,
        },
    )
    monkeypatch.setattr(
        promotion_validator,
        "EXPECTED_ENVIRONMENT_DEFINITION_RELPATH",
        environment_relpath,
    )
    monkeypatch.setattr(
        promotion_validator,
        "EXPECTED_VERIFICATION_REPORT_RELPATH",
        verification_relpath,
    )
    monkeypatch.setattr(
        promotion_validator,
        "EXPECTED_ENVIRONMENT_REPORT_RELPATH",
        environment_report_relpath,
    )
    monkeypatch.setattr(
        promotion_validator,
        "EXPECTED_IMAGE_IDENTITY_RELPATH",
        image_identity_relpath,
    )
    monkeypatch.setattr(
        promotion_validator,
        "EXPECTED_RUN_LOG_RELPATH",
        run_log_relpath,
    )
    return {
        "record": record,
        "reproduction_path": reproduction_path,
        "verification_path": tmp_path / verification_relpath,
        "verification_payload": verification_payload,
    }


def rebind_verification_report(fixture: dict[str, Any], payload: dict[str, Any]) -> None:
    """Rewrite a fixture report and bind its new digest in the reproduction registry."""
    verification_sha256 = write_json(fixture["verification_path"], payload)
    fixture["record"]["verification_report_sha256"] = verification_sha256
    write_json(
        fixture["reproduction_path"],
        {"schema_version": 1, "records": [fixture["record"]]},
    )


def test_current_registry_has_no_illegal_promotions():
    payload = json.loads(promotion_validator.REPRODUCTION_PATH.read_text(encoding="ascii"))
    assert len(payload["records"]) == 2
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


def test_live_reproduction_output_tampering_is_recomputed(tmp_path, monkeypatch):
    build_validation_fixture(tmp_path, monkeypatch)
    write_text(
        tmp_path / "data/reproduction/beta_plane_production_arrays.tar",
        "tampered\n",
    )
    errors = promotion_validator.validate_promotions()
    assert any("clean-reproduction verification did not pass" in error for error in errors)


def test_forged_source_digest_is_recomputed(tmp_path, monkeypatch):
    fixture = build_validation_fixture(tmp_path, monkeypatch)
    verification = deepcopy(fixture["verification_payload"])
    verification["source_identity"][0]["committed_sha256"] = "f" * 64
    verification["source_identity"][0]["image_sha256"] = "f" * 64
    rebind_verification_report(fixture, verification)
    errors = promotion_validator.validate_promotions()
    assert any("clean-reproduction verification did not pass" in error for error in errors)


def test_omitted_committed_source_path_is_rejected(tmp_path, monkeypatch):
    fixture = build_validation_fixture(tmp_path, monkeypatch)
    verification = deepcopy(fixture["verification_payload"])
    verification["source_identity"].pop()
    verification["source_tree_contract"]["image_file_count"] = 1
    rebind_verification_report(fixture, verification)
    errors = promotion_validator.validate_promotions()
    assert any("clean-reproduction verification did not pass" in error for error in errors)


def test_comparison_path_substitution_is_rejected(tmp_path, monkeypatch):
    fixture = build_validation_fixture(tmp_path, monkeypatch)
    verification = deepcopy(fixture["verification_payload"])
    first_path = verification["json_comparisons"][0]["primary_relpath"]
    verification["json_comparisons"][0]["primary_relpath"] = verification[
        "json_comparisons"
    ][1]["primary_relpath"]
    verification["json_comparisons"][1]["primary_relpath"] = first_path
    rebind_verification_report(fixture, verification)
    errors = promotion_validator.validate_promotions()
    assert any("clean-reproduction verification did not pass" in error for error in errors)


def test_omitted_comparison_digest_is_rejected_by_schema(tmp_path, monkeypatch):
    fixture = build_validation_fixture(tmp_path, monkeypatch)
    verification = deepcopy(fixture["verification_payload"])
    del verification["json_comparisons"][0]["primary_sha256"]
    rebind_verification_report(fixture, verification)
    errors = promotion_validator.validate_promotions()
    assert any("verification schema json_comparisons.0" in error for error in errors)
    assert any("clean-reproduction verification did not pass" in error for error in errors)


def test_verification_harness_drift_is_rejected(tmp_path, monkeypatch):
    build_validation_fixture(tmp_path, monkeypatch)
    write_text(tmp_path / "scripts/verify_clean_reproduction.py", "changed\n")
    errors = promotion_validator.validate_promotions()
    assert any("clean-reproduction verification did not pass" in error for error in errors)


def test_outer_record_path_substitution_is_rejected(tmp_path, monkeypatch):
    fixture = build_validation_fixture(tmp_path, monkeypatch)
    unrelated_primary = "unrelated_primary.json"
    unrelated_reproduction = "unrelated_reproduction.json"
    payload = {"schema_version": 1, "scientific_outcome": "falsified"}
    fixture["record"]["primary_result_relpath"] = unrelated_primary
    fixture["record"]["primary_result_sha256"] = write_json(
        tmp_path / unrelated_primary, payload
    )
    fixture["record"]["reproduction_result_relpath"] = unrelated_reproduction
    fixture["record"]["reproduction_result_sha256"] = write_json(
        tmp_path / unrelated_reproduction, payload
    )
    write_json(
        fixture["reproduction_path"],
        {"schema_version": 1, "records": [fixture["record"]]},
    )
    errors = promotion_validator.validate_promotions()
    assert any("primary_result_relpath violates exact evidence binding" in error for error in errors)
    assert any(
        "reproduction_result_relpath violates exact evidence binding" in error for error in errors
    )


def test_primary_result_must_match_its_source_commit(tmp_path, monkeypatch):
    fixture = build_validation_fixture(tmp_path, monkeypatch)
    altered_digest = write_json(
        tmp_path / fixture["record"]["primary_result_relpath"],
        {"schema_version": 1, "scientific_outcome": "falsified", "altered": True},
    )
    fixture["record"]["primary_result_sha256"] = altered_digest
    write_json(
        fixture["reproduction_path"],
        {"schema_version": 1, "records": [fixture["record"]]},
    )
    errors = promotion_validator.validate_promotions()
    assert any("primary result is not bound to its artifact commit" in error for error in errors)


def test_live_result_receipt_cannot_be_rewritten_as_fresh(tmp_path, monkeypatch):
    fixture = build_validation_fixture(tmp_path, monkeypatch)
    reproduction_relpath = promotion_validator.EXPECTED_JSON_COMPARISONS[
        "beta_plane_production"
    ][1]
    reproduction_path = tmp_path / reproduction_relpath
    reproduction = json.loads(reproduction_path.read_text(encoding="ascii"))
    reproduction["execution_receipt"] = {
        "fresh_execution_required": True,
        "work_root_existed_before": True,
        "resumed_count": 1,
        "pending_count": 539,
        "total_count": 540,
    }
    reproduction_sha256 = write_json(reproduction_path, reproduction)

    environment_path = tmp_path / promotion_validator.EXPECTED_ENVIRONMENT_REPORT_RELPATH
    environment = json.loads(environment_path.read_text(encoding="ascii"))
    environment_output = next(
        record for record in environment["outputs"] if record["relpath"] == reproduction_relpath
    )
    environment_output["sha256"] = reproduction_sha256
    environment_output["size_bytes"] = reproduction_path.stat().st_size
    environment_sha256 = write_json(environment_path, environment)

    verification = deepcopy(fixture["verification_payload"])
    verification["environment_report"]["sha256"] = environment_sha256
    verification_output = next(
        record
        for record in verification["environment_outputs"]
        if record["relpath"] == reproduction_relpath
    )
    verification_output["declared_sha256"] = reproduction_sha256
    verification_output["actual_sha256"] = reproduction_sha256
    verification_output["declared_size_bytes"] = reproduction_path.stat().st_size
    verification_output["actual_size_bytes"] = reproduction_path.stat().st_size
    comparison = next(
        record
        for record in verification["json_comparisons"]
        if record["comparison_id"] == "beta_plane_production"
    )
    comparison["reproduction_sha256"] = reproduction_sha256
    assert promotion_validator.normalized_result(
        json.loads((tmp_path / comparison["primary_relpath"]).read_text(encoding="ascii"))
    ) == promotion_validator.normalized_result(reproduction)
    assert not promotion_validator.recompute_verification(verification)
