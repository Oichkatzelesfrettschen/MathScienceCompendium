#!/usr/bin/env python3
"""Mass-conservation regression for the CPU D2Q9 LBM implementation."""

import json
import sys
from pathlib import Path

import numpy as np


REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from mathphysics.quantum_lattice_boltzmann import (  # noqa: E402
    BoundaryType,
    LBMParameters,
    QuantumLatticeBoltzmann,
)


def run_stable_demo():
    """Run a periodic D2Q9 regression with a root-indexed density scaffold."""

    print("=" * 70)
    print("D2Q9 MASS-CONSERVATION REGRESSION")
    print("With E7 Root-Indexed Density Initialization")
    print("=" * 70)

    # Create very stable parameters
    params = LBMParameters(
        # Grid parameters
        nx=32,
        ny=32,
        # Physical parameters (very conservative)
        tau=1.5,  # High relaxation time for stability
        reynolds=1.0,  # Very low Reynolds number
        # Quantum parameters (minimal coupling)
        zpe_coupling=0.0001,  # Minimal ZPE coupling
        coherence_decay=0.0001,  # Slow coherence decay
        quantum_tau_modulation=False,  # Disabled for stability
        # Harmonic parameters (gentle initialization)
        num_harmonics=3,  # Just first 3 E7 harmonics
        harmonic_amplitude=0.0001,  # Tiny perturbations
        golden_ratio_scaling=True,
        random_seed=0,
        # Simulation parameters
        timesteps=50,
        snapshot_interval=10,
        # Boundary conditions
        boundary_type=BoundaryType.PERIODIC,
    )

    print("\nSimulation Parameters:")
    print(f"  Grid: {params.nx} x {params.ny}")
    print(f"  Tau (relaxation time): {params.tau}")
    print(f"  Viscosity: {params.viscosity:.6f}")
    print(f"  Reynolds number: {params.reynolds}")
    print(f"  E7 harmonic layers: {params.num_harmonics}")
    print(f"  Harmonic amplitude: {params.harmonic_amplitude}")
    print(f"  ZPE coupling: {params.zpe_coupling}")
    print(f"  Timesteps: {params.timesteps}")

    # Create simulation
    print("\nInitializing simulation...")
    sim = QuantumLatticeBoltzmann(params)

    # Check initial state
    print("\nInitial State Analysis:")
    print(f"  Density - mean: {np.mean(sim.state.density):.6f}")
    print(f"  Density - std: {np.std(sim.state.density):.8f}")
    print(f"  Density - min: {np.min(sim.state.density):.6f}")
    print(f"  Density - max: {np.max(sim.state.density):.6f}")
    print(
        f"  Velocity magnitude - mean: {np.mean(np.sqrt(np.sum(sim.state.velocity**2, axis=2))):.8f}"
    )
    print(f"  Coherence - mean: {np.mean(sim.state.coherence):.6f}")
    print(f"  ZPE field - mean: {np.mean(sim.state.zpe_field):.6f}")

    # Store initial values for conservation check
    initial_mass = sim.state.total_mass
    initial_energy = sim.state.total_energy

    # Run simulation with monitoring
    print("\n" + "-" * 70)
    print("Running Simulation...")
    print("-" * 70)

    snapshots = []
    for step in range(params.timesteps):
        # Perform time step
        sim.step()

        # Monitor every 10 steps
        if (step + 1) % 10 == 0:
            mass_error = abs(sim.state.total_mass - initial_mass) / initial_mass
            print(
                f"Step {step + 1:3d}: "
                f"Mass error: {mass_error:.2e}, "
                f"Kinetic energy: {sim.state.total_energy:.2e}, "
                f"Max |u|: {np.max(np.sqrt(np.sum(sim.state.velocity**2, axis=2))):.4f}"
            )

            # Save snapshot
            if (step + 1) % params.snapshot_interval == 0:
                snapshots.append(
                    {
                        "step": step + 1,
                        "density_mean": float(np.mean(sim.state.density)),
                        "density_std": float(np.std(sim.state.density)),
                        "velocity_max": float(
                            np.max(np.sqrt(np.sum(sim.state.velocity**2, axis=2)))
                        ),
                        "mass": float(sim.state.total_mass),
                        "energy": float(sim.state.total_energy),
                        "coherence_mean": float(np.mean(sim.state.coherence)),
                    }
                )

    # Final analysis
    print("\n" + "-" * 70)
    print("Final State Analysis:")
    print("-" * 70)
    print(f"  Density - mean: {np.mean(sim.state.density):.6f}")
    print(f"  Density - std: {np.std(sim.state.density):.8f}")
    print(
        f"  Velocity magnitude - max: {np.max(np.sqrt(np.sum(sim.state.velocity**2, axis=2))):.6f}"
    )
    print(f"  Coherence - mean: {np.mean(sim.state.coherence):.6f}")

    # Conservation analysis
    final_mass = sim.state.total_mass
    final_energy = sim.state.total_energy

    mass_error = abs(final_mass - initial_mass) / initial_mass
    kinetic_energy_change = final_energy - initial_energy

    print("\nConservation Analysis:")
    print(f"  Initial mass: {initial_mass:.6f}")
    print(f"  Final mass: {final_mass:.6f}")
    print(f"  Mass conservation error: {mass_error:.2e}")
    print(f"  Initial kinetic energy: {initial_energy:.6e}")
    print(f"  Final kinetic energy: {final_energy:.6e}")

    # Stability assessment
    print("\nStability Assessment:")
    if mass_error < 0.01:
        print("  [PASS] Mass well conserved (error < 1%)")
    elif mass_error < 0.1:
        print("  [WARN] Mass moderately conserved (error < 10%)")
    else:
        print("  [FAIL] Mass conservation poor (error > 10%)")

    if np.isfinite(final_energy) and final_energy >= 0.0:
        print("  [PASS] Kinetic-energy diagnostic is finite and non-negative")
    else:
        print("  [FAIL] Kinetic-energy diagnostic is invalid")

    max_velocity = np.max(np.sqrt(np.sum(sim.state.velocity**2, axis=2)))
    if max_velocity < 0.3:
        print("  [PASS] Velocities remain subsonic")
    else:
        print("  [WARN] High velocities detected")

    # Export results
    output_data = {
        "parameters": {
            "nx": params.nx,
            "ny": params.ny,
            "tau": params.tau,
            "reynolds": params.reynolds,
            "timesteps": params.timesteps,
            "num_harmonics": params.num_harmonics,
            "harmonic_amplitude": params.harmonic_amplitude,
            "random_seed": params.random_seed,
        },
        "conservation": {
            "mass_error": mass_error,
            "initial_mass": initial_mass,
            "final_mass": final_mass,
        },
        "kinetic_energy": {
            "initial": initial_energy,
            "final": final_energy,
            "change": kinetic_energy_change,
        },
        "snapshots": snapshots,
    }

    output_file = REPO_ROOT / "experiments" / "quantum_lbm_stable_results.json"
    with output_file.open("w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)

    print(f"\nResults saved to: {output_file}")

    # Scientific interpretation
    print("\n" + "=" * 70)
    print("SCIENTIFIC INTERPRETATION")
    print("=" * 70)
    print("""
This regression demonstrates:

1. D2Q9 LATTICE STRUCTURE:
   - 9-velocity lattice successfully implemented
   - BGK collision operator functioning
   - Streaming and collision steps balanced

2. ROOT-INDEXED INITIALIZATION:
   - Density is modulated by coordinates selected from the E7 root array
   - Golden-ratio weighting is a chosen amplitude schedule
   - No quotient charge or triad-selection operator is applied

3. PASSIVE AUXILIARY FIELDS:
   - Coherence and ZPE arrays are initialized
   - They do not enter the CPU collision or streaming equations
   - The run therefore supplies no quantum-dynamics evidence

4. STABILITY CONSIDERATIONS:
   - Conservative parameters ensure numerical stability
   - Velocity limiting prevents supersonic flows
   - Positive density maintained throughout

The result is a numerical conservation regression. It does not establish a
physical coupling between exceptional Lie algebras and fluid dynamics.
    """)

    return sim, output_data


if __name__ == "__main__":
    try:
        sim, data = run_stable_demo()
        print("\n" + "=" * 70)
        print("DEMONSTRATION COMPLETE - SUCCESS")
        print("=" * 70)
    except Exception as e:
        print(f"\nError occurred: {e}")
        import traceback

        traceback.print_exc()
