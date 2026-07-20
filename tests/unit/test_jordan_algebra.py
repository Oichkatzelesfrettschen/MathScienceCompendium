"""Tests for the non-placeholder Albert algebra product."""

from __future__ import annotations

import numpy as np
import pytest

from mathphysics.algebras.jordan import AlbertAlgebraElement


def hermitian_element(scale: float) -> AlbertAlgebraElement:
    data = np.zeros((3, 3, 8), dtype=np.float64)
    data[0, 0, 0] = 1.0 * scale
    data[1, 1, 0] = -2.0 * scale
    data[2, 2, 0] = 0.5 * scale
    data[0, 1, [1, 3]] = [0.25 * scale, -0.5 * scale]
    data[1, 0] = data[0, 1]
    data[1, 0, 1:] *= -1.0
    data[0, 2, [2, 5]] = [0.75 * scale, 0.125 * scale]
    data[2, 0] = data[0, 2]
    data[2, 0, 1:] *= -1.0
    data[1, 2, [4, 7]] = [-0.375 * scale, 0.625 * scale]
    data[2, 1] = data[1, 2]
    data[2, 1, 1:] *= -1.0
    return AlbertAlgebraElement(data)


def test_albert_identity_is_hermitian_and_unital():
    identity = AlbertAlgebraElement.identity()
    element = hermitian_element(1.0)
    assert identity.is_hermitian()
    assert element.is_hermitian()
    np.testing.assert_allclose(
        np.asarray(identity.jordan_product(element).data),
        np.asarray(element.data),
        rtol=1e-6,
        atol=1e-6,
    )


def test_jordan_product_is_commutative_and_nonzero():
    left = hermitian_element(1.0)
    right = hermitian_element(-0.4) + AlbertAlgebraElement.identity()
    left_right = np.asarray(left.jordan_product(right).data)
    right_left = np.asarray(right.jordan_product(left).data)
    np.testing.assert_allclose(left_right, right_left, rtol=1e-6, atol=1e-6)
    assert np.linalg.norm(left_right) > 0.0


def test_albert_product_satisfies_jordan_identity():
    left = hermitian_element(0.6)
    right = hermitian_element(-0.35) + AlbertAlgebraElement.identity()
    left_squared = left.jordan_product(left)
    first = left.jordan_product(right.jordan_product(left_squared))
    second = left.jordan_product(right).jordan_product(left_squared)
    np.testing.assert_allclose(
        np.asarray(first.data),
        np.asarray(second.data),
        rtol=2e-5,
        atol=2e-5,
    )


def test_albert_shape_is_enforced():
    try:
        AlbertAlgebraElement(np.zeros((3, 3, 7)))
    except ValueError as error:
        assert "shape" in str(error)
    else:
        raise AssertionError("invalid Albert shape was accepted")


def test_albert_hermitian_carrier_is_enforced():
    nonhermitian = np.zeros((3, 3, 8), dtype=np.float64)
    nonhermitian[0, 1, 1] = 1.0
    with pytest.raises(ValueError, match="Hermitian"):
        AlbertAlgebraElement(nonhermitian)
