"""JAX-Accelerated Quantum Lattice Boltzmann Method.

This module provides a high-performance implementation of the Quantum LBM
framework using JAX for GPU acceleration (via CUDA) and JIT compilation.

Target Architecture: SM89 (CUDA 12)
"""

from __future__ import annotations
import jax
import jax.numpy as jnp
from .quantum_lattice_boltzmann import LBMParameters, WEIGHTS, VELOCITIES, OPPOSITE

class AcceleratedLBM:
    """JAX-accelerated Lattice Boltzmann simulation."""

    def __init__(self, params: LBMParameters) -> None:
        self.params = params
        self.nx = params.nx
        self.ny = params.ny
        
        # Move constants to JAX arrays
        self.weights = jnp.array(WEIGHTS)
        self.velocities = jnp.array(VELOCITIES)
        self.opposite = jnp.array(OPPOSITE)
        self.cs2 = 1.0 / 3.0
        self.cs4 = self.cs2 * self.cs2

        # Initialize state on device
        self._init_state()
        
        # Bind JIT functions
        self.step_jit = jax.jit(self._step_internal)

    def _init_state(self):
        """Initialize the distribution functions and fields."""
        from .quantum_lattice_boltzmann import QuantumLatticeBoltzmann
        cpu_sim = QuantumLatticeBoltzmann(self.params)
        
        self.f = jnp.array(cpu_sim.state.f)
        self.coherence = jnp.array(cpu_sim.state.coherence)
        self.zpe_field = jnp.array(cpu_sim.state.zpe_field)
        self.iteration = 0

    @staticmethod
    def get_equilibrium(density, velocity, weights, velocities, cs2, cs4):
        usq = jnp.sum(velocity**2, axis=-1)
        # Reshape for broadcasting
        # velocities: (9, 2), velocity: (nx, ny, 2)
        # cu = sum(v_i * u) -> (nx, ny, 9)
        cu = jnp.tensordot(velocity, velocities, axes=([2], [1]))
        
        # equilibrium formula: w * rho * (1 + 3cu + 4.5cu^2 - 1.5usq)
        # Usurping weighted sum for vectorized expansion
        eq = weights * density[..., jnp.newaxis] * (
            1.0 + 3.0 * cu + 4.5 * cu**2 - 1.5 * usq[..., jnp.newaxis]
        )
        return eq

    @staticmethod
    def update_macroscopic(f, velocities):
        density = jnp.sum(f, axis=-1)
        density = jnp.maximum(density, 1e-10)
        # Momentum sum: (nx, ny, 9) * (9, 2) -> (nx, ny, 2)
        momentum = jnp.tensordot(f, velocities, axes=([2], [0]))
        velocity = momentum / density[..., jnp.newaxis]
        return density, velocity

    def _step_internal(self, f, coherence, key):
        """The core JIT-compiled LBM step."""
        density, velocity = self.update_macroscopic(f, self.velocities)
        f_eq = self.get_equilibrium(density, velocity, self.weights, self.velocities, self.cs2, self.cs4)
        
        # Collision
        tau_field = self.params.tau * self.zpe_field * (1.0 + 0.1 * coherence)
        tau_field = jnp.maximum(tau_field, 0.51)
        f_post_collision = f - (f - f_eq) / tau_field[..., jnp.newaxis]
        
        # Quantum noise
        noise = jax.random.normal(key, f.shape) * 0.00001 * coherence[..., jnp.newaxis]
        f_post_collision = jnp.maximum(f_post_collision + noise, 0.0)
        
        # Streaming
        f_next = jnp.stack([
            f_post_collision[..., 0],
            jnp.roll(f_post_collision[..., 1], 1, axis=0),
            jnp.roll(f_post_collision[..., 2], 1, axis=1),
            jnp.roll(f_post_collision[..., 3], -1, axis=0),
            jnp.roll(f_post_collision[..., 4], -1, axis=1),
            jnp.roll(jnp.roll(f_post_collision[..., 5], 1, axis=0), 1, axis=1),
            jnp.roll(jnp.roll(f_post_collision[..., 6], -1, axis=0), 1, axis=1),
            jnp.roll(jnp.roll(f_post_collision[..., 7], -1, axis=0), -1, axis=1),
            jnp.roll(jnp.roll(f_post_collision[..., 8], 1, axis=0), -1, axis=1)
        ], axis=-1)
        
        coherence_next = coherence * jnp.exp(-self.params.coherence_decay)
        
        return f_next, coherence_next

    def step(self, key):
        self.f, self.coherence = self.step_jit(self.f, self.coherence, key)
        self.iteration += 1
        return self.update_macroscopic(self.f, self.velocities)

    def run(self, num_steps: int):
        print(f"[JAX] Starting {num_steps} steps on GPU...")
        def body_fun(carry, _):
            f, coherence, key = carry
            f_next, coherence_next = self.step_jit(f, coherence, key)
            new_key = jax.random.split(key)[0]
            return (f_next, coherence_next, new_key), None

        (self.f, self.coherence, _), _ = jax.lax.scan(
            body_fun, (self.f, self.coherence, jax.random.PRNGKey(0)), None, length=num_steps
        )
        self.iteration += num_steps
        print(f"[JAX] Completed {num_steps} steps. Iteration: {self.iteration}")