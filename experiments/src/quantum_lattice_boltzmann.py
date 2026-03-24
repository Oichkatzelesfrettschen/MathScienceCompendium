"""Quantum Lattice Boltzmann Method with E7/E8 Harmonic Scaffolds.

This module implements a complete D2Q9 Lattice Boltzmann Method (LBM) simulation
framework enhanced with quantum-inspired modifications and initialized using
E7/E8 exceptional Lie algebra harmonic patterns from the Genesis Framework.

Mathematical Foundation:
- D2Q9 lattice: 2D grid with 9 velocity directions
- BGK collision operator with quantum coherence coupling
- E7 (126 roots + zero) and E8 (240 roots) harmonic initialization
- Zero-point energy (ZPE) modulated relaxation dynamics
- Symmetry-preserving boundary conditions

Physical Modeling:
- Fluid dynamics on 2D lattice
- Harmonic scaffold from exceptional Lie algebras
- Quantum coherence field evolution
- Fractal self-similarity patterns
- Energy conservation monitoring

References:
- Succi, "The Lattice Boltzmann Equation" (2018)
- Chen & Doolen, "Lattice Boltzmann Method" (1998)
- Genesis Framework specifications (2025)
"""

from __future__ import annotations
from typing import List, Tuple, Dict, Any, Optional, Callable, Union
import numpy as np
from dataclasses import dataclass, field
from scipy.special import jv, erf
from scipy.ndimage import convolve
import json
from pathlib import Path
from enum import Enum
import warnings
import time

# Import Genesis harmonics and E7/E8 modules
try:
    from genesis_harmonics import (
        GenesisHarmonics, MaterialType, MaterialProperties,
        PHI, PHI_INV, SQRT_PHI, HBAR, C, KB
    )
    from e7_root_system import E7RootSystem, E7Properties
except ImportError:
    warnings.warn("Genesis harmonics or E7 modules not found. Using fallback values.")
    PHI = (1 + np.sqrt(5)) / 2
    PHI_INV = 1 / PHI
    SQRT_PHI = np.sqrt(PHI)

# D2Q9 Lattice Constants
C_LATTICE = 1.0  # Lattice speed
CS = C_LATTICE / np.sqrt(3)  # Speed of sound
CS2 = CS * CS  # Speed of sound squared
CS4 = CS2 * CS2  # Fourth power

# D2Q9 Velocity Directions
# Ordering: rest, E, N, W, S, NE, NW, SW, SE
VELOCITIES = np.array([
    [0, 0],   # 0: rest
    [1, 0],   # 1: East
    [0, 1],   # 2: North
    [-1, 0],  # 3: West
    [0, -1],  # 4: South
    [1, 1],   # 5: NE
    [-1, 1],  # 6: NW
    [-1, -1], # 7: SW
    [1, -1]   # 8: SE
], dtype=np.float64)

# D2Q9 Weights
WEIGHTS = np.array([
    4.0/9.0,   # rest
    1.0/9.0,   # E
    1.0/9.0,   # N
    1.0/9.0,   # W
    1.0/9.0,   # S
    1.0/36.0,  # NE
    1.0/36.0,  # NW
    1.0/36.0,  # SW
    1.0/36.0   # SE
], dtype=np.float64)

# Opposite directions for bounce-back
OPPOSITE = np.array([0, 3, 4, 1, 2, 7, 8, 5, 6], dtype=np.int32)

# Boundary condition types
class BoundaryType(Enum):
    """Supported boundary conditions."""
    PERIODIC = "periodic"
    BOUNCE_BACK = "bounce_back"
    SYMMETRY_PRESERVING = "symmetry_preserving"
    OPEN = "open"


