#!/usr/bin/env python3
"""Reject supported or negative result promotion without clean reproduction."""

from __future__ import annotations

import copy
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any, cast

from jsonschema import Draft202012Validator


REPO_ROOT = Path(__file__).resolve().parent.parent
HYPOTHESIS_PATH = REPO_ROOT / "data" / "registry" / "hypothesis_registry.json"
REPRODUCTION_PATH = REPO_ROOT / "data" / "registry" / "independent_reproduction_registry.json"
MANUSCRIPT_RESULTS_PATH = REPO_ROOT / "data" / "registry" / "manuscript_result_claims.json"
VERIFICATION_SCHEMA_PATH = (
    REPO_ROOT / "schemas" / "registry" / "clean_reproduction_verification.schema.json"
)
EXPECTED_INPUT_PATHS = {"data/registry/lbm_evidence_audit.json"}
EXPECTED_JSON_COMPARISONS = {
    "triad_selector_audit": (
        "data/registry/triad_selector_audit.json",
        "data/reproduction/triad_selector_audit.json",
    ),
    "beta_plane_production": (
        "data/registry/beta_plane_sweep_results.json",
        "data/reproduction/beta_plane_sweep_results.json",
    ),
    "beta_plane_refinement": (
        "data/registry/beta_plane_refinement_results.json",
        "data/reproduction/beta_plane_refinement_results.json",
    ),
    "beta_plane_controls": (
        "data/registry/beta_plane_control_results.json",
        "data/reproduction/beta_plane_control_results.json",
    ),
}
EXPECTED_ARCHIVE_COMPARISONS = {
    "beta_plane_production_arrays": (
        "data/evidence/beta_plane/production_run_arrays.tar",
        "data/reproduction/beta_plane_production_arrays.tar",
    ),
    "beta_plane_refinement_arrays": (
        "data/evidence/beta_plane/refinement_run_arrays.tar",
        "data/reproduction/beta_plane_refinement_arrays.tar",
    ),
    "beta_plane_control_arrays": (
        "data/evidence/beta_plane/control_final_states.tar",
        "data/reproduction/beta_plane_control_arrays.tar",
    ),
}
EXPECTED_JSON_COMPARISON_IDS = set(EXPECTED_JSON_COMPARISONS)
EXPECTED_ARCHIVE_COMPARISON_IDS = set(EXPECTED_ARCHIVE_COMPARISONS)
EXPECTED_REPRODUCTION_OUTPUT_PATHS = {
    "data/reproduction/triad_selector_audit.json",
    "data/reproduction/beta_plane_sweep_results.json",
    "data/reproduction/beta_plane_refinement_results.json",
    "data/reproduction/beta_plane_control_results.json",
    "data/reproduction/beta_plane_production_arrays.tar",
    "data/reproduction/beta_plane_refinement_arrays.tar",
    "data/reproduction/beta_plane_control_arrays.tar",
}
EXPECTED_EXECUTION_RECEIPTS = {
    "production": {
        "fresh_execution_required": True,
        "work_root_existed_before": False,
        "resumed_count": 0,
        "pending_count": 540,
        "total_count": 540,
    },
    "refinement": {
        "fresh_execution_required": True,
        "work_root_existed_before": False,
        "resumed_count": 0,
        "pending_count": 48,
        "total_count": 48,
    },
}
EXPECTED_VERIFICATION_HARNESS_PATHS = {
    "scripts/verify_clean_reproduction.py",
    "scripts/validate_hypothesis_promotions.py",
    "schemas/registry/clean_reproduction_verification.schema.json",
}
ALLOWED_IMAGE_EXCLUDED_PREFIXES = ("data/evidence/", "data/reproduction/")
EXPECTED_RECORD_BINDINGS = {
    "hyp_e7_nonhomomorphic_fourier_selector": {
        "comparison_id": "triad_selector_audit",
        "preregistration_relpath": "data/registry/e7_selector_preregistration.json",
        "primary_result_relpath": "data/registry/triad_selector_audit.json",
        "reproduction_result_relpath": "data/reproduction/triad_selector_audit.json",
    },
    "hyp_beta_plane_transient_zonalization": {
        "comparison_id": "beta_plane_production",
        "preregistration_relpath": "data/registry/beta_plane_sweep_preregistration.json",
        "primary_result_relpath": "data/registry/beta_plane_sweep_results.json",
        "reproduction_result_relpath": "data/reproduction/beta_plane_sweep_results.json",
    },
}
EXPECTED_ENVIRONMENT_DEFINITION_RELPATH = "requirements-lock.txt"
EXPECTED_VERIFICATION_REPORT_RELPATH = "data/reproduction/verification_report.json"
EXPECTED_ENVIRONMENT_REPORT_RELPATH = "data/reproduction/environment_report.json"
EXPECTED_IMAGE_IDENTITY_RELPATH = "data/reproduction/image_identity.json"
EXPECTED_RUN_LOG_RELPATH = "data/reproduction/docker_compose_run.log"


