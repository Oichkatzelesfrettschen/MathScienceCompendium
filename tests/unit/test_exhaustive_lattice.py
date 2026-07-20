"""Exhaustive tests for lattice_theory.py.

Covers:
- E8Lattice dimension, kissing number, packing density
- E8Lattice basis_vectors shape and first entry
- E8Lattice minimal_vectors shape and norm
- E8Lattice theta_series length, first coefficient, and formula correctness
- LeechLattice dimension and kissing number
- SpherePackingAnalyzer center_density keys
- SpherePackingAnalyzer kissing_number_bounds for known and unknown dims
- analyze_lattice_properties return keys and values
- analyze_lattice_properties with output_dir (tmp_path)
"""

from __future__ import annotations

import json

import numpy as np

from mathphysics.lattice_theory import (
    E8Lattice,
    LeechLattice,
    SpherePackingAnalyzer,
    analyze_lattice_properties,
)


# ---------------------------------------------------------------------------
# E8Lattice
# ---------------------------------------------------------------------------


def test_e8_lattice_dimension():
    e8 = E8Lattice()
    assert e8.dimension == 8


def test_e8_lattice_kissing_number():
    e8 = E8Lattice()
    assert e8.kissing_number() == 240


def test_e8_lattice_packing_density_value():
    e8 = E8Lattice()
    expected = (np.pi**4) / 384.0
    assert abs(e8.packing_density() - expected) < 1e-12


def test_e8_lattice_packing_density_positive():
    e8 = E8Lattice()
    assert e8.packing_density() > 0.0


def test_e8_lattice_basis_vectors_shape():
    e8 = E8Lattice()
    basis = e8.basis_vectors()
    assert basis.shape == (8, 8)


def test_e8_lattice_basis_first_diagonal_entry():
    e8 = E8Lattice()
    basis = e8.basis_vectors()
    # basis[0,0] is set to 2.0 in the simplified implementation
    assert basis[0, 0] == 2.0


def test_e8_lattice_minimal_vectors_count():
    e8 = E8Lattice()
    roots = e8.minimal_vectors()
    assert len(roots) == 240


def test_e8_lattice_minimal_vectors_shape():
    e8 = E8Lattice()
    roots = e8.minimal_vectors()
    assert roots.shape == (240, 8)


def test_e8_lattice_minimal_vectors_norm():
    # All E8 minimal vectors have squared norm 2
    e8 = E8Lattice()
    roots = e8.minimal_vectors()
    norms_sq = np.sum(roots**2, axis=1)
    np.testing.assert_allclose(norms_sq, np.full(240, 2.0), atol=1e-10)


def test_e8_lattice_minimal_vectors_are_finite():
    e8 = E8Lattice()
    roots = e8.minimal_vectors()
    assert np.all(np.isfinite(roots))


def test_e8_lattice_theta_series_length():
    e8 = E8Lattice()
    coeffs = e8.theta_series(max_n=5)
    # Should have max_n + 1 = 6 entries
    assert len(coeffs) == 6


def test_e8_theta_series_first_coefficient():
    e8 = E8Lattice()
    coeffs = e8.theta_series(max_n=3)
    # coeffs[0] = 1 (the constant term)
    assert coeffs[0] == 1


def test_e8_theta_series_n1_coefficient():
    e8 = E8Lattice()
    coeffs = e8.theta_series(max_n=3)
    # a_1 = 240 * sigma_3(1) = 240 * 1 = 240
    assert coeffs[1] == 240


def test_e8_theta_series_n2_coefficient():
    e8 = E8Lattice()
    coeffs = e8.theta_series(max_n=3)
    # a_2 = 240 * sigma_3(2) = 240 * (1^3 + 2^3) = 240 * 9 = 2160
    assert coeffs[2] == 2160


def test_e8_theta_series_n3_coefficient():
    e8 = E8Lattice()
    coeffs = e8.theta_series(max_n=3)
    # a_3 = 240 * sigma_3(3) = 240 * (1 + 27) = 240 * 28 = 6720
    assert coeffs[3] == 6720


def test_e8_theta_series_all_positive():
    e8 = E8Lattice()
    coeffs = e8.theta_series(max_n=5)
    assert np.all(coeffs >= 0)


# ---------------------------------------------------------------------------
# LeechLattice
# ---------------------------------------------------------------------------


def test_leech_lattice_dimension():
    leech = LeechLattice()
    assert leech.dimension == 24


def test_leech_lattice_kissing_number():
    leech = LeechLattice()
    assert leech.kissing_number() == 196560


# ---------------------------------------------------------------------------
# SpherePackingAnalyzer
# ---------------------------------------------------------------------------


def test_sphere_packing_center_density_has_upper_lower():
    analyzer = SpherePackingAnalyzer()
    result = analyzer.center_density(8)
    assert "upper" in result
    assert "lower" in result


def test_sphere_packing_center_density_bounds_ordering():
    analyzer = SpherePackingAnalyzer()
    result = analyzer.center_density(8)
    assert result["lower"] <= result["upper"]


def test_sphere_packing_kissing_bounds_dim8_exact():
    analyzer = SpherePackingAnalyzer()
    lo, hi = analyzer.kissing_number_bounds(8)
    assert lo == 240
    assert hi == 240


def test_sphere_packing_kissing_bounds_dim24_exact():
    analyzer = SpherePackingAnalyzer()
    lo, hi = analyzer.kissing_number_bounds(24)
    assert lo == 196560
    assert hi == 196560


def test_sphere_packing_kissing_bounds_unknown_dim():
    analyzer = SpherePackingAnalyzer()
    lo, hi = analyzer.kissing_number_bounds(10)
    assert lo >= 1
    assert hi >= lo


def test_sphere_packing_center_density_static_method():
    # Also callable as a static method
    result = SpherePackingAnalyzer.center_density(8)
    assert "upper" in result


# ---------------------------------------------------------------------------
# analyze_lattice_properties
# ---------------------------------------------------------------------------


def test_analyze_lattice_returns_required_keys():
    results = analyze_lattice_properties()
    assert "dimension" in results
    assert "kissing_number" in results
    assert "density" in results
    assert "num_minimal_vectors" in results


def test_analyze_lattice_dimension_is_8():
    results = analyze_lattice_properties()
    assert results["dimension"] == 8


def test_analyze_lattice_kissing_number_is_240():
    results = analyze_lattice_properties()
    assert results["kissing_number"] == 240


def test_analyze_lattice_num_minimal_vectors():
    results = analyze_lattice_properties()
    assert results["num_minimal_vectors"] == 240


def test_analyze_lattice_density_positive():
    results = analyze_lattice_properties()
    assert results["density"] > 0.0


def test_analyze_lattice_with_output_dir_writes_json(tmp_path):
    analyze_lattice_properties(output_dir=tmp_path)
    outfile = tmp_path / "lattice_analysis.json"
    assert outfile.exists()
    with outfile.open() as f:
        data = json.load(f)
    assert data["kissing_number"] == 240


def test_analyze_lattice_with_output_dir_returns_same(tmp_path):
    results = analyze_lattice_properties(output_dir=tmp_path)
    assert results["dimension"] == 8