@dataclass
class LBMParameters:
    """Parameters for Lattice Boltzmann simulation."""

    # Grid parameters
    nx: int = 128  # Grid width
    ny: int = 128  # Grid height

    # Physical parameters
    tau: float = 0.8  # Relaxation time (must be > 0.5 for stability)
    viscosity: float = None  # Kinematic viscosity (computed from tau)
    reynolds: float = 100.0  # Reynolds number

    # Quantum parameters
    zpe_coupling: float = 0.1  # ZPE field coupling strength
    coherence_decay: float = 0.01  # Coherence decay rate
    quantum_tau_modulation: bool = True  # Enable quantum tau modulation

    # Harmonic parameters
    num_harmonics: int = 127  # Number of E7 harmonic layers
    harmonic_amplitude: float = 0.01  # Initial harmonic amplitude (reduced for stability)
    golden_ratio_scaling: bool = True  # Use golden ratio in harmonics

    # Simulation parameters
    timesteps: int = 1000  # Total simulation steps
    snapshot_interval: int = 250  # Save snapshots every N steps

    # Boundary conditions
    boundary_type: BoundaryType = BoundaryType.SYMMETRY_PRESERVING

    def __post_init__(self):
        """Compute derived parameters."""
        if self.viscosity is None:
            self.viscosity = CS2 * (self.tau - 0.5)
        else:
            # Recompute tau from viscosity if provided
            self.tau = self.viscosity / CS2 + 0.5

        # Stability check
        if self.tau <= 0.5:
            raise ValueError(f"Relaxation time tau={self.tau} must be > 0.5 for stability")

        # Maximum stable tau
        if self.tau > 2.0:
            warnings.warn(f"Large tau={self.tau} may cause numerical issues")


@dataclass
class LBMState:
    """State variables for LBM simulation."""

    # Distribution functions
    f: np.ndarray  # Shape: (nx, ny, 9) - distribution functions
    f_eq: np.ndarray  # Equilibrium distribution

    # Macroscopic variables
    density: np.ndarray  # Shape: (nx, ny) - fluid density
    velocity: np.ndarray  # Shape: (nx, ny, 2) - velocity field
    pressure: np.ndarray  # Shape: (nx, ny) - pressure field

    # Quantum fields
    coherence: np.ndarray  # Shape: (nx, ny) - quantum coherence field
    zpe_field: np.ndarray  # Shape: (nx, ny) - ZPE modulation field

    # Derived fields
    vorticity: np.ndarray  # Shape: (nx, ny) - vorticity
    energy: np.ndarray  # Shape: (nx, ny) - kinetic energy density

    # Harmonic components
    harmonic_coefficients: np.ndarray  # Shape: (num_harmonics,) - harmonic amplitudes

    # Simulation metadata
    time: float = 0.0
    iteration: int = 0
    total_mass: float = 0.0
    total_energy: float = 0.0

    def update_macroscopic(self):
        """Update macroscopic variables from distribution functions."""
        # Density: sum of all distributions
        self.density = np.sum(self.f, axis=2)

        # Ensure positive density
        self.density = np.maximum(self.density, 1e-10)

        # Momentum: weighted sum
        for i in range(2):  # x, y components
            self.velocity[..., i] = np.sum(
                self.f * VELOCITIES[:, i], axis=2
            ) / self.density

        # Limit velocity for stability
        u_mag = np.sqrt(np.sum(self.velocity**2, axis=2))
        u_max = 0.3 * CS  # Mach number limit
        scaling = np.where(u_mag > u_max, u_max / (u_mag + 1e-10), 1.0)
        self.velocity *= scaling[..., np.newaxis]

        # Pressure (ideal gas approximation)
        self.pressure = CS2 * self.density

        # Vorticity (curl of velocity)
        dvx_dy = np.gradient(self.velocity[..., 0], axis=0)
        dvy_dx = np.gradient(self.velocity[..., 1], axis=1)
        self.vorticity = dvy_dx - dvx_dy

        # Kinetic energy density
        speed_squared = np.sum(self.velocity**2, axis=2)
        self.energy = 0.5 * self.density * speed_squared

        # Conservation quantities
        self.total_mass = np.sum(self.density)
        self.total_energy = np.sum(self.energy)


