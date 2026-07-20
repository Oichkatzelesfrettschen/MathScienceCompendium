"""Algebraic and boundary tests for the Clifford multivector implementation."""

from __future__ import annotations

import numpy as np
import pytest

from mathphysics.algebras.clifford import Multivector


def basis_vector(index: int) -> Multivector:
    coefficients = np.zeros(4)
    coefficients[1 << index] = 1.0
    return Multivector(coefficients, (2, 0, 0))


def test_vector_wedge_itself_is_zero():
    vector = basis_vector(0)
    np.testing.assert_allclose(vector.wedge(vector).coeffs, 0.0)


def test_vector_wedge_is_antisymmetric():
    first = basis_vector(0)
    second = basis_vector(1)
    np.testing.assert_allclose(first.wedge(second).coeffs, -second.wedge(first).coeffs)


def test_constructor_rejects_wrong_coefficient_count():
    with pytest.raises(ValueError, match="coefficients must have shape"):
        Multivector(np.zeros(3), (2, 0, 0))


def test_binary_operations_reject_mixed_signatures():
    euclidean = Multivector(np.zeros(4), (2, 0, 0))
    lorentzian = Multivector(np.zeros(4), (1, 1, 0))
    with pytest.raises(ValueError, match="signatures differ"):
        euclidean.geometric_product(lorentzian)
    with pytest.raises(ValueError, match="signatures differ"):
        euclidean.wedge(lorentzian)
    with pytest.raises(ValueError, match="signatures differ"):
        _ = euclidean + lorentzian
