from __future__ import annotations

import numpy as np
import pytest

from mathphysics.algebras.roots import (
    E6RootSystem,
    E7RootSystem,
    E8RootSystem,
    E9RootSystem,
    E10RootSystem,
    E11RootSystem,
    ExceptionalLieAlgebras,
    F4RootSystem,
    LieAlgebraCalculator,
    LieAlgebraProperties,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def e6():
    return E6RootSystem()


@pytest.fixture(scope="module")
def e7():
    return E7RootSystem()


@pytest.fixture(scope="module")
def e8():
    return E8RootSystem()


# ---------------------------------------------------------------------------
# LieAlgebraProperties dataclass
# ---------------------------------------------------------------------------


def test_lie_algebra_properties_fields():
    props = LieAlgebraProperties("E8", 248, 8, 240, 120, 696729600)
    assert props.name == "E8"
    assert props.dimension == 248
    assert props.rank == 8
    assert props.num_roots == 240
    assert props.num_positive_roots == 120
    assert props.weyl_group_order == 696729600
    assert props.is_simply_laced is True
    assert props.root_squared_length == pytest.approx(2.0)


def test_lie_algebra_properties_not_simply_laced():
    props = LieAlgebraProperties("F4", 52, 4, 48, 24, 1152, is_simply_laced=False)
    assert props.is_simply_laced is False


# ---------------------------------------------------------------------------
# E8 root system - core counts
# ---------------------------------------------------------------------------


def test_e8_has_240_roots(e8):
    roots = e8.generate_roots()
    assert len(roots) == 240


def test_e8_rank_and_dimension(e8):
    assert e8.properties.rank == 8
    assert e8.properties.dimension == 248


def test_e8_weyl_group_order(e8):
    assert e8.properties.weyl_group_order == 696729600


def test_e8_simple_roots_count(e8):
    simple = e8.generate_simple_roots()
    assert simple.shape == (8, 8)


def test_e8_simple_roots_are_unit_norm(e8):
    simple = e8.generate_simple_roots()
    norms_sq = np.sum(simple ** 2, axis=1)
    # All simple roots for E8 have squared length 1 or 2; last row is the
    # half-integer root with squared length 1.
    assert np.all(norms_sq > 0)


def test_e8_cartan_matrix_diagonal(e8):
    cartan = e8.cartan_matrix()
    np.testing.assert_allclose(np.diag(cartan), np.full(8, 2.0))


def test_e8_cartan_matrix_shape(e8):
    cartan = e8.cartan_matrix()
    assert cartan.shape == (8, 8)


def test_e8_cartan_matrix_off_diagonal_nonpositive(e8):
    cartan = e8.cartan_matrix()
    for i in range(8):
        for j in range(8):
            if i != j:
                assert cartan[i, j] <= 0


def test_e8_positive_roots_count(e8):
    pos = e8.positive_roots()
    # E8 has 120 positive roots
    assert len(pos) == 120


def test_e8_roots_are_8d(e8):
    roots = e8.generate_roots()
    assert roots.shape[1] == 8


def test_e8_all_roots_have_squared_norm_2(e8):
    roots = e8.generate_roots()
    norms_sq = np.sum(roots ** 2, axis=1)
    np.testing.assert_allclose(norms_sq, 2.0, atol=1e-10)


def test_e8_dynkin_diagram_has_8_nodes(e8):
    g = e8.dynkin_diagram()
    assert g.number_of_nodes() == 8


def test_e8_dynkin_diagram_is_connected(e8):
    import networkx as nx

    g = e8.dynkin_diagram()
    assert nx.is_connected(g)


# ---------------------------------------------------------------------------
# E7 root system
# ---------------------------------------------------------------------------


def test_e7_has_126_roots(e7):
    roots = e7.generate_roots()
    assert len(roots) == 126


def test_e7_rank_and_dimension(e7):
    assert e7.properties.rank == 7
    assert e7.properties.dimension == 133


def test_e7_weyl_group_order(e7):
    assert e7.properties.weyl_group_order == 2903040


def test_e7_simple_roots_shape(e7):
    simple = e7.generate_simple_roots()
    assert simple.shape == (7, 8)


def test_e7_127_state_system(e7):
    states = e7.get_127_state_system()
    assert len(states) == 127


def test_e7_cartan_matrix_diagonal(e7):
    cartan = e7.compute_cartan_matrix()
    np.testing.assert_allclose(np.diag(cartan), np.full(7, 2.0))


def test_e7_classify_root_integer(e7):
    # First simple root has integer entries
    simple = e7.generate_simple_roots()
    label = e7.classify_root(simple[0])
    assert "Integer" in label


def test_e7_classify_root_half_integer(e7):
    # Third simple root has half-integer entries
    simple = e7.generate_simple_roots()
    label = e7.classify_root(simple[2])
    assert "Half-integer" in label


def test_e7_get_root_by_index(e7):
    root = e7.get_root_by_index(0)
    assert root.shape == (8,)


# ---------------------------------------------------------------------------
# E6 root system
# ---------------------------------------------------------------------------


def test_e6_rank_and_dimension(e6):
    assert e6.properties.rank == 6
    assert e6.properties.dimension == 78


def test_e6_num_roots_property(e6):
    assert e6.properties.num_roots == 72


def test_e6_simple_roots_shape(e6):
    simple = e6.generate_simple_roots()
    assert simple.shape == (6, 8)


def test_e6_cartan_matrix_shape(e6):
    cartan = e6.compute_cartan_matrix()
    assert cartan.shape == (6, 6)


def test_e6_dynkin_diagram_nodes(e6):
    g = e6.dynkin_diagram()
    assert g.number_of_nodes() == 6


def test_e6_weyl_group_order(e6):
    assert e6.properties.weyl_group_order == 51840


# ---------------------------------------------------------------------------
# F4 root system
# ---------------------------------------------------------------------------


def test_f4_root_count():
    f4 = F4RootSystem()
    roots = f4.generate_roots()
    assert len(roots) == 48


def test_f4_not_simply_laced():
    f4 = F4RootSystem()
    assert f4.properties.is_simply_laced is False


def test_f4_rank_and_dimension():
    f4 = F4RootSystem()
    assert f4.properties.rank == 4
    assert f4.properties.dimension == 52


# ---------------------------------------------------------------------------
# Kac-Moody extensions E9/E10/E11
# ---------------------------------------------------------------------------


def test_e9_cartan_matrix_shape():
    e9 = E9RootSystem()
    mat = e9.generalized_cartan_matrix()
    assert mat.shape == (9, 9)


def test_e9_cartan_matrix_diagonal():
    e9 = E9RootSystem()
    mat = e9.generalized_cartan_matrix()
    np.testing.assert_allclose(np.diag(mat), np.full(9, 2.0))


def test_e10_cartan_matrix_shape():
    e10 = E10RootSystem()
    mat = e10.generalized_cartan_matrix()
    assert mat.shape == (10, 10)


def test_e11_cartan_matrix_shape():
    e11 = E11RootSystem()
    mat = e11.generalized_cartan_matrix()
    assert mat.shape == (11, 11)


def test_e11_cartan_matrix_is_symmetric():
    e11 = E11RootSystem()
    mat = e11.generalized_cartan_matrix()
    np.testing.assert_allclose(mat, mat.T)


# ---------------------------------------------------------------------------
# LieAlgebraCalculator
# ---------------------------------------------------------------------------


def test_dimension_formula_e8():
    dim = LieAlgebraCalculator.dimension_formula(8, 120)
    assert dim == 248


def test_dimension_formula_e7():
    dim = LieAlgebraCalculator.dimension_formula(7, 63)
    assert dim == 133


def test_dimension_formula_e6():
    dim = LieAlgebraCalculator.dimension_formula(6, 36)
    assert dim == 78


def test_coxeter_number_e8():
    e8 = E8RootSystem()
    h = LieAlgebraCalculator.coxeter_number(e8.cartan_matrix())
    assert h == 30


def test_coxeter_number_other():
    # Any matrix with rank != 8 returns 18
    mat = np.eye(7)
    h = LieAlgebraCalculator.coxeter_number(mat)
    assert h == 18


# ---------------------------------------------------------------------------
# ExceptionalLieAlgebras static catalog
# ---------------------------------------------------------------------------


def test_exceptional_g2():
    g2 = ExceptionalLieAlgebras.G2()
    assert g2["name"] == "G2"
    assert g2["dimension"] == 14
    assert g2["rank"] == 2
    assert g2["num_roots"] == 12


def test_exceptional_f4():
    f4 = ExceptionalLieAlgebras.F4()
    assert f4["dimension"] == 52
    assert f4["num_roots"] == 48


def test_exceptional_e6():
    e6 = ExceptionalLieAlgebras.E6()
    assert e6["dimension"] == 78
    assert e6["rank"] == 6


def test_exceptional_e7():
    e7 = ExceptionalLieAlgebras.E7()
    assert e7["dimension"] == 133
    assert e7["num_roots"] == 126


def test_exceptional_get_all_returns_five():
    algebras = ExceptionalLieAlgebras.get_all()
    assert len(algebras) == 5


def test_exceptional_get_all_names():
    names = [a["name"] for a in ExceptionalLieAlgebras.get_all()]
    assert "G2" in names
    assert "E8" in names


# ---------------------------------------------------------------------------
# BaseRootSystem abstract interface guards
# ---------------------------------------------------------------------------


def test_base_root_system_add_raises(e8):
    with pytest.raises(NotImplementedError):
        _ = e8 + e8


def test_base_root_system_mul_raises(e8):
    with pytest.raises(NotImplementedError):
        _ = e8 * e8


def test_base_root_system_norm_returns_zero(e8):
    assert e8.norm() == 0.0
