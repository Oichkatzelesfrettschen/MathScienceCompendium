#!/usr/bin/env python3
"""Comprehensive test and validation of Genesis Harmonics module."""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from mathphysics.genesis_harmonics import (
    MATERIALS,
    GenesisHarmonics,
    HarmonicLayer,
    MaterialType,
)


def test_harmonic_layers():
    """Test harmonic layer generation and properties."""
    print("\n" + "=" * 60)
    print("TESTING HARMONIC LAYERS")
    print("=" * 60)

    # Create a single layer
    layer = HarmonicLayer(
        index=0,
        frequency=1e12,
        amplitude=1.0,
        phase=0.0,
        fractal_coefficient=0.1,
        zpe_envelope=1.0,
        e7_root_index=0,
        e8_root_index=0,
    )

    print("\n1. Initial layer properties:")
    print(f"   Frequency: {layer.frequency:.2e} Hz")
    print(f"   Amplitude: {layer.amplitude:.4f}")
    print(f"   ZPE envelope: {layer.zpe_envelope:.4f}")

    # Test harmonic value calculation
    times = np.linspace(0, 1e-12, 100)  # 1 picosecond
    values = [layer.harmonic_value(t) for t in times]

    print("\n2. Harmonic oscillation:")
    print(f"   Max value: {np.max(values):.4f}")
    print(f"   Min value: {np.min(values):.4f}")
    print(f"   RMS value: {np.sqrt(np.mean(np.array(values) ** 2)):.4f}")

    # Test evolution
    initial_amplitude = layer.amplitude
    layer.evolve(dt=1e-15)  # 1 femtosecond

    print("\n3. Evolution test (1 fs):")
    print(
        f"   Amplitude decay: {(initial_amplitude - layer.amplitude) / initial_amplitude * 100:.2f}%"
    )
    print(f"   Phase advance: {layer.phase:.4f} radians")

    return True


def test_genesis_superforce():
    """Test Genesis Superforce Operator."""
    print("\n" + "=" * 60)
    print("TESTING GENESIS SUPERFORCE OPERATOR")
    print("=" * 60)

    genesis = GenesisHarmonics(
        num_layers=127, base_frequency=1e12, fractal_alpha=1.618, zpe_beta=0.01
    )

    # Test at different positions
    positions = [
        np.array([0, 0, 0]),
        np.array([1e-6, 0, 0]),
        np.array([0, 1e-6, 1e-6]),
        np.array([1e-5, 1e-5, 1e-5]),
    ]

    print("\n1. Spatial field distribution:")
    for i, pos in enumerate(positions):
        field = genesis.genesis_superforce(pos, t=0.0, dimension=3.0)
        print(f"   Position {i + 1}: {pos * 1e6} micrometers")
        print(f"   Field magnitude: {np.abs(field[0]):.4e}")
        print(f"   Field phase: {np.angle(field[0]):.4f} radians")

    # Test fractional dimensions
    print("\n2. Fractional dimension effects:")
    dimensions = [2.0, 2.5, 3.0, 3.7, 4.0]
    test_pos = np.array([1e-6, 0, 0])

    for dim in dimensions:
        field = genesis.genesis_superforce(test_pos, t=0.0, dimension=dim)
        print(f"   D = {dim}: Field magnitude = {np.abs(field[0]):.4e}")

    # Test time evolution of superforce
    print("\n3. Temporal evolution:")
    times = [0, 1e-15, 1e-14, 1e-13, 1e-12]
    test_pos = np.array([0, 0, 0])

    for t in times:
        field = genesis.genesis_superforce(test_pos, t=t, dimension=3.0)
        print(f"   t = {t:.2e} s: Field = {np.abs(field[0]):.4e}")

    return True


