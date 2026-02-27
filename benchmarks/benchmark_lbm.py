"""Benchmark comparing NumPy vs JAX implementation of LBM."""

import time
import numpy as np
import jax
from mathphysics.quantum_lattice_boltzmann import QuantumLatticeBoltzmann, LBMParameters
from mathphysics.accelerated_lbm import AcceleratedLBM


def benchmark():
    # Setup parameters
    nx, ny = 128, 128
    timesteps = 100
    params = LBMParameters(nx=nx, ny=ny, timesteps=timesteps)

    print(f"Benchmarking LBM on {nx}x{ny} grid for {timesteps} steps")
    print(f"JAX Devices: {jax.devices()}")

    # 1. NumPy Benchmark
    print("\nRunning NumPy implementation...")
    cpu_sim = QuantumLatticeBoltzmann(params)
    start_cpu = time.time()
    cpu_sim.run_simulation(timesteps)
    end_cpu = time.time()
    cpu_time = end_cpu - start_cpu
    print(f"NumPy Time: {cpu_time:.4f}s ({timesteps / cpu_time:.2f} steps/s)")

    # 2. JAX Benchmark
    print("\nRunning JAX implementation...")
    jax_sim = AcceleratedLBM(params)

    # Warm-up (JIT compilation)
    print("Warming up JIT...")
    key = jax.random.PRNGKey(0)
    jax_sim.step(key)

    start_jax = time.time()
    jax_sim.run(timesteps)
    end_jax = time.time()
    jax_time = end_jax - start_jax
    print(f"JAX Time: {jax_time:.4f}s ({timesteps / jax_time:.2f} steps/s)")

    speedup = cpu_time / jax_time
    print(f"\nSpeedup: {speedup:.2f}x")


if __name__ == "__main__":
    benchmark()
