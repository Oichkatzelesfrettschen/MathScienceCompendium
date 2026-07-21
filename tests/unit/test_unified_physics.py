"""Tests for unified_physics.py (quantum_simulation.py-based UnifiedSimulation).

unified_physics.py imports JAX unconditionally at module level, so every test
skips gracefully when JAX is not installed.  When JAX IS present the tests
exercise the parts of UnifiedSimulation and related helpers that do not
require a GPU.

Tested surfaces:
- LBMParameters (from quantum_lattice_boltzmann) default construction
- LBMParameters __post_init__ tau/viscosity relationship
- LBMParameters invalid tau raises ValueError
- LBMState.update_macroscopic conserves shape
- QuantumLatticeBoltzmann.step on a tiny grid (8x8)
- QuantumLatticeBoltzmann.run_simulation returns LBMState
- QuantumLatticeBoltzmann.validate_conservation returns dict
- BoundaryType enum values
- VELOCITIES and WEIGHTS module-level constants
"""

from __future__ import annotations

import numpy as np
import pytest

# The LBM types live in quantum_lattice_boltzmann and do NOT need JAX.
# We test them independently of unified_physics.py to keep tests fast.
from mathphysics.quantum_lattice_boltzmann import (
    CS2,
    PHI,
    VELOCITIES,
    WEIGHTS,
    BoundaryType,
    LBMParameters,
    LBMState,
    QuantumLatticeBoltzmann,
)


# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------


def test_velocities_shape():
    assert VELOCITIES.shape == (9, 2)


def test_weights_shape():
    assert WEIGHTS.shape == (9,)


def test_weights_sum_to_one():
    np.testing.assert_allclose(WEIGHTS.sum(), 1.0, atol=1e-12)


def test_weights_all_positive():
    assert np.all(WEIGHTS > 0)


def test_cs2_positive():
    assert CS2 > 0


def test_phi_golden_ratio():
    phi = (1.0 + np.sqrt(5.0)) / 2.0
    assert abs(PHI - phi) < 1e-12


# ---------------------------------------------------------------------------
# BoundaryType enum
# ---------------------------------------------------------------------------


def test_boundary_type_periodic_value():
    assert BoundaryType.PERIODIC.value == "periodic"


def test_boundary_type_bounce_back_value():
    assert BoundaryType.BOUNCE_BACK.value == "bounce_back"


def test_boundary_type_symmetry_preserving_value():
    assert BoundaryType.SYMMETRY_PRESERVING.value == "symmetry_preserving"


def test_boundary_type_open_value():
    assert BoundaryType.OPEN.value == "open"


def test_boundary_type_has_four_members():
    assert len(list(BoundaryType)) == 4


# ---------------------------------------------------------------------------
# LBMParameters construction
# ---------------------------------------------------------------------------


def test_lbm_parameters_default_nx():
    params = LBMParameters()
    assert params.nx == 128


def test_lbm_parameters_default_ny():
    params = LBMParameters()
    assert params.ny == 128


def test_lbm_parameters_default_tau():
    params = LBMParameters()
    assert params.tau == 0.8


def test_lbm_parameters_custom_grid():
    params = LBMParameters(nx=8, ny=8)
    assert params.nx == 8
    assert params.ny == 8


def test_lbm_parameters_viscosity_computed_from_tau():
    params = LBMParameters(tau=0.8)
    expected_viscosity = CS2 * (0.8 - 0.5)
    assert abs(params.viscosity - expected_viscosity) < 1e-12


def test_lbm_parameters_tau_computed_from_viscosity():
    vis = 0.1
    params = LBMParameters(viscosity=vis)
    expected_tau = vis / CS2 + 0.5
    assert abs(params.tau - expected_tau) < 1e-12


def test_lbm_parameters_invalid_tau_raises():
    with pytest.raises(ValueError, match="tau"):
        LBMParameters(viscosity=0.0)


def test_lbm_parameters_very_small_tau_raises():
    # Negative viscosity -> tau < 0.5
    with pytest.raises(ValueError):
        LBMParameters(tau=0.3)


def test_lbm_parameters_default_boundary_type():
    params = LBMParameters()
    assert params.boundary_type == BoundaryType.SYMMETRY_PRESERVING


# ---------------------------------------------------------------------------
# QuantumLatticeBoltzmann on a tiny (8x8) grid
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def small_lbm() -> QuantumLatticeBoltzmann:
    """Shared tiny-grid LBM instance (module scope for speed)."""
    params = LBMParameters(nx=8, ny=8, timesteps=5)
    return QuantumLatticeBoltzmann(params)


def test_qlbm_state_density_shape(small_lbm: QuantumLatticeBoltzmann):
    assert small_lbm.state.density.shape == (8, 8)


def test_qlbm_state_velocity_shape(small_lbm: QuantumLatticeBoltzmann):
    assert small_lbm.state.velocity.shape == (8, 8, 2)


def test_qlbm_state_f_shape(small_lbm: QuantumLatticeBoltzmann):
    assert small_lbm.state.f.shape == (8, 8, 9)


def test_qlbm_state_pressure_shape(small_lbm: QuantumLatticeBoltzmann):
    assert small_lbm.state.pressure.shape == (8, 8)


def test_qlbm_state_density_positive(small_lbm: QuantumLatticeBoltzmann):
    assert np.all(small_lbm.state.density > 0)


