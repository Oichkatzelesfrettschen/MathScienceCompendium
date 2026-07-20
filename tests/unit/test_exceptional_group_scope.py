"""Tests for the exceptional-group and moonshine scope audit."""

from __future__ import annotations

from scripts.audit_exceptional_group_scope import build_audit


def test_albert_group_roles_are_not_conflated():
    audit = build_audit()
    roles = {record["group"]: record for record in audit["albert_ladder"]}
    assert roles["F4"]["status"] == "established"
    assert "automorphism" in roles["F4"]["role"]
    assert "determinant-preserving" in roles["E6(-26)"]["role"]
    assert "not its automorphism group" in roles["E7(-25)"]["role"]
    assert roles["E7 as Aut(J3(S))"]["status"] == "rejected"


def test_albert_product_is_executable_and_satisfies_regressions():
    implementation = build_audit()["albert_implementation"]
    assert implementation["coordinate_dimension"] == 27
    assert implementation["inputs_are_hermitian"] is True
    assert implementation["nonzero_product_norm"] > 0.0
    assert implementation["identity_residual_maximum_absolute"] < 1e-6
    assert implementation["commutativity_residual_maximum_absolute"] < 1e-6
    assert implementation["jordan_identity_residual_maximum_absolute"] < 2e-5


def test_kac_moody_and_moonshine_scopes_are_bounded():
    audit = build_audit()
    extensions = {record["name"]: record for record in audit["kac_moody_extensions"]}
    assert extensions["E9"]["determinant"] == 0
    assert extensions["E10"]["determinant"] == -1
    assert extensions["E11"]["determinant"] == -2
    assert audit["moonshine_scope"]["physical_stability_claim_status"] == "rejected"
