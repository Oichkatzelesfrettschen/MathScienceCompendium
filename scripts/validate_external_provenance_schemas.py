#!/usr/bin/env python3
"""Validate external provenance JSON files against schemas."""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_EXTERNAL = REPO_ROOT / "data" / "external"
SCHEMA_DIR = REPO_ROOT / "schemas" / "external"
TOP_LEVEL_PROVENANCE = DATA_EXTERNAL / "PROVENANCE.json"
TOP_LEVEL_SCHEMA = SCHEMA_DIR / "provenance_fetch_results.schema.json"
LANE_SCHEMA = SCHEMA_DIR / "provenance_lane.schema.json"


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


def semantic_checks(path: Path, payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    results = payload.get("results")
    if isinstance(results, list):
        for idx, item in enumerate(results):
            if not isinstance(item, dict):
                continue
            status = str(item.get("status", "")).strip()
            target_relpath = str(item.get("target_relpath", "")).strip()
            if status in {"downloaded", "exists"} and target_relpath:
                target_path = REPO_ROOT / target_relpath
                if not target_path.exists():
                    errors.append(
                        f"$.results[{idx}].target_relpath: missing local target file {target_relpath}"
                    )

    assets = payload.get("assets")
    if isinstance(assets, list):
        asset_count = payload.get("asset_count")
        if isinstance(asset_count, int) and asset_count != len(assets):
            errors.append(
                f"$.asset_count: expected {len(assets)} based on assets length, got {asset_count}"
            )

        for idx, item in enumerate(assets):
            if not isinstance(item, dict):
                continue
            local_relpath = str(item.get("local_relpath", "")).strip()
            if local_relpath:
                local_path = REPO_ROOT / local_relpath
                if not local_path.exists():
                    errors.append(
                        f"$.assets[{idx}].local_relpath: missing local file {local_relpath}"
                    )

    return errors


def main() -> int:
    failures: list[str] = []

    if not TOP_LEVEL_SCHEMA.exists():
        failures.append(f"missing schema file: {TOP_LEVEL_SCHEMA.relative_to(REPO_ROOT).as_posix()}")
    if not LANE_SCHEMA.exists():
        failures.append(f"missing schema file: {LANE_SCHEMA.relative_to(REPO_ROOT).as_posix()}")

    if not TOP_LEVEL_PROVENANCE.exists():
        failures.append("missing required provenance file: data/external/PROVENANCE.json")

    lane_provenance_paths: list[Path] = []
    for subdir in sorted(DATA_EXTERNAL.iterdir()):
        if not subdir.is_dir():
            continue
        if subdir.name in {"fetch_traces"}:
            continue
        provenance = subdir / "PROVENANCE.json"
        if provenance.exists():
            lane_provenance_paths.append(provenance)
        else:
            has_files = any(child.is_file() for child in subdir.iterdir())
            if has_files:
                failures.append(
                    f"missing lane provenance file: {provenance.relative_to(REPO_ROOT).as_posix()}"
                )

    if failures:
        print("External provenance schema validation FAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1

    top_schema = load_json(TOP_LEVEL_SCHEMA)
    lane_schema = load_json(LANE_SCHEMA)

    files_to_validate = [(TOP_LEVEL_PROVENANCE, top_schema)]
    for path in lane_provenance_paths:
        files_to_validate.append((path, lane_schema))

    for path, schema in files_to_validate:
        relpath = path.relative_to(REPO_ROOT).as_posix()
        try:
            payload = load_json(path)
        except json.JSONDecodeError as exc:
            failures.append(f"{relpath}: invalid JSON: {exc}")
            continue

        schema_errors = validate_with_jsonschema(payload, schema)
        for error in schema_errors:
            failures.append(f"{relpath}: {error}")

        for error in semantic_checks(path, payload):
            failures.append(f"{relpath}: {error}")

    if failures:
        print("External provenance schema validation FAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("External provenance schema validation PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
