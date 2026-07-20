"""Tests for registry-driven paper evidence artifacts."""

from __future__ import annotations

from pathlib import Path

from scripts.generate_paper_evidence_artifacts import main


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_generator_emits_nonempty_ascii_tables_and_figures():
    assert main() == 0
    for filename in (
        "review_claim_status.png",
        "review_framework_overlap.png",
        "review_evidence_flow.png",
        "review_beta_ablation.png",
    ):
        output_path = REPO_ROOT / "figures" / filename
        assert output_path.is_file()
        assert output_path.stat().st_size > 1000

    for filename in (
        "review_claim_status_rows.tex",
        "review_cayley_property_rows.tex",
        "review_admission_rows.tex",
        "review_beta_result_rows.tex",
    ):
        output_path = REPO_ROOT / "papers" / "generated" / filename
        payload = output_path.read_bytes()
        assert len(payload) > 50
        assert all(byte < 128 for byte in payload)
        assert all(line == line.rstrip() for line in payload.decode("ascii").splitlines())