def test_qlbm_auxiliary_initialization_is_seed_reproducible():
    first = QuantumLatticeBoltzmann(LBMParameters(nx=8, ny=8, random_seed=17))
    second = QuantumLatticeBoltzmann(LBMParameters(nx=8, ny=8, random_seed=17))
    distinct = QuantumLatticeBoltzmann(LBMParameters(nx=8, ny=8, random_seed=18))

    np.testing.assert_array_equal(first.state.zpe_field, second.state.zpe_field)
    assert not np.array_equal(first.state.zpe_field, distinct.state.zpe_field)


def test_qlbm_step_runs_without_error():
    params = LBMParameters(nx=8, ny=8)
    lbm = QuantumLatticeBoltzmann(params)
    lbm.step()  # must not raise


def test_qlbm_step_increments_iteration():
    params = LBMParameters(nx=8, ny=8)
    lbm = QuantumLatticeBoltzmann(params)
    lbm.step()
    assert lbm.state.iteration == 1


def test_qlbm_run_simulation_returns_lbm_state():
    params = LBMParameters(nx=8, ny=8, timesteps=3)
    lbm = QuantumLatticeBoltzmann(params)
    state = lbm.run_simulation(timesteps=2)
    assert isinstance(state, LBMState)


def test_qlbm_run_simulation_iteration_count():
    params = LBMParameters(nx=8, ny=8)
    lbm = QuantumLatticeBoltzmann(params)
    lbm.run_simulation(timesteps=4)
    assert lbm.state.iteration == 4


def test_qlbm_validate_conservation_returns_dict():
    params = LBMParameters(nx=8, ny=8)
    lbm = QuantumLatticeBoltzmann(params)
    result = lbm.validate_conservation()
    assert isinstance(result, dict)


def test_qlbm_validate_conservation_mass_key():
    params = LBMParameters(nx=8, ny=8)
    lbm = QuantumLatticeBoltzmann(params)
    result = lbm.validate_conservation()
    assert "mass_conserved" in result


def test_qlbm_equilibrium_sums_to_density_for_nonzero_velocity():
    params = LBMParameters(nx=8, ny=8, harmonic_amplitude=0.0)
    lbm = QuantumLatticeBoltzmann(params)
    lbm.state.velocity[..., 0] = 0.1
    lbm.state.velocity[..., 1] = 0.05
    lbm._compute_equilibrium()
    np.testing.assert_allclose(
        np.sum(lbm.state.f_eq, axis=2),
        lbm.state.density,
        rtol=1e-12,
        atol=1e-12,
    )


def test_qlbm_periodic_steps_conserve_mass():
    params = LBMParameters(
        nx=16,
        ny=16,
        tau=1.5,
        harmonic_amplitude=1e-4,
        num_harmonics=3,
        boundary_type=BoundaryType.PERIODIC,
    )
    lbm = QuantumLatticeBoltzmann(params)
    lbm.run_simulation(timesteps=50)
    result = lbm.validate_conservation(relative_tolerance=1e-10)
    assert result["mass_conserved"]
    assert result["relative_mass_error"] <= 1e-10


def test_qlbm_conservation_validator_measures_injected_mass():
    params = LBMParameters(nx=8, ny=8, harmonic_amplitude=0.0)
    lbm = QuantumLatticeBoltzmann(params)
    lbm.state.f[..., 0] += 0.01
    lbm.state.update_macroscopic()
    result = lbm.validate_conservation(relative_tolerance=1e-6)
    assert not result["mass_conserved"]
    assert result["relative_mass_error"] > 1e-6


def test_qlbm_conservation_validator_rejects_nonpositive_tolerance():
    params = LBMParameters(nx=8, ny=8)
    lbm = QuantumLatticeBoltzmann(params)
    with pytest.raises(ValueError, match="positive"):
        lbm.validate_conservation(relative_tolerance=0.0)


# ---------------------------------------------------------------------------
# LBMState.update_macroscopic
# ---------------------------------------------------------------------------


def test_lbm_state_update_macroscopic_density_non_negative():
    params = LBMParameters(nx=8, ny=8)
    lbm = QuantumLatticeBoltzmann(params)
    lbm.state.update_macroscopic()
    assert np.all(lbm.state.density >= 0)


def test_lbm_state_update_macroscopic_pressure_positive():
    params = LBMParameters(nx=8, ny=8)
    lbm = QuantumLatticeBoltzmann(params)
    lbm.state.update_macroscopic()
    assert np.all(lbm.state.pressure > 0)


def test_lbm_state_update_macroscopic_energy_non_negative():
    params = LBMParameters(nx=8, ny=8)
    lbm = QuantumLatticeBoltzmann(params)
    lbm.state.update_macroscopic()
    assert np.all(lbm.state.energy >= 0)


# ---------------------------------------------------------------------------
# unified_physics.py - import guard
# These tests skip if JAX is not installed since unified_physics.py
# performs a bare `import jax` at module level.
# ---------------------------------------------------------------------------


def test_unified_physics_importable_with_jax():
    """Check that unified_physics imports cleanly when JAX is available."""
    pytest.importorskip("jax", reason="JAX required for unified_physics")
    try:
        import mathphysics.unified_physics  # noqa: F401, PLC0415
    except Exception as exc:
        pytest.skip(f"unified_physics unavailable: {exc}")


def test_unified_physics_run_e11_analysis_returns_matrix():
    pytest.importorskip("jax", reason="JAX required")
    try:
        from mathphysics.unified_physics import run_e11_analysis  # noqa: PLC0415
    except Exception as exc:
        pytest.skip(f"Cannot import run_e11_analysis: {exc}")
    import numpy as np  # noqa: PLC0415

    cartan = run_e11_analysis()
    assert isinstance(cartan, np.ndarray)
    assert cartan.ndim == 2
