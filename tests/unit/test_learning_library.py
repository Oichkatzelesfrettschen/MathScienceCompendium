"""Reject routes whose navigation would skip a prerequisite or lose a lesson."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "learning_library", ROOT / "scripts/validate_learning_library.py"
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def library():
    return json.loads((ROOT / "docs/learning/library.json").read_text())


def test_valid_library():
    assert MODULE.validate_library(library()) == []


def test_cycle_rejected():
    data = library()
    data["nodes"][0]["requires"] = ["proof"]
    assert any("cycle" in issue for issue in MODULE.validate_library(data))


def test_skipped_prerequisite_rejected():
    data = library()
    data["routes"][0]["nodes"].remove("proof")
    assert any("precedes" in issue for issue in MODULE.validate_library(data))


def test_duplicate_unknown_and_escaping_sources_rejected():
    baseline = library()
    data = copy.deepcopy(baseline)
    data["nodes"].append(copy.deepcopy(data["nodes"][0]))
    assert any("duplicate" in issue for issue in MODULE.validate_library(data))
    data = copy.deepcopy(baseline)
    data["routes"][0]["nodes"].append("unwritten_book")
    assert any("unknown node" in issue for issue in MODULE.validate_library(data))
    data = copy.deepcopy(baseline)
    data["nodes"][1]["source"] = "../outside.tex"
    assert any("escapes" in issue for issue in MODULE.validate_library(data))


def test_unpinned_external_and_missing_assessment_rejected():
    data = library()
    data["books"][0]["revision"] = "main"
    data["nodes"][1]["assessment"] = ""
    errors = MODULE.validate_library(data)
    assert any("exact commit" in issue for issue in errors)
    assert any("assessment" in issue for issue in errors)


def test_external_sources_checked_when_checkout_is_supplied(tmp_path):
    data = library()
    external = tmp_path / "external"
    external.mkdir()
    data["nodes"][0]["source"] = "missing.tex"
    errors = MODULE.validate_library(data, external_roots={"precalculus": external})
    assert any("missing source" in error for error in errors)


def test_source_symlink_escape_is_rejected(tmp_path):
    data = library()
    external = tmp_path / "external"
    external.mkdir()
    outside = tmp_path / "outside.tex"
    outside.write_text("A lesson outside its source checkout")
    (external / "source.tex").symlink_to(outside)
    data["nodes"][0]["source"] = "source.tex"
    errors = MODULE.validate_library(data, external_roots={"precalculus": external})
    assert any("resolved path" in error for error in errors)


def test_blank_assessments_and_empty_routes_are_rejected():
    data = library()
    data["nodes"][0]["assessment"] = "  \n "
    data["routes"].append({"id": "empty", "title": "Empty", "nodes": []})
    errors = MODULE.validate_library(data)
    assert any("assessment" in error for error in errors)
    assert any("empty route" in error for error in errors)
