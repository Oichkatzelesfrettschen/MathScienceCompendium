"""Tests for the preregistered barotropic beta-plane solver."""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest

from mathphysics.beta_plane import (
    BarotropicBetaPlane,
    BetaPlaneConfig,
    NonlinearFilter,
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


def test_short_run_closes_energy_and_enstrophy_budgets():
    result = BarotropicBetaPlane(compact_config()).run()
    assert np.isfinite(result.final_vorticity).all()
    assert abs(result.energy_budget_residual) < 1e-6
    assert abs(result.enstrophy_budget_residual) < 1e-6


@pytest.mark.parametrize(
    "overrides",
    [
        {"grid_size": 7},
        {"time_step": 0.0},
        {"viscosity": -1.0},
        {"initial_wavenumber_minimum": 7.0, "initial_wavenumber_maximum": 6.0},
    ],
)
def test_invalid_configs_are_rejected(overrides):
    with pytest.raises(ValueError):
        replace(BetaPlaneConfig(), **overrides)
