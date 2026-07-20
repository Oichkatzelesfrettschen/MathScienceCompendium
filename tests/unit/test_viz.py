from __future__ import annotations

import matplotlib


matplotlib.use("Agg")  # Non-interactive backend; must be set before other matplotlib imports

import matplotlib.pyplot as plt
import numpy as np
import pytest

from mathphysics.algebras.roots import E8RootSystem
from mathphysics.viz import ColorScheme, Visualizer, VizConfig


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def close_figures():
    """Ensure all matplotlib figures are closed after each test."""
    yield
    plt.close("all")


@pytest.fixture
def viz():
    return Visualizer()


@pytest.fixture
def small_roots():
    """Small set of 2D roots for fast testing."""
    rng = np.random.default_rng(0)
    return rng.standard_normal((20, 4))


@pytest.fixture
def e8_roots_fixture():
    return E8RootSystem().generate_roots()


# ---------------------------------------------------------------------------
# VizConfig
# ---------------------------------------------------------------------------


def test_vizconfig_defaults():
    cfg = VizConfig()
    assert cfg.dpi == 300
    assert cfg.color_scheme == ColorScheme.NEON_DARK


def test_vizconfig_get_size_inches():
    cfg = VizConfig(width_pixels=300, height_pixels=300, dpi=100)
    w, h = cfg.get_size_inches()
    assert w == pytest.approx(3.0)
    assert h == pytest.approx(3.0)


def test_vizconfig_cyberpunk_scheme():
    cfg = VizConfig(color_scheme=ColorScheme.CYBERPUNK)
    assert cfg.color_scheme == ColorScheme.CYBERPUNK


# ---------------------------------------------------------------------------
# Visualizer construction
# ---------------------------------------------------------------------------


def test_visualizer_instantiation(viz):
    assert viz is not None


def test_visualizer_has_colors(viz):
    assert isinstance(viz.colors, list)
    assert len(viz.colors) > 0


def test_visualizer_colors_are_hex_strings(viz):
    for color in viz.colors:
        assert color.startswith("#")
        assert len(color) == 7


def test_visualizer_cyberpunk_palette():
    cfg = VizConfig(color_scheme=ColorScheme.CYBERPUNK)
    v = Visualizer(cfg)
    assert "#00d9ff" in v.colors


def test_visualizer_default_palette_contains_cyan(viz):
    assert "#00ffff" in viz.colors


# ---------------------------------------------------------------------------
# plot_roots_2d
# ---------------------------------------------------------------------------


def test_plot_roots_2d_returns_figure(viz, small_roots):
    fig = viz.plot_roots_2d(small_roots, title="Test Roots")
    assert isinstance(fig, plt.Figure)


def test_plot_roots_2d_with_weights(viz, small_roots):
    weights = np.ones(len(small_roots))
    fig = viz.plot_roots_2d(small_roots, weights=weights)
    assert isinstance(fig, plt.Figure)


def test_plot_roots_2d_e8(viz, e8_roots_fixture):
    fig = viz.plot_roots_2d(e8_roots_fixture, title="E8")
    assert isinstance(fig, plt.Figure)


def test_plot_roots_2d_no_exception_on_minimal_input(viz):
    roots = np.array([[1.0, 0.0], [0.0, 1.0], [-1.0, 0.0]])
    fig = viz.plot_roots_2d(roots)
    assert fig is not None


# ---------------------------------------------------------------------------
# plot_time_series_with_stats
# ---------------------------------------------------------------------------


def test_plot_time_series_returns_figure(viz):
    x = np.linspace(0, 10, 30)
    y = np.sin(x)
    fig = viz.plot_time_series_with_stats(x, y)
    assert isinstance(fig, plt.Figure)


def test_plot_time_series_with_error_bars(viz):
    x = np.linspace(0, 5, 20)
    y = np.cos(x)
    y_err = np.full_like(y, 0.05)
    fig = viz.plot_time_series_with_stats(x, y, y_err=y_err)
    assert isinstance(fig, plt.Figure)


def test_plot_time_series_custom_labels(viz):
    x = np.arange(10, dtype=float)
    y = x**2
    fig = viz.plot_time_series_with_stats(
        x, y, title="Custom Title", xlabel="Time", ylabel="Energy"
    )
    ax = fig.axes[0]
    assert ax.get_title() == "Custom Title"
    assert ax.get_xlabel() == "Time"
    assert ax.get_ylabel() == "Energy"


def test_plot_time_series_constant_signal(viz):
    # Constant signal: no significant deviations, std=0
    x = np.arange(10, dtype=float)
    y = np.ones(10)
    fig = viz.plot_time_series_with_stats(x, y)
    assert isinstance(fig, plt.Figure)


# ---------------------------------------------------------------------------
# plot_lbm_field
# ---------------------------------------------------------------------------


def test_plot_lbm_field_returns_figure(viz):
    field = np.random.default_rng(1).standard_normal((16, 16))
    fig = viz.plot_lbm_field(field)
    assert isinstance(fig, plt.Figure)


def test_plot_lbm_field_custom_title(viz):
    field = np.ones((8, 8))
    fig = viz.plot_lbm_field(field, title="Density Field")
    ax = fig.axes[0]
    assert ax.get_title() == "Density Field"


def test_plot_lbm_field_non_square(viz):
    field = np.random.default_rng(2).standard_normal((8, 16))
    fig = viz.plot_lbm_field(field)
    assert isinstance(fig, plt.Figure)


# ---------------------------------------------------------------------------
# plot_persistence_barcode
# ---------------------------------------------------------------------------


def test_plot_persistence_barcode_returns_figure(viz):
    # persistence: array of [dimension, birth, death]
    persistence = np.array([[0, 0.0, 1.0], [1, 0.2, 0.8], [0, 0.1, 0.5]])
    fig = viz.plot_persistence_barcode(persistence)
    assert isinstance(fig, plt.Figure)


def test_plot_persistence_barcode_custom_title(viz):
    persistence = np.array([[0, 0.0, 1.0]])
    fig = viz.plot_persistence_barcode(persistence, title="Topology")
    ax = fig.axes[0]
    assert ax.get_title() == "Topology"


def test_plot_persistence_barcode_multiple_dimensions(viz):
    persistence = np.array(
        [
            [0, 0.0, 1.5],
            [1, 0.3, 1.0],
            [2, 0.5, 0.7],
        ]
    )
    fig = viz.plot_persistence_barcode(persistence)
    assert isinstance(fig, plt.Figure)
