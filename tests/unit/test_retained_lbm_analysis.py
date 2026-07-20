"""Tests for retained LBM evidence diagnostics."""

import numpy as np
import pytest
from scripts.analyze_retained_lbm import analyze_arrays

from mathphysics.diagnostics import calculate_vorticity


def test_uniform_rest_state_has_zero_speed_and_nominal_mass():
    density = np.ones((8, 8))
    velocity_x = np.zeros_like(density)
    velocity_y = np.zeros_like(density)
    result = analyze_arrays(density, velocity_x, velocity_y)
    assert result["mass"] == 64.0
    assert result["relative_mass_drift_from_unit_density"] == 0.0
    assert result["rms_speed"] == 0.0
    assert result["zonal_to_total_rms_ratio"] is None


def test_zonal_profile_reports_prescribed_mode():
    grid_size = 32
    y_coordinate = np.arange(grid_size)
    profile = np.sin(2.0 * np.pi * 4.0 * y_coordinate / grid_size)
    velocity_x = np.repeat(profile[np.newaxis, :], grid_size, axis=0)
    velocity_y = np.zeros_like(velocity_x)
    result = analyze_arrays(np.ones_like(velocity_x), velocity_x, velocity_y)
    assert result["dominant_zonal_mode"] == 4
    assert result["zonal_to_total_rms_ratio"] == pytest.approx(1.0)


def test_vorticity_uses_axis_zero_as_x_coordinate():
    grid_size = 32
    x_coordinate = np.arange(grid_size)[:, np.newaxis]
    y_coordinate = np.arange(grid_size)[np.newaxis, :]
    velocity_x = np.zeros((grid_size, grid_size))
    velocity_y = np.sin(2.0 * np.pi * 2.0 * x_coordinate / grid_size) + np.sin(
        2.0 * np.pi * 5.0 * y_coordinate / grid_size
    )
    result = analyze_arrays(np.ones_like(velocity_x), velocity_x, velocity_y)
    assert result["vorticity_spectral_second_moment_ratio_x_to_y"] > 1e12


def test_shared_vorticity_helper_matches_solid_body_rotation():
    grid_size = 12
    x_coordinate = np.arange(grid_size)[:, np.newaxis]
    y_coordinate = np.arange(grid_size)[np.newaxis, :]
    velocity = np.empty((grid_size, grid_size, 2))
    velocity[..., 0] = -y_coordinate
    velocity[..., 1] = x_coordinate

    np.testing.assert_allclose(
        calculate_vorticity(velocity),
        np.full((grid_size, grid_size), 2.0),
    )


def test_shared_vorticity_helper_rejects_invalid_shape():
    with pytest.raises(ValueError, match=r"\(x, y, 2\)"):
        calculate_vorticity(np.zeros((8, 8)))


def test_mismatched_shapes_are_rejected():
    with pytest.raises(ValueError, match="identical"):
        analyze_arrays(np.ones((4, 4)), np.ones((4, 4)), np.ones((4, 5)))