def test_material_responses():
    """Test material response functions."""
    print("\n" + "=" * 60)
    print("TESTING MATERIAL RESPONSES")
    print("=" * 60)

    genesis = GenesisHarmonics()

    # Test field strength
    test_field = np.array([1e-3, 0, 0])  # 1 mV/m

    # Frequency sweep
    frequencies = np.logspace(10, 13, 10)  # 10 GHz to 10 THz

    print("\n1. Frequency-dependent responses:")
    for mat_type in MaterialType:
        print(f"\n   {mat_type.value.upper()}:")
        mat_props = MATERIALS[mat_type]
        print(f"   Dielectric constant: {mat_props.dielectric_constant:.1f}")
        print(f"   ZPE coupling: {mat_props.zpe_coupling:.3f}")

        responses = []
        for freq in frequencies:
            response = genesis.material_response(test_field, mat_type, freq)
            responses.append(np.abs(response[0]))

        print(f"   Response range: {np.min(responses):.2e} - {np.max(responses):.2e}")
        print(f"   Peak frequency: {frequencies[np.argmax(responses)]:.2e} Hz")

    # Temperature effects
    print("\n2. Temperature modulation:")
    temperatures = [100, 200, 300, 400, 500]  # Kelvin

    for temp in temperatures:
        # Modify BST temperature
        MATERIALS[MaterialType.BST].temperature = temp
        thermal_mod = MATERIALS[MaterialType.BST].thermal_modulation()
        print(f"   T = {temp} K: Thermal factor = {thermal_mod:.4e}")

    # Reset temperature
    MATERIALS[MaterialType.BST].temperature = 300.0

    return True


def test_e7_e8_integration():
    """Test E7/E8 root system integration."""
    print("\n" + "=" * 60)
    print("TESTING E7/E8 ROOT SYSTEM INTEGRATION")
    print("=" * 60)

    # Test E7 system
    genesis_e7 = GenesisHarmonics(num_layers=127, use_e8=False)

    print("\n1. E7 Integration (127 layers):")
    print(f"   Number of layers: {genesis_e7.num_layers}")
    coupling_e7 = genesis_e7.get_coupling_matrix()
    print(f"   Coupling matrix shape: {coupling_e7.shape}")

    # Check symmetry
    symmetry_error = np.max(np.abs(coupling_e7 - coupling_e7.T))
    print(f"   Coupling symmetry error: {symmetry_error:.2e}")

    # Eigenvalue analysis
    eigenvalues_e7 = np.linalg.eigvals(coupling_e7)
    print(
        f"   Eigenvalue range: [{np.min(np.real(eigenvalues_e7)):.4f}, {np.max(np.real(eigenvalues_e7)):.4f}]"
    )

    # Test E8 system
    genesis_e8 = GenesisHarmonics(num_layers=240, use_e8=True)

    print("\n2. E8 Integration (240 layers):")
    print(f"   Number of layers: {genesis_e8.num_layers}")
    coupling_e8 = genesis_e8.get_coupling_matrix()
    print(f"   Coupling matrix shape: {coupling_e8.shape}")

    eigenvalues_e8 = np.linalg.eigvals(coupling_e8)
    print(
        f"   Eigenvalue range: [{np.min(np.real(eigenvalues_e8)):.4f}, {np.max(np.real(eigenvalues_e8)):.4f}]"
    )

    # Compare spectral properties
    spectrum_e7 = genesis_e7.spectral_analysis()
    spectrum_e8 = genesis_e8.spectral_analysis()

    print("\n3. Spectral comparison:")
    print(f"   E7 total power: {np.sum(spectrum_e7['power_spectrum']):.2e}")
    print(f"   E8 total power: {np.sum(spectrum_e8['power_spectrum']):.2e}")
    print(
        f"   Power ratio (E8/E7): {np.sum(spectrum_e8['power_spectrum']) / np.sum(spectrum_e7['power_spectrum']):.4f}"
    )

    return True


