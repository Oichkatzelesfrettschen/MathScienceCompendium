#!/usr/bin/env python3
"""Validate TOML and JSON registry files against JSON schemas for drift detection."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import tarfile
from datetime import datetime
from pathlib import Path
from typing import Any


try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib


try:
    from jsonschema import Draft202012Validator, FormatChecker
except ImportError:
    Draft202012Validator = None
    FormatChecker = None


REPO_ROOT = Path(__file__).resolve().parent.parent
REGISTRY_DIR = REPO_ROOT / "data" / "registry"
SCHEMA_DIR = REPO_ROOT / "schemas" / "registry"

TOML_SCHEMA_BY_REGISTRY: dict[str, str] = {
    "artifacts_index.toml": "artifacts_index.schema.json",
    "claim_coverage_report.toml": "claim_coverage_report.schema.json",
    "claim_source_crosswalk.toml": "claim_source_crosswalk.schema.json",
    "corpus_dedupe_report.toml": "corpus_dedupe_report.schema.json",
    "corpus_index.toml": "corpus_index.schema.json",
    "docs_index.toml": "docs_index.schema.json",
    "experiments_index.toml": "experiments_index.schema.json",
}

JSON_SCHEMA_BY_REGISTRY: dict[str, dict[str, object]] = {
    "aligned_research_mineru_run.json": {
        "schema": "aligned_research_mineru_run.schema.json",
        "required": True,
    },
    "beta_plane_ablation_preregistration.json": {
        "schema": "beta_plane_ablation_preregistration.schema.json",
        "required": True,
    },
    "beta_plane_ablation_results.json": {
        "schema": "beta_plane_ablation_results.schema.json",
        "required": True,
    },
    "beta_plane_control_results.json": {
        "schema": "beta_plane_control_results.schema.json",
        "required": True,
    },
    "beta_plane_refinement_results.json": {
        "schema": "beta_plane_refinement_results.schema.json",
        "required": True,
    },
    "beta_plane_refinement_protocol_amendment.json": {
        "schema": "beta_plane_refinement_protocol_amendment.schema.json",
        "required": True,
    },
    "beta_plane_sweep_preregistration.json": {
        "schema": "beta_plane_sweep_preregistration.schema.json",
        "required": True,
    },
    "beta_plane_sweep_results.json": {
        "schema": "beta_plane_sweep_results.schema.json",
        "required": True,
    },
    "cayley_dickson_property_audit.json": {
        "schema": "cayley_dickson_property_audit.schema.json",
        "required": True,
    },
    "exceptional_group_scope_audit.json": {
        "schema": "exceptional_group_scope_audit.schema.json",
        "required": True,
    },
    "experimental_admission_packages.json": {
        "schema": "experimental_admission_packages.schema.json",
        "required": True,
    },
    "e7_selector_preregistration.json": {
        "schema": "e7_selector_preregistration.schema.json",
        "required": True,
    },
    "claim_gate_registry.json": {
        "schema": "claim_gate_registry.schema.json",
        "required": True,
    },
    "claim_gate_results.json": {
        "schema": "claim_gate_results.schema.json",
        "required": True,
    },
    "critique_evidence_ledger.json": {
        "schema": "critique_evidence_ledger.schema.json",
        "required": True,
    },
    "document_decomposition_audit.json": {
        "schema": "document_decomposition_audit.schema.json",
        "required": True,
    },
    "document_ocr_run_manifest.json": {
        "schema": "document_ocr_run_manifest.schema.json",
        "required": True,
    },
    "framework_document_decomposition.json": {
        "schema": "framework_document_decomposition.schema.json",
        "required": True,
    },
    "framework_overlap_audit.json": {
        "schema": "framework_overlap_audit.schema.json",
        "required": True,
    },
    "lbm_evidence_audit.json": {
        "schema": "lbm_evidence_audit.schema.json",
        "required": True,
    },
    "fourier_quotient_audit.json": {
        "schema": "fourier_quotient_audit.schema.json",
        "required": True,
    },
    "hypothesis_registry.json": {
        "schema": "hypothesis_registry.schema.json",
        "required": True,
    },
    "independent_reproduction_registry.json": {
        "schema": "independent_reproduction_registry.schema.json",
        "required": True,
    },
    "manuscript_result_claims.json": {
        "schema": "manuscript_result_claims.schema.json",
        "required": True,
    },
    "lbm_root_order_audit.json": {
        "schema": "lbm_root_order_audit.schema.json",
        "required": True,
    },
    "parquet_audit.json": {
        "schema": "parquet_audit.schema.json",
        "required": True,
    },
    "physical_admission_program.json": {
        "schema": "physical_admission_program.schema.json",
        "required": True,
    },
    "pdf_archive_index.json": {
        "schema": "pdf_archive_index.schema.json",
        "required": False,
    },
    "pdf_ocr_comparison.json": {
        "schema": "pdf_ocr_comparison.schema.json",
        "required": True,
    },
    "pdf_ocr_visual_review.json": {
        "schema": "pdf_ocr_visual_review.schema.json",
        "required": True,
    },
    "pdf_text_quality_audit.json": {
        "schema": "pdf_text_quality_audit.schema.json",
        "required": True,
    },
    "tesseract_fallback_run.json": {
        "schema": "tesseract_fallback_run.schema.json",
        "required": True,
    },
    "triad_selector_audit.json": {
        "schema": "triad_selector_audit.schema.json",
        "required": True,
    },
    "unified_framework_claims.json": {
        "schema": "unified_framework_claims.schema.json",
        "required": True,
    },
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file_handle:
        while chunk := file_handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def check_live_digest(
    errors: list[str],
    field_path: str,
    relpath: object,
    expected_sha256: object,
) -> None:
    live_path = REPO_ROOT / str(relpath)
    if not live_path.is_file():
        errors.append(f"{field_path}: missing repository file {relpath!r}")
        return
    actual_sha256 = sha256_file(live_path)
    if actual_sha256 != expected_sha256:
        errors.append(
            f"{field_path}: SHA-256 mismatch for {relpath!r}: "
            f"registry={expected_sha256} live={actual_sha256}"
        )


def check_retained_digest(
    errors: list[str],
    field_path: str,
    relpath: object,
    expected_sha256: object,
) -> None:
    """Validate a local OCR artifact when present and constrain absent retained paths."""
    relpath_text = str(relpath)
    live_path = REPO_ROOT / relpath_text
    if live_path.is_file():
        check_live_digest(errors, field_path, relpath_text, expected_sha256)
    elif not relpath_text.startswith("build/document_ocr/"):
        errors.append(f"{field_path}: missing repository file {relpath!r}")


def check_committed_digest(
    errors: list[str], field_path: str, commit: object, relpath: object, expected_sha256: object
) -> None:
    """Verify that a result's source commit already contains the locked input."""
    completed = subprocess.run(
        ["git", "show", f"{commit}:{relpath}"],
        cwd=REPO_ROOT,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        errors.append(f"{field_path}: cannot read {relpath!r} from commit {commit!r}")
        return
    if hashlib.sha256(completed.stdout).hexdigest() != expected_sha256:
        errors.append(f"{field_path}: committed input digest mismatch")


def check_beta_evidence_archive(
    errors: list[str], payload: dict[str, Any], records: list[object]
) -> None:
    """Require every beta record's raw arrays inside one tracked archive."""
    archive_record = payload.get("evidence_archive", {})
    if not isinstance(archive_record, dict):
        return
    relpath = archive_record.get("relpath")
    check_live_digest(errors, "$.evidence_archive.sha256", relpath, archive_record.get("sha256"))
    archive_path = REPO_ROOT / str(relpath)
    if not archive_path.is_file():
        return
    try:
        with tarfile.open(archive_path, mode="r") as archive:
            members = {member.name: member for member in archive.getmembers() if member.isfile()}
            expected_members: set[str] = set()
            for record_index, record in enumerate(records):
                if not isinstance(record, dict):
                    continue
                member_name = str(record.get("arrays_archive_member", ""))
                expected_members.add(member_name)
                member = members.get(member_name)
                if member is None:
                    errors.append(
                        f"$.records[{record_index}].arrays_archive_member: missing archive member"
                    )
                    continue
                extracted = archive.extractfile(member)
                if extracted is None:
                    errors.append(
                        f"$.records[{record_index}].arrays_archive_member: unreadable member"
                    )
                    continue
                if hashlib.sha256(extracted.read()).hexdigest() != record.get("arrays_sha256"):
                    errors.append(f"$.records[{record_index}].arrays_sha256: archive mismatch")
            extra_members = sorted(set(members) - expected_members)
            if extra_members:
                errors.append(f"$.evidence_archive: unreferenced members {extra_members[:3]!r}")
    except tarfile.TarError as error:
        errors.append(f"$.evidence_archive: invalid tar archive: {error}")


def validate_decomposition_manifest_contract(
    decomposition: dict[str, Any],
    run_manifest: dict[str, Any],
) -> list[str]:
    """Cross-check the committed decomposition summary against the retained MinerU ledger."""
    errors: list[str] = []
    engine_fields = (
        "name",
        "version",
        "backend",
        "effort",
        "mode",
        "formula",
        "table",
        "image_analysis",
    )
    manifest_engine = run_manifest.get("engine", {})
    decomposition_engine = decomposition.get("engine", {})
    if isinstance(manifest_engine, dict) and isinstance(decomposition_engine, dict):
        for field in engine_fields:
            if decomposition_engine.get(field) != manifest_engine.get(field):
                errors.append(f"$.engine.{field}: MinerU run manifest mismatch")

    manifest_sources = {
        str(source.get("source_relpath")): source
        for source in run_manifest.get("sources", [])
        if isinstance(source, dict) and source.get("status") in {"complete", "generated"}
    }
    decomposition_documents = {
        str(document.get("source_relpath")): document
        for document in decomposition.get("documents", [])
        if isinstance(document, dict)
    }
    if set(decomposition_documents) != set(manifest_sources):
        missing = sorted(set(manifest_sources) - set(decomposition_documents))
        extra = sorted(set(decomposition_documents) - set(manifest_sources))
        errors.append(f"$.documents: MinerU source mismatch missing={missing}, extra={extra}")

    role_fields = {
        "markdown": ("markdown_relpath", "markdown_sha256", "markdown_bytes"),
        "content_list": ("content_list_relpath", "content_list_sha256", None),
    }
    for source_relpath, document in decomposition_documents.items():
        source = manifest_sources.get(source_relpath)
        if source is None:
            continue
        if document.get("source_sha256") != source.get("source_sha256"):
            errors.append(f"$.documents[{source_relpath}].source_sha256: manifest mismatch")
        outputs = {
            str(output.get("role")): output
            for output in source.get("outputs", [])
            if isinstance(output, dict)
        }
        for role, (relpath_field, sha256_field, size_field) in role_fields.items():
            output = outputs.get(role)
            if output is None:
                errors.append(f"$.documents[{source_relpath}].{role}: missing manifest output")
                continue
            if document.get(relpath_field) != output.get("relpath"):
                errors.append(f"$.documents[{source_relpath}].{relpath_field}: manifest mismatch")
            if document.get(sha256_field) != output.get("sha256"):
                errors.append(f"$.documents[{source_relpath}].{sha256_field}: manifest mismatch")
            if size_field is not None and document.get(size_field) != output.get("size_bytes"):
                errors.append(f"$.documents[{source_relpath}].{size_field}: manifest mismatch")
    return errors


def type_matches(value: Any, expected: str) -> bool:
    if expected == "object":
        matches = isinstance(value, dict)
    elif expected == "array":
        matches = isinstance(value, list)
    elif expected == "string":
        matches = isinstance(value, str)
    elif expected == "integer":
        matches = isinstance(value, int) and not isinstance(value, bool)
    elif expected == "number":
        matches = isinstance(value, (int, float)) and not isinstance(value, bool)
    elif expected == "boolean":
        matches = isinstance(value, bool)
    elif expected == "null":
        matches = value is None
    else:
        matches = False
    return matches


def validate_datetime(value: str) -> bool:
    try:
        normalized = value.replace("Z", "+00:00")
        datetime.fromisoformat(normalized)
    except ValueError:
        return False
    return True


def validate_minimal_schema(instance: Any, schema: dict[str, Any], path: str = "$") -> list[str]:
    errors: list[str] = []

    expected_type = schema.get("type")
    if expected_type is not None:
        expected_types = expected_type if isinstance(expected_type, list) else [expected_type]
        if not any(type_matches(instance, item) for item in expected_types):
            errors.append(f"{path}: expected type {expected_types}, got {type(instance).__name__}")
            return errors

    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{path}: value {instance!r} not in enum {schema['enum']!r}")

    if isinstance(instance, str):
        min_length = schema.get("minLength")
        if isinstance(min_length, int) and len(instance) < min_length:
            errors.append(f"{path}: string shorter than minLength={min_length}")
        pattern = schema.get("pattern")
        if isinstance(pattern, str) and re.search(pattern, instance) is None:
            errors.append(f"{path}: string does not match pattern {pattern!r}")
        fmt = schema.get("format")
        if fmt == "date-time" and not validate_datetime(instance):
            errors.append(f"{path}: invalid date-time format")

    if isinstance(instance, int) and not isinstance(instance, bool):
        minimum = schema.get("minimum")
        if isinstance(minimum, (int, float)) and instance < minimum:
            errors.append(f"{path}: value {instance} below minimum={minimum}")

    if isinstance(instance, list):
        min_items = schema.get("minItems")
        if isinstance(min_items, int) and len(instance) < min_items:
            errors.append(f"{path}: array shorter than minItems={min_items}")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(instance):
                errors.extend(validate_minimal_schema(item, item_schema, f"{path}[{index}]"))

    if isinstance(instance, dict):
        required = schema.get("required", [])
        if isinstance(required, list):
            for key in required:
                if key not in instance:
                    errors.append(f"{path}: missing required key {key!r}")

        properties = schema.get("properties", {})
        if isinstance(properties, dict):
            for key, value in instance.items():
                child_schema = properties.get(key)
                child_path = f"{path}.{key}"
                if isinstance(child_schema, dict):
                    errors.extend(validate_minimal_schema(value, child_schema, child_path))
                elif schema.get("additionalProperties") is False:
                    errors.append(f"{path}: additional property not allowed: {key!r}")

    return errors


def validate_with_jsonschema(instance: Any, schema: dict[str, Any]) -> list[str]:
    if Draft202012Validator is None or FormatChecker is None:
        return validate_minimal_schema(instance, schema)

    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(instance), key=lambda error: list(error.absolute_path))

    formatted: list[str] = []
    for error in errors:
        path = "$"
        for token in error.absolute_path:
            if isinstance(token, int):
                path += f"[{token}]"
            else:
                path += f".{token}"
        formatted.append(f"{path}: {error.message}")
    return formatted


