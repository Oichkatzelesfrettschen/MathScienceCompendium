"""Lattice Boltzmann Method with an E7 root-indexed density scaffold.

Module for D2Q9 LBM simulation with auxiliary arrays and an E7 root-indexed
initialization pattern.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass
from enum import Enum
from typing import Any

import numpy as np

from .diagnostics import calculate_vorticity


# Import core modules
try:
    from .algebras.roots import E7RootSystem

    HAS_E7 = True
except ImportError:
    HAS_E7 = False

try:
    from .genesis_harmonics import GenesisHarmonics

    HAS_GENESIS = True
except ImportError:
    HAS_GENESIS = False

# Constants
PHI = (1.0 + np.sqrt(5.0)) / 2.0
PHI_INV = 1.0 / PHI
C_LATTICE = 1.0
CS = C_LATTICE / np.sqrt(3)
CS2 = CS * CS
CS4 = CS2 * CS2

# D2Q9 Velocity Directions
VELOCITIES = np.array(
    [[0, 0], [1, 0], [0, 1], [-1, 0], [0, -1], [1, 1], [-1, 1], [-1, -1], [1, -1]], dtype=np.float64
)

# D2Q9 Weights
WEIGHTS = np.array(
    [4.0 / 9, 1.0 / 9, 1.0 / 9, 1.0 / 9, 1.0 / 9, 1.0 / 36, 1.0 / 36, 1.0 / 36, 1.0 / 36],
    dtype=np.float64,
)

OPPOSITE = np.array([0, 3, 4, 1, 2, 7, 8, 5, 6], dtype=np.int32)


class BoundaryType(Enum):
    PERIODIC = "periodic"
    BOUNCE_BACK = "bounce_back"
    SYMMETRY_PRESERVING = "symmetry_preserving"
    OPEN = "open"


@dataclass
class LBMParameters:
    """Parameters for Lattice Boltzmann simulation."""

    nx: int = 128
    ny: int = 128
    tau: float = 0.8
    viscosity: float | None = None
    reynolds: float = 100.0
    zpe_coupling: float = 0.1
    coherence_decay: float = 0.01
    quantum_tau_modulation: bool = True
    num_harmonics: int = 127
    harmonic_amplitude: float = 0.01
    golden_ratio_scaling: bool = True
    random_seed: int = 0
    timesteps: int = 1000
    snapshot_interval: int = 250
    boundary_type: BoundaryType = BoundaryType.SYMMETRY_PRESERVING

    def __post_init__(self) -> None:
        if self.viscosity is None:
            self.viscosity = CS2 * (self.tau - 0.5)
        else:
            self.tau = self.viscosity / CS2 + 0.5
        if self.tau <= 0.5:
            raise ValueError(f"Relaxation time tau={self.tau} must be > 0.5")


@dataclass
class LBMState:
    """State variables for LBM simulation."""

    f: np.ndarray
    f_eq: np.ndarray
    density: np.ndarray
    velocity: np.ndarray
    pressure: np.ndarray
    coherence: np.ndarray
    zpe_field: np.ndarray
    vorticity: np.ndarray
    energy: np.ndarray
    harmonic_coefficients: np.ndarray
    time: float = 0.0
    iteration: int = 0
    total_mass: float = 0.0
    total_energy: float = 0.0

    def update_macroscopic(self) -> None:
        self.density = np.sum(self.f, axis=2)
        self.density = np.maximum(self.density, 1e-10)
        for i in range(2):
            self.velocity[..., i] = np.sum(self.f * VELOCITIES[:, i], axis=2) / self.density
        u_mag = np.sqrt(np.sum(self.velocity**2, axis=2))
        u_max = 0.3 * CS
        scaling = np.where(u_mag > u_max, u_max / (u_mag + 1e-10), 1.0)
        self.velocity *= scaling[..., np.newaxis]
        self.pressure = CS2 * self.density
        self.vorticity = calculate_vorticity(self.velocity)
        speed_squared = np.sum(self.velocity**2, axis=2)
        self.energy = 0.5 * self.density * speed_squared
        self.total_mass = np.sum(self.density)
        self.total_energy = np.sum(self.energy)


class QuantumLatticeBoltzmann:
    """Quantum-enhanced D2Q9 Lattice Boltzmann simulation."""

    def __init__(self, params: LBMParameters) -> None:
        self.params = params
        self.state: LBMState
        self.genesis: GenesisHarmonics | None = None
        self.e7_system: E7RootSystem | None = None
        self.snapshots: list[dict[str, Any]] = []
        self._initialize_modules()
        self._initialize_state()

    def _initialize_modules(self) -> None:
        try:
            if HAS_GENESIS:
                self.genesis = GenesisHarmonics(
                    num_layers=self.params.num_harmonics,
                    base_frequency=1e12,
                    fractal_alpha=1.5,
                    zpe_beta=self.params.zpe_coupling,
                )
            if HAS_E7:
                self.e7_system = E7RootSystem()
                self.e7_system.generate_roots()
        except Exception as e:
            warnings.warn(f"Module initialization failed: {e}", stacklevel=2)

    def _initialize_state(self) -> None:
        nx, ny = self.params.nx, self.params.ny
        self.state = LBMState(
            f=np.zeros((nx, ny, 9)),
            f_eq=np.zeros((nx, ny, 9)),
            density=np.ones((nx, ny)),
            velocity=np.zeros((nx, ny, 2)),
            pressure=np.ones((nx, ny)) * CS2,
            coherence=np.ones((nx, ny)),
            zpe_field=np.ones((nx, ny)),
            vorticity=np.zeros((nx, ny)),
            energy=np.zeros((nx, ny)),
            harmonic_coefficients=np.zeros(self.params.num_harmonics),
        )
        self._initialize_harmonic_scaffold()
        self._compute_equilibrium()
        self.state.f[:] = self.state.f_eq
        self.state.update_macroscopic()
        self._initial_mass = float(self.state.total_mass)

    def _initialize_harmonic_scaffold(self) -> None:
        nx, ny = self.params.nx, self.params.ny
        x, y = np.linspace(0, 2 * np.pi, nx), np.linspace(0, 2 * np.pi, ny)
        X, Y = np.meshgrid(x, y, indexing="ij")
        self.state.density[:] = 1.0
        if self.e7_system and self.e7_system._roots is not None:
            for i, root in enumerate(self.e7_system._roots[: self.params.num_harmonics]):
                omega_x, omega_y = np.abs(root[0]) * (i + 1), np.abs(root[1]) * (i + 1)
                amplitude = self.params.harmonic_amplitude * (PHI_INV ** (i / 10)) / (i + 1)
                self.state.density += amplitude * np.sin(omega_x * X) * np.cos(omega_y * Y)
        else:
            for n in range(min(self.params.num_harmonics, 10)):
                omega = (n + 1) * PHI
                self.state.density += (
                    self.params.harmonic_amplitude * (PHI_INV**n) * np.sin(omega * X)
                )
        self._initialize_quantum_fields()

    def _initialize_quantum_fields(self) -> None:
        self.state.coherence[:] = 1.0
        generator = np.random.default_rng(self.params.random_seed)
        phase = generator.random()
        self.state.zpe_field[:] = 1.0 + self.params.zpe_coupling * np.sin(PHI * phase)

    def _compute_equilibrium(self) -> None:
        rho, u = self.state.density, self.state.velocity
        usq = np.sum(u**2, axis=2)
        for i in range(9):
            cu = VELOCITIES[i, 0] * u[..., 0] + VELOCITIES[i, 1] * u[..., 1]
            self.state.f_eq[..., i] = (
                WEIGHTS[i] * rho * (1.0 + cu / CS2 + 0.5 * cu**2 / CS4 - 0.5 * usq / CS2)
            )

    def step(self) -> None:
        self._compute_equilibrium()
        tau = self.params.tau
        for i in range(9):
            self.state.f[..., i] -= (self.state.f[..., i] - self.state.f_eq[..., i]) / tau
        f_temp = self.state.f.copy()
        for i in range(9):
            self.state.f[:, :, i] = np.roll(
                np.roll(f_temp[:, :, i], int(VELOCITIES[i, 0]), axis=0),
                int(VELOCITIES[i, 1]),
                axis=1,
            )
        self.state.update_macroscopic()
        self.state.iteration += 1

    def run_simulation(self, timesteps: int | None = None) -> LBMState:
        """Run the simulation for a given number of timesteps."""
        steps = timesteps if timesteps is not None else self.params.timesteps
        for _ in range(steps):
            self.step()
        return self.state

    def validate_conservation(self, relative_tolerance: float = 1e-10) -> dict[str, Any]:
        """Measure mass conservation against the initialized state."""
        if relative_tolerance <= 0.0:
            raise ValueError("relative_tolerance must be positive")

        current_mass = float(self.state.total_mass)
        relative_mass_error = abs(current_mass - self._initial_mass) / self._initial_mass
        mass_conserved = bool(
            np.isfinite(relative_mass_error) and relative_mass_error <= relative_tolerance
        )
        return {
            "mass_conserved": mass_conserved,
            "relative_mass_error": relative_mass_error,
            "relative_tolerance": relative_tolerance,
            "initial_mass": self._initial_mass,
            "current_mass": current_mass,
        }
