from __future__ import annotations

import numpy as np
import pytest

from mathphysics.projective_geometry import (
    FanoPlane,
    GF2Vector,
    PGConfig,
    ProjectiveLine,
    ProjectivePoint,
    ProjectiveSpace,
)


# ---------------------------------------------------------------------------
# GF2Vector
# ---------------------------------------------------------------------------


def test_gf2_vector_construction_list():
    v = GF2Vector([1, 0, 1])
    assert list(v.components) == [1, 0, 1]


def test_gf2_vector_reduces_mod2():
    v = GF2Vector([3, 2, 1])
    assert list(v.components) == [1, 0, 1]


def test_gf2_vector_addition_xor():
    a = GF2Vector([1, 0, 1])
    b = GF2Vector([1, 1, 0])
    c = a + b
    assert list(c.components) == [0, 1, 1]


def test_gf2_vector_scalar_mul_by_1():
    v = GF2Vector([1, 0, 1])
    assert list((v * 1).components) == [1, 0, 1]


def test_gf2_vector_scalar_mul_by_0():
    v = GF2Vector([1, 0, 1])
    assert list((v * 0).components) == [0, 0, 0]


def test_gf2_vector_dot_product():
    a = GF2Vector([1, 1, 0])
    b = GF2Vector([1, 0, 1])
    assert a.dot(b) == 1  # 1*1 + 1*0 + 0*1 = 1 mod 2


def test_gf2_vector_is_zero_true():
    v = GF2Vector([0, 0, 0])
    assert v.is_zero()


def test_gf2_vector_is_zero_false():
    v = GF2Vector([0, 1, 0])
    assert not v.is_zero()


def test_gf2_vector_to_tuple():
    v = GF2Vector([1, 0, 1])
    assert v.to_tuple() == (1, 0, 1)


def test_gf2_vector_hash_consistent():
    v1 = GF2Vector([1, 0, 1])
    v2 = GF2Vector([1, 0, 1])
    assert hash(v1) == hash(v2)


def test_gf2_vector_equality():
    v1 = GF2Vector([1, 0, 1])
    v2 = GF2Vector([1, 0, 1])
    assert v1 == v2


def test_gf2_vector_from_integer():
    # integer 5 = 101 in binary
    v = GF2Vector(5)
    assert list(v.components) == [1, 0, 1]


# ---------------------------------------------------------------------------
# ProjectivePoint
# ---------------------------------------------------------------------------


def test_projective_point_construction():
    v = GF2Vector([1, 0, 0])
    p = ProjectivePoint(v)
    assert np.array_equal(p.coordinates(), [1, 0, 0])


def test_projective_point_raises_on_zero_vector():
    v = GF2Vector([0, 0, 0])
    with pytest.raises(ValueError, match="zero vector"):
        ProjectivePoint(v)


def test_projective_point_equality():
    p1 = ProjectivePoint(GF2Vector([1, 0, 1]))
    p2 = ProjectivePoint(GF2Vector([1, 0, 1]))
    assert p1 == p2


def test_projective_point_inequality():
    p1 = ProjectivePoint(GF2Vector([1, 0, 1]))
    p2 = ProjectivePoint(GF2Vector([0, 1, 1]))
    assert p1 != p2


def test_projective_point_hash_consistent():
    p1 = ProjectivePoint(GF2Vector([1, 1, 0]))
    p2 = ProjectivePoint(GF2Vector([1, 1, 0]))
    assert hash(p1) == hash(p2)


def test_projective_point_repr():
    p = ProjectivePoint(GF2Vector([1, 0, 0]))
    r = repr(p)
    assert "P" in r


# ---------------------------------------------------------------------------
# ProjectiveLine
# ---------------------------------------------------------------------------


def test_projective_line_requires_distinct_points():
    p = ProjectivePoint(GF2Vector([1, 0, 0]))
    with pytest.raises(ValueError):
        ProjectiveLine(p, p)


def test_projective_line_get_all_points_has_three():
    p1 = ProjectivePoint(GF2Vector([1, 0, 0]))
    p2 = ProjectivePoint(GF2Vector([0, 1, 0]))
    line = ProjectiveLine(p1, p2)
    pts = line.get_all_points()
    assert len(pts) == 3


def test_projective_line_contains_defining_points():
    p1 = ProjectivePoint(GF2Vector([1, 0, 0]))
    p2 = ProjectivePoint(GF2Vector([0, 1, 0]))
    line = ProjectiveLine(p1, p2)
    assert line.contains(p1)
    assert line.contains(p2)


def test_projective_line_contains_sum_point():
    p1 = ProjectivePoint(GF2Vector([1, 0, 0]))
    p2 = ProjectivePoint(GF2Vector([0, 1, 0]))
    p3 = ProjectivePoint(GF2Vector([1, 1, 0]))  # p1 + p2
    line = ProjectiveLine(p1, p2)
    assert line.contains(p3)


def test_projective_line_does_not_contain_unrelated_point():
    p1 = ProjectivePoint(GF2Vector([1, 0, 0]))
    p2 = ProjectivePoint(GF2Vector([0, 1, 0]))
    p_other = ProjectivePoint(GF2Vector([0, 0, 1]))
    line = ProjectiveLine(p1, p2)
    assert not line.contains(p_other)


