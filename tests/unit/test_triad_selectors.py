"""Exact tests for structural Fourier-triad selectors."""

from __future__ import annotations

from fractions import Fraction

import pytest

from mathphysics.algebras.roots import E7RootSystem
from mathphysics.fourier_quotient import enumerate_exact_triads
from mathphysics.triad_selectors import (
    E7_CARTAN_MATRIX,
    barotropic_channel_is_active,
    build_triad_selector_audit,
    checkerboard_kernel_admits,
    e7_discriminant_form_audit,
    e7_quadratic_defect_admits,
    e7_quadratic_defect_mod_four,
    is_nonzero_triad,
    rossby_exact_resonance,
    rossby_frequency,
    transform_triad,
)


def test_barotropic_support_rejects_collinear_and_equal_radius_sources():
    assert not barotropic_channel_is_active(((2, 0), (-1, 0), (-1, 0)))
    assert not barotropic_channel_is_active(((-1, -1), (1, 0), (0, 1)))
    assert barotropic_channel_is_active(((-2, -1), (2, 0), (0, 1)))


def test_rossby_frequency_and_exact_resonance_use_exact_arithmetic():
    assert rossby_frequency((2, 1), beta=5) == Fraction(-2, 1)
    assert rossby_exact_resonance(((-4, -2), (0, 4), (4, -2)))
    with pytest.raises(ValueError, match="zero mode"):
        rossby_frequency((0, 0))


def test_e7_quadratic_defect_rejects_two_odd_labels():
    all_even = ((2, 0), (0, 2), (-2, -2))
    two_odd = ((1, 0), (0, 1), (-1, -1))
    assert e7_quadratic_defect_mod_four(all_even) == 0
    assert e7_quadratic_defect_admits(all_even)
    assert e7_quadratic_defect_mod_four(two_odd) == 2
    assert not e7_quadratic_defect_admits(two_odd)


def test_e7_discriminant_form_is_derived_from_repository_cartan_matrix():
    repository_cartan = E7RootSystem().compute_cartan_matrix()
    assert tuple(tuple(round(value) for value in row) for row in repository_cartan) == (
        E7_CARTAN_MATRIX
    )
    audit = e7_discriminant_form_audit()
    assert audit["cartan_determinant"] == 2
    assert audit["generator_norm_squared"] == "3/2"
    assert audit["half_normalized_quadratic_value_mod_one"] == "3/4"
    assert audit["generator_is_outside_root_lattice"] is True
    assert audit["doubled_generator_is_in_root_lattice"] is True
    assert audit["quadratic_form_is_nonadditive"] is True


@pytest.mark.parametrize("radius", [1, 2, 4, 8])
def test_quadratic_defect_is_exactly_the_generic_checkerboard_kernel(radius):
    triads = tuple(triad for triad in enumerate_exact_triads(radius) if is_nonzero_triad(triad))
    assert all(
        e7_quadratic_defect_admits(triad) == checkerboard_kernel_admits(triad)
        for triad in triads
    )


@pytest.mark.parametrize(
    "transform",
    [
        "identity",
        "rotate_90",
        "rotate_180",
        "rotate_270",
        "reflect_x",
        "reflect_y",
        "reflect_diagonal",
        "reflect_antidiagonal",
    ],
)
def test_e7_selector_is_square_symmetry_invariant(transform):
    triads = tuple(triad for triad in enumerate_exact_triads(3) if is_nonzero_triad(triad))
    assert all(
        e7_quadratic_defect_admits(transform_triad(triad, transform))
        == e7_quadratic_defect_admits(triad)
        for triad in triads
    )


def test_radius_four_selector_audit_matches_exact_counts():
    audit = build_triad_selector_audit(radius=4)
    assert audit["ordered_exact_triad_count_including_zero_modes"] == 3721
    assert audit["ordered_nonzero_exact_triad_count"] == 3480
    assert audit["barotropic_active_channel_count"] == 3120
    assert audit["barotropic_zero_support_channel_count"] == 360
    assert audit["rossby_exact_resonant_triad_count"] == 132
    assert audit["rossby_active_exact_resonant_channel_count"] == 64
    assert audit["e7_quadratic_defect_admitted_triad_count"] == 828
    assert audit["e7_quadratic_defect_rejected_triad_count"] == 2652
    assert audit["e7_quadratic_defect_active_admitted_count"] == 656
    assert audit["e7_quadratic_defect_active_rejected_count"] == 2464
    assert audit["e7_square_symmetry_pass"] is True
    assert audit["e7_permutation_closure_pass"] is True
    assert audit["e7_selector_nontrivial"] is True
    assert audit["checkerboard_kernel_exact_equivalence_pass"] is True
    assert audit["e7_specificity_falsified"] is True
    assert audit["scientific_outcome"] == (
        "e7_specificity_falsified_generic_parity_kernel_retained"
    )


def test_unknown_triad_transform_is_rejected():
    with pytest.raises(ValueError, match="unknown triad transform"):
        transform_triad(((1, 0), (0, 1), (-1, -1)), "not_a_symmetry")
