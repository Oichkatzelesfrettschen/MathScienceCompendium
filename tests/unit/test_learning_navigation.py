"""Check generated reader journeys and the operations behind repair links."""

from __future__ import annotations

import copy
import importlib
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
render_outputs = importlib.import_module("render_learning_routes").render_outputs
validate_library = importlib.import_module("validate_learning_library").validate_library


def curriculum():
    return json.loads((ROOT / "docs/learning/library.json").read_text())


def test_generated_surfaces_match_and_local_links_resolve():
    for target, content in render_outputs(curriculum()).items():
        assert target.read_text() == content, target
        if target.suffix != ".md":
            continue
        for link in re.findall(r"\]\(([^)]+)\)", content):
            if "://" in link:
                continue
            path, _, anchor = link.partition("#")
            destination = target.parent / path if path else target
            assert destination.is_file(), (target, link)
            if anchor:
                headings = re.findall(r"^#+ (.+)$", destination.read_text(), re.MULTILINE)
                slugs = [
                    re.sub(r"[^\w -]", "", heading.lower()).replace(" ", "-")
                    for heading in headings
                ]
                assert anchor in slugs, (target, link)


def test_every_bridge_node_has_entry_readiness_and_solutions():
    data = curriculum()
    main = (ROOT / "papers/learning/main.tex").read_text()
    solutions = (ROOT / "papers/learning/generated_solutions.tex").read_text()
    for node in data["nodes"]:
        if node["book"] != "bridge":
            continue
        identifier = node["id"]
        source = (ROOT / node["source"]).read_text()
        assert f"generated/{identifier}_entry" in source
        assert f"generated/{identifier}_ready" in source
        assert f"solution:entry:{identifier}" in solutions
        assert f"solution:ready:{identifier}" in solutions
        assert node["source"].removesuffix(".tex") in main


def test_claim_reader_can_enter_without_quantum_or_foundation_detour():
    data = curriculum()
    route = next(route for route in data["routes"] if route["id"] == "claims")
    assert route["nodes"][0] == "review_evidence"
    assert "quantum" not in route["nodes"]
    assert "precalc" not in route["nodes"]
    assert validate_library(data) == []


def test_repairs_name_the_owner_of_the_failed_operation():
    nodes = {node["id"]: node for node in curriculum()["nodes"]}
    for identifier in ("matrix_maps", "complex_numbers", "probability", "calculus"):
        assert nodes[identifier]["entry_check"]["repair"] == "precalc"
    for identifier in ("quantum", "geometry", "hypercomplex"):
        assert nodes[identifier]["entry_check"]["repair"] == "complex_numbers"


def test_missing_readiness_solution_and_broken_next_link_are_rejected():
    data = copy.deepcopy(curriculum())
    data["nodes"][1]["readiness"]["answer"] = ""
    data["nodes"][2]["next"][0]["node"] = "missing"
    issues = validate_library(data)
    assert any("readiness" in issue for issue in issues)
    assert any("next destination" in issue for issue in issues)
