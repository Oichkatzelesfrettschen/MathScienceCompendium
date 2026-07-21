"""Tests for normalized clean-reproduction comparisons."""

from __future__ import annotations

from copy import deepcopy

from scripts.verify_clean_reproduction import normalized_result


def test_normalization_removes_only_execution_provenance():
    primary = {
        "source_commit": "a" * 40,
        "aggregate_decision": "not_supported",
        "primary_contrasts": [{"effect_estimate": -0.02}],
        "evidence_archive": {
            "relpath": "data/evidence/primary.tar",
            "sha256": "1" * 64,
        },
    }
    reproduction = deepcopy(primary)
    reproduction["source_commit"] = "b" * 40
    reproduction["evidence_archive"]["relpath"] = "data/reproduction/replay.tar"
    assert normalized_result(primary) == normalized_result(reproduction)


def test_normalization_preserves_scientific_differences():
    primary = {
        "source_commit": "a" * 40,
        "aggregate_decision": "not_supported",
        "evidence_archive": {"relpath": "primary.tar", "sha256": "1" * 64},
    }
    reproduction = deepcopy(primary)
    reproduction["aggregate_decision"] = "supported"
    assert normalized_result(primary) != normalized_result(reproduction)
