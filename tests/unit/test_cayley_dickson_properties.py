"""Property-table and counterexample tests for Cayley-Dickson algebras."""

from __future__ import annotations

from scripts.audit_cayley_dickson_properties import build_audit

from mathphysics.algebras.cayley_dickson import Chingon, Polyxon, Rouxion


EXPECTED = {
    "Real": (True, True, True, True, True, True, True, False),
    "Complex": (True, True, True, True, True, True, True, False),
    "Quaternion": (False, True, True, True, True, True, True, False),
    "Octonion": (False, False, True, True, True, True, True, False),
    "Sedenion": (False, False, False, True, True, False, False, True),
    "Pathion": (False, False, False, True, True, False, False, True),
}


def test_declared_property_table_matches_theorem_boundaries():
    records = {record["name"]: record for record in build_audit()["algebras"]}
    for name, expected in EXPECTED.items():
        properties = records[name]["properties"]
        actual = (
            properties["is_commutative"],
            properties["is_associative"],
            properties["is_alternative"],
            properties["is_power_associative"],
            properties["is_flexible"],
            properties["norm_is_multiplicative"],
            properties["is_division_algebra"],
            properties["has_zero_divisors"],
        )
        assert actual == expected


def test_failed_properties_have_executable_counterexamples():
    records = {record["name"]: record for record in build_audit()["algebras"]}
    assert records["Quaternion"]["witnesses"]["commutator_maximum_absolute"] > 0.0
    assert records["Octonion"]["witnesses"]["associator_maximum_absolute"] > 0.0
    for name in ("Sedenion", "Pathion"):
        witnesses = records[name]["witnesses"]
        assert witnesses["left_alternative_residual_maximum_absolute"] > 0.0
        assert witnesses["norm_composition_absolute_residual"] > 0.0
        assert witnesses["zero_divisor"]["left_norm_squared"] > 0.0
        assert witnesses["zero_divisor"]["right_norm_squared"] > 0.0
        assert witnesses["zero_divisor"]["product_norm_squared"] == 0.0


def test_quadratic_and_flexible_identities_hold_for_dense_regression_vectors():
    for record in build_audit()["algebras"]:
        witnesses = record["witnesses"]
        assert witnesses["quadratic_identity_residual_maximum_absolute"] == 0.0
        assert witnesses["flexibility_residual_maximum_absolute"] == 0.0


def test_exported_higher_algebras_construct_and_multiply_at_declared_dimension():
    for algebra_class, dimension in ((Chingon, 256), (Rouxion, 512), (Polyxon, 1024)):
        identity = algebra_class.basis_element(0)
        basis = algebra_class.basis_element(dimension - 1)
        product = identity * basis
        assert len(identity.coeffs) == dimension
        assert len(product.coeffs) == dimension
        assert isinstance(product, algebra_class)
        assert product.coeffs[dimension - 1] == 1.0
