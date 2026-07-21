"""Tests for the preregistered barotropic beta-plane solver."""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest
from scripts.run_beta_plane_controls import (
    prescribed_zonal_diagnostic_control,
    retained_lbm_null_control,
)

from mathphysics.beta_plane import (
    BarotropicBetaPlane,
    BetaPlaneConfig,
    NonlinearFilter,
    circular_peak_indices,
    classify_final_window,
)


def compact_config(**overrides):
    return replace(
        BetaPlaneConfig(grid_size=24, time_step=0.005, steps=20, seed=11),
        **overrides,
    )


def test_initial_condition_has_preregistered_energy():
    solver = BarotropicBetaPlane(compact_config())
    assert solver.kinetic_energy(solver.initial_vorticity()) == pytest.approx(0.01)


def test_beta_term_changes_tendency():
    beta_solver = BarotropicBetaPlane(compact_config(beta=5.0))
    f_plane_solver = BarotropicBetaPlane(compact_config(beta=0.0))
    vorticity_hat = beta_solver.initial_vorticity()
    difference = beta_solver.tendency_hat(vorticity_hat) - f_plane_solver.tendency_hat(
        vorticity_hat
    )
    assert np.linalg.norm(difference) > 0.0


def test_homomorphic_filter_is_exact_identity_control():
    identity_solver = BarotropicBetaPlane(compact_config(nonlinear_filter=NonlinearFilter.IDENTITY))
    quotient_solver = BarotropicBetaPlane(
        compact_config(nonlinear_filter=NonlinearFilter.E7_PQ_HOMOMORPHISM)
    )
    vorticity_hat = identity_solver.initial_vorticity()
    np.testing.assert_array_equal(
        identity_solver.tendency_hat(vorticity_hat),
        quotient_solver.tendency_hat(vorticity_hat),
    )


def test_matched_filter_runs_are_bit_identical():
    identity_run = BarotropicBetaPlane(
        compact_config(nonlinear_filter=NonlinearFilter.IDENTITY)
    ).run()
    quotient_run = BarotropicBetaPlane(
        compact_config(nonlinear_filter=NonlinearFilter.E7_PQ_HOMOMORPHISM)
    ).run()
    np.testing.assert_array_equal(identity_run.final_vorticity, quotient_run.final_vorticity)


def test_beta_and_f_plane_runs_diverge():
    beta_run = BarotropicBetaPlane(compact_config(beta=5.0)).run()
    f_plane_run = BarotropicBetaPlane(compact_config(beta=0.0)).run()
    relative_difference = np.linalg.norm(
        beta_run.final_vorticity - f_plane_run.final_vorticity
    ) / np.linalg.norm(f_plane_run.final_vorticity)
    assert relative_difference > 1e-6


def test_run_accepts_a_locked_initial_spectrum():
    solver = BarotropicBetaPlane(compact_config())
    initial_hat = solver.initial_vorticity()
    generated = solver.run()
    injected = solver.run(initial_hat)
    np.testing.assert_array_equal(generated.initial_vorticity, injected.initial_vorticity)
    np.testing.assert_array_equal(generated.final_vorticity, injected.final_vorticity)


def test_run_rejects_an_initial_spectrum_with_wrong_shape():
    solver = BarotropicBetaPlane(compact_config())
    with pytest.raises(ValueError, match="must have shape"):
        solver.run(np.zeros((8, 8), dtype=np.complex128))


def test_prescribed_zonal_control_is_detected():
    control = prescribed_zonal_diagnostic_control(
        {
            "production_grid_size": 64,
            "initial_kinetic_energy": 0.01,
            "initial_shell": [4.0, 6.0],
        }
    )
    assert control["passed"]
    assert control["observed_total_jet_count"] == 8
    assert control["full_window_classification"]["persistent_jet"] is True


def test_retained_lbm_null_control_is_non_zonal():
    control = retained_lbm_null_control()
    assert control["passed"]
    assert control["snapshot_count"] == 5


def test_short_run_closes_energy_and_enstrophy_budgets():
    result = BarotropicBetaPlane(compact_config()).run()
    assert np.isfinite(result.final_vorticity).all()
    assert abs(result.energy_budget_residual) < 1e-6
    assert abs(result.enstrophy_budget_residual) < 1e-6


def test_jet_prominence_is_fixed_by_initial_energy():
    result = BarotropicBetaPlane(compact_config()).run()
    assert result.jet_prominence_threshold == pytest.approx(0.05 * np.sqrt(0.02))


def test_circular_peak_detection_resolves_boundary_peak():
    profile = np.array([2.0, 0.0, -1.0, 0.0])
    peaks = circular_peak_indices(profile, prominence=1.0, distance=1)
    np.testing.assert_array_equal(peaks, np.array([0]))


def test_final_window_classifier_rejects_weak_or_unstable_profiles():
    assert classify_final_window([0.2] * 10, [4] * 10)["persistent_jet"] is True
    assert classify_final_window([0.09] * 10, [4] * 10)["persistent_jet"] is False
    assert classify_final_window([0.2] * 10, [2, 4] * 5)["persistent_jet"] is False


def test_final_window_classifier_rejects_malformed_inputs():
    with pytest.raises(ValueError, match="nonempty and aligned"):
        classify_final_window([], [])
    with pytest.raises(ValueError, match="nonempty and aligned"):
        classify_final_window([0.2], [2, 2])
    with pytest.raises(ValueError, match="finite"):
        classify_final_window([float("nan")], [2])


@pytest.mark.parametrize(
    "overrides",
    [
        {"grid_size": 7},
        {"time_step": 0.0},
        {"viscosity": -1.0},
        {"sample_interval_steps": 0},
        {"analysis_window_fraction": 1.1},
        {"initial_wavenumber_minimum": 7.0, "initial_wavenumber_maximum": 6.0},
    ],
)
def test_invalid_configs_are_rejected(overrides):
    with pytest.raises(ValueError):
        replace(BetaPlaneConfig(), **overrides)