class QuantumLatticeBoltzmann:
    """Quantum-enhanced D2Q9 Lattice Boltzmann simulation."""

    def __init__(self, params: LBMParameters):
        """Initialize the quantum LBM simulation.

        Args:
            params: Simulation parameters
        """
        self.params = params
        self.state = None
        self.genesis = None
        self.e7_system = None
        self.e8_roots = None
        self.snapshots = []

        # Initialize modules if available
        self._initialize_modules()

        # Setup simulation
        self._initialize_state()

    def _initialize_modules(self):
        """Initialize Genesis harmonics and E7/E8 systems."""
        try:
            # Initialize Genesis harmonics with correct parameters
            self.genesis = GenesisHarmonics(
                num_layers=self.params.num_harmonics,  # Corrected parameter name
                base_frequency=1e12,  # 1 THz base frequency
                fractal_alpha=1.5,
                zpe_beta=self.params.zpe_coupling,
                use_e8=False  # Use E7 by default
            )

            # Initialize E7 root system
            self.e7_system = E7RootSystem()
            self.e7_system.generate_roots()

            # Generate E8 roots (simplified - full implementation would import E8 module)
            self._generate_e8_roots()

        except Exception as e:
            warnings.warn(f"Module initialization failed: {e}")
            self.genesis = None
            self.e7_system = None

    def _generate_e8_roots(self):
        """Generate E8 root system (240 roots)."""
        # E8 roots in 8D space
        # This is a simplified version - full E8 would be more complex
        roots = []

        # Type 1: All permutations of (+/-1, +/-1, 0, 0, 0, 0, 0, 0) with even number of -1s
        # This gives 112 roots
        for positions in [(i, j) for i in range(8) for j in range(i+1, 8)]:
            base = np.zeros(8)
            for i in positions:
                for signs in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
                    if sum([s < 0 for s in signs]) % 2 == 0:  # Even number of -1s
                        vec = base.copy()
                        vec[positions[0]] = signs[0]
                        vec[positions[1]] = signs[1]
                        roots.append(vec)

        # Type 2: All permutations of (1/2, 1/2, ..., 1/2) with even number of minus signs
        # This gives 128 roots
        for num_neg in [0, 2, 4, 6, 8]:
            from itertools import combinations
            for neg_positions in combinations(range(8), num_neg):
                vec = np.ones(8) * 0.5
                for i in neg_positions:
                    vec[i] = -0.5
                roots.append(vec)

        self.e8_roots = np.array(roots[:240])  # Take first 240 for E8

    def _initialize_state(self):
        """Initialize simulation state with harmonic scaffold."""
        nx, ny = self.params.nx, self.params.ny

        # Create state arrays
        self.state = LBMState(
            f=np.zeros((nx, ny, 9), dtype=np.float64),
            f_eq=np.zeros((nx, ny, 9), dtype=np.float64),
            density=np.ones((nx, ny), dtype=np.float64),
            velocity=np.zeros((nx, ny, 2), dtype=np.float64),
            pressure=np.ones((nx, ny), dtype=np.float64) * CS2,
            coherence=np.ones((nx, ny), dtype=np.float64),
            zpe_field=np.ones((nx, ny), dtype=np.float64),
            vorticity=np.zeros((nx, ny), dtype=np.float64),
            energy=np.zeros((nx, ny), dtype=np.float64),
            harmonic_coefficients=np.zeros(self.params.num_harmonics, dtype=np.float64)
        )

        # Initialize with harmonic scaffold
        self._initialize_harmonic_scaffold()

        # Compute equilibrium distribution
        self._compute_equilibrium()

        # Set initial distribution to equilibrium
        self.state.f[:] = self.state.f_eq

        # Update macroscopic variables
        self.state.update_macroscopic()

    def _initialize_harmonic_scaffold(self):
        """Initialize density field with E7/E8 harmonic patterns."""
        nx, ny = self.params.nx, self.params.ny
        x = np.linspace(0, 2*np.pi, nx)
        y = np.linspace(0, 2*np.pi, ny)
        X, Y = np.meshgrid(x, y, indexing='ij')

        # Base density
        rho_0 = 1.0
        self.state.density[:] = rho_0

        # Add E7 harmonic layers (127 states including zero)
        if self.e7_system is not None and self.e7_system._roots is not None:
            roots = self.e7_system._roots[:126]  # First 126 roots

            for i, root in enumerate(roots):
                if i >= self.params.num_harmonics - 1:
                    break

                # Extract frequency components from root
                # Use first 2 components for 2D spatial frequencies
                if len(root) >= 2:
                    omega_x = np.abs(root[0]) * (i + 1)
                    omega_y = np.abs(root[1]) * (i + 1)
                else:
                    omega_x = (i + 1) * PHI
                    omega_y = (i + 1) * PHI_INV

                # Golden ratio modulation with decay
                if self.params.golden_ratio_scaling:
                    amplitude = self.params.harmonic_amplitude * (PHI_INV ** (i/10)) / (i + 1)
                else:
                    amplitude = self.params.harmonic_amplitude / ((i + 1) ** 2)

                # Limit frequency to prevent aliasing
                omega_x = np.minimum(omega_x, self.params.nx / 4)
                omega_y = np.minimum(omega_y, self.params.ny / 4)

                # Add harmonic layer with reduced amplitude
                harmonic = amplitude * np.sin(omega_x * X) * np.cos(omega_y * Y)

                # Add fractal modulation
                fractal_scale = 1.0 + 0.1 * np.sin(PHI * omega_x * X) * np.cos(PHI * omega_y * Y)
                harmonic *= fractal_scale

                self.state.density += harmonic
                self.state.harmonic_coefficients[i] = amplitude

        else:
            # Fallback: Use simple harmonic initialization
            for n in range(min(self.params.num_harmonics, 10)):
                omega_n = (n + 1) * PHI
                amplitude = self.params.harmonic_amplitude * (PHI_INV ** n)

                harmonic = amplitude * (
                    np.sin(omega_n * X) * np.cos(omega_n * Y) +
                    0.5 * np.sin(PHI * omega_n * X) * np.sin(PHI * omega_n * Y)
                )

                self.state.density += harmonic
                self.state.harmonic_coefficients[n] = amplitude

        # Add E8-inspired modulation if available
        if self.e8_roots is not None and len(self.e8_roots) > 0:
            # Use E8 roots for additional spatial modulation
            for i in range(min(5, len(self.e8_roots))):
                root = self.e8_roots[i]
                if len(root) >= 2:
                    k_x = np.abs(root[0]) * 2 * np.pi
                    k_y = np.abs(root[1]) * 2 * np.pi
                    modulation = 0.01 * np.cos(k_x * X + k_y * Y)
                    self.state.density += modulation

        # Initialize velocity field with very small perturbations
        self.state.velocity[..., 0] = 0.001 * np.sin(2 * X) * np.cos(2 * Y)
        self.state.velocity[..., 1] = -0.001 * np.cos(2 * X) * np.sin(2 * Y)

        # Initialize quantum fields
        self._initialize_quantum_fields()

    def _initialize_quantum_fields(self):
        """Initialize quantum coherence and ZPE fields."""
        nx, ny = self.params.nx, self.params.ny

        # Coherence field starts at maximum coherence
        self.state.coherence[:] = 1.0

        # Add spatial variation based on density gradients
        grad_x = np.gradient(self.state.density, axis=0)
        grad_y = np.gradient(self.state.density, axis=1)
        gradient_magnitude = np.sqrt(grad_x**2 + grad_y**2)

        # Coherence is reduced in regions of high gradients
        self.state.coherence *= np.exp(-0.1 * gradient_magnitude)

        # ZPE field modulation
        if self.genesis is not None and hasattr(self.genesis, 'zpe_beta'):
            # Use Genesis-inspired ZPE field (simplified)
            x = np.linspace(0, 2*np.pi, nx)
            y = np.linspace(0, 2*np.pi, ny)
            X, Y = np.meshgrid(x, y, indexing='ij')

            # Create ZPE field with Genesis parameters
            zpe_modulation = self.genesis.zpe_beta * (
                np.sin(PHI * X) * np.cos(PHI * Y) +
                0.5 * np.cos(PHI_INV * X) * np.sin(PHI_INV * Y)
            )
            self.state.zpe_field = 1.0 + self.params.zpe_coupling * zpe_modulation
        else:
            # Fallback: Simple ZPE field
            x = np.linspace(0, 2*np.pi, nx)
            y = np.linspace(0, 2*np.pi, ny)
            X, Y = np.meshgrid(x, y, indexing='ij')

            # ZPE field with golden ratio frequencies
            self.state.zpe_field = 1.0 + self.params.zpe_coupling * (
                0.5 * np.sin(PHI * X) * np.cos(PHI * Y) +
                0.3 * np.cos(PHI_INV * X) * np.sin(PHI_INV * Y)
            )

        # Ensure ZPE field is positive
        self.state.zpe_field = np.maximum(self.state.zpe_field, 0.1)

    def _compute_equilibrium(self):
        """Compute equilibrium distribution function."""
        # Ensure density is positive
        rho = np.maximum(self.state.density, 1e-10)
        u = self.state.velocity

        # Limit velocity magnitude for stability
        u_mag = np.sqrt(u[..., 0]**2 + u[..., 1]**2)
        u_max = 0.3 * CS  # Mach number limit
        scaling = np.where(u_mag > u_max, u_max / (u_mag + 1e-10), 1.0)
        u = u * scaling[..., np.newaxis]

        # Speed squared
        usq = u[..., 0]**2 + u[..., 1]**2

        for i in range(9):
            # Velocity in lattice direction
            cu = VELOCITIES[i, 0] * u[..., 0] + VELOCITIES[i, 1] * u[..., 1]

            # Equilibrium distribution (Maxwell-Boltzmann)
            self.state.f_eq[..., i] = WEIGHTS[i] * rho * (
                1.0 +
                3.0 * cu / CS2 +
                4.5 * cu**2 / CS4 -
                1.5 * usq / CS2
            )

        # Ensure non-negative equilibrium
        self.state.f_eq = np.maximum(self.state.f_eq, 0)

    def _compute_tau_field(self) -> np.ndarray:
        """Compute spatially varying relaxation time with quantum modulation.

        Returns:
            Tau field array
        """
        if self.params.quantum_tau_modulation:
            # Quantum-modulated tau
            tau_field = self.params.tau * self.state.zpe_field

            # Add coherence coupling
            tau_field *= (1.0 + 0.1 * self.state.coherence)

            # Ensure stability (tau > 0.5)
            tau_field = np.maximum(tau_field, 0.51)

            return tau_field
        else:
            # Uniform tau
            return np.full_like(self.state.density, self.params.tau)

    def collision_step(self):
        """Perform BGK collision with quantum modifications."""
        # Compute equilibrium
        self._compute_equilibrium()

        # Get spatially varying tau
        tau_field = self._compute_tau_field()

        # BGK collision: f = f - (f - f_eq) / tau
        for i in range(9):
            self.state.f[..., i] -= (
                self.state.f[..., i] - self.state.f_eq[..., i]
            ) / tau_field

        # Apply quantum coherence decay
        coherence_factor = np.exp(-self.params.coherence_decay)
        self.state.coherence *= coherence_factor

        # Add quantum fluctuations (small noise term)
        if self.params.zpe_coupling > 0:
            noise_amplitude = 0.0001 * self.params.zpe_coupling  # Reduced noise
            noise = np.random.normal(0, noise_amplitude, self.state.f.shape)
            self.state.f += noise * self.state.coherence[..., np.newaxis]

        # Ensure non-negative distributions (stability)
        self.state.f = np.maximum(self.state.f, 0)

    def streaming_step(self):
        """Stream distribution functions to neighboring lattice sites."""
        f_temp = self.state.f.copy()

        for i in range(9):
            # Get velocity vector
            cx = int(VELOCITIES[i, 0])
            cy = int(VELOCITIES[i, 1])

            # Stream to neighboring site
            self.state.f[:, :, i] = np.roll(
                np.roll(f_temp[:, :, i], cx, axis=0),
                cy, axis=1
            )

    def apply_boundary_conditions(self):
        """Apply boundary conditions based on configuration."""
        if self.params.boundary_type == BoundaryType.PERIODIC:
            # Periodic boundaries handled by np.roll in streaming
            pass

        elif self.params.boundary_type == BoundaryType.BOUNCE_BACK:
            # Bounce-back at walls
            # Left wall (x=0)
            self.state.f[0, :, [1, 5, 8]] = self.state.f[0, :, [3, 7, 6]]
            # Right wall (x=nx-1)
            self.state.f[-1, :, [3, 6, 7]] = self.state.f[-1, :, [1, 8, 5]]
            # Bottom wall (y=0)
            self.state.f[:, 0, [2, 5, 6]] = self.state.f[:, 0, [4, 7, 8]]
            # Top wall (y=ny-1)
            self.state.f[:, -1, [4, 7, 8]] = self.state.f[:, -1, [2, 6, 5]]

        elif self.params.boundary_type == BoundaryType.SYMMETRY_PRESERVING:
            # E7/E8 symmetry-preserving boundaries
            self._apply_symmetry_preserving_bc()

        elif self.params.boundary_type == BoundaryType.OPEN:
            # Open boundaries (zero gradient)
            # Left/right
            self.state.f[0, :, :] = self.state.f[1, :, :]
            self.state.f[-1, :, :] = self.state.f[-2, :, :]
            # Top/bottom
            self.state.f[:, 0, :] = self.state.f[:, 1, :]
            self.state.f[:, -1, :] = self.state.f[:, -2, :]

    def _apply_symmetry_preserving_bc(self):
        """Apply E7/E8 symmetry-preserving boundary conditions."""
        # Use modular arithmetic to preserve symmetry
        nx, ny = self.params.nx, self.params.ny

        # Apply reflection with phase shift based on E7 structure
        if self.e7_system is not None:
            # Use E7 Weyl group reflection
            # This is a simplified version - full implementation would use Weyl group

            # Left boundary
            phase = np.exp(2j * np.pi * PHI_INV)
            self.state.f[0, :, [1, 5, 8]] = (
                self.state.f[1, :, [3, 7, 6]] * np.real(phase)
            )

            # Right boundary
            self.state.f[-1, :, [3, 6, 7]] = (
                self.state.f[-2, :, [1, 8, 5]] * np.real(phase)
            )

            # Bottom boundary
            self.state.f[:, 0, [2, 5, 6]] = (
                self.state.f[:, 1, [4, 7, 8]] * np.real(phase)
            )

            # Top boundary
            self.state.f[:, -1, [4, 7, 8]] = (
                self.state.f[:, -2, [2, 6, 5]] * np.real(phase)
            )
        else:
            # Fallback to modified bounce-back
            self.params.boundary_type = BoundaryType.BOUNCE_BACK
            self.apply_boundary_conditions()
            self.params.boundary_type = BoundaryType.SYMMETRY_PRESERVING

    def evolve_quantum_fields(self):
        """Evolve quantum coherence and ZPE fields."""
        dt = 1.0  # Lattice time unit

        # Coherence evolution with diffusion
        laplacian = np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]]) / 4.0
        coherence_diffusion = convolve(self.state.coherence, laplacian, mode='wrap')

        self.state.coherence += dt * (
            0.01 * coherence_diffusion -
            self.params.coherence_decay * self.state.coherence
        )

        # Maintain coherence bounds [0, 1]
        self.state.coherence = np.clip(self.state.coherence, 0, 1)

        # ZPE field evolution
        if self.genesis is not None:
            # Use Genesis dynamics
            # This would involve full Genesis evolution - simplified here
            zpe_evolution = -0.001 * (self.state.zpe_field - 1.0)
            self.state.zpe_field += dt * zpe_evolution
        else:
            # Simple relaxation dynamics
            target_zpe = 1.0 + self.params.zpe_coupling * np.sin(
                0.1 * self.state.iteration * PHI_INV
            )
            self.state.zpe_field += 0.01 * (target_zpe - self.state.zpe_field)

        # Ensure ZPE remains positive
        self.state.zpe_field = np.maximum(self.state.zpe_field, 0.1)

    def step(self):
        """Perform one complete LBM time step."""
        # 1. Collision step (relaxation)
        self.collision_step()

        # 2. Streaming step (propagation)
        self.streaming_step()

        # 3. Boundary conditions
        self.apply_boundary_conditions()

        # 4. Update macroscopic variables
        self.state.update_macroscopic()

        # 5. Evolve quantum fields
        self.evolve_quantum_fields()

        # 6. Update time and iteration
        self.state.time += 1.0
        self.state.iteration += 1

    def run_simulation(self, timesteps: Optional[int] = None) -> List[Dict]:
        """Run the complete simulation.

        Args:
            timesteps: Number of steps to run (default from params)

        Returns:
            List of snapshots
        """
        if timesteps is None:
            timesteps = self.params.timesteps

        print(f"Starting Quantum LBM simulation")
        print(f"Grid: {self.params.nx}x{self.params.ny}")
        print(f"Timesteps: {timesteps}")
        print(f"Tau: {self.params.tau:.3f}")
        print(f"Reynolds: {self.params.reynolds:.1f}")

        # Save initial state
        self.save_snapshot()

        # Time evolution
        start_time = time.time()

        for t in range(timesteps):
            # Perform time step
            self.step()

            # Save snapshots at intervals
            if (t + 1) % self.params.snapshot_interval == 0:
                self.save_snapshot()

                # Progress report
                elapsed = time.time() - start_time
                steps_per_sec = (t + 1) / elapsed
                print(f"Step {t+1}/{timesteps} - "
                      f"Speed: {steps_per_sec:.1f} steps/s - "
                      f"Mass: {self.state.total_mass:.6f} - "
                      f"Energy: {self.state.total_energy:.6f}")

        # Final snapshot
        if timesteps % self.params.snapshot_interval != 0:
            self.save_snapshot()

        print(f"Simulation complete in {time.time() - start_time:.2f} seconds")
        return self.snapshots

    def save_snapshot(self) -> Dict:
        """Save current state as snapshot.

        Returns:
            Snapshot dictionary
        """
        snapshot = {
            'time': float(self.state.time),
            'iteration': int(self.state.iteration),
            'density': self.state.density.tolist(),
            'velocity': self.state.velocity.tolist(),
            'pressure': self.state.pressure.tolist(),
            'vorticity': self.state.vorticity.tolist(),
            'energy': self.state.energy.tolist(),
            'coherence': self.state.coherence.tolist(),
            'zpe_field': self.state.zpe_field.tolist(),
            'total_mass': float(self.state.total_mass),
            'total_energy': float(self.state.total_energy),
            'harmonic_coefficients': self.state.harmonic_coefficients.tolist()
        }

        self.snapshots.append(snapshot)
        return snapshot

    def export_results(self, filepath: Union[str, Path]) -> None:
        """Export simulation results to JSON file.

        Args:
            filepath: Output file path
        """
        filepath = Path(filepath)

        # Prepare export data
        export_data = {
            'parameters': {
                'nx': self.params.nx,
                'ny': self.params.ny,
                'tau': self.params.tau,
                'viscosity': self.params.viscosity,
                'reynolds': self.params.reynolds,
                'timesteps': self.params.timesteps,
                'zpe_coupling': self.params.zpe_coupling,
                'coherence_decay': self.params.coherence_decay,
                'num_harmonics': self.params.num_harmonics,
                'boundary_type': self.params.boundary_type.value
            },
            'lattice_constants': {
                'c_lattice': C_LATTICE,
                'cs': CS,
                'velocities': VELOCITIES.tolist(),
                'weights': WEIGHTS.tolist()
            },
            'snapshots': self.snapshots
        }

        # Write JSON file
        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)

        print(f"Results exported to {filepath}")

    def validate_conservation(self) -> Dict[str, float]:
        """Validate conservation laws.

        Returns:
            Dictionary of conservation metrics
        """
        if len(self.snapshots) < 2:
            return {}

        initial = self.snapshots[0]
        final = self.snapshots[-1]

        # Mass conservation
        initial_mass = initial['total_mass']
        final_mass = final['total_mass']
        mass_error = abs(final_mass - initial_mass) / initial_mass

        # Energy conservation (approximate due to dissipation)
        initial_energy = initial['total_energy']
        final_energy = final['total_energy']
        energy_change = abs(final_energy - initial_energy) / (initial_energy + 1e-10)

        # Coherence decay
        initial_coherence = np.mean(initial['coherence'])
        final_coherence = np.mean(final['coherence'])
        coherence_decay = 1.0 - final_coherence / initial_coherence

        return {
            'mass_conservation_error': mass_error,
            'energy_change_fraction': energy_change,
            'coherence_decay_fraction': coherence_decay,
            'mass_conserved': mass_error < 1e-6,
            'energy_bounded': energy_change < 0.5
        }


