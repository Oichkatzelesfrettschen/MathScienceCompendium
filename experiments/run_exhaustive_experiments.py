"""Exhaustive Experimental Suite for Mathematical Physics Compendium.

Runs high-resolution accelerated simulations, saves data to Parquet,
and performs deep analysis of harmonic interactions.
"""

import os
import time
import jax
import jax.numpy as jnp
import numpy as np
import pandas as pd
from mathphysics.quantum_lattice_boltzmann import LBMParameters
from mathphysics.accelerated_lbm import AcceleratedLBM
from mathphysics.data_handler import DataHandler
from mathphysics.config import Config
import matplotlib.pyplot as plt

def run_high_res_experiment():
    # 1. Setup high-resolution parameters
    nx, ny = 512, 512
    timesteps = 500
    params = LBMParameters(
        nx=nx, ny=ny, 
        timesteps=timesteps,
        tau=0.6, # Lower tau for higher Reynolds
        harmonic_amplitude=0.05
    )
    
    print(f"Starting High-Res Experiment: {nx}x{ny} grid, {timesteps} steps")
    print(f"Device: {jax.devices()[0]}")
    
    # 2. Initialize Accelerated Simulation
    sim = AcceleratedLBM(params)
    
    # 3. Execution Loop with Data Pipeline
    key = jax.random.PRNGKey(42)
    start_time = time.time()
    
    for i in range(timesteps):
        key, subkey = jax.random.split(key)
        density, velocity = sim.step(subkey)
        
        # Save state every 100 steps
        if (i + 1) % 100 == 0:
            print(f"Step {i+1}/{timesteps} - Saving state...")
            DataHandler.save_simulation_state(
                np.array(density), 
                np.array(velocity), 
                i + 1, 
                filename_prefix="highres_lbm"
            )
            
    end_time = time.time()
    print(f"Simulation complete in {end_time - start_time:.2f}s")
    
    # 4. Final Analysis: Vorticity Spectral Power
    # Compute vorticity from final velocity
    u = np.array(velocity)
    dvx_dy = np.gradient(u[..., 0], axis=0)
    dvy_dx = np.gradient(u[..., 1], axis=1)
    vorticity = dvy_dx - dvx_dy
    
    # FFT Analysis
    vort_fft = np.fft.fft2(vorticity)
    psd = np.abs(vort_fft)**2
    freqs = np.fft.fftfreq(nx)
    
    # Save PSD plot
    plt.figure(figsize=(10, 6))
    plt.imshow(np.log10(np.fft.fftshift(psd) + 1e-10))
    plt.colorbar(label='log10(PSD)')
    plt.title(f'Vorticity Power Spectral Density (E7 Harmonics)')
    
    fig_path = Config.get_figure_path("vorticity_psd_highres.png")
    plt.savefig(fig_path)
    print(f"Analysis figure saved to: {fig_path}")
    
    # Save final vorticity map
    plt.figure(figsize=(10, 8))
    plt.imshow(vorticity, cmap='RdBu_r')
    plt.colorbar(label='Vorticity')
    plt.title(f'Final Vorticity Field ({nx}x{ny})')
    vort_fig_path = Config.get_figure_path("vorticity_map_highres.png")
    plt.savefig(vort_fig_path)
    print(f"Vorticity map saved to: {vort_fig_path}")

if __name__ == "__main__":
    run_high_res_experiment()
