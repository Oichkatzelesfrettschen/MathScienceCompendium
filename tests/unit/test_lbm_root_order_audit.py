"""Tests for the LBM root-order sensitivity audit."""

import numpy as np
from scripts.audit_lbm_root_order import build_audit, compare_orders, density_scaffold


def test_identical_root_orders_produce_identical_density():
    roots = np.array([[1.0, 0.0], [0.0, 1.0], [-1.0, 0.0]])
    result = compare_orders(roots, roots.copy(), (16, 16), 3, 0.01)
    assert result["relative_perturbation_l2_difference"] == 0.0
    assert result["maximum_absolute_density_difference"] == 0.0


def test_reversing_root_order_changes_index_weighted_density():
    roots = np.array([[1.0, 0.0], [0.0, 1.0], [2.0, 1.0]])
    result = compare_orders(roots, roots[::-1], (16, 16), 3, 0.01)
    assert result["relative_perturbation_l2_difference"] > 0.0
    assert result["maximum_absolute_density_difference"] > 0.0


def test_density_scaffold_has_requested_shape():
    roots = np.array([[1.0, 1.0]])
    density = density_scaffold(roots, (7, 9), 1, 0.01)
    assert density.shape == (7, 9)


def test_audit_distinguishes_requested_and_effective_harmonic_counts():
    audit = build_audit((8, 8), harmonic_count=127, harmonic_amplitude=0.01)

    assert audit["root_count"] == 126
    assert audit["requested_harmonic_count"] == 127
    assert audit["effective_harmonic_count"] == 126