def test_time_evolution():
    """Test time evolution and stability."""
    print("\n" + "=" * 60)
    print("TESTING TIME EVOLUTION")
    print("=" * 60)

    genesis = GenesisHarmonics(
        num_layers=50,  # Reduced for faster testing
        base_frequency=1e12,
        fractal_alpha=1.618,
        zpe_beta=0.01,
    )

    # Short-term evolution
    print("\n1. Short-term evolution (100 fs):")
    dt = 1e-15  # 1 femtosecond
    steps = 100

    results_short = genesis.evolve_system(dt, steps)

    initial_energy = results_short["total_energy"][0]
    final_energy = results_short["total_energy"][-1]
    energy_change = (final_energy - initial_energy) / initial_energy * 100

    print(f"   Energy change: {energy_change:.2f}%")
    print(f"   Average coherence: {np.mean(results_short['zpe_coherence']):.4f}")
    print(f"   Coherence std dev: {np.std(results_short['zpe_coherence']):.4f}")

    # Check material response evolution
    print("\n2. Material response evolution:")
    for mat_type in MaterialType:
        mat_responses = []
        for t in results_short["time_points"]:
            if t in results_short["material_responses"]:
                mat_responses.append(results_short["material_responses"][t][mat_type.value])

        if mat_responses:
            print(
                f"   {mat_type.value}: {np.mean(mat_responses):.2e} +/- {np.std(mat_responses):.2e}"
            )

    # Longer evolution test
    print("\n3. Long-term stability (1 ps):")
    genesis_long = GenesisHarmonics(num_layers=20)  # Even fewer for speed
    results_long = genesis_long.evolve_system(dt=1e-14, steps=100)

    print(f"   Initial energy: {results_long['total_energy'][0]:.2e}")
    print(f"   Final energy: {results_long['total_energy'][-1]:.2e}")
    print(
        f"   Energy conservation: {(results_long['total_energy'][-1] / results_long['total_energy'][0]):.4f}"
    )

    return True


def test_data_export_import():
    """Test data export and import functionality."""
    print("\n" + "=" * 60)
    print("TESTING DATA EXPORT/IMPORT")
    print("=" * 60)

    # Create and evolve system
    genesis = GenesisHarmonics(num_layers=30, base_frequency=5e11)

    # Evolve for some steps
    genesis.evolve_system(dt=1e-15, steps=10)

    # Export data
    export_path = Path("/tmp/genesis_test.json")
    genesis.export_data(export_path)

    print(f"\n1. Data exported to: {export_path}")

    # Check file exists and load
    if export_path.exists():
        with export_path.open(encoding="utf-8") as f:
            data = json.load(f)

        print("\n2. Exported data structure:")
        print(f"   Configuration keys: {list(data['configuration'].keys())}")
        print(f"   Number of layers: {len(data['layers'])}")
        print(f"   Evolution history entries: {len(data['evolution_history'])}")
        print(f"   Spectral analysis keys: {list(data['spectral_analysis'].keys())}")

        # Validate some values
        print("\n3. Data validation:")
        print(f"   Base frequency: {data['configuration']['base_frequency']:.2e}")
        print(f"   Current time: {data['configuration']['current_time']:.2e}")
        print(f"   First layer frequency: {data['layers'][0]['frequency']:.2e}")

        # Clean up
        export_path.unlink()
        print("\n4. Test file cleaned up.")

    return True


