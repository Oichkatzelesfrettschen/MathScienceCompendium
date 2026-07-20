from __future__ import annotations

import numpy as np
import pytest


# loop_algebras imports JAX at the module level; skip the whole file if JAX is absent.
jnp = pytest.importorskip("jax.numpy", reason="JAX is required for loop_algebras")

from mathphysics.algebras.loop_algebras import (  # noqa: E402
    AffineLieAlgebra,
    SL2Affine,
    SL3Affine,
)
from mathphysics.algebras.roots import E6RootSystem, E7RootSystem, E8RootSystem  # noqa: E402


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def sl2():
    return SL2Affine(level=1.0)


@pytest.fixture(scope="module")
def sl3():
    return SL3Affine(level=2.0)


@pytest.fixture(scope="module")
def affine_e8():
    return AffineLieAlgebra(E8RootSystem(), level=1.0)


@pytest.fixture(scope="module")
def affine_e7():
    return AffineLieAlgebra(E7RootSystem(), level=1.0)


@pytest.fixture(scope="module")
def affine_e6():
    return AffineLieAlgebra(E6RootSystem(), level=1.0)


# ---------------------------------------------------------------------------
# SL2Affine construction
# ---------------------------------------------------------------------------


def test_sl2_default_level():
    sl2 = SL2Affine()
    assert sl2.level == pytest.approx(1.0)


def test_sl2_custom_level():
    sl2 = SL2Affine(level=3.0)
    assert sl2.level == pytest.approx(3.0)


def test_sl2_rank_is_two():
    # affine rank = finite rank + 1 = 1 + 1 = 2
    sl2 = SL2Affine()
    assert sl2.rank == 2


def test_sl2_finite_g_name():
    sl2 = SL2Affine()
    assert sl2.finite_g.properties.name == "A1"


def test_sl2_dimension_is_infinite():
    sl2 = SL2Affine()
    assert sl2._dimension == float("inf")


# ---------------------------------------------------------------------------
# SL3Affine construction
# ---------------------------------------------------------------------------


def test_sl3_level(sl3):
    assert sl3.level == pytest.approx(2.0)


def test_sl3_rank(sl3):
    # affine rank = 2 + 1 = 3
    assert sl3.rank == 3


def test_sl3_finite_g_name(sl3):
    assert sl3.finite_g.properties.name == "A2"


# ---------------------------------------------------------------------------
# AffineLieAlgebra.get_generalized_cartan_matrix - SL2
# ---------------------------------------------------------------------------


def test_sl2_affine_cartan_matrix_shape(sl2):
    mat = sl2.get_generalized_cartan_matrix()
    assert mat.shape == (2, 2)


def test_sl2_affine_cartan_matrix_diagonal(sl2):
    mat = np.array(sl2.get_generalized_cartan_matrix())
    np.testing.assert_allclose(np.diag(mat), [2.0, 2.0])


def test_sl2_affine_cartan_matrix_off_diagonal(sl2):
    # A1^(1) case: off-diagonal entries should be -2
    mat = np.array(sl2.get_generalized_cartan_matrix())
    assert mat[0, 1] == pytest.approx(-2.0)
    assert mat[1, 0] == pytest.approx(-2.0)


# ---------------------------------------------------------------------------
# AffineLieAlgebra.get_generalized_cartan_matrix - SL3
# ---------------------------------------------------------------------------


def test_sl3_affine_cartan_matrix_shape(sl3):
    mat = sl3.get_generalized_cartan_matrix()
    assert mat.shape == (3, 3)


def test_sl3_affine_cartan_matrix_diagonal(sl3):
    mat = np.array(sl3.get_generalized_cartan_matrix())
    np.testing.assert_allclose(np.diag(mat), [2.0, 2.0, 2.0])


def test_sl3_affine_cartan_matrix_off_diag_first_last(sl3):
    mat = np.array(sl3.get_generalized_cartan_matrix())
    # A2^(1): extended node connects to first and last
    assert mat[0, 1] == pytest.approx(-1.0)
    assert mat[1, 0] == pytest.approx(-1.0)
    assert mat[0, 2] == pytest.approx(-1.0)
    assert mat[2, 0] == pytest.approx(-1.0)


# ---------------------------------------------------------------------------
# AffineLieAlgebra over E8
# ---------------------------------------------------------------------------


def test_affine_e8_rank(affine_e8):
    # affine rank = 8 + 1 = 9
    assert affine_e8.rank == 9


def test_affine_e8_cartan_matrix_shape(affine_e8):
    mat = affine_e8.get_generalized_cartan_matrix()
    assert mat.shape == (9, 9)


def test_affine_e8_cartan_matrix_diagonal(affine_e8):
    mat = np.array(affine_e8.get_generalized_cartan_matrix())
    np.testing.assert_allclose(np.diag(mat), np.full(9, 2.0))


def test_affine_e8_level(affine_e8):
    assert affine_e8.level == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# AffineLieAlgebra over E7
# ---------------------------------------------------------------------------


def test_affine_e7_rank(affine_e7):
    assert affine_e7.rank == 8


def test_affine_e7_cartan_matrix_shape(affine_e7):
    mat = affine_e7.get_generalized_cartan_matrix()
    assert mat.shape == (8, 8)


# ---------------------------------------------------------------------------
# Interface guards
# ---------------------------------------------------------------------------


def test_affine_lie_algebra_add_raises(affine_e8):
    with pytest.raises(NotImplementedError):
        _ = affine_e8 + affine_e8


def test_affine_lie_algebra_mul_raises(affine_e8):
    with pytest.raises(NotImplementedError):
        _ = affine_e8 * affine_e8


def test_affine_lie_algebra_norm_is_zero(affine_e8):
    assert affine_e8.norm() == 0.0


def test_affine_lie_algebra_bracket_raises(affine_e8):
    with pytest.raises(NotImplementedError):
        affine_e8.bracket(affine_e8)
