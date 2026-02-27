#!/usr/bin/env python3
"""Validate TOML and JSON registry files against JSON schemas for drift detection."""

from __future__ import annotations

import json
import re
import tomllib
from datetime import datetime
from pathlib import Path
from typing import Any


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
    "parquet_audit.json": {
        "schema": "parquet_audit.schema.json",
        "required": True,
    },
    "pdf_archive_index.json": {
        "schema": "pdf_archive_index.schema.json",
        "required": False,
    },
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def type_matches(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return (isinstance(value, int) or isinstance(value, float)) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    return False


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
            errors.append(
                f"{path}: expected type {expected_types}, got {type(instance).__name__}"
            )
            return errors

    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{path}: value {instance!r} not in enum {schema['enum']!r}")

    if isinstance(instance, str):
        min_length = schema.get("minLength")
        if isinstance(min_length, int) and len(instance) < min_length:
            errors.append(f"{path}: string shorter than minLength={min_length}")
        pattern = schema.get("pattern")
        if isinstance(pattern, str):
            if re.search(pattern, instance) is None:
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
    try:
        from jsonschema import Draft202012Validator, FormatChecker
    except Exception:
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
        if isinstance(exact_duplicate_groups, int) and exact_duplicate_groups != len(duplicate_groups):
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
        if isinstance(parquet_count, int) and isinstance(records, list) and parquet_count != len(records):
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
        if (
            isinstance(unknown_source_id_count, int)
            and unknown_source_id_count != len(unknown_source_ids)
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
        failures.append(
            "missing expected registry TOML files: " + ", ".join(missing_expected_toml)
        )

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
            failures.append(f"invalid JSON registry schema mapping for {registry_name}: empty schema name")
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
