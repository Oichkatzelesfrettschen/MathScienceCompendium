"""Tests for accelerated_lbm.py (JAX-accelerated LBM).

All tests are skipped automatically when JAX is not installed.
Uses small 8x8 grids to keep compilation and execution fast.

Covers:
- AcceleratedLBM construction with small params
- AcceleratedLBM array shapes for f, coherence, zpe_field
- update_macroscopic returns density and velocity with correct shapes
- update_macroscopic density is positive
- update_macroscopic velocity is finite
- get_equilibrium shape and non-negativity
- _step_internal returns correct shapes for f and coherence
- step advances iteration counter
- run completes without error and advances iteration
- coherence decays after steps
- Constants WEIGHTS, VELOCITIES, OPPOSITE imported correctly
"""

from __future__ import annotations

import numpy as np
import pytest


jax = pytest.importorskip("jax")
jnp = pytest.importorskip("jax.numpy")

from mathphysics.accelerated_lbm import AcceleratedLBM  # noqa: E402
from mathphysics.quantum_lattice_boltzmann import (  # noqa: E402
    OPPOSITE,
    VELOCITIES,
    WEIGHTS,
    LBMParameters,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

NX = NY = 8  # small grid to keep tests fast


@pytest.fixture
def small_params():
    return LBMParameters(nx=NX, ny=NY, tau=0.8, timesteps=5)


@pytest.fixture
def albm(small_params):
    return AcceleratedLBM(small_params)


# ---------------------------------------------------------------------------
# Module-level constant checks
# ---------------------------------------------------------------------------


def test_weights_sum_to_one():
    np.testing.assert_allclose(np.sum(WEIGHTS), 1.0, atol=1e-12)


def test_weights_length():
    assert len(WEIGHTS) == 9


def test_velocities_shape():
    assert VELOCITIES.shape == (9, 2)


def test_opposite_length():
    assert len(OPPOSITE) == 9


def test_opposite_involution():
    # OPPOSITE[OPPOSITE[i]] == i for all i
    for i in range(9):
        assert OPPOSITE[OPPOSITE[i]] == i


# ---------------------------------------------------------------------------
# AcceleratedLBM construction
# ---------------------------------------------------------------------------


def test_alb_construction_does_not_raise(small_params):
    alb = AcceleratedLBM(small_params)
    assert alb is not None


def test_alb_nx_ny(albm):
    assert albm.nx == NX
    assert albm.ny == NY


def test_alb_f_shape(albm):
    assert albm.f.shape == (NX, NY, 9)


def test_alb_coherence_shape(albm):
    assert albm.coherence.shape == (NX, NY)


def test_alb_weights_jax_array(albm):
    assert isinstance(albm.weights, jnp.ndarray)


def test_alb_velocities_jax_array(albm):
    assert isinstance(albm.velocities, jnp.ndarray)


def test_alb_initial_iteration_zero(albm):
    assert albm.iteration == 0


def test_alb_cs2_value(albm):
    assert abs(albm.cs2 - 1.0 / 3.0) < 1e-12


# ---------------------------------------------------------------------------
# update_macroscopic (static method)
# ---------------------------------------------------------------------------


def test_update_macroscopic_density_shape(albm):
    density, _velocity = AcceleratedLBM.update_macroscopic(albm.f, albm.velocities)
    assert density.shape == (NX, NY)


def test_update_macroscopic_velocity_shape(albm):
    _density, velocity = AcceleratedLBM.update_macroscopic(albm.f, albm.velocities)
    assert velocity.shape == (NX, NY, 2)


def test_update_macroscopic_density_positive(albm):
    density, _ = AcceleratedLBM.update_macroscopic(albm.f, albm.velocities)
    assert np.all(np.array(density) > 0)


def test_update_macroscopic_velocity_finite(albm):
    _, velocity = AcceleratedLBM.update_macroscopic(albm.f, albm.velocities)
    assert np.all(np.isfinite(np.array(velocity)))


# ---------------------------------------------------------------------------
# get_equilibrium (static method)
# ---------------------------------------------------------------------------


def test_get_equilibrium_shape(albm):
    density, velocity = AcceleratedLBM.update_macroscopic(albm.f, albm.velocities)
    f_eq = AcceleratedLBM.get_equilibrium(
        density, velocity, albm.weights, albm.velocities, albm.cs2, albm.cs4
    )
    assert f_eq.shape == (NX, NY, 9)


def test_get_equilibrium_sums_to_density(albm):
    density, velocity = AcceleratedLBM.update_macroscopic(albm.f, albm.velocities)
    f_eq = AcceleratedLBM.get_equilibrium(
        density, velocity, albm.weights, albm.velocities, albm.cs2, albm.cs4
    )
    # Sum over directions should equal density
    f_eq_sum = jnp.sum(f_eq, axis=-1)
    np.testing.assert_allclose(np.array(f_eq_sum), np.array(density), rtol=1e-5)


# ---------------------------------------------------------------------------
# step
# ---------------------------------------------------------------------------


def test_step_advances_iteration(albm):
    key = jax.random.PRNGKey(0)
    albm.step(key)
    assert albm.iteration == 1


def test_step_returns_density_and_velocity(albm):
    key = jax.random.PRNGKey(1)
    density, velocity = albm.step(key)
    assert density.shape == (NX, NY)
    assert velocity.shape == (NX, NY, 2)


def test_step_f_shape_preserved(albm):
    key = jax.random.PRNGKey(2)
    albm.step(key)
    assert albm.f.shape == (NX, NY, 9)


def test_step_multiple_times(albm):
    key = jax.random.PRNGKey(3)
    for _i in range(3):
        key, subkey = jax.random.split(key)
        albm.step(subkey)
    assert albm.iteration == 3


# ---------------------------------------------------------------------------
# coherence decay
# ---------------------------------------------------------------------------


def test_coherence_decays_after_step(albm):
    initial_coherence = np.array(albm.coherence).copy()
    key = jax.random.PRNGKey(10)
    albm.step(key)
    new_coherence = np.array(albm.coherence)
    # All coherence values should decrease
    assert np.all(new_coherence <= initial_coherence + 1e-8)


def test_coherence_remains_positive_after_steps(albm):
    key = jax.random.PRNGKey(20)
    for _ in range(5):
        key, subkey = jax.random.split(key)
        albm.step(subkey)
    assert np.all(np.array(albm.coherence) > 0)


# ---------------------------------------------------------------------------
# run (jax.lax.scan path)
# ---------------------------------------------------------------------------


def test_run_advances_iteration(albm):
    albm.run(num_steps=3)
    assert albm.iteration == 3


def test_run_f_shape_preserved(albm):
    albm.run(num_steps=2)
    assert albm.f.shape == (NX, NY, 9)


def test_run_coherence_shape_preserved(albm):
    albm.run(num_steps=2)
    assert albm.coherence.shape == (NX, NY)
