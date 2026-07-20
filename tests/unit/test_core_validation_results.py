"""Tests for deterministic core validation artifact generation."""

from __future__ import annotations

import json

from scripts.generate_core_validation_results import (
    build_e8_validation,
    build_real_validation,
    generate_results,
)


def test_real_validation_reports_implemented_base_properties():
    payload = build_real_validation()
    result = payload["result"]
    assert result["algebra"] == "Real"
    assert result["dimension"] == 1
    assert result["closure"]
    assert result["associative"]
    assert result["commutative"]


def test_e8_validation_reports_exact_root_invariants():
    payload = build_e8_validation()
    assert payload["root_count"] == 240
    assert payload["positive_root_count"] == 120
    assert payload["rank"] == 8
    assert payload["dimension_from_rank_and_roots"] == 248
    assert payload["squared_root_norm_multiplicities"] == {"2": 240}
    assert payload["opposite_root_closure"]
    assert payload["cartan_determinant"] == 1


def test_generated_results_are_complete_json(tmp_path):
    output_paths = generate_results(tmp_path)
    assert len(output_paths) == 2
    for output_path in output_paths:
        payload = json.loads(output_path.read_text(encoding="utf-8"))
        assert payload["schema_version"] == 1
        assert payload["generator"] == "scripts/generate_core_validation_results.py"
