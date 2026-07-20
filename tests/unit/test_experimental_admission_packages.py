"""Tests for operational physical-claim admission packages."""

from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_PATH = REPO_ROOT / "data" / "registry" / "experimental_admission_packages.json"


def load_packages():
    payload = json.loads(PACKAGE_PATH.read_text(encoding="ascii"))
    return {package["claim_id"]: package for package in payload["packages"]}


def test_packages_cover_admission_and_exclusion_claims():
    packages = load_packages()
    assert set(packages) == {
        "scalar_field_curvature_mechanism",
        "zpe_energy_harvesting",
        "time_crystal_energy_amplification",
        "tourmaline_novel_energy_effect",
        "origami_fold_merge_operator",
        "consciousness_resonance",
    }


def test_measurable_packages_define_observables_controls_and_energy_closure():
    packages = load_packages()
    for package in packages.values():
        if not package["measurable"]:
            continue
        assert len(package["observables"]) >= 3
        assert len(package["controls"]) >= 3
        assert package["energy_accounting"]["required"] is True
        assert len(package["energy_accounting"]["channels"]) >= 6
        assert "residual" in package["energy_accounting"]["closure_equation"]
        assert len(package["acceptance_criteria"]) >= 3
        assert len(package["rejection_criteria"]) >= 3


def test_energy_claims_retain_every_major_input_output_and_storage_class():
    packages = load_packages()
    for claim_id in (
        "zpe_energy_harvesting",
        "time_crystal_energy_amplification",
        "tourmaline_novel_energy_effect",
    ):
        directions = {
            channel["direction"] for channel in packages[claim_id]["energy_accounting"]["channels"]
        }
        assert "input" in directions
        assert "output" in directions
        assert "stored" in directions
        assert packages[claim_id]["admission_ready"] is False


def test_excluded_claims_have_no_pretend_observables_or_energy_budget():
    packages = load_packages()
    for claim_id in ("origami_fold_merge_operator", "consciousness_resonance"):
        package = packages[claim_id]
        assert package["current_outcome"] == "excluded"
        assert package["measurable"] is False
        assert package["observables"] == []
        assert package["controls"] == []
        assert package["energy_accounting"]["required"] is False
