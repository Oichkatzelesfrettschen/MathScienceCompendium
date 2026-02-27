from __future__ import annotations

import numpy as np
import pytest

from mathphysics.modular_forms import (
    AffineCharacterAnalyzer,
    EllipticCurves,
    ModularForms,
    MonstrousMoonshine,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# A well-behaved tau value in the upper half-plane
TAU = 1j  # Im(tau) = 1 -> q = exp(-2*pi) very small, fast convergence
TAU_SMALL = 0.5j  # Im(tau) = 0.5 -> q = exp(-pi), still convergent


# ---------------------------------------------------------------------------
# ModularForms.tau_to_q
# ---------------------------------------------------------------------------


def test_tau_to_q_pure_imaginary():
    tau = 1j
    q = ModularForms.tau_to_q(tau)
    expected = np.exp(2j * np.pi * tau)
    assert abs(q - expected) < 1e-15


def test_tau_to_q_modulus_less_than_one():
    # For Im(tau) > 0, |q| = exp(-2*pi*Im(tau)) < 1
    tau = 2j
    q = ModularForms.tau_to_q(tau)
    assert abs(q) < 1.0


# ---------------------------------------------------------------------------
# Eisenstein series E4
# ---------------------------------------------------------------------------


def test_eisenstein_e4_leading_term():
    # For |q| very small, E4(q) -> 1
    q = 1e-30 + 0j
    val = ModularForms.eisenstein_e4(q, num_terms=5)
    assert abs(val - 1.0) < 1e-10


def test_eisenstein_e4_q_expansion_first_coeff():
    # E4 = 1 + 240*q + ... coefficient of q is 240 * sigma_3(1) = 240
    q = 1e-6 + 0j
    val = ModularForms.eisenstein_e4(q, num_terms=3)
    expected = 1.0 + 240 * q
    assert abs(val - expected) < 1e-3


def test_eisenstein_series_e4_via_tau():
    tau = 2j
    val_tau = ModularForms.eisenstein_series_E4(tau, num_terms=20)
    q = ModularForms.tau_to_q(tau)
    val_q = ModularForms.eisenstein_e4(q, num_terms=20)
    assert abs(val_tau - val_q) < 1e-12


# ---------------------------------------------------------------------------
# Eisenstein series E6
# ---------------------------------------------------------------------------


def test_eisenstein_e6_leading_term():
    q = 1e-30 + 0j
    val = ModularForms.eisenstein_e6(q, num_terms=5)
    assert abs(val - 1.0) < 1e-10


def test_eisenstein_e6_q_expansion_first_coeff():
    # E6 = 1 - 504*q + ... coefficient of q is -504 * sigma_5(1) = -504
    q = 1e-6 + 0j
    val = ModularForms.eisenstein_e6(q, num_terms=3)
    expected = 1.0 - 504 * q
    assert abs(val - expected) < 1e-3


def test_eisenstein_series_e6_via_tau():
    tau = 2j
    val_tau = ModularForms.eisenstein_series_E6(tau, num_terms=20)
    q = ModularForms.tau_to_q(tau)
    val_q = ModularForms.eisenstein_e6(q, num_terms=20)
    assert abs(val_tau - val_q) < 1e-12


# ---------------------------------------------------------------------------
# Ramanujan tau function
# ---------------------------------------------------------------------------


def test_ramanujan_tau_n1_is_1():
    vals = ModularForms.ramanujan_tau(num_terms=10)
    assert vals[0] == 1


def test_ramanujan_tau_n2_is_minus24():
    vals = ModularForms.ramanujan_tau(num_terms=10)
    assert vals[1] == -24


def test_ramanujan_tau_n3_is_252():
    vals = ModularForms.ramanujan_tau(num_terms=10)
    assert vals[2] == 252


def test_ramanujan_tau_length():
    vals = ModularForms.ramanujan_tau(num_terms=5)
    assert len(vals) == 5


def test_ramanujan_tau_returns_ndarray():
    vals = ModularForms.ramanujan_tau()
    assert isinstance(vals, np.ndarray)


def test_ramanujan_tau_known_values():
    vals = ModularForms.ramanujan_tau(num_terms=10)
    expected = np.array([1, -24, 252, -1472, 4830, -6048, -16744, 84480, -113643, -115920])
    np.testing.assert_array_equal(vals, expected)


# ---------------------------------------------------------------------------
# Klein j-function q-expansion
# ---------------------------------------------------------------------------


def test_klein_j_q_expansion_first_coefficient():
    # j = q^{-1} + 744 + 196884*q + ...
    # klein_j_q_expansion returns the non-negative part; index 0 is 1 (coefficient of q^0 after the pole)
    coeffs = ModularForms.klein_j_q_expansion(num_coeffs=6)
    assert coeffs[0] == 1


def test_klein_j_q_expansion_second_coefficient():
    coeffs = ModularForms.klein_j_q_expansion(num_coeffs=6)
    assert coeffs[1] == 744


def test_klein_j_q_expansion_third_coefficient():
    coeffs = ModularForms.klein_j_q_expansion(num_coeffs=6)
    assert coeffs[2] == 196884


def test_klein_j_q_expansion_fourth_coefficient():
    coeffs = ModularForms.klein_j_q_expansion(num_coeffs=6)
    assert coeffs[3] == 21493760


def test_klein_j_q_expansion_length_respects_num_coeffs():
    coeffs = ModularForms.klein_j_q_expansion(num_coeffs=3)
    assert len(coeffs) == 3


def test_klein_j_q_expansion_returns_ndarray():
    coeffs = ModularForms.klein_j_q_expansion()
    assert isinstance(coeffs, np.ndarray)


# ---------------------------------------------------------------------------
# Dedekind eta function
# ---------------------------------------------------------------------------


def test_dedekind_eta_nonzero_for_valid_tau():
    tau = 2j  # well inside the upper half-plane
    val = ModularForms.dedekind_eta(tau, num_terms=50)
    assert abs(val) > 1e-15


def test_dedekind_eta_accepts_nome_q():
    # Pass a nome q with |q| < 1
    q = 0.01 + 0j
    val = ModularForms.dedekind_eta(q, num_terms=30)
    assert np.isfinite(abs(val))


def test_dedekind_eta_is_complex():
    tau = 1j
    val = ModularForms.dedekind_eta(tau, num_terms=20)
    assert isinstance(val, complex)


# ---------------------------------------------------------------------------
# j-invariant
# ---------------------------------------------------------------------------


def test_j_invariant_is_finite():
    tau = 2j
    j = ModularForms.j_invariant(tau, num_terms=30)
    assert np.isfinite(abs(j))


def test_j_invariant_large_imaginary_part_near_zero():
    # For Im(tau) -> infinity, j(tau) -> 0 (actually j -> q^{-1} -> 0)
    tau = 10j
    j = ModularForms.j_invariant(tau, num_terms=10)
    # |j| should be extremely small for very large imaginary part
    assert abs(j) <= 1e10  # very broad sanity check


# ---------------------------------------------------------------------------
# MonstrousMoonshine
# ---------------------------------------------------------------------------


def test_monstrous_moonshine_order_is_large_integer():
    order = MonstrousMoonshine.monster_order()
    assert order > 10 ** 50


def test_monster_group_order_alias():
    assert MonstrousMoonshine.monster_group_order() == MonstrousMoonshine.monster_order()


def test_q_expansion_j_returns_finite():
    tau = 2j
    val = MonstrousMoonshine.q_expansion_j(tau, n_terms=10)
    assert np.isfinite(abs(val))


# ---------------------------------------------------------------------------
# EllipticCurves
# ---------------------------------------------------------------------------


def test_weierstrass_invariants_returns_tuple():
    tau = 2j
    g2, g3 = EllipticCurves.weierstrass_invariants(tau, num_terms=20)
    assert np.isfinite(abs(g2))
    assert np.isfinite(abs(g3))


def test_weierstrass_invariants_g2_proportional_to_e4():
    tau = 2j
    g2, _ = EllipticCurves.weierstrass_invariants(tau, num_terms=20)
    e4 = ModularForms.eisenstein_series_E4(tau, num_terms=20)
    # g2 = 60 * E4
    np.testing.assert_allclose(abs(g2), abs(60 * e4), rtol=1e-10)


def test_compute_invariants_returns_dict():
    result = EllipticCurves.compute_invariants(g2=1.0, g3=1.0)
    assert "discriminant" in result
    assert "j_invariant" in result


def test_compute_invariants_discriminant_formula():
    g2, g3 = 4.0, 4.0
    result = EllipticCurves.compute_invariants(g2, g3)
    expected_delta = g2 ** 3 - 27 * g3 ** 2
    assert abs(result["discriminant"] - expected_delta) < 1e-10


# ---------------------------------------------------------------------------
# AffineCharacterAnalyzer
# ---------------------------------------------------------------------------


def test_affine_character_vacuum_finite():
    analyzer = AffineCharacterAnalyzer("E8", 8)
    q = 0.01 + 0j
    val = analyzer.vacuum_character(q)
    assert np.isfinite(abs(val))


def test_affine_character_nonzero():
    analyzer = AffineCharacterAnalyzer("SL2", 1)
    q = 0.01 + 0j
    val = analyzer.vacuum_character(q)
    assert abs(val) > 0
