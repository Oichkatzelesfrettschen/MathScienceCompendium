"""Tests for the external Fourier-lattice map into E7 P/Q."""

from __future__ import annotations

import pytest

from mathphysics.fourier_quotient import (
    Z2FourierHomomorphism,
    all_z2_fourier_homomorphisms,
    build_fourier_quotient_audit,
    e7_weight_root_quotient_order,
    enumerate_exact_triads,
    square_symmetry_orbit,
)


def test_e7_weight_root_quotient_has_order_two():
    assert e7_weight_root_quotient_order() == 2


def test_all_fourier_homomorphisms_are_enumerated():
    coefficients = {
        (homomorphism.coefficient_x, homomorphism.coefficient_y)
        for homomorphism in all_z2_fourier_homomorphisms()
    }
    assert coefficients == {(0, 0), (0, 1), (1, 0), (1, 1)}


def test_nontrivial_square_symmetry_invariant_map_is_unique():
    maps = [
        homomorphism
        for homomorphism in all_z2_fourier_homomorphisms()
        if homomorphism.is_nontrivial and homomorphism.is_square_symmetry_invariant
    ]
    assert maps == [Z2FourierHomomorphism(1, 1)]


@pytest.mark.parametrize("mode", [(1, 0), (2, 3), (-4, 1), (0, 0)])
def test_parity_sum_map_is_constant_on_square_symmetry_orbits(mode):
    homomorphism = Z2FourierHomomorphism(1, 1)
    charges = {homomorphism.charge(image) for image in square_symmetry_orbit(mode)}
    assert charges == {homomorphism.charge(mode)}


@pytest.mark.parametrize("radius", [1, 2, 4])
def test_every_exact_triad_is_admitted_by_every_homomorphism(radius):
    triads = enumerate_exact_triads(radius)
    assert triads
    for homomorphism in all_z2_fourier_homomorphisms():
        assert all(homomorphism.admits_exact_triad(triad) for triad in triads)


def test_audit_separates_map_existence_from_filter_failure():
    audit = build_fourier_quotient_audit(radius=3)
    assert audit["nontrivial_square_symmetry_map_exists"] is True
    assert audit["map_existence_outcome"] == "established"
    assert audit["triad_filter_outcome"] == "falsified"
    assert audit["maximum_rejected_exact_triad_count"] == 0


def test_invalid_z2_coefficients_are_rejected():
    with pytest.raises(ValueError, match="zero or one"):
        Z2FourierHomomorphism(2, 0)