def load_json(path: Path) -> dict[str, Any]:
    """Load an ASCII JSON registry."""
    return cast("dict[str, Any]", json.loads(path.read_text(encoding="ascii")))


def sha256_file(path: Path) -> str:
    """Return a file digest."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def contained_repository_path(relpath: str) -> Path | None:
    """Resolve a canonical relative path only when it remains inside the repository."""
    relative_path = Path(relpath)
    if relative_path.is_absolute() or ".." in relative_path.parts:
        return None
    repository_root = REPO_ROOT.resolve()
    resolved_path = (repository_root / relative_path).resolve()
    return resolved_path if resolved_path.is_relative_to(repository_root) else None


def committed_digest(commit: str, relpath: str) -> str | None:
    """Return a file digest from a committed tree, or None when absent."""
    if contained_repository_path(relpath) is None:
        return None
    completed = subprocess.run(
        ["git", "show", f"{commit}:{relpath}"],
        cwd=REPO_ROOT,
        capture_output=True,
        check=False,
    )
    return hashlib.sha256(completed.stdout).hexdigest() if completed.returncode == 0 else None


def committed_paths(commit: str) -> set[str] | None:
    """Return every regular path in a committed Git tree."""
    completed = subprocess.run(
        ["git", "ls-tree", "-r", "-z", "--name-only", commit],
        cwd=REPO_ROOT,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        return None
    return {
        path.decode("utf-8")
        for path in completed.stdout.split(b"\0")
        if path
    }


def check_file_digest(errors: list[str], prefix: str, relpath: str, digest: str) -> None:
    """Require a repository file and its declared digest."""
    path = contained_repository_path(relpath)
    if path is None:
        errors.append(f"{prefix}: unsafe evidence path {relpath}")
        return
    if not path.is_file():
        errors.append(f"{prefix}: missing evidence {relpath}")
    elif sha256_file(path) != digest:
        errors.append(f"{prefix}: digest mismatch for {relpath}")


def result_outcome(relpath: str) -> str | None:
    """Read the declared scientific outcome from a result JSON artifact."""
    path = contained_repository_path(relpath)
    if path is None or not path.is_file():
        return None
    payload = load_json(path)
    for field in ("aggregate_decision", "scientific_outcome"):
        value = payload.get(field)
        if isinstance(value, str):
            return value
    return None


def result_source_commit(relpath: str) -> str | None:
    """Read a source commit from a result artifact when the format carries one."""
    path = contained_repository_path(relpath)
    if path is None or not path.is_file():
        return None
    value = load_json(path).get("source_commit")
    return value if isinstance(value, str) else None


def normalized_result(payload: dict[str, Any]) -> dict[str, Any]:
    """Remove only declared execution-provenance differences."""
    normalized = copy.deepcopy(payload)
    if "source_commit" in normalized:
        normalized["source_commit"] = "<execution-source-commit>"
    normalized.pop("execution_receipt", None)
    evidence_archive = normalized.get("evidence_archive")
    if isinstance(evidence_archive, dict) and "relpath" in evidence_archive:
        evidence_archive["relpath"] = "<independent-output-root>"
    return normalized


def records_by_key(value: Any, key: str) -> dict[str, dict[str, Any]] | None:
    """Index a record list only when keys are strings and unique."""
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        return None
    keyed: dict[str, dict[str, Any]] = {}
    for item in value:
        item_key = item.get(key)
        if not isinstance(item_key, str) or item_key in keyed:
            return None
        keyed[item_key] = item
    return keyed


def nonempty_records_all_true(value: Any, field: str) -> bool:
    """Require a nonempty record list whose named field is the JSON boolean true."""
    return (
        isinstance(value, list)
        and bool(value)
        and all(isinstance(item, dict) and item.get(field) is True for item in value)
    )


def record_values(value: Any, field: str) -> list[Any] | None:
    """Return one field from a record list, or None for malformed input."""
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        return None
    return [item.get(field) for item in value]


def recompute_verification(verification: dict[str, Any]) -> bool:
    """Recompute every live or committed claim in a clean-reproduction report."""
    try:
        source_commit = verification["source_commit"]
        source_identity = records_by_key(verification["source_identity"], "relpath")
        source_contract = verification["source_tree_contract"]
        if source_identity is None or not source_identity:
            raise ValueError("verification evidence mismatch")
        source_matches = all(
            record["committed_sha256"] == committed_digest(source_commit, relpath)
            and record["image_sha256"] == record["committed_sha256"]
            and record["match"] is True
            for relpath, record in source_identity.items()
        )
        all_committed_paths = committed_paths(source_commit)
        if all_committed_paths is None:
            raise ValueError("verification evidence mismatch")
        omitted_image_paths = all_committed_paths.difference(source_identity)
        exact_source_set_matches = (
            set(source_identity).issubset(all_committed_paths)
            and all(
                relpath.startswith(ALLOWED_IMAGE_EXCLUDED_PREFIXES)
                for relpath in omitted_image_paths
            )
        )
        source_contract_matches = (
            source_contract["all_image_files_match_commit"] is True
            and source_contract["missing_required_source_paths"] == []
            and source_contract["unexpected_image_paths"] == []
            and source_contract["image_file_count"] == len(source_identity)
            and source_contract["committed_file_count"] == len(all_committed_paths)
        )

        input_identity = records_by_key(verification["input_identity"], "relpath")
        if input_identity is None or set(input_identity) != EXPECTED_INPUT_PATHS:
            raise ValueError("verification evidence mismatch")
        primary_controls = load_json(REPO_ROOT / "data/registry/beta_plane_control_results.json")
        reproduction_controls = load_json(
            REPO_ROOT / "data/reproduction/beta_plane_control_results.json"
        )
        input_matches = True
        for relpath, record in input_identity.items():
            input_path = contained_repository_path(relpath)
            if input_path is None or not input_path.is_file():
                raise ValueError("verification evidence mismatch")
            host_digest = sha256_file(input_path)
            primary_declared = primary_controls["retained_lbm_null_control"]["audit_sha256"]
            reproduction_declared = reproduction_controls["retained_lbm_null_control"][
                "audit_sha256"
            ]
            input_matches &= (
                record["host_sha256"] == host_digest
                and record["image_sha256"] == host_digest
                and record["primary_declared_sha256"] == primary_declared == host_digest
                and record["reproduction_declared_sha256"]
                == reproduction_declared
                == host_digest
                and record["match"] is True
            )

        environment_evidence = verification["environment_report"]
        if environment_evidence["relpath"] != EXPECTED_ENVIRONMENT_REPORT_RELPATH:
            raise ValueError("verification evidence mismatch")
        environment_path = contained_repository_path(environment_evidence["relpath"])
        if environment_path is None or not environment_path.is_file():
            raise ValueError("verification evidence mismatch")
        environment_report = load_json(environment_path)
        environment_declared = records_by_key(environment_report["outputs"], "relpath")
        environment_outputs = records_by_key(verification["environment_outputs"], "relpath")
        if (
            environment_declared is None
            or environment_outputs is None
            or set(environment_declared) != EXPECTED_REPRODUCTION_OUTPUT_PATHS
            or set(environment_outputs) != EXPECTED_REPRODUCTION_OUTPUT_PATHS
        ):
            raise ValueError("verification evidence mismatch")
        environment_matches = environment_report["source_commit"] == source_commit
        for relpath, record in environment_outputs.items():
            output_path = contained_repository_path(relpath)
            if output_path is None or not output_path.is_file():
                raise ValueError("verification evidence mismatch")
            actual_digest = sha256_file(output_path)
            actual_size = output_path.stat().st_size
            declared = environment_declared[relpath]
            environment_matches &= (
                declared["sha256"] == actual_digest
                and declared["size_bytes"] == actual_size
                and record["declared_sha256"] == actual_digest
                and record["actual_sha256"] == actual_digest
                and record["declared_size_bytes"] == actual_size
                and record["actual_size_bytes"] == actual_size
                and record["match"] is True
            )

        cache = verification["cache_isolation"]
        if cache["relpath"] != EXPECTED_RUN_LOG_RELPATH:
            raise ValueError("verification evidence mismatch")
        cache_path = contained_repository_path(cache["relpath"])
        if cache_path is None or not cache_path.is_file():
            raise ValueError("verification evidence mismatch")
        cache_matches = (
            cache["sha256"] == sha256_file(cache_path)
            and cache["execution_receipts"] == EXPECTED_EXECUTION_RECEIPTS
            and cache["expected_execution_receipts"] == EXPECTED_EXECUTION_RECEIPTS
            and environment_report["execution_receipts"] == EXPECTED_EXECUTION_RECEIPTS
            and cache["match"] is True
        )

        json_comparisons = records_by_key(verification["json_comparisons"], "comparison_id")
        if json_comparisons is None or set(json_comparisons) != set(EXPECTED_JSON_COMPARISONS):
            raise ValueError("verification evidence mismatch")
        json_matches = True
        for comparison_id, expected_paths in EXPECTED_JSON_COMPARISONS.items():
            record = json_comparisons[comparison_id]
            primary_relpath, reproduction_relpath = expected_paths
            if (
                record["primary_relpath"] != primary_relpath
                or record["reproduction_relpath"] != reproduction_relpath
            ):
                raise ValueError("verification evidence mismatch")
            primary_path = contained_repository_path(primary_relpath)
            reproduction_path = contained_repository_path(reproduction_relpath)
            if (
                primary_path is None
                or reproduction_path is None
                or not primary_path.is_file()
                or not reproduction_path.is_file()
            ):
                raise ValueError("verification evidence mismatch")
            primary_payload = load_json(primary_path)
            reproduction_payload = load_json(reproduction_path)
            byte_identical = primary_path.read_bytes() == reproduction_path.read_bytes()
            normalized_identical = normalized_result(primary_payload) == normalized_result(
                reproduction_payload
            )
            if comparison_id in {"beta_plane_production", "beta_plane_refinement"}:
                receipt_id = (
                    "production"
                    if comparison_id == "beta_plane_production"
                    else "refinement"
                )
                expected_receipt = EXPECTED_EXECUTION_RECEIPTS[receipt_id]
                if (
                    primary_payload.get("execution_receipt") != expected_receipt
                    or reproduction_payload.get("execution_receipt") != expected_receipt
                ):
                    raise ValueError("verification evidence mismatch")
            json_matches &= (
                record["primary_sha256"] == sha256_file(primary_path)
                and record["reproduction_sha256"] == sha256_file(reproduction_path)
                and record["primary_source_commit"] == primary_payload.get("source_commit")
                and record["reproduction_source_commit"]
                == reproduction_payload.get("source_commit")
                and record["byte_identical"] is byte_identical
                and record["normalized_json_identical"] is normalized_identical
                and normalized_identical
            )

        archive_comparisons = records_by_key(
            verification["archive_comparisons"], "comparison_id"
        )
        if archive_comparisons is None or set(archive_comparisons) != set(
            EXPECTED_ARCHIVE_COMPARISONS
        ):
            raise ValueError("verification evidence mismatch")
        archive_matches = True
        for comparison_id, expected_paths in EXPECTED_ARCHIVE_COMPARISONS.items():
            record = archive_comparisons[comparison_id]
            primary_relpath, reproduction_relpath = expected_paths
            if (
                record["primary_relpath"] != primary_relpath
                or record["reproduction_relpath"] != reproduction_relpath
            ):
                raise ValueError("verification evidence mismatch")
            primary_path = contained_repository_path(primary_relpath)
            reproduction_path = contained_repository_path(reproduction_relpath)
            if (
                primary_path is None
                or reproduction_path is None
                or not primary_path.is_file()
                or not reproduction_path.is_file()
            ):
                raise ValueError("verification evidence mismatch")
            primary_digest = sha256_file(primary_path)
            reproduction_digest = sha256_file(reproduction_path)
            byte_identical = primary_digest == reproduction_digest
            archive_matches &= (
                record["primary_sha256"] == primary_digest
                and record["reproduction_sha256"] == reproduction_digest
                and record["byte_identical"] is byte_identical
                and byte_identical
            )

        image_evidence = verification["image_identity"]
        if image_evidence["relpath"] != EXPECTED_IMAGE_IDENTITY_RELPATH:
            raise ValueError("verification evidence mismatch")
        image_path = contained_repository_path(image_evidence["relpath"])
        if image_path is None or not image_path.is_file():
            raise ValueError("verification evidence mismatch")
        image_identity = load_json(image_path)
        verification_harness = records_by_key(verification["verification_harness"], "relpath")
        if verification_harness is None or set(verification_harness) != set(
            EXPECTED_VERIFICATION_HARNESS_PATHS
        ):
            raise ValueError("verification evidence mismatch")
        harness_matches = True
        for relpath, record in verification_harness.items():
            harness_path = contained_repository_path(relpath)
            if harness_path is None or not harness_path.is_file():
                raise ValueError("verification evidence mismatch")
            harness_matches &= record["sha256"] == sha256_file(harness_path)
        nested_evidence_matches = (
            environment_evidence["sha256"] == sha256_file(environment_path)
            and image_evidence["sha256"] == sha256_file(image_path)
            and image_identity["image_id"] == verification["image_digest"]
            and image_identity["image_reference"] == verification["image_reference"]
        )
        return bool(
            verification["all_checks_passed"] is True
            and source_matches
            and exact_source_set_matches
            and source_contract_matches
            and input_matches
            and environment_matches
            and cache_matches
            and json_matches
            and archive_matches
            and harness_matches
            and nested_evidence_matches
        )
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return False


def validate_promotions() -> list[str]:
    """Return all violations of the manuscript-promotion contract."""
    hypothesis_payload = load_json(HYPOTHESIS_PATH)
    reproduction_payload = load_json(REPRODUCTION_PATH)
    manuscript_payload = load_json(MANUSCRIPT_RESULTS_PATH)
    errors: list[str] = []
    records = reproduction_payload["records"]
    reproduction_ids = [record["reproduction_id"] for record in records]
    hypothesis_ids = [record["hypothesis_id"] for record in records]
    if len(reproduction_ids) != len(set(reproduction_ids)):
        errors.append("reproduction registry contains duplicate reproduction IDs")
    if len(hypothesis_ids) != len(set(hypothesis_ids)):
        errors.append("reproduction registry contains duplicate hypothesis records")
    reproduction_by_hypothesis = {record["hypothesis_id"]: record for record in records}
    known_hypotheses = {hypothesis["id"] for hypothesis in hypothesis_payload["hypotheses"]}
    for record in records:
        prefix = record["reproduction_id"]
        expected_binding = EXPECTED_RECORD_BINDINGS.get(record["hypothesis_id"])
        if record["hypothesis_id"] not in known_hypotheses:
            errors.append(f"{prefix}: unknown hypothesis")
        if expected_binding is None:
            errors.append(f"{prefix}: no exact evidence binding exists for hypothesis")
        else:
            for binding_field in (
                "preregistration_relpath",
                "primary_result_relpath",
                "reproduction_result_relpath",
            ):
                if record[binding_field] != expected_binding[binding_field]:
                    errors.append(f"{prefix}: {binding_field} violates exact evidence binding")
        if (
            record["environment_definition_relpath"]
            != EXPECTED_ENVIRONMENT_DEFINITION_RELPATH
        ):
            errors.append(f"{prefix}: environment definition path is not canonical")
        if record["verification_report_relpath"] != EXPECTED_VERIFICATION_REPORT_RELPATH:
            errors.append(f"{prefix}: verification report path is not canonical")
        if record["runner_id"] == record["reviewed_by"]:
            errors.append(f"{prefix}: runner and reviewer must differ")
        if record["primary_result_relpath"] == record["reproduction_result_relpath"]:
            errors.append(f"{prefix}: primary and reproduction result paths must differ")
        if record["primary_outcome"] != record["reproduction_outcome"]:
            errors.append(f"{prefix}: declared outcomes differ")
        if record["outcome_match"] != (record["primary_outcome"] == record["reproduction_outcome"]):
            errors.append(f"{prefix}: outcome_match is inconsistent")
        for source_role in ("primary_source_commit", "reproduction_source_commit"):
            bound_digest = committed_digest(record[source_role], record["preregistration_relpath"])
            if bound_digest != record["preregistration_sha256"]:
                errors.append(f"{prefix}: {source_role} does not bind the protocol digest")
            environment_digest = committed_digest(
                record[source_role], record["environment_definition_relpath"]
            )
            if environment_digest != record["environment_definition_sha256"]:
                errors.append(
                    f"{prefix}: {source_role} does not bind the environment definition"
                )
        primary_committed_digest = committed_digest(
            record["primary_artifact_commit"], record["primary_result_relpath"]
        )
        if primary_committed_digest != record["primary_result_sha256"]:
            errors.append(f"{prefix}: primary result is not bound to its artifact commit")
        digest_fields = (
            (
                "environment definition",
                "environment_definition_relpath",
                "environment_definition_sha256",
            ),
            ("verification report", "verification_report_relpath", "verification_report_sha256"),
            ("preregistration", "preregistration_relpath", "preregistration_sha256"),
            ("primary result", "primary_result_relpath", "primary_result_sha256"),
            ("reproduction result", "reproduction_result_relpath", "reproduction_result_sha256"),
        )
        for label, path_field, digest_field in digest_fields:
            check_file_digest(
                errors, f"{prefix}: {label}", record[path_field], record[digest_field]
            )
        primary_outcome = result_outcome(record["primary_result_relpath"])
        reproduction_outcome = result_outcome(record["reproduction_result_relpath"])
        if primary_outcome != record["primary_outcome"]:
            errors.append(f"{prefix}: primary result outcome does not match its artifact")
        if reproduction_outcome != record["reproduction_outcome"]:
            errors.append(f"{prefix}: reproduction outcome does not match its artifact")
        primary_artifact_commit = result_source_commit(record["primary_result_relpath"])
        reproduction_artifact_commit = result_source_commit(record["reproduction_result_relpath"])
        if (
            primary_artifact_commit is not None
            and primary_artifact_commit != record["primary_source_commit"]
        ):
            errors.append(f"{prefix}: primary result source commit does not match")
        if (
            reproduction_artifact_commit is not None
            and reproduction_artifact_commit != record["reproduction_source_commit"]
        ):
            errors.append(f"{prefix}: reproduction result source commit does not match")
        verification_path = contained_repository_path(record["verification_report_relpath"])
        if verification_path is not None and verification_path.is_file():
            verification = load_json(verification_path)
            verification_schema = load_json(VERIFICATION_SCHEMA_PATH)
            for schema_error in sorted(
                Draft202012Validator(verification_schema).iter_errors(verification),
                key=lambda item: list(item.absolute_path),
            ):
                location = ".".join(str(part) for part in schema_error.absolute_path)
                errors.append(
                    f"{prefix}: verification schema {location or '$'}: {schema_error.message}"
                )
            source_identity = verification.get("source_identity", [])
            source_tree_contract = verification.get("source_tree_contract", {})
            input_identity = verification.get("input_identity", [])
            environment_outputs = verification.get("environment_outputs", [])
            cache_isolation = verification.get("cache_isolation", {})
            json_comparisons = verification.get("json_comparisons", [])
            archive_comparisons = verification.get("archive_comparisons", [])
            verification_checks = (
                nonempty_records_all_true(source_identity, "match")
                and nonempty_records_all_true(input_identity, "match")
                and nonempty_records_all_true(environment_outputs, "match")
                and cache_isolation.get("match") is True
                and nonempty_records_all_true(json_comparisons, "normalized_json_identical")
                and nonempty_records_all_true(archive_comparisons, "byte_identical")
            )
            input_paths = record_values(input_identity, "relpath")
            environment_paths = record_values(environment_outputs, "relpath")
            json_ids = record_values(json_comparisons, "comparison_id")
            archive_ids = record_values(archive_comparisons, "comparison_id")
            source_paths = record_values(source_identity, "relpath")
            exact_sets_match = (
                input_paths is not None
                and len(input_paths) == len(set(input_paths))
                and set(input_paths) == EXPECTED_INPUT_PATHS
                and environment_paths is not None
                and len(environment_paths) == len(set(environment_paths))
                and set(environment_paths) == EXPECTED_REPRODUCTION_OUTPUT_PATHS
                and json_ids is not None
                and len(json_ids) == len(set(json_ids))
                and set(json_ids) == EXPECTED_JSON_COMPARISON_IDS
                and archive_ids is not None
                and len(archive_ids) == len(set(archive_ids))
                and set(archive_ids) == EXPECTED_ARCHIVE_COMPARISON_IDS
            )
            source_tree_matches = (
                isinstance(source_tree_contract, dict)
                and source_tree_contract.get("all_image_files_match_commit") is True
                and source_tree_contract.get("missing_required_source_paths") == []
                and source_tree_contract.get("unexpected_image_paths") == []
                and isinstance(source_tree_contract.get("image_file_count"), int)
                and source_tree_contract.get("image_file_count", 0) > 0
                and source_paths is not None
                and len(source_paths) == source_tree_contract.get("image_file_count")
                and len(source_paths) == len(set(source_paths))
            )
            if (
                verification.get("all_checks_passed") is not True
                or not verification_checks
                or not exact_sets_match
                or not source_tree_matches
                or not recompute_verification(verification)
            ):
                errors.append(f"{prefix}: clean-reproduction verification did not pass")
            if verification.get("source_commit") != record["reproduction_source_commit"]:
                errors.append(f"{prefix}: verification source commit does not match")
            if verification.get("image_digest") != record["environment_image_digest"]:
                errors.append(f"{prefix}: verification image digest does not match")
            if expected_binding is not None:
                comparisons_by_id = records_by_key(
                    verification.get("json_comparisons", []), "comparison_id"
                )
                comparison = (
                    comparisons_by_id.get(expected_binding["comparison_id"])
                    if comparisons_by_id is not None
                    else None
                )
                if (
                    comparison is None
                    or comparison.get("primary_relpath") != record["primary_result_relpath"]
                    or comparison.get("reproduction_relpath")
                    != record["reproduction_result_relpath"]
                    or comparison.get("primary_sha256") != record["primary_result_sha256"]
                    or comparison.get("reproduction_sha256")
                    != record["reproduction_result_sha256"]
                ):
                    errors.append(f"{prefix}: outer record is not bound to verified comparison")
            for nested_label in ("environment_report", "image_identity"):
                nested = verification.get(nested_label, {})
                nested_relpath = nested.get("relpath")
                nested_sha256 = nested.get("sha256")
                if not isinstance(nested_relpath, str) or not isinstance(nested_sha256, str):
                    errors.append(f"{prefix}: verification lacks {nested_label}")
                else:
                    check_file_digest(
                        errors,
                        f"{prefix}: verification {nested_label}",
                        nested_relpath,
                        nested_sha256,
                    )
            cache_relpath = cache_isolation.get("relpath")
            cache_sha256 = cache_isolation.get("sha256")
            if not isinstance(cache_relpath, str) or not isinstance(cache_sha256, str):
                errors.append(f"{prefix}: verification lacks cache-isolation evidence")
            else:
                check_file_digest(
                    errors,
                    f"{prefix}: verification cache isolation",
                    cache_relpath,
                    cache_sha256,
                )
        seen_evidence_paths: set[str] = set()
        for evidence in record["evidence_paths"]:
            relpath = evidence["relpath"]
            if relpath in seen_evidence_paths:
                errors.append(f"{prefix}: duplicate evidence path {relpath}")
            seen_evidence_paths.add(relpath)
            check_file_digest(errors, prefix, relpath, evidence["sha256"])
    for hypothesis in hypothesis_payload["hypotheses"]:
        promotion = hypothesis["paper_promotion"]
        if promotion not in {"eligible", "promoted"}:
            continue
        hypothesis_id = hypothesis["id"]
        if hypothesis["implementation_status"] not in {
            "implemented_supported",
            "implemented_negative",
        }:
            errors.append(f"{hypothesis_id}: promotable implementation result is absent")
        if hypothesis["independent_reproduction"]["status"] != "passed":
            errors.append(f"{hypothesis_id}: hypothesis reproduction status is not passed")
        record = reproduction_by_hypothesis.get(hypothesis_id)
        if record is None:
            errors.append(f"{hypothesis_id}: independent reproduction record is absent")
            continue
        if record["status"] != "passed":
            errors.append(f"{hypothesis_id}: reproduction record did not pass")
        if not record["independent_execution"]:
            errors.append(f"{hypothesis_id}: reproduction was not independently executed")
        if record["primary_cache_reused"]:
            errors.append(f"{hypothesis_id}: reproduction reused the primary run cache")
        if not record["clean_environment"]:
            errors.append(f"{hypothesis_id}: reproduction environment was not clean")
        if not record["outcome_match"]:
            errors.append(f"{hypothesis_id}: reproduction outcome does not match")
    manuscript_records = manuscript_payload["records"]
    manuscript_ids = [record["hypothesis_id"] for record in manuscript_records]
    if len(manuscript_ids) != len(set(manuscript_ids)):
        errors.append("manuscript result registry contains duplicate hypotheses")
    marker_pattern = re.compile(r"\\registeredresult\{(hyp_[a-z0-9_]+)\}")
    marked_hypotheses: set[str] = set()
    for source_path in sorted((REPO_ROOT / "papers").rglob("*.tex")):
        marked_hypotheses.update(marker_pattern.findall(source_path.read_text(encoding="utf-8")))
    if marked_hypotheses != set(manuscript_ids):
        errors.append("manuscript result markers do not match the result registry")
    promoted_hypotheses = {
        hypothesis["id"]
        for hypothesis in hypothesis_payload["hypotheses"]
        if hypothesis["paper_promotion"] == "promoted"
    }
    if promoted_hypotheses != marked_hypotheses:
        errors.append("promoted hypotheses do not match manuscript result markers")
    for manuscript_record in manuscript_records:
        hypothesis_id = manuscript_record["hypothesis_id"]
        reproduction_record = reproduction_by_hypothesis.get(hypothesis_id)
        if reproduction_record is None:
            errors.append(f"{hypothesis_id}: manuscript result lacks reproduction record")
            continue
        result_relpath = manuscript_record["result_relpath"]
        if result_relpath not in {
            reproduction_record["primary_result_relpath"],
            reproduction_record["reproduction_result_relpath"],
        }:
            errors.append(f"{hypothesis_id}: manuscript result path is not reproduced")
        if contained_repository_path(result_relpath) is None:
            errors.append(f"{hypothesis_id}: manuscript result path is unsafe")
        for section_relpath in manuscript_record["section_relpaths"]:
            section_path = contained_repository_path(section_relpath)
            if section_path is None or not section_path.is_file():
                errors.append(f"{hypothesis_id}: manuscript section is missing or unsafe")
            elif f"\\registeredresult{{{hypothesis_id}}}" not in section_path.read_text(
                encoding="utf-8"
            ):
                errors.append(f"{hypothesis_id}: manuscript section lacks result marker")
    return errors


def main() -> int:
    errors = validate_promotions()
    if errors:
        print("Hypothesis promotion validation FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Hypothesis promotion validation PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