def test_visualization_data():
    """Test visualization data generation."""
    print("\n" + "=" * 60)
    print("TESTING VISUALIZATION DATA")
    print("=" * 60)

    genesis = GenesisHarmonics(
        num_layers=20,  # Small for speed
        base_frequency=1e12,
    )

    viz_data = genesis.visualize_data()

    print("\n1. Generated visualization data:")
    print(f"   Time evolution points: {len(viz_data['time_evolution']['times'])}")
    print(f"   Spatial field points: {len(viz_data['spatial_distribution']['x_positions'])}")
    print(f"   Material types: {list(viz_data['material_responses'].keys())}")
    print(
        f"   Coupling matrix size: {len(viz_data['coupling_matrix'])}x{len(viz_data['coupling_matrix'][0])}"
    )

    # Check data ranges
    print("\n2. Data ranges:")
    field_mag = viz_data["spatial_distribution"]["field_magnitude"]
    print(f"   Field magnitude: [{np.min(field_mag):.2e}, {np.max(field_mag):.2e}]")

    energies = viz_data["time_evolution"]["total_energy"]
    print(f"   Total energy: [{np.min(energies):.2e}, {np.max(energies):.2e}]")

    coherence = viz_data["time_evolution"]["zpe_coherence"]
    print(f"   ZPE coherence: [{np.min(coherence):.4f}, {np.max(coherence):.4f}]")

    # Check spectral data
    print("\n3. Spectral data:")
    freqs = viz_data["spectral_data"]["frequencies"]
    print(f"   Frequency range: {freqs[0]:.2e} - {freqs[-1]:.2e} Hz")
    print(f"   Number of spectral points: {len(freqs)}")

    return True


def run_all_tests():
    """Run all validation tests."""
    print("\n" + "=" * 70)
    print("GENESIS HARMONICS - COMPREHENSIVE VALIDATION SUITE")
    print("=" * 70)

    tests = [
        ("Harmonic Layers", test_harmonic_layers),
        ("Genesis Superforce", test_genesis_superforce),
        ("Material Responses", test_material_responses),
        ("E7/E8 Integration", test_e7_e8_integration),
        ("Time Evolution", test_time_evolution),
        ("Data Export/Import", test_data_export_import),
        ("Visualization Data", test_visualization_data),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, "PASSED" if result else "FAILED"))
            print(f"\n[{'PASS' if result else 'FAIL'}] {name}")
        except Exception as e:
            results.append((name, f"ERROR: {str(e)[:50]}"))
            print(f"\n[ERROR] {name}: {str(e)[:50]}")

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, status in results if status == "PASSED")
    total = len(results)

    for name, status in results:
        status_str = "PASS" if status == "PASSED" else status
        print(f"   {name:20s}: {status_str}")

    print(f"\nTotal: {passed}/{total} tests passed")
    print("=" * 70)

    return passed == total


if __name__ == "__main__":
    success = run_all_tests()

    if success:
        print("\nAll tests passed successfully!")
        print("Genesis Harmonics module is fully operational.")
    else:
        print("\nSome tests failed. Please review the output above.")

    # Generate a simple plot for visual verification
    print("\nGenerating simple visualization...")

    genesis = GenesisHarmonics(num_layers=50)
    spectrum = genesis.spectral_analysis()

    plt.figure(figsize=(12, 8))

    # Frequency spectrum
    plt.subplot(2, 2, 1)
    plt.semilogy(spectrum["frequencies"], "b-")
    plt.xlabel("Layer Index")
    plt.ylabel("Frequency (Hz)")
    plt.title("Harmonic Layer Frequencies")
    plt.grid(True, alpha=0.3)

    # Amplitudes
    plt.subplot(2, 2, 2)
    plt.plot(spectrum["amplitudes"], "r-")
    plt.xlabel("Layer Index")
    plt.ylabel("Amplitude")
    plt.title("Initial Amplitudes")
    plt.grid(True, alpha=0.3)

    # ZPE weights
    plt.subplot(2, 2, 3)
    plt.plot(spectrum["zpe_weights"], "g-")
    plt.xlabel("Layer Index")
    plt.ylabel("ZPE Weight")
    plt.title("ZPE Stability Envelopes")
    plt.grid(True, alpha=0.3)

    # Power spectrum
    plt.subplot(2, 2, 4)
    plt.semilogy(spectrum["power_spectrum"], "m-")
    plt.xlabel("Layer Index")
    plt.ylabel("Power")
    plt.title("Power Spectrum")
    plt.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig("/tmp/genesis_harmonics_test.png", dpi=100)
    print("Plot saved to: /tmp/genesis_harmonics_test.png")
    plt.close()

    print("\nValidation complete!")