def semantic_checks(registry_name: str, payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    if registry_name == "aligned_research_mineru_run.json":
        check_live_digest(
            errors,
            "$.manifest_sha256",
            payload.get("manifest_relpath"),
            payload.get("manifest_sha256"),
        )
        sources = payload.get("sources", [])
        if isinstance(sources, list):
            expected_complete = sum(
                source.get("status") in {"complete", "generated"}
                for source in sources
                if isinstance(source, dict)
            )
            expected_failed = sum(
                source.get("status") == "failed" for source in sources if isinstance(source, dict)
            )
            if payload.get("source_count") != len(sources):
                errors.append("$.source_count: source list length mismatch")
            if payload.get("complete_count") != expected_complete:
                errors.append("$.complete_count: status tally mismatch")
            if payload.get("failed_count") != expected_failed:
                errors.append("$.failed_count: status tally mismatch")

            expected_roles = {
                "markdown",
                "content_list",
                "content_list_v2",
                "middle",
                "model",
                "layout_pdf",
                "origin_pdf",
            }
            seen_source_ids: set[str] = set()
            for source_index, source in enumerate(sources):
                if not isinstance(source, dict):
                    continue
                prefix = f"$.sources[{source_index}]"
                source_id = str(source.get("source_id", ""))
                if source_id in seen_source_ids:
                    errors.append(f"{prefix}.source_id: duplicate id {source_id!r}")
                seen_source_ids.add(source_id)
                check_live_digest(
                    errors,
                    f"{prefix}.source_sha256",
                    source.get("source_relpath"),
                    source.get("source_sha256"),
                )
                source_path = REPO_ROOT / str(source.get("source_relpath"))
                if (
                    source_path.is_file()
                    and source.get("source_size_bytes") != source_path.stat().st_size
                ):
                    errors.append(f"{prefix}.source_size_bytes: live size mismatch")
                outputs = source.get("outputs", [])
                output_roles: set[str] = set()
                if isinstance(outputs, list):
                    for output_index, output in enumerate(outputs):
                        if not isinstance(output, dict):
                            continue
                        output_prefix = f"{prefix}.outputs[{output_index}]"
                        role = str(output.get("role", ""))
                        if role in output_roles:
                            errors.append(f"{output_prefix}.role: duplicate role {role!r}")
                        output_roles.add(role)
                        check_retained_digest(
                            errors,
                            f"{output_prefix}.sha256",
                            output.get("relpath"),
                            output.get("sha256"),
                        )
                        output_path = REPO_ROOT / str(output.get("relpath"))
                        if (
                            output_path.is_file()
                            and output.get("size_bytes") != output_path.stat().st_size
                        ):
                            errors.append(f"{output_prefix}.size_bytes: live size mismatch")
                if (
                    source.get("status") in {"complete", "generated"}
                    and output_roles != expected_roles
                ):
                    errors.append(
                        f"{prefix}.outputs: complete source must contain all primary roles"
                    )

    if registry_name == "tesseract_fallback_run.json":
        check_live_digest(
            errors,
            "$.quality_audit_sha256",
            payload.get("quality_audit_relpath"),
            payload.get("quality_audit_sha256"),
        )
        documents = payload.get("documents", [])
        if isinstance(documents, list):
            if payload.get("document_count") != len(documents):
                errors.append("$.document_count: document list length mismatch")
            expected_page_count = sum(
                len(document.get("selected_pages", []))
                for document in documents
                if isinstance(document, dict)
            )
            if payload.get("page_count") != expected_page_count:
                errors.append("$.page_count: selected-page tally mismatch")
            for document_index, document in enumerate(documents):
                if not isinstance(document, dict):
                    continue
                prefix = f"$.documents[{document_index}]"
                check_live_digest(
                    errors,
                    f"{prefix}.source_sha256",
                    document.get("source_relpath"),
                    document.get("source_sha256"),
                )
                check_retained_digest(
                    errors,
                    f"{prefix}.manifest_sha256",
                    document.get("manifest_relpath"),
                    document.get("manifest_sha256"),
                )
                manifest_path = REPO_ROOT / str(document.get("manifest_relpath"))
                if not manifest_path.is_file():
                    continue
                manifest = load_json(manifest_path)
                if manifest.get("source_sha256") != document.get("source_sha256"):
                    errors.append(f"{prefix}.manifest_relpath: source digest mismatch")
                if manifest.get("dpi") != payload.get("dpi"):
                    errors.append(f"{prefix}.manifest_relpath: DPI mismatch")
                if manifest.get("page_segmentation_mode") != payload.get("page_segmentation_mode"):
                    errors.append(f"{prefix}.manifest_relpath: page segmentation mode mismatch")
                page_records = manifest.get("pages", [])
                manifest_pages = [
                    page.get("page") for page in page_records if isinstance(page, dict)
                ]
                if manifest_pages != document.get("selected_pages"):
                    errors.append(f"{prefix}.manifest_relpath: selected pages mismatch")
                for page_index, page in enumerate(page_records):
                    if not isinstance(page, dict):
                        continue
                    page_prefix = f"{prefix}.manifest.pages[{page_index}]"
                    check_live_digest(
                        errors,
                        f"{page_prefix}.output_sha256",
                        page.get("output_relpath"),
                        page.get("output_sha256"),
                    )
                    output_path = REPO_ROOT / str(page.get("output_relpath"))
                    if (
                        output_path.is_file()
                        and page.get("output_bytes") != output_path.stat().st_size
                    ):
                        errors.append(f"{page_prefix}.output_bytes: live size mismatch")

    if registry_name == "critique_evidence_ledger.json":
        claims = payload.get("claims", [])
        seen_ids: set[str] = set()
        if isinstance(claims, list):
            for index, claim in enumerate(claims):
                if not isinstance(claim, dict):
                    continue
                claim_id = str(claim.get("id", "")).strip()
                if claim_id in seen_ids:
                    errors.append(f"$.claims[{index}].id: duplicate id {claim_id!r}")
                seen_ids.add(claim_id)
                evidence_paths = claim.get("evidence_paths", [])
                if not isinstance(evidence_paths, list):
                    continue
                for evidence_relpath in evidence_paths:
                    evidence_path = REPO_ROOT / str(evidence_relpath)
                    if not evidence_path.exists():
                        errors.append(
                            f"$.claims[{index}].evidence_paths: missing repository path "
                            f"{evidence_relpath!r}"
                        )

    if registry_name == "document_ocr_run_manifest.json":
        mineru = payload.get("mineru", {})
        container = mineru.get("container", {}) if isinstance(mineru, dict) else {}
        if isinstance(container, dict):
            check_live_digest(
                errors,
                "$.mineru.container.dockerfile_sha256",
                container.get("dockerfile_relpath"),
                container.get("dockerfile_sha256"),
            )
            check_live_digest(
                errors,
                "$.mineru.container.compose_sha256",
                container.get("compose_relpath"),
                container.get("compose_sha256"),
            )
        tesseract = payload.get("tesseract", {})
        if isinstance(tesseract, dict):
            check_retained_digest(
                errors,
                "$.tesseract.manifest_sha256",
                tesseract.get("manifest_relpath"),
                tesseract.get("manifest_sha256"),
            )

    if registry_name == "pdf_ocr_visual_review.json":
        source_pdf = payload.get("source_pdf", {})
        if isinstance(source_pdf, dict):
            check_live_digest(
                errors,
                "$.source_pdf.sha256",
                source_pdf.get("relpath"),
                source_pdf.get("sha256"),
            )

    if registry_name == "pdf_ocr_comparison.json":
        provenance = payload.get("provenance", {})
        if isinstance(provenance, dict):
            check_live_digest(
                errors,
                "$.provenance.run_manifest_sha256",
                provenance.get("run_manifest_relpath"),
                provenance.get("run_manifest_sha256"),
            )
            check_live_digest(
                errors,
                "$.provenance.visual_review_sha256",
                provenance.get("visual_review_relpath"),
                provenance.get("visual_review_sha256"),
            )
        outputs = payload.get("outputs", {})
        selection = payload.get("selection", {})
        if isinstance(outputs, dict) and isinstance(selection, dict):
            for selection_field in ("primary", "fallback"):
                selected_output = selection.get(selection_field)
                if selected_output not in outputs:
                    errors.append(
                        f"$.selection.{selection_field}: unknown output {selected_output!r}"
                    )

    if registry_name == "document_decomposition_audit.json":
        run_manifest = payload.get("run_manifest", {})
        if isinstance(run_manifest, dict):
            check_live_digest(
                errors,
                "$.run_manifest.sha256",
                run_manifest.get("relpath"),
                run_manifest.get("sha256"),
            )
            run_manifest_path = REPO_ROOT / str(run_manifest.get("relpath"))
            if run_manifest_path.is_file():
                errors.extend(
                    validate_decomposition_manifest_contract(payload, load_json(run_manifest_path))
                )
        documents = payload.get("documents", [])
        seen_source_paths: set[str] = set()
        if isinstance(documents, list):
            for document_index, document in enumerate(documents):
                if not isinstance(document, dict):
                    continue
                prefix = f"$.documents[{document_index}]"
                source_relpath = str(document.get("source_relpath", ""))
                if source_relpath in seen_source_paths:
                    errors.append(f"{prefix}.source_relpath: duplicate source")
                seen_source_paths.add(source_relpath)
                check_live_digest(
                    errors,
                    f"{prefix}.source_sha256",
                    source_relpath,
                    document.get("source_sha256"),
                )
                check_retained_digest(
                    errors,
                    f"{prefix}.markdown_sha256",
                    document.get("markdown_relpath"),
                    document.get("markdown_sha256"),
                )
                check_retained_digest(
                    errors,
                    f"{prefix}.content_list_sha256",
                    document.get("content_list_relpath"),
                    document.get("content_list_sha256"),
                )
                markdown_path = REPO_ROOT / str(document.get("markdown_relpath"))
                if markdown_path.is_file():
                    markdown_text = markdown_path.read_text(encoding="utf-8", errors="replace")
                    if document.get("markdown_bytes") != markdown_path.stat().st_size:
                        errors.append(f"{prefix}.markdown_bytes: live size mismatch")
                    if document.get("markdown_nonspace_characters") != len(
                        re.sub(r"\s", "", markdown_text)
                    ):
                        errors.append(f"{prefix}.markdown_nonspace_characters: live count mismatch")
                content_list_path = REPO_ROOT / str(document.get("content_list_relpath"))
                if content_list_path.is_file():
                    content_list = json.loads(content_list_path.read_text(encoding="utf-8"))
                    if not isinstance(content_list, list):
                        errors.append(f"{prefix}.content_list_relpath: expected array")
                        continue
                    if document.get("content_item_count") != len(content_list):
                        errors.append(f"{prefix}.content_item_count: live count mismatch")
                    live_type_counts: dict[str, int] = {}
                    for item in content_list:
                        if isinstance(item, dict) and isinstance(item.get("type"), str):
                            item_type = item["type"]
                            live_type_counts[item_type] = live_type_counts.get(item_type, 0) + 1
                    if document.get("content_type_counts") != dict(
                        sorted(live_type_counts.items())
                    ):
                        errors.append(f"{prefix}.content_type_counts: live tally mismatch")

    if registry_name == "framework_document_decomposition.json":
        check_live_digest(
            errors,
            "$.index_sha256",
            payload.get("index_relpath"),
            payload.get("index_sha256"),
        )
        documents = payload.get("documents", [])
        if isinstance(documents, list):
            aggregate_fields = {
                "document_count": len(documents),
                "source_line_count": sum(
                    int(document.get("line_count", 0))
                    for document in documents
                    if isinstance(document, dict)
                ),
                "chunk_count": sum(
                    int(document.get("chunk_count", 0))
                    for document in documents
                    if isinstance(document, dict)
                ),
                "heading_count": sum(
                    int(document.get("heading_count", 0))
                    for document in documents
                    if isinstance(document, dict)
                ),
                "reference_count": sum(
                    int(document.get("reference_count", 0))
                    for document in documents
                    if isinstance(document, dict)
                ),
                "formula_candidate_count": sum(
                    int(document.get("formula_candidate_count", 0))
                    for document in documents
                    if isinstance(document, dict)
                ),
                "table_row_candidate_count": sum(
                    int(document.get("table_row_candidate_count", 0))
                    for document in documents
                    if isinstance(document, dict)
                ),
                "code_fence_count": sum(
                    int(document.get("code_fence_count", 0))
                    for document in documents
                    if isinstance(document, dict)
                ),
            }
            for field_name, expected_value in aggregate_fields.items():
                if payload.get(field_name) != expected_value:
                    errors.append(
                        f"$.{field_name}: expected {expected_value} from document records, "
                        f"got {payload.get(field_name)!r}"
                    )

            seen_document_ids: set[str] = set()
            for document_index, document in enumerate(documents):
                if not isinstance(document, dict):
                    continue
                field_prefix = f"$.documents[{document_index}]"
                document_id = str(document.get("id", ""))
                if document_id in seen_document_ids:
                    errors.append(f"{field_prefix}.id: duplicate id {document_id!r}")
                seen_document_ids.add(document_id)
                source_relpath = document.get("source_relpath")
                check_live_digest(
                    errors,
                    f"{field_prefix}.source_sha256",
                    source_relpath,
                    document.get("source_sha256"),
                )
                check_live_digest(
                    errors,
                    f"{field_prefix}.index_sha256",
                    document.get("index_relpath"),
                    document.get("index_sha256"),
                )
                check_live_digest(
                    errors,
                    f"{field_prefix}.reference_index_sha256",
                    document.get("reference_index_relpath"),
                    document.get("reference_index_sha256"),
                )
                check_live_digest(
                    errors,
                    f"{field_prefix}.structure_index_sha256",
                    document.get("structure_index_relpath"),
                    document.get("structure_index_sha256"),
                )
                source_path = REPO_ROOT / str(source_relpath)
                if not source_path.is_file():
                    continue
                source_text = source_path.read_text(encoding="utf-8", errors="strict")
                source_lines = source_text.splitlines(keepends=True)
                chunks = document.get("chunks", [])
                headings = document.get("headings", [])
                if document.get("source_bytes") != source_path.stat().st_size:
                    errors.append(f"{field_prefix}.source_bytes: live size mismatch")
                if document.get("line_count") != len(source_lines):
                    errors.append(f"{field_prefix}.line_count: live line count mismatch")

                reference_path = REPO_ROOT / str(document.get("reference_index_relpath"))
                if reference_path.is_file():
                    reference_payload = load_json(reference_path)
                    references = reference_payload.get("references", [])
                    if reference_payload.get("source_sha256") != document.get("source_sha256"):
                        errors.append(f"{field_prefix}.reference_index_relpath: source mismatch")
                    if not isinstance(references, list) or document.get("reference_count") != len(
                        references
                    ):
                        errors.append(f"{field_prefix}.reference_count: index length mismatch")
                    elif any(
                        not str(record.get("context", "")).isascii()
                        or not str(record.get("value", "")).isascii()
                        for record in references
                        if isinstance(record, dict)
                    ):
                        errors.append(f"{field_prefix}.reference_index_relpath: non-ASCII view")

                structure_path = REPO_ROOT / str(document.get("structure_index_relpath"))
                if structure_path.is_file():
                    structure_payload = load_json(structure_path)
                    if structure_payload.get("source_sha256") != document.get("source_sha256"):
                        errors.append(f"{field_prefix}.structure_index_relpath: source mismatch")
                    structure_specs = {
                        "formula_candidates": "formula_candidate_count",
                        "table_row_candidates": "table_row_candidate_count",
                        "code_fences": "code_fence_count",
                    }
                    for records_field, count_field in structure_specs.items():
                        records = structure_payload.get(records_field, [])
                        if not isinstance(records, list) or document.get(count_field) != len(
                            records
                        ):
                            errors.append(f"{field_prefix}.{count_field}: index length mismatch")
                            continue
                        for record_index, record in enumerate(records):
                            if not isinstance(record, dict):
                                continue
                            record_prefix = (
                                f"{field_prefix}.structure_index.{records_field}[{record_index}]"
                            )
                            source_line = record.get("source_line")
                            if not isinstance(source_line, int) or not 1 <= source_line <= len(
                                source_lines
                            ):
                                errors.append(f"{record_prefix}.source_line: invalid line")
                                continue
                            live_line = source_lines[source_line - 1]
                            if hashlib.sha256(live_line.encode("utf-8")).hexdigest() != record.get(
                                "source_line_sha256"
                            ):
                                errors.append(f"{record_prefix}.source_line_sha256: live mismatch")
                            if record.get("source_text") != live_line.strip():
                                errors.append(f"{record_prefix}.source_text: live mismatch")
                            if not str(record.get("ascii_text", "")).isascii():
                                errors.append(f"{record_prefix}.ascii_text: non-ASCII view")
                if not isinstance(chunks, list):
                    continue
                if document.get("chunk_count") != len(chunks):
                    errors.append(f"{field_prefix}.chunk_count: chunk list length mismatch")
                if isinstance(headings, list) and document.get("heading_count") != len(headings):
                    errors.append(f"{field_prefix}.heading_count: heading list length mismatch")
                expected_start = 1
                for chunk_index, chunk in enumerate(chunks):
                    if not isinstance(chunk, dict):
                        continue
                    chunk_prefix = f"{field_prefix}.chunks[{chunk_index}]"
                    start = chunk.get("source_line_start")
                    end = chunk.get("source_line_end")
                    if not isinstance(start, int) or not isinstance(end, int):
                        continue
                    if start != expected_start:
                        errors.append(
                            f"{chunk_prefix}.source_line_start: expected contiguous line "
                            f"{expected_start}, got {start}"
                        )
                    if end < start or end > len(source_lines):
                        errors.append(
                            f"{chunk_prefix}.source_line_end: invalid range {start}-{end}"
                        )
                        continue
                    source_slice = "".join(source_lines[start - 1 : end]).encode("utf-8")
                    if hashlib.sha256(source_slice).hexdigest() != chunk.get("source_chunk_sha256"):
                        errors.append(f"{chunk_prefix}.source_chunk_sha256: source slice mismatch")
                    check_live_digest(
                        errors,
                        f"{chunk_prefix}.markdown_sha256",
                        chunk.get("markdown_relpath"),
                        chunk.get("markdown_sha256"),
                    )
                    markdown_path = REPO_ROOT / str(chunk.get("markdown_relpath"))
                    if markdown_path.is_file():
                        markdown_bytes = markdown_path.read_bytes()
                        if not markdown_bytes.isascii():
                            errors.append(f"{chunk_prefix}.markdown_relpath: non-ASCII output")
                        if chunk.get("markdown_bytes") != len(markdown_bytes):
                            errors.append(f"{chunk_prefix}.markdown_bytes: live size mismatch")
                    expected_start = end + 1
                if chunks and expected_start != len(source_lines) + 1:
                    errors.append(f"{field_prefix}.chunks: source coverage is incomplete")

    if registry_name == "framework_overlap_audit.json":
        check_live_digest(
            errors,
            "$.source_registry_sha256",
            payload.get("source_registry_relpath"),
            payload.get("source_registry_sha256"),
        )
        documents = payload.get("documents", [])
        duplicate_groups = payload.get("duplicate_groups", [])
        if isinstance(documents, list) and payload.get("document_count") != len(documents):
            errors.append("$.document_count: document list length mismatch")
        if isinstance(duplicate_groups, list) and payload.get("duplicate_group_count") != len(
            duplicate_groups
        ):
            errors.append("$.duplicate_group_count: duplicate group list length mismatch")
        if isinstance(duplicate_groups, list):
            expected_cross_document = sum(
                bool(group.get("cross_document"))
                for group in duplicate_groups
                if isinstance(group, dict)
            )
            if payload.get("cross_document_duplicate_group_count") != expected_cross_document:
                errors.append(
                    "$.cross_document_duplicate_group_count: duplicate group tally mismatch"
                )
        if isinstance(documents, list):
            for index, document in enumerate(documents):
                if not isinstance(document, dict):
                    continue
                check_live_digest(
                    errors,
                    f"$.documents[{index}].source_sha256",
                    document.get("source_relpath"),
                    document.get("source_sha256"),
                )

    if registry_name == "unified_framework_claims.json":
        decomposition_path = REGISTRY_DIR / "framework_document_decomposition.json"
        decomposition = load_json(decomposition_path)
        document_by_id = {
            document["id"]: document
            for document in decomposition.get("documents", [])
            if isinstance(document, dict) and isinstance(document.get("id"), str)
        }
        external_manifest = tomllib.loads(
            (REPO_ROOT / "data/external/sources.toml").read_text(encoding="utf-8")
        )
        external_source_ids = {
            str(source.get("id"))
            for source in external_manifest.get("sources", [])
            if isinstance(source, dict)
        }
        seen_claim_ids: set[str] = set()
        claims = payload.get("claims", [])
        if isinstance(claims, list):
            for claim_index, claim in enumerate(claims):
                if not isinstance(claim, dict):
                    continue
                prefix = f"$.claims[{claim_index}]"
                claim_id = str(claim.get("id", ""))
                if claim_id in seen_claim_ids:
                    errors.append(f"{prefix}.id: duplicate id {claim_id!r}")
                seen_claim_ids.add(claim_id)
                for anchor_index, anchor in enumerate(claim.get("source_anchors", [])):
                    if not isinstance(anchor, dict):
                        continue
                    anchor_prefix = f"{prefix}.source_anchors[{anchor_index}]"
                    document = document_by_id.get(anchor.get("document_id"))
                    if document is None:
                        errors.append(f"{anchor_prefix}.document_id: unknown document")
                        continue
                    source_line = anchor.get("source_line")
                    if not isinstance(source_line, int) or source_line > int(
                        document.get("line_count", 0)
                    ):
                        errors.append(f"{anchor_prefix}.source_line: outside source document")
                for source_id in claim.get("evidence_source_ids", []):
                    if source_id not in external_source_ids:
                        errors.append(
                            f"{prefix}.evidence_source_ids: unknown source id {source_id!r}"
                        )
                for evidence_relpath in claim.get("repo_evidence_paths", []):
                    if not (REPO_ROOT / str(evidence_relpath)).exists():
                        errors.append(
                            f"{prefix}.repo_evidence_paths: missing path {evidence_relpath!r}"
                        )

    if registry_name == "hypothesis_registry.json":
        claim_payload = load_json(REGISTRY_DIR / "unified_framework_claims.json")
        claims = {
            str(claim["id"]): claim
            for claim in claim_payload.get("claims", [])
            if isinstance(claim, dict) and isinstance(claim.get("id"), str)
        }
        source_statuses = payload.get("source_claim_statuses", [])
        expected_statuses = {"bounded", "excluded", "falsified", "unsupported"}
        if set(source_statuses) != expected_statuses:
            errors.append(
                "$.source_claim_statuses: expected bounded, excluded, falsified, and unsupported"
            )
        expected_claim_ids = {
            claim_id
            for claim_id, claim in claims.items()
            if claim.get("status") in expected_statuses
        }
        external_manifest = tomllib.loads(
            (REPO_ROOT / "data/external/sources.toml").read_text(encoding="utf-8")
        )
        external_source_ids = {
            str(source.get("id"))
            for source in external_manifest.get("sources", [])
            if isinstance(source, dict)
        }
        seen_hypothesis_ids: set[str] = set()
        covered_claim_ids: list[str] = []
        hypotheses = payload.get("hypotheses", [])
        if isinstance(hypotheses, list):
            for hypothesis_index, hypothesis in enumerate(hypotheses):
                if not isinstance(hypothesis, dict):
                    continue
                prefix = f"$.hypotheses[{hypothesis_index}]"
                hypothesis_id = str(hypothesis.get("id", ""))
                if hypothesis_id in seen_hypothesis_ids:
                    errors.append(f"{prefix}.id: duplicate id {hypothesis_id!r}")
                seen_hypothesis_ids.add(hypothesis_id)
                for claim_id in hypothesis.get("source_claim_ids", []):
                    claim = claims.get(str(claim_id))
                    if claim is None:
                        errors.append(f"{prefix}.source_claim_ids: unknown claim {claim_id!r}")
                        continue
                    if claim.get("status") not in expected_statuses:
                        errors.append(
                            f"{prefix}.source_claim_ids: claim {claim_id!r} is not open, "
                            "excluded, or a falsified replacement target"
                        )
                    covered_claim_ids.append(str(claim_id))
                for source_id in hypothesis.get("literature_source_ids", []):
                    if source_id not in external_source_ids:
                        errors.append(
                            f"{prefix}.literature_source_ids: unknown source id {source_id!r}"
                        )
                for evidence_index, evidence in enumerate(hypothesis.get("required_evidence", [])):
                    if not isinstance(evidence, dict) or evidence.get("status") != "present":
                        continue
                    for artifact_path in evidence.get("artifact_paths", []):
                        if not (REPO_ROOT / str(artifact_path)).exists():
                            errors.append(
                                f"{prefix}.required_evidence[{evidence_index}].artifact_paths: "
                                f"missing present artifact {artifact_path!r}"
                            )
                reproduction = hypothesis.get("independent_reproduction", {})
                if isinstance(reproduction, dict):
                    for evidence_path in reproduction.get("evidence_paths", []):
                        if not (REPO_ROOT / str(evidence_path)).exists():
                            errors.append(
                                f"{prefix}.independent_reproduction.evidence_paths: "
                                f"missing path {evidence_path!r}"
                            )
        duplicate_claim_ids = sorted(
            claim_id for claim_id in set(covered_claim_ids) if covered_claim_ids.count(claim_id) > 1
        )
        if duplicate_claim_ids:
            errors.append(
                "$.hypotheses.source_claim_ids: claims assigned more than once: "
                + ", ".join(duplicate_claim_ids)
            )
        covered_set = set(covered_claim_ids)
        if covered_set != expected_claim_ids:
            missing = sorted(expected_claim_ids - covered_set)
            extra = sorted(covered_set - expected_claim_ids)
            if missing:
                errors.append(
                    "$.hypotheses.source_claim_ids: missing claim coverage: " + ", ".join(missing)
                )
            if extra:
                errors.append(
                    "$.hypotheses.source_claim_ids: unexpected claim coverage: " + ", ".join(extra)
                )
        archival_groups = payload.get("archival_conjecture_dispositions", [])
        expected_group_counts = {
            "papers/sections/vol4_ch12_unresolved.tex": 22,
            "papers/sections/vol2_ch6_string_theory.tex": 4,
            "papers/sections/vol2_ch7_quantum_gravity.tex": 4,
            "papers/sections/vol2_ch6_quantum_encoding.tex": 3,
            "papers/sections/vol3_ch10_predictions.tex": 18,
            "papers/sections/vol2_ch5_superforce.tex": 3,
        }
        seen_archival_ids: set[str] = set()
        seen_archival_paths: set[str] = set()
        if isinstance(archival_groups, list):
            for group_index, group in enumerate(archival_groups):
                if not isinstance(group, dict):
                    continue
                prefix = f"$.archival_conjecture_dispositions[{group_index}]"
                source_relpath = str(group.get("source_relpath", ""))
                seen_archival_paths.add(source_relpath)
                source_path = REPO_ROOT / source_relpath
                if not source_path.is_file():
                    errors.append(f"{prefix}.source_relpath: missing source")
                items = group.get("items", [])
                expected_count = expected_group_counts.get(source_relpath)
                if expected_count is None:
                    errors.append(f"{prefix}.source_relpath: unbounded archival surface")
                elif not isinstance(items, list) or len(items) != expected_count:
                    errors.append(
                        f"{prefix}.items: expected {expected_count} explicit items, "
                        f"got {len(items) if isinstance(items, list) else 'non-array'}"
                    )
                for item_index, item in enumerate(items if isinstance(items, list) else []):
                    if not isinstance(item, dict):
                        continue
                    item_prefix = f"{prefix}.items[{item_index}]"
                    archival_id = str(item.get("id", ""))
                    if archival_id in seen_archival_ids:
                        errors.append(f"{item_prefix}.id: duplicate archival id")
                    seen_archival_ids.add(archival_id)
                    for hypothesis_id in item.get("mapped_hypothesis_ids", []):
                        if hypothesis_id not in seen_hypothesis_ids:
                            errors.append(
                                f"{item_prefix}.mapped_hypothesis_ids: unknown hypothesis "
                                f"{hypothesis_id!r}"
                            )
        if seen_archival_paths != set(expected_group_counts):
            missing_paths = sorted(set(expected_group_counts) - seen_archival_paths)
            extra_paths = sorted(seen_archival_paths - set(expected_group_counts))
            errors.append(
                "$.archival_conjecture_dispositions: source coverage mismatch "
                f"missing={missing_paths}, extra={extra_paths}"
            )

    if registry_name == "physical_admission_program.json":
        states = payload.get("promotion_states", [])
        claim_payload = load_json(REGISTRY_DIR / "unified_framework_claims.json")
        hypothesis_payload = load_json(REGISTRY_DIR / "hypothesis_registry.json")
        claim_ids = {str(claim.get("id")) for claim in claim_payload.get("claims", [])}
        hypothesis_ids = {
            str(hypothesis.get("id"))
            for hypothesis in hypothesis_payload.get("hypotheses", [])
        }
        for package_index, package in enumerate(payload.get("packages", [])):
            if not isinstance(package, dict):
                continue
            prefix = f"$.packages[{package_index}]"
            if package.get("claim_id") not in claim_ids:
                errors.append(f"{prefix}.claim_id: unknown canonical claim")
            if package.get("hypothesis_id") not in hypothesis_ids:
                errors.append(f"{prefix}.hypothesis_id: unknown canonical hypothesis")
            current_state = package.get("current_state")
            next_state = package.get("next_required_state")
            if current_state in states:
                current_index = states.index(current_state)
                expected_next = states[current_index + 1] if current_index + 1 < len(states) else "none"
                if next_state != expected_next:
                    errors.append(f"{prefix}.next_required_state: expected {expected_next!r}")
                state_evidence = package.get("state_evidence", {})
                if isinstance(state_evidence, dict):
                    for completed_state in states[1 : current_index + 1]:
                        evidence_records = state_evidence.get(completed_state, [])
                        if not evidence_records:
                            errors.append(
                                f"{prefix}.state_evidence.{completed_state}: required for state"
                            )
                        for evidence_index, evidence in enumerate(evidence_records):
                            if isinstance(evidence, dict):
                                check_live_digest(
                                    errors,
                                    f"{prefix}.state_evidence.{completed_state}"
                                    f"[{evidence_index}].sha256",
                                    evidence.get("relpath"),
                                    evidence.get("sha256"),
                                )
            if current_state == "admitted" and package.get("blockers"):
                errors.append(f"{prefix}.blockers: admitted package cannot retain blockers")

    if registry_name == "triad_selector_audit.json":
        check_live_digest(
            errors,
            "$.preregistration_sha256",
            payload.get("preregistration_relpath"),
            payload.get("preregistration_sha256"),
        )
        if payload.get("e7_quadratic_defect_admitted_triad_count", 0) + payload.get(
            "e7_quadratic_defect_rejected_triad_count", 0
        ) != payload.get("ordered_nonzero_exact_triad_count"):
            errors.append("$.e7_quadratic_defect_*: admitted and rejected counts do not close")
        if payload.get("e7_quadratic_defect_active_admitted_count", 0) + payload.get(
            "e7_quadratic_defect_active_rejected_count", 0
        ) != payload.get("barotropic_active_channel_count"):
            errors.append("$.e7_quadratic_defect_active_*: active counts do not close")
        domains = payload.get("evaluation_domains", [])
        if isinstance(domains, list) and [
            domain.get("square_domain_radius") for domain in domains if isinstance(domain, dict)
        ] != [2, 4, 8]:
            errors.append("$.evaluation_domains: expected locked radii [2, 4, 8]")

    if registry_name == "beta_plane_sweep_results.json":
        check_live_digest(
            errors,
            "$.preregistration_sha256",
            payload.get("preregistration_relpath"),
            payload.get("preregistration_sha256"),
        )
        check_live_digest(
            errors,
            "$.environment_lock_sha256",
            payload.get("environment_lock_relpath"),
            payload.get("environment_lock_sha256"),
        )
        check_committed_digest(
            errors,
            "$.preregistration_sha256",
            payload.get("source_commit"),
            payload.get("preregistration_relpath"),
            payload.get("preregistration_sha256"),
        )
        records = payload.get("records", [])
        if isinstance(records, list):
            if payload.get("run_count") != len(records):
                errors.append("$.run_count: does not match records length")
            run_ids = [
                str(record.get("run_id", "")) for record in records if isinstance(record, dict)
            ]
            if len(run_ids) != len(set(run_ids)):
                errors.append("$.records: duplicate run_id")
            for record_index, record in enumerate(records):
                if not isinstance(record, dict):
                    continue
                if "arrays_relpath" in record:
                    errors.append(f"$.records[{record_index}].arrays_relpath: ignored path forbidden")
                if record.get("cluster_count") is not None:
                    errors.append(f"$.records[{record_index}].cluster_count: misplaced contrast field")
            check_beta_evidence_archive(errors, payload, records)
        for contrast_index, contrast in enumerate(payload.get("primary_contrasts", [])):
            if not isinstance(contrast, dict):
                continue
            if contrast.get("cluster_count") != 12:
                errors.append(f"$.primary_contrasts[{contrast_index}].cluster_count: expected 12")
            if contrast.get("cell_pair_count") != 108:
                errors.append(
                    f"$.primary_contrasts[{contrast_index}].cell_pair_count: expected 108"
                )
            if "paired_count" in contrast or "holm_corrected_ci_lower" in contrast:
                errors.append(
                    f"$.primary_contrasts[{contrast_index}]: obsolete statistical field"
                )
        numerical_pass = payload.get("numerical_gate_passed") is True
        primary_pass = payload.get("primary_hypothesis_passed") is True
        expected_decision = (
            "primary_supported_pending_refinement_and_reproduction"
            if numerical_pass and primary_pass
            else "not_supported"
        )
        if payload.get("aggregate_decision") != expected_decision:
            errors.append(f"$.aggregate_decision: expected {expected_decision!r} from gate states")

    if registry_name == "beta_plane_refinement_results.json":
        check_live_digest(
            errors,
            "$.preregistration_sha256",
            payload.get("preregistration_relpath"),
            payload.get("preregistration_sha256"),
        )
        check_live_digest(
            errors,
            "$.protocol_amendment_sha256",
            payload.get("protocol_amendment_relpath"),
            payload.get("protocol_amendment_sha256"),
        )
        check_live_digest(
            errors,
            "$.environment_lock_sha256",
            payload.get("environment_lock_relpath"),
            payload.get("environment_lock_sha256"),
        )
        check_committed_digest(
            errors,
            "$.preregistration_sha256",
            payload.get("source_commit"),
            payload.get("preregistration_relpath"),
            payload.get("preregistration_sha256"),
        )
        check_committed_digest(
            errors,
            "$.protocol_amendment_sha256",
            payload.get("source_commit"),
            payload.get("protocol_amendment_relpath"),
            payload.get("protocol_amendment_sha256"),
        )
        records = payload.get("records", [])
        if isinstance(records, list):
            if payload.get("run_count") != len(records):
                errors.append("$.run_count: does not match refinement records length")
            check_beta_evidence_archive(errors, payload, records)

    if registry_name == "beta_plane_control_results.json":
        check_live_digest(
            errors,
            "$.preregistration_sha256",
            payload.get("preregistration_relpath"),
            payload.get("preregistration_sha256"),
        )
        check_committed_digest(
            errors,
            "$.preregistration_sha256",
            payload.get("source_commit"),
            payload.get("preregistration_relpath"),
            payload.get("preregistration_sha256"),
        )
        check_live_digest(
            errors,
            "$.environment_lock_sha256",
            payload.get("environment_lock_relpath"),
            payload.get("environment_lock_sha256"),
        )
        archive_record = payload.get("evidence_archive", {})
        if isinstance(archive_record, dict):
            check_live_digest(
                errors,
                "$.evidence_archive.sha256",
                archive_record.get("relpath"),
                archive_record.get("sha256"),
            )
            archive_path = REPO_ROOT / str(archive_record.get("relpath"))
            if archive_path.is_file():
                try:
                    with tarfile.open(archive_path, mode="r") as archive:
                        members = {
                            member.name: member for member in archive.getmembers() if member.isfile()
                        }
                        digest_fields = {
                            "identity": "identity_final_sha256",
                            "quotient": "quotient_final_sha256",
                            "f_plane": "f_plane_final_sha256",
                            "rotated_f_plane": "rotated_f_plane_final_sha256",
                        }
                        for record_index, record in enumerate(payload.get("records", [])):
                            if not isinstance(record, dict):
                                continue
                            archive_members = record.get("archive_members", {})
                            for arm_name, digest_field in digest_fields.items():
                                member_name = (
                                    archive_members.get(arm_name)
                                    if isinstance(archive_members, dict)
                                    else None
                                )
                                member = members.get(str(member_name))
                                if member is None:
                                    errors.append(
                                        f"$.records[{record_index}].archive_members.{arm_name}: "
                                        "missing archive member"
                                    )
                                    continue
                                extracted = archive.extractfile(member)
                                if extracted is None or hashlib.sha256(
                                    extracted.read()
                                ).hexdigest() != record.get(digest_field):
                                    errors.append(
                                        f"$.records[{record_index}].{digest_field}: "
                                        "archive mismatch"
                                    )
                except tarfile.TarError as error:
                    errors.append(f"$.evidence_archive: invalid tar archive: {error}")
        retained_lbm = payload.get("retained_lbm_null_control", {})
        if isinstance(retained_lbm, dict):
            check_live_digest(
                errors,
                "$.retained_lbm_null_control.audit_sha256",
                retained_lbm.get("audit_relpath"),
                retained_lbm.get("audit_sha256"),
            )

    if registry_name == "docs_index.toml":
        documents = payload.get("documents", [])
        total = payload.get("documents_total")
        if isinstance(total, int) and isinstance(documents, list) and total != len(documents):
            errors.append(
                f"$.documents_total: expected {len(documents)} based on documents length, got {total}"
            )

    if registry_name == "corpus_dedupe_report.toml":
        duplicate_groups = payload.get("duplicate_groups", [])
        hash_mismatches = payload.get("hash_mismatches", [])

        if not isinstance(duplicate_groups, list):
            duplicate_groups = []
        if not isinstance(hash_mismatches, list):
            hash_mismatches = []

        exact_duplicate_groups = payload.get("exact_duplicate_groups")
        if isinstance(exact_duplicate_groups, int) and exact_duplicate_groups != len(
            duplicate_groups
        ):
            errors.append(
                "$.exact_duplicate_groups: expected "
                f"{len(duplicate_groups)} based on duplicate_groups length, got {exact_duplicate_groups}"
            )

        exact_duplicate_documents = payload.get("exact_duplicate_documents")
        expected_duplicate_documents = 0
        for group in duplicate_groups:
            if isinstance(group, dict):
                count = group.get("count")
                if isinstance(count, int):
                    expected_duplicate_documents += count

        if (
            isinstance(exact_duplicate_documents, int)
            and exact_duplicate_documents != expected_duplicate_documents
        ):
            errors.append(
                "$.exact_duplicate_documents: expected "
                f"{expected_duplicate_documents} based on duplicate_groups counts, got {exact_duplicate_documents}"
            )

        hash_mismatch_count = payload.get("hash_mismatch_count")
        if isinstance(hash_mismatch_count, int) and hash_mismatch_count != len(hash_mismatches):
            errors.append(
                f"$.hash_mismatch_count: expected {len(hash_mismatches)} based on hash_mismatches length, got {hash_mismatch_count}"
            )

    if registry_name == "parquet_audit.json":
        records = payload.get("records", [])
        parquet_count = payload.get("parquet_count")
        if (
            isinstance(parquet_count, int)
            and isinstance(records, list)
            and parquet_count != len(records)
        ):
            errors.append(
                f"$.parquet_count: expected {len(records)} based on records length, got {parquet_count}"
            )

    if registry_name == "pdf_archive_index.json":
        items = payload.get("items", [])
        pdf_count = payload.get("pdf_count")
        if isinstance(pdf_count, int) and isinstance(items, list) and pdf_count != len(items):
            errors.append(
                f"$.pdf_count: expected {len(items)} based on items length, got {pdf_count}"
            )

    if registry_name in {"document_decomposition_audit.json", "pdf_text_quality_audit.json"}:
        documents = payload.get("documents", [])
        document_count = payload.get("document_count")
        page_count = payload.get("page_count")
        if isinstance(documents, list):
            if isinstance(document_count, int) and document_count != len(documents):
                errors.append(
                    f"$.document_count: expected {len(documents)} based on documents length, "
                    f"got {document_count}"
                )
            expected_pages = sum(
                document.get("page_count", 0)
                for document in documents
                if isinstance(document, dict) and isinstance(document.get("page_count"), int)
            )
            if isinstance(page_count, int) and page_count != expected_pages:
                errors.append(
                    f"$.page_count: expected {expected_pages} based on document page counts, "
                    f"got {page_count}"
                )
            if registry_name == "document_decomposition_audit.json":
                expected_type_counts: dict[str, int] = {}
                for document in documents:
                    if not isinstance(document, dict):
                        continue
                    type_counts = document.get("content_type_counts", {})
                    if not isinstance(type_counts, dict):
                        continue
                    for item_type, count in type_counts.items():
                        if isinstance(count, int):
                            expected_type_counts[str(item_type)] = (
                                expected_type_counts.get(str(item_type), 0) + count
                            )
                if payload.get("content_type_counts") != dict(sorted(expected_type_counts.items())):
                    errors.append("$.content_type_counts: expected aggregate of document tallies")

    if registry_name == "lbm_evidence_audit.json":
        snapshots = payload.get("snapshots", [])
        snapshot_count = payload.get("snapshot_count")
        if (
            isinstance(snapshots, list)
            and isinstance(snapshot_count, int)
            and snapshot_count != len(snapshots)
        ):
            errors.append(
                f"$.snapshot_count: expected {len(snapshots)} based on snapshots length, "
                f"got {snapshot_count}"
            )

    if registry_name == "lbm_root_order_audit.json":
        root_count = payload.get("root_count")
        requested_count = payload.get("requested_harmonic_count")
        effective_count = payload.get("effective_harmonic_count")
        if (
            isinstance(root_count, int)
            and isinstance(requested_count, int)
            and isinstance(effective_count, int)
            and effective_count != min(root_count, requested_count)
        ):
            errors.append(
                "$.effective_harmonic_count: expected "
                f"min(root_count, requested_harmonic_count)={min(root_count, requested_count)}, "
                f"got {effective_count}"
            )

    if registry_name == "claim_coverage_report.toml":
        chapter_coverage = payload.get("chapter_coverage", [])
        group_coverage = payload.get("group_coverage", [])
        unknown_source_ids = payload.get("unknown_source_ids", [])

        if not isinstance(chapter_coverage, list):
            chapter_coverage = []
        if not isinstance(group_coverage, list):
            group_coverage = []
        if not isinstance(unknown_source_ids, list):
            unknown_source_ids = []

        chapters_with_claims = payload.get("chapters_with_claims")
        if isinstance(chapters_with_claims, int) and chapters_with_claims != len(chapter_coverage):
            errors.append(
                "$.chapters_with_claims: expected "
                f"{len(chapter_coverage)} based on chapter_coverage length, got {chapters_with_claims}"
            )

        groups_tracked = payload.get("groups_tracked")
        if isinstance(groups_tracked, int) and groups_tracked != len(group_coverage):
            errors.append(
                "$.groups_tracked: expected "
                f"{len(group_coverage)} based on group_coverage length, got {groups_tracked}"
            )

        unknown_source_id_count = payload.get("unknown_source_id_count")
        if isinstance(unknown_source_id_count, int) and unknown_source_id_count != len(
            unknown_source_ids
        ):
            errors.append(
                "$.unknown_source_id_count: expected "
                f"{len(unknown_source_ids)} based on unknown_source_ids length, got {unknown_source_id_count}"
            )

        claims_total = payload.get("claims_total")
        if isinstance(claims_total, int):
            inferred_claims_total = 0
            for row in chapter_coverage:
                if not isinstance(row, dict):
                    continue
                claim_ids = row.get("claim_ids", [])
                if isinstance(claim_ids, list):
                    inferred_claims_total += len(claim_ids)
            if claims_total != inferred_claims_total:
                errors.append(
                    "$.claims_total: expected "
                    f"{inferred_claims_total} based on chapter_coverage claim_ids lengths, got {claims_total}"
                )

    return errors


def main() -> int:
    failures: list[str] = []

    present_toml = {path.name for path in REGISTRY_DIR.glob("*.toml") if path.is_file()}
    expected_toml = set(TOML_SCHEMA_BY_REGISTRY.keys())
    present_json = {path.name for path in REGISTRY_DIR.glob("*.json") if path.is_file()}
    expected_json = set(JSON_SCHEMA_BY_REGISTRY.keys())

    unknown_toml = sorted(present_toml - expected_toml)
    if unknown_toml:
        failures.append(
            "unmapped registry TOML files (add schemas/mapping): " + ", ".join(unknown_toml)
        )

    unknown_json = sorted(present_json - expected_json)
    if unknown_json:
        failures.append(
            "unmapped registry JSON files (add schemas/mapping): " + ", ".join(unknown_json)
        )

    missing_expected_toml = sorted(expected_toml - present_toml)
    if missing_expected_toml:
        failures.append("missing expected registry TOML files: " + ", ".join(missing_expected_toml))

    for registry_name, schema_name in sorted(TOML_SCHEMA_BY_REGISTRY.items()):
        registry_path = REGISTRY_DIR / registry_name
        schema_path = SCHEMA_DIR / schema_name

        if not schema_path.exists():
            failures.append(f"missing schema file: {schema_path.relative_to(REPO_ROOT).as_posix()}")
            continue
        if not registry_path.exists():
            continue

        schema = load_json(schema_path)
        payload = tomllib.loads(registry_path.read_text(encoding="utf-8"))

        schema_errors = validate_with_jsonschema(payload, schema)
        for error in schema_errors:
            failures.append(f"{registry_path.relative_to(REPO_ROOT).as_posix()}: {error}")

        for error in semantic_checks(registry_name, payload):
            failures.append(f"{registry_path.relative_to(REPO_ROOT).as_posix()}: {error}")

    for registry_name, config in sorted(JSON_SCHEMA_BY_REGISTRY.items()):
        schema_name = str(config.get("schema", "")).strip()
        required = bool(config.get("required", False))
        registry_path = REGISTRY_DIR / registry_name
        schema_path = SCHEMA_DIR / schema_name

        if not schema_name:
            failures.append(
                f"invalid JSON registry schema mapping for {registry_name}: empty schema name"
            )
            continue
        if not schema_path.exists():
            failures.append(f"missing schema file: {schema_path.relative_to(REPO_ROOT).as_posix()}")
            continue
        if not registry_path.exists():
            if required:
                failures.append(f"missing expected registry JSON file: {registry_name}")
            continue

        schema = load_json(schema_path)
        try:
            payload = load_json(registry_path)
        except json.JSONDecodeError as exc:
            failures.append(
                f"{registry_path.relative_to(REPO_ROOT).as_posix()}: invalid JSON: {exc}"
            )
            continue

        schema_errors = validate_with_jsonschema(payload, schema)
        for error in schema_errors:
            failures.append(f"{registry_path.relative_to(REPO_ROOT).as_posix()}: {error}")

        for error in semantic_checks(registry_name, payload):
            failures.append(f"{registry_path.relative_to(REPO_ROOT).as_posix()}: {error}")

    if failures:
        print("Registry schema validation FAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Registry schema validation PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