def test_projective_line_all_points_cached():
    p1 = ProjectivePoint(GF2Vector([1, 0, 0]))
    p2 = ProjectivePoint(GF2Vector([0, 1, 0]))
    line = ProjectiveLine(p1, p2)
    pts1 = line.get_all_points()
    pts2 = line.get_all_points()
    assert pts1 is pts2


def test_projective_line_equality():
    p1 = ProjectivePoint(GF2Vector([1, 0, 0]))
    p2 = ProjectivePoint(GF2Vector([0, 1, 0]))
    l1 = ProjectiveLine(p1, p2)
    l2 = ProjectiveLine(p2, p1)
    assert l1 == l2


# ---------------------------------------------------------------------------
# ProjectiveSpace PG(2, 2) - the Fano plane as a projective space
# ---------------------------------------------------------------------------


def test_pg22_num_points():
    pg = ProjectiveSpace(dimension=2)
    # 2^3 - 1 = 7
    assert pg.num_points() == 7


def test_pg22_generate_points_count():
    pg = ProjectiveSpace(dimension=2)
    pts = pg.generate_points()
    assert len(pts) == 7


def test_pg22_num_lines():
    pg = ProjectiveSpace(dimension=2)
    # (2^3 - 1)(2^2 - 1) / 3 = 7 * 3 / 3 = 7
    assert pg.num_lines() == 7


def test_pg22_generate_lines_count():
    pg = ProjectiveSpace(dimension=2)
    lines = pg.generate_lines()
    assert len(lines) == 7


def test_pg22_incidence_matrix_shape():
    pg = ProjectiveSpace(dimension=2)
    mat = pg.incidence_matrix()
    assert mat.shape == (7, 7)


def test_pg22_incidence_matrix_binary():
    pg = ProjectiveSpace(dimension=2)
    mat = pg.incidence_matrix()
    assert set(np.unique(mat)).issubset({0, 1})


def test_pg22_each_line_has_3_points_in_incidence():
    pg = ProjectiveSpace(dimension=2)
    mat = pg.incidence_matrix()
    col_sums = np.sum(mat, axis=0)
    np.testing.assert_array_equal(col_sums, np.full(7, 3))


def test_pg22_properties_dict():
    pg = ProjectiveSpace(dimension=2)
    props = pg.properties()
    assert props["num_points"] == 7
    assert props["num_lines"] == 7
    assert props["points_per_line"] == 3
    assert props["field"] == "GF(2)"


# ---------------------------------------------------------------------------
# FanoPlane
# ---------------------------------------------------------------------------


def test_fano_plane_has_7_points():
    fano = FanoPlane()
    assert len(fano.points) == 7


def test_fano_plane_has_7_lines():
    fano = FanoPlane()
    assert len(fano.lines) == 7


def test_fano_plane_each_line_has_3_points():
    fano = FanoPlane()
    for line in fano.lines:
        assert len(line) == 3


def test_fano_plane_verify_incidence_axioms():
    fano = FanoPlane()
    assert fano.verify_incidence_axioms() is True


def test_fano_plane_automorphism_group_order():
    fano = FanoPlane()
    # |GL(3,2)| = |PSL(3,2)| = 168
    assert fano.automorphism_group_order() == 168


def test_fano_plane_is_self_dual():
    fano = FanoPlane()
    dual = fano.dual_plane()
    assert dual is fano


def test_fano_plane_every_point_on_three_lines():
    fano = FanoPlane()
    from collections import Counter

    point_count = Counter()
    for line in fano.lines:
        for p in line:
            point_count[p] += 1
    for p in range(7):
        assert point_count[p] == 3


def test_fano_plane_any_two_points_on_exactly_one_line():
    fano = FanoPlane()
    from collections import defaultdict

    membership = defaultdict(set)
    for i, line in enumerate(fano.lines):
        for p in line:
            membership[p].add(i)
    for i in range(7):
        for j in range(i + 1, 7):
            common = membership[i] & membership[j]
            assert len(common) == 1


# ---------------------------------------------------------------------------
# PGConfig validation
# ---------------------------------------------------------------------------


def test_pg_config_valid():
    cfg = PGConfig(dimension=6, field_characteristic=2)
    cfg.validate()  # should not raise


def test_pg_config_invalid_dimension():
    cfg = PGConfig(dimension=0)
    with pytest.raises(ValueError, match="positive"):
        cfg.validate()


def test_pg_config_invalid_field():
    cfg = PGConfig(field_characteristic=3)
    with pytest.raises(ValueError, match="GF.2."):
        cfg.validate()


# ---------------------------------------------------------------------------
# PG(6,2) point count
# ---------------------------------------------------------------------------


def test_pg62_num_points():
    pg = ProjectiveSpace(dimension=6)
    assert pg.num_points() == 127


def test_pg62_num_lines_formula():
    pg = ProjectiveSpace(dimension=6)
    expected = (2 ** 7 - 1) * (2 ** 6 - 1) // 3
    assert pg.num_lines() == expected
