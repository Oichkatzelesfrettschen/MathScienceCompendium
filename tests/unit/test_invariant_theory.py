from __future__ import annotations

import pytest

from mathphysics.invariant_theory import InvariantAnalyzer


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def analyzer():
    return InvariantAnalyzer()


# ---------------------------------------------------------------------------
# verify_e8_invariants
# ---------------------------------------------------------------------------


def test_verify_e8_invariants_returns_dict(analyzer):
    result = analyzer.verify_e8_invariants()
    assert isinstance(result, dict)


def test_verify_e8_invariants_has_degrees_key(analyzer):
    result = analyzer.verify_e8_invariants()
    assert "degrees" in result


def test_verify_e8_invariants_eight_degrees(analyzer):
    result = analyzer.verify_e8_invariants()
    assert len(result["degrees"]) == 8


def test_verify_e8_invariants_degree_values(analyzer):
    result = analyzer.verify_e8_invariants()
    expected = [2, 8, 12, 14, 18, 20, 24, 30]
    assert result["degrees"] == expected


def test_verify_e8_invariants_smallest_degree_is_2(analyzer):
    result = analyzer.verify_e8_invariants()
    assert result["degrees"][0] == 2


def test_verify_e8_invariants_largest_degree_is_30(analyzer):
    result = analyzer.verify_e8_invariants()
    assert result["degrees"][-1] == 30


def test_verify_e8_invariants_degrees_are_sorted(analyzer):
    result = analyzer.verify_e8_invariants()
    degrees = result["degrees"]
    assert degrees == sorted(degrees)


def test_verify_e8_invariants_degrees_are_even_or_have_pattern(analyzer):
    result = analyzer.verify_e8_invariants()
    # All known E8 invariant degrees: 2, 8, 12, 14, 18, 20, 24, 30
    for d in result["degrees"]:
        assert isinstance(d, int)
        assert d > 0


# ---------------------------------------------------------------------------
# compute_hilbert_series
# ---------------------------------------------------------------------------


def test_hilbert_series_at_zero_is_one():
    # H(0) = 1 / product(1 - 0^d) = 1 / 1^n = 1
    h = InvariantAnalyzer.compute_hilbert_series([2, 4, 6])
    assert abs(h(0) - 1.0) < 1e-12


def test_hilbert_series_e8_degrees_at_small_t():
    degrees = [2, 8, 12, 14, 18, 20, 24, 30]
    h = InvariantAnalyzer.compute_hilbert_series(degrees)
    t = 0.01
    val = h(t)
    # Should be finite and close to 1 for small t
    assert abs(val) < 1000
    assert abs(val - 1.0) < 1.0  # first-order correction is small


def test_hilbert_series_returns_callable():
    h = InvariantAnalyzer.compute_hilbert_series([2, 3])
    assert callable(h)


def test_hilbert_series_single_degree():
    # H(t) = 1 / (1 - t^2) for degrees=[2]
    h = InvariantAnalyzer.compute_hilbert_series([2])
    t = 0.5
    expected = 1.0 / (1.0 - t**2)
    assert abs(h(t) - expected) < 1e-12


def test_hilbert_series_two_degrees():
    h = InvariantAnalyzer.compute_hilbert_series([2, 3])
    t = 0.1
    expected = 1.0 / ((1.0 - t**2) * (1.0 - t**3))
    assert abs(h(t) - expected) < 1e-12


# ---------------------------------------------------------------------------
# molien_series
# ---------------------------------------------------------------------------


def test_molien_series_returns_callable():
    m = InvariantAnalyzer.molien_series(4, [])
    assert callable(m)


def test_molien_series_placeholder_returns_zero():
    m = InvariantAnalyzer.molien_series(4, [])
    result = m(0.5)
    assert result == 0j


def test_molien_series_with_character_table():
    char_table = [{"class": "e", "chi": 1}]
    m = InvariantAnalyzer.molien_series(2, char_table)
    assert callable(m)


# ---------------------------------------------------------------------------
# InvariantAnalyzer is instantiable (no __init__ required)
# ---------------------------------------------------------------------------


def test_invariant_analyzer_instantiation():
    obj = InvariantAnalyzer()
    assert obj is not None


def test_verify_e8_invariants_idempotent():
    # Calling twice returns same result
    analyzer1 = InvariantAnalyzer()
    r1 = analyzer1.verify_e8_invariants()
    r2 = analyzer1.verify_e8_invariants()
    assert r1 == r2
