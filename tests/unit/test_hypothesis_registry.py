"""Tests for exhaustive hypothesis coverage and report generation."""

from __future__ import annotations

import json

from scripts.build_hypothesis_registry_report import REPO_ROOT, render_report


def load_json(relative_path: str) -> dict[str, object]:
    """Load a repository JSON artifact as ASCII."""
    return json.loads((REPO_ROOT / relative_path).read_text(encoding="ascii"))


def test_hypothesis_registry_covers_every_open_canonical_claim_once():
    claims = load_json("data/registry/unified_framework_claims.json")["claims"]
    hypotheses = load_json("data/registry/hypothesis_registry.json")["hypotheses"]
    eligible_statuses = {"bounded", "excluded", "falsified", "unsupported"}
    expected = {claim["id"] for claim in claims if claim["status"] in eligible_statuses}
    covered = [claim_id for hypothesis in hypotheses for claim_id in hypothesis["source_claim_ids"]]
    assert set(covered) == expected
    assert len(covered) == len(set(covered))


def test_result_promotion_requires_independent_reproduction():
    hypotheses = load_json("data/registry/hypothesis_registry.json")["hypotheses"]
    for hypothesis in hypotheses:
        if hypothesis["paper_promotion"] in {"eligible", "promoted"}:
            assert hypothesis["implementation_status"] in {
                "implemented_supported",
                "implemented_negative",
            }
            assert hypothesis["independent_reproduction"]["status"] == "passed"


def test_every_archival_conjecture_has_a_unique_disposition():
    payload = load_json("data/registry/hypothesis_registry.json")
    items = [
        item for group in payload["archival_conjecture_dispositions"] for item in group["items"]
    ]
    assert len(items) == 54
    assert len({item["id"] for item in items}) == 54
    assert all(item["rationale"] for item in items)


def test_generated_report_is_current_and_ascii():
    registry = load_json("data/registry/hypothesis_registry.json")
    expected = render_report(registry)
    actual = (REPO_ROOT / "docs/framework/HYPOTHESIS_REGISTRY.md").read_text(encoding="ascii")
    assert actual == expected
    assert actual.isascii()