def create_demo_simulation() -> QuantumLatticeBoltzmann:
    """Create a demonstration simulation with E7/E8 harmonic initialization.

    Returns:
        Configured QuantumLatticeBoltzmann instance
    """
    # Setup parameters (conservative for stability)
    params = LBMParameters(
        nx=64,
        ny=64,
        tau=1.2,  # Higher tau for stability
        reynolds=10.0,  # Lower Reynolds for stability
        zpe_coupling=0.01,  # Reduced coupling
        coherence_decay=0.005,
        quantum_tau_modulation=False,  # Disable for stability
        num_harmonics=10,  # Fewer harmonics initially
        harmonic_amplitude=0.002,  # Very small amplitude
        golden_ratio_scaling=True,
        timesteps=100,
        snapshot_interval=25,
        boundary_type=BoundaryType.PERIODIC  # Simpler BC
    )

    # Create simulation
    sim = QuantumLatticeBoltzmann(params)

    print("Demo simulation created:")
    print(f"- Grid size: {params.nx}x{params.ny}")
    print(f"- E7 harmonic layers: {params.num_harmonics}")
    print(f"- Quantum coupling: {params.zpe_coupling}")
    print(f"- Boundary: {params.boundary_type.value}")

    return sim


def run_validation_tests() -> Dict[str, Any]:
    """Run validation tests on the implementation.

    Returns:
        Test results dictionary
    """
    print("Running validation tests...")
    results = {}

    # Test 1: Small grid stability
    print("Test 1: Small grid stability")
    params = LBMParameters(nx=32, ny=32, timesteps=100, snapshot_interval=50)
    sim = QuantumLatticeBoltzmann(params)
    snapshots = sim.run_simulation()
    conservation = sim.validate_conservation()
    results['small_grid'] = {
        'completed': True,
        'snapshots': len(snapshots),
        'conservation': conservation
    }

    # Test 2: Harmonic initialization
    print("Test 2: Harmonic initialization")
    params = LBMParameters(
        nx=64, ny=64,
        num_harmonics=10,
        harmonic_amplitude=0.2,
        timesteps=50
    )
    sim = QuantumLatticeBoltzmann(params)
    initial_density = sim.state.density.copy()

    # Check harmonic content
    fft_density = np.fft.fft2(initial_density)
    spectral_power = np.abs(fft_density)**2

    results['harmonic_init'] = {
        'mean_density': float(np.mean(initial_density)),
        'std_density': float(np.std(initial_density)),
        'spectral_peak': float(np.max(spectral_power)),
        'num_harmonics': int(np.sum(sim.state.harmonic_coefficients > 0))
    }

    # Test 3: Boundary conditions
    print("Test 3: Boundary conditions")
    for bc_type in [BoundaryType.PERIODIC, BoundaryType.BOUNCE_BACK]:
        params = LBMParameters(
            nx=32, ny=32,
            boundary_type=bc_type,
            timesteps=20
        )
        sim = QuantumLatticeBoltzmann(params)
        sim.run_simulation()

        results[f'boundary_{bc_type.value}'] = {
            'completed': True,
            'final_mass': float(sim.state.total_mass)
        }

    # Test 4: Quantum field evolution
    print("Test 4: Quantum field evolution")
    params = LBMParameters(
        nx=32, ny=32,
        zpe_coupling=0.2,
        coherence_decay=0.05,
        timesteps=50
    )
    sim = QuantumLatticeBoltzmann(params)
    initial_coherence = sim.state.coherence.copy()
    sim.run_simulation()
    final_coherence = sim.state.coherence

    results['quantum_fields'] = {
        'initial_coherence_mean': float(np.mean(initial_coherence)),
        'final_coherence_mean': float(np.mean(final_coherence)),
        'zpe_variation': float(np.std(sim.state.zpe_field))
    }

    print("Validation tests complete")
    return results


if __name__ == "__main__":
    """Main execution for testing and demonstration."""

    print("=" * 60)
    print("Quantum Lattice Boltzmann with E7/E8 Harmonic Scaffolds")
    print("=" * 60)

    # Create and run demo simulation
    demo_sim = create_demo_simulation()

    print("\nRunning simulation...")
    snapshots = demo_sim.run_simulation()

    # Validate conservation
    print("\nValidating conservation laws...")
    conservation = demo_sim.validate_conservation()
    for key, value in conservation.items():
        print(f"  {key}: {value}")

    # Export results
    output_path = Path("quantum_lbm_results.json")
    demo_sim.export_results(output_path)

    # Run validation tests
    print("\n" + "=" * 60)
    test_results = run_validation_tests()

    print("\nTest Results Summary:")
    for test_name, test_data in test_results.items():
        print(f"\n{test_name}:")
        for key, value in test_data.items():
            print(f"  {key}: {value}")

    print("\n" + "=" * 60)
    print("Quantum LBM implementation complete!")
    print(f"Results saved to: {output_path}")