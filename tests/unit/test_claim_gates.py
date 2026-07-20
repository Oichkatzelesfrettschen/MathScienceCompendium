"""Tests for the executable framework claim gates."""

from __future__ import annotations

import json

from scripts.run_claim_gates import REPO_ROOT, SPECIAL_CHECKERS, execute_claim_gates


def test_gate_registry_covers_claim_ledger_exactly():
    claims = json.loads(
        (REPO_ROOT / "data/registry/unified_framework_claims.json").read_text(encoding="ascii")
    )["claims"]
    gates = json.loads(
        (REPO_ROOT / "data/registry/claim_gate_registry.json").read_text(encoding="ascii")
    )["gates"]
    claim_ids = [claim["id"] for claim in claims]
    gate_ids = [gate["claim_id"] for gate in gates]
    assert len(gate_ids) == 23
    assert gate_ids == claim_ids
    assert len(set(gate_ids)) == 23


def test_all_claim_gates_match_declared_outcomes():
    payload = execute_claim_gates()
    assert payload["claim_count"] == 23
    assert payload["gate_count"] == 23
    assert payload["failed_count"] == 0
    assert payload["all_gates_passed"] is True


def test_every_registered_gate_has_an_executable_checker():
    gates = json.loads(
        (REPO_ROOT / "data/registry/claim_gate_registry.json").read_text(encoding="ascii")
    )["gates"]
    assert {gate["checker"] for gate in gates} == set(SPECIAL_CHECKERS)


def test_gate_results_retain_structural_counterexamples():
    results = {result["claim_id"]: result for result in execute_claim_gates()["results"]}
    assert (
        results["octonion_normed_division_boundary"]["metrics"]["zero_divisor_product_norm_squared"]
        == 0.0
    )
    assert (
        results["external_fourier_quotient_map"]["metrics"]["maximum_rejected_exact_triad_count"]
        == 0
    )
    assert results["e7_root_quotient_charge"]["metrics"]["maximum_basis_residual"] == 0.0
    assert results["e7_root_quotient_charge"]["metrics"]["maximum_integrality_error"] == 0.0
    assert results["e9_e10_e11_classification"]["metrics"]["E9"]["determinant"] == 0
    assert (
        results["higher_cayley_dickson_physical_mapping"]["metrics"]["present_experimental_fields"]
        == []
    )
    assert results["e10_e11_supergravity_scope"]["metrics"]["e11_is_conjectural"] is True
    assert (
        len(results["fractional_and_negative_dimension_scope"]["metrics"]["implemented_estimators"])
        == 4
    )
    assert results["kac_moody_fluid_transfer"]["metrics"]["not_implemented_method_count"] >= 4
    assert results["gravitoelectromagnetism_scope"]["metrics"]["paper_rejects_new_coupling"] is True
