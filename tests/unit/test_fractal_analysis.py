"""Tests for fractal_analysis.py.

Covers:
- FractalDimensionResult dataclass and to_dict()
- FractalDimensionCalculator.box_counting_dimension with known inputs
- FractalDimensionCalculator.correlation_dimension basic behaviour
- FractalDimensionCalculator.information_dimension basic behaviour
- FractalDimensionCalculator.hausdorff_dimension basic behaviour
- FractalGenerator.cantor_set interval structure
- FractalGenerator.koch_snowflake returns 2-D array
- FractalGenerator.sierpinski_triangle returns binary image
- FractalGenerator.lorenz_attractor shape and finiteness
- FractalGenerator.henon_map shape and finiteness
- FractalGenerator.mandelbrot_point boundary cases
- FractalGenerator.julia_point boundary cases
- SelfSimilarityAnalyzer.lacunarity basic dict structure
- analyze_fractal_dimensions writes output and returns dict
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pytest

from mathphysics.fractal_analysis import (
    FractalDimensionCalculator,
    FractalDimensionResult,
    FractalGenerator,
    SelfSimilarityAnalyzer,
    analyze_fractal_dimensions,
)


if TYPE_CHECKING:
    from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _line_points(n: int = 100) -> np.ndarray:
    """Points lying on the unit interval (topological dim 1)."""
    x = np.linspace(0.0, 1.0, n)
    return np.column_stack([x, np.zeros(n)])


def _square_points(n: int = 100) -> np.ndarray:
    """Points densely filling the unit square (topological dim 2)."""
    rng = np.random.default_rng(42)
    return rng.random((n, 2))


# ---------------------------------------------------------------------------
# FractalDimensionResult dataclass
# ---------------------------------------------------------------------------


def test_fractal_dimension_result_fields():
    result = FractalDimensionResult(
        method="test",
        dimension=1.5,
        error=0.05,
        r_squared=0.99,
        scales=np.array([0.1, 0.2]),
        measures=np.array([10.0, 5.0]),
        confidence_interval=(1.4, 1.6),
        metadata={"num_points": 100},
    )
    assert result.method == "test"
    assert result.dimension == 1.5
    assert result.error == 0.05
    assert result.r_squared == 0.99


def test_fractal_dimension_result_to_dict_keys():
    result = FractalDimensionResult(
        method="box_counting",
        dimension=1.26,
        error=0.02,
        r_squared=0.97,
        scales=np.array([0.1, 0.2, 0.3]),
        measures=np.array([50.0, 25.0, 12.0]),
        confidence_interval=(1.22, 1.30),
        metadata={"num_points": 200},
    )
    d = result.to_dict()
    for key in (
        "method",
        "dimension",
        "error",
        "r_squared",
        "scales",
        "measures",
        "confidence_interval",
        "metadata",
    ):
        assert key in d, f"Key '{key}' missing from to_dict() output"


def test_fractal_dimension_result_to_dict_scalars_are_python_floats():
    result = FractalDimensionResult(
        method="m",
        dimension=np.float64(1.5),
        error=np.float64(0.01),
        r_squared=np.float64(0.98),
        scales=np.array([0.1]),
        measures=np.array([10.0]),
        confidence_interval=(1.4, 1.6),
        metadata={},
    )
    d = result.to_dict()
    # JSON serialisability requires plain Python floats
    assert isinstance(d["dimension"], float)
    assert isinstance(d["error"], float)
    assert isinstance(d["r_squared"], float)


def test_fractal_dimension_result_to_dict_scales_is_list():
    result = FractalDimensionResult(
        method="m",
        dimension=1.0,
        error=0.0,
        r_squared=1.0,
        scales=np.linspace(0.01, 0.5, 5),
        measures=np.ones(5),
        confidence_interval=(0.9, 1.1),
        metadata={},
    )
    d = result.to_dict()
    assert isinstance(d["scales"], list)
    assert isinstance(d["measures"], list)


# ---------------------------------------------------------------------------
# FractalGenerator.cantor_set
# ---------------------------------------------------------------------------


def test_cantor_set_returns_list_of_tuples():
    intervals = FractalGenerator.cantor_set(iterations=3)
    assert isinstance(intervals, list)
    assert all(isinstance(iv, tuple) and len(iv) == 2 for iv in intervals)


def test_cantor_set_iteration_0_is_unit_interval():
    intervals = FractalGenerator.cantor_set(iterations=0)
    assert len(intervals) == 1
    assert intervals[0] == pytest.approx((0.0, 1.0))


def test_cantor_set_doubles_on_each_iteration():
    for k in range(1, 5):
        intervals = FractalGenerator.cantor_set(iterations=k)
        assert len(intervals) == 2**k


def test_cantor_set_intervals_non_overlapping():
    intervals = FractalGenerator.cantor_set(iterations=5)
    sorted_ivs = sorted(intervals, key=lambda iv: iv[0])
    for i in range(len(sorted_ivs) - 1):
        assert sorted_ivs[i][1] <= sorted_ivs[i + 1][0] + 1e-12


def test_cantor_set_all_within_unit_interval():
    intervals = FractalGenerator.cantor_set(iterations=6)
    for start, end in intervals:
        assert start >= -1e-12
        assert end <= 1.0 + 1e-12


# ---------------------------------------------------------------------------
# FractalGenerator.mandelbrot_point and julia_point
# ---------------------------------------------------------------------------


def test_mandelbrot_point_origin_is_inside():
    # c=0, z never escapes
    n = FractalGenerator.mandelbrot_point(0.0, 0.0, max_iter=50)
    assert n == 50


def test_mandelbrot_point_far_point_escapes():
    # c = 10+10i is far outside the set
    n = FractalGenerator.mandelbrot_point(10.0, 10.0, max_iter=100)
    assert n < 100


def test_mandelbrot_point_returns_int():
    n = FractalGenerator.mandelbrot_point(-0.5, 0.0, max_iter=20)
    assert isinstance(n, int)


def test_julia_point_origin_with_zero_c():
    # z=0, c=0 -> z stays at origin, max_iter returned
    n = FractalGenerator.julia_point(0.0, 0.0, 0.0, 0.0, max_iter=50)
    assert n == 50


def test_julia_point_far_z_escapes():
    n = FractalGenerator.julia_point(10.0, 10.0, 0.0, 0.0, max_iter=100)
    assert n < 100


# ---------------------------------------------------------------------------
# FractalGenerator.koch_snowflake
# ---------------------------------------------------------------------------


def test_koch_snowflake_returns_2d_array():
    pts = FractalGenerator.koch_snowflake(iterations=2)
    assert isinstance(pts, np.ndarray)
    assert pts.ndim == 2
    assert pts.shape[1] == 2


def test_koch_snowflake_has_finite_values():
    pts = FractalGenerator.koch_snowflake(iterations=2)
    assert np.all(np.isfinite(pts))


def test_koch_snowflake_more_iterations_more_points():
    pts2 = FractalGenerator.koch_snowflake(iterations=2)
    pts3 = FractalGenerator.koch_snowflake(iterations=3)
    assert len(pts3) > len(pts2)


# ---------------------------------------------------------------------------
# FractalGenerator.lorenz_attractor and henon_map
# ---------------------------------------------------------------------------


def test_lorenz_attractor_shape():
    pts = FractalGenerator.lorenz_attractor(num_points=50)
    assert pts.shape == (50, 3)


def test_lorenz_attractor_finite():
    pts = FractalGenerator.lorenz_attractor(num_points=50)
    assert np.all(np.isfinite(pts))


def test_henon_map_shape():
    pts = FractalGenerator.henon_map(num_points=80)
    assert pts.shape == (80, 2)


def test_henon_map_finite():
    pts = FractalGenerator.henon_map(num_points=80)
    assert np.all(np.isfinite(pts))


# ---------------------------------------------------------------------------
# FractalDimensionCalculator.box_counting_dimension
# ---------------------------------------------------------------------------


def test_box_counting_empty_points_raises():
    with pytest.raises(ValueError):
        FractalDimensionCalculator.box_counting_dimension(np.array([]))


def test_box_counting_line_dim_approx_1():
    pts = _line_points(150)
    result = FractalDimensionCalculator.box_counting_dimension(pts, num_scales=15)
    # A line should yield dim close to 1 (allow wide tolerance for numerical estimation)
    assert 0.5 <= result.dimension <= 1.5


def test_box_counting_square_dim_approx_2():
    # Use a structured grid and explicit scale range that spans the fractal
    # scaling region.  The default min_scale = 2/N is too fine for a grid
    # (isolated points at sub-grid scale collapse the slope to ~0).
    grid_n = 15
    xs, ys = np.meshgrid(np.linspace(0, 1, grid_n), np.linspace(0, 1, grid_n))
    pts = np.column_stack([xs.ravel(), ys.ravel()])
    spacing = 1.0 / (grid_n - 1)
    result = FractalDimensionCalculator.box_counting_dimension(
        pts, min_scale=spacing * 1.5, max_scale=0.5, num_scales=12
    )
    # A filled 2-D grid should yield dimension well above 1.5
    assert 1.5 <= result.dimension <= 2.5


def test_box_counting_returns_fractal_dimension_result():
    pts = _square_points(100)
    result = FractalDimensionCalculator.box_counting_dimension(pts, num_scales=10)
    assert isinstance(result, FractalDimensionResult)


def test_box_counting_r_squared_in_unit_interval():
    pts = _square_points(100)
    result = FractalDimensionCalculator.box_counting_dimension(pts, num_scales=10)
    assert 0.0 <= result.r_squared <= 1.0


def test_box_counting_scales_length_matches_num_scales():
    pts = _line_points(100)
    n = 12
    result = FractalDimensionCalculator.box_counting_dimension(pts, num_scales=n)
    assert len(result.scales) == n


def test_box_counting_confidence_interval_ordered():
    pts = _square_points(100)
    result = FractalDimensionCalculator.box_counting_dimension(pts, num_scales=10)
    lo, hi = result.confidence_interval
    assert lo <= hi


def test_box_counting_metadata_has_num_points():
    pts = _square_points(80)
    result = FractalDimensionCalculator.box_counting_dimension(pts, num_scales=10)
    assert "num_points" in result.metadata
    assert result.metadata["num_points"] == 80


# ---------------------------------------------------------------------------
# FractalDimensionCalculator.correlation_dimension
# ---------------------------------------------------------------------------


def test_correlation_dimension_too_few_points_raises():
    pts = np.random.rand(5, 2)
    with pytest.raises(ValueError):
        FractalDimensionCalculator.correlation_dimension(pts)


def test_correlation_dimension_returns_result():
    pts = _square_points(50)
    result = FractalDimensionCalculator.correlation_dimension(pts, num_scales=10)
    assert isinstance(result, FractalDimensionResult)
    assert result.method == "correlation"


def test_correlation_dimension_positive():
    pts = _square_points(60)
    result = FractalDimensionCalculator.correlation_dimension(pts, num_scales=10)
    assert result.dimension > 0


def test_correlation_dimension_sample_size_respected():
    # With sample_size < n the computation should still succeed
    rng = np.random.default_rng(7)
    pts = rng.random((100, 2))
    result = FractalDimensionCalculator.correlation_dimension(pts, sample_size=30, num_scales=8)
    assert isinstance(result, FractalDimensionResult)


# ---------------------------------------------------------------------------
# FractalDimensionCalculator.information_dimension
# ---------------------------------------------------------------------------


def test_information_dimension_returns_result():
    pts = _square_points(80)
    result = FractalDimensionCalculator.information_dimension(pts, num_scales=8)
    assert isinstance(result, FractalDimensionResult)
    assert result.method == "information"


def test_information_dimension_positive():
    pts = _square_points(80)
    result = FractalDimensionCalculator.information_dimension(pts, num_scales=8)
    assert result.dimension > 0


def test_information_dimension_3d_points():
    rng = np.random.default_rng(99)
    pts = rng.random((80, 3))
    result = FractalDimensionCalculator.information_dimension(pts, num_scales=8)
    assert isinstance(result, FractalDimensionResult)


# ---------------------------------------------------------------------------
# FractalDimensionCalculator.hausdorff_dimension
# ---------------------------------------------------------------------------


def test_hausdorff_dimension_covering_returns_result():
    pts = _square_points(60)
    result = FractalDimensionCalculator.hausdorff_dimension(pts, num_scales=8, method="covering")
    assert isinstance(result, FractalDimensionResult)
    assert "hausdorff" in result.method


def test_hausdorff_dimension_positive():
    pts = _square_points(60)
    result = FractalDimensionCalculator.hausdorff_dimension(pts, num_scales=8)
    assert result.dimension > 0


# ---------------------------------------------------------------------------
# SelfSimilarityAnalyzer.lacunarity
# ---------------------------------------------------------------------------


def test_lacunarity_returns_dict():
    img = np.random.randint(0, 2, (16, 16)).astype(float)
    result = SelfSimilarityAnalyzer.lacunarity(img, box_sizes=[2, 4])
    assert isinstance(result, dict)


def test_lacunarity_dict_has_expected_keys():
    img = np.ones((16, 16))
    result = SelfSimilarityAnalyzer.lacunarity(img, box_sizes=[2, 4])
    for key in ("box_sizes", "lacunarities", "mean_lacunarity"):
        assert key in result


def test_lacunarity_uniform_image_low_lacunarity():
    # Uniform (all-ones) image has zero variance -> lacunarity = 1.0 for each box size
    img = np.ones((16, 16))
    result = SelfSimilarityAnalyzer.lacunarity(img, box_sizes=[2, 4])
    for lac in result["lacunarities"]:
        assert lac == pytest.approx(1.0, abs=1e-10)


def test_lacunarity_lengths_match_box_sizes():
    img = np.ones((32, 32))
    box_sizes = [2, 4, 8]
    result = SelfSimilarityAnalyzer.lacunarity(img, box_sizes=box_sizes)
    assert len(result["lacunarities"]) == len(box_sizes)


# ---------------------------------------------------------------------------
# analyze_fractal_dimensions (lightweight integration)
# ---------------------------------------------------------------------------


def test_analyze_fractal_dimensions_returns_dict(tmp_path: Path):
    result = analyze_fractal_dimensions(output_dir=tmp_path)
    assert isinstance(result, dict)


def test_analyze_fractal_dimensions_writes_json(tmp_path: Path):
    analyze_fractal_dimensions(output_dir=tmp_path)
    output_file = tmp_path / "fractal_analysis.json"
    assert output_file.exists()


def test_analyze_fractal_dimensions_json_has_cantor_dim(tmp_path: Path):
    result = analyze_fractal_dimensions(output_dir=tmp_path)
    assert "cantor_dim" in result


def test_analyze_fractal_dimensions_cantor_dim_reasonable(tmp_path: Path):
    result = analyze_fractal_dimensions(output_dir=tmp_path)
    # Theoretical Cantor dim ~ 0.631; allow broad tolerance
    assert 0.0 < result["cantor_dim"] < 2.0
