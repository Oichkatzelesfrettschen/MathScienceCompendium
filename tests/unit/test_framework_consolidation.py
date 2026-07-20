"""Tests for framework deduplication and claim-admission contracts."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import tomllib
from scripts.analyze_framework_overlap import extract_blocks, normalize_block
from scripts.decompose_framework_documents import REPO_ROOT
from scripts.run_mineru_manifest import expected_outputs, outputs_complete


if TYPE_CHECKING:
    from pathlib import Path


def test_overlap_normalization_ignores_case_punctuation_and_spacing():
    left = normalize_block("E_8:  A root system!\n")
    right = normalize_block("e 8 -- a ROOT system")
    assert left == right == "e 8 a root system"


def test_overlap_blocks_retain_source_line_ranges():
    blocks = extract_blocks(
        [
            "Short heading\n",
            "\n",
            "This paragraph is deliberately long enough to enter the normalized overlap "
            "audit and retain its exact source range.\n",
            "It continues on a second source line.\n",
        ]
    )
    assert len(blocks) == 1
    assert blocks[0]["source_line_start"] == 3
    assert blocks[0]["source_line_end"] == 4


def test_live_overlap_audit_proves_alpha001_maximal_containment():
    audit = json.loads(
        (REPO_ROOT / "data/registry/framework_overlap_audit.json").read_text(encoding="ascii")
    )
    match = next(
        record
        for record in audit["pairwise_overlap"]
        if {
            record["left_document_id"],
            record["right_document_id"],
        }
        == {
            "alpha001-06-draft-aether-framework",
            "maximal-extraction-set1-set2",
        }
    )
    assert match["shared_block_count"] == 390
    assert match["left_block_containment"] == 1.0
    assert match["right_block_containment"] == 1.0


def test_live_claim_ledger_has_valid_anchors_sources_and_evidence_paths():
    claims = json.loads(
        (REPO_ROOT / "data/registry/unified_framework_claims.json").read_text(encoding="ascii")
    )
    decomposition = json.loads(
        (REPO_ROOT / "data/registry/framework_document_decomposition.json").read_text(
            encoding="ascii"
        )
    )
    documents = {document["id"]: document for document in decomposition["documents"]}
    manifest = tomllib.loads((REPO_ROOT / "data/external/sources.toml").read_text(encoding="utf-8"))
    external_ids = {source["id"] for source in manifest["sources"]}
    claim_ids = [claim["id"] for claim in claims["claims"]]
    assert len(claim_ids) == len(set(claim_ids))

    for claim in claims["claims"]:
        assert claim["status"] in claims["status_vocabulary"]
        assert claim["falsification_test"].strip()
        assert claim["integration_action"].strip()
        for anchor in claim["source_anchors"]:
            document = documents[anchor["document_id"]]
            assert 1 <= anchor["source_line"] <= document["line_count"]
        assert set(claim["evidence_source_ids"]) <= external_ids
        for evidence_relpath in claim["repo_evidence_paths"]:
            assert (REPO_ROOT / evidence_relpath).exists()


def test_mineru_completion_requires_every_primary_output(tmp_path: Path):
    pdf_path = REPO_ROOT / "source_materials/pdfs/example.pdf"
    outputs = expected_outputs(pdf_path, tmp_path)
    assert not outputs_complete(outputs)
    for path in outputs.values():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"content")
    assert outputs_complete(outputs)


def test_live_mineru_run_registry_is_complete_when_present():
    registry_path = REPO_ROOT / "data/registry/aligned_research_mineru_run.json"
    if not registry_path.is_file():
        return
    payload = json.loads(registry_path.read_text(encoding="ascii"))
    assert payload["source_count"] == len(payload["sources"])
    assert payload["complete_count"] + payload["failed_count"] == payload["source_count"]
    for source in payload["sources"]:
        if source["status"] in {"complete", "generated"}:
            assert {output["role"] for output in source["outputs"]} == {
                "markdown",
                "content_list",
                "content_list_v2",
                "middle",
                "model",
                "layout_pdf",
                "origin_pdf",
            }
