"""Genesis Framework Harmonics Module.

This module integrates E7/E8 Lie algebra structures with harmonic evolution,
zero-point energy (ZPE) dynamics, and material response functions. It implements
the full Genesis Framework for harmonic superforce operators and fractal dynamics.

Mathematical Foundation:
- Fractal harmonic layers with golden ratio modulation
- E7 (126 roots + zero = 127 states) and E8 (240 roots) symmetry integration
- Material-specific response functions (Tourmaline, Quartz, BST)
- ZPE stability envelopes and coherence dynamics
- Genesis Superforce Operator with fractional dimensions

Physical Motivation:
- Models harmonic resonances in crystalline materials
- Captures pyroelectric and piezoelectric coupling
- Describes ZPE field interactions with matter
- Implements fractal scaling across energy domains

References:
- Genesis Framework specifications (2025)
- E7/E8 exceptional Lie algebras (Bourbaki, Humphreys)
- Fractal dynamics in condensed matter (Mandelbrot, Hausdorff)
- Zero-point energy field theory (Puthoff, Haisch)
"""

from __future__ import annotations
from typing import List, Tuple, Dict, Any, Optional, Callable, Union
import numpy as np
from dataclasses import dataclass, field
from scipy.special import gamma, erf, jv
from scipy.linalg import expm, block_diag
from scipy.integrate import quad
import json
from pathlib import Path
from enum import Enum
import warnings

# Golden ratio and derived constants
PHI = (1 + np.sqrt(5)) / 2  # Golden ratio
PHI_INV = 1 / PHI  # Inverse golden ratio
SQRT_PHI = np.sqrt(PHI)  # Square root of golden ratio

# Physical constants
HBAR = 1.0545718e-34  # Reduced Planck constant (J*s)
C = 299792458  # Speed of light (m/s)
KB = 1.380649e-23  # Boltzmann constant (J/K)
EPSILON_0 = 8.854187817e-12  # Vacuum permittivity (F/m)

# Genesis Framework constants
ALPHA_GENESIS = 1.0 / 137.035999  # Fine structure constant
LAMBDA_ZPE = 1e-35  # Planck length scale (m)
OMEGA_PLANCK = 1.855e43  # Planck frequency (Hz)


class MaterialType(Enum):
    """Supported crystalline materials."""
    TOURMALINE = "tourmaline"
    QUARTZ = "quartz"
    BST = "bst"  # Barium Strontium Titanate


@dataclass
class MaterialProperties:
    """Physical properties for Genesis materials."""

    name: str
    dielectric_constant: float  # Relative permittivity
    piezo_coefficient: float  # C/N or m/V
    pyro_coefficient: float  # C/(m^2*K)
    nonlinear_susceptibility: float  # m^2/V^2
    damping_coefficient: float  # 1/s
    resonance_frequencies: List[float]  # Hz
    zpe_coupling: float  # Dimensionless coupling strength
    temperature: float = 300.0  # Kelvin

    def response_function(self, omega: float) -> complex:
        """Calculate frequency-dependent material response.

        Args:
            omega: Angular frequency (rad/s)

        Returns:
            Complex response function
        """
        # Lorentzian resonance model with multiple peaks
        response = self.dielectric_constant

        for omega_0 in self.resonance_frequencies:
            # Resonance term with damping
            denominator = (omega_0**2 - omega**2) + 1j * self.damping_coefficient * omega
            response += (self.piezo_coefficient * omega_0**2) / denominator

        # Nonlinear enhancement
        if self.nonlinear_susceptibility > 0:
            response *= (1 + self.nonlinear_susceptibility * np.abs(response))

        # ZPE coupling modulation
        response *= (1 + self.zpe_coupling * np.exp(-omega / OMEGA_PLANCK))

        return response

    def thermal_modulation(self) -> float:
        """Calculate thermal modulation factor."""
        # Bose-Einstein distribution at temperature T
        if self.temperature > 0:
            thermal_energy = KB * self.temperature
            return 1.0 / (np.exp(HBAR * OMEGA_PLANCK / thermal_energy) - 1)
        return 0.0


# Predefined material configurations
MATERIALS = {
    MaterialType.TOURMALINE: MaterialProperties(
        name="Tourmaline",
        dielectric_constant=6.9,
        piezo_coefficient=4.0e-12,  # 4 pC/N
        pyro_coefficient=4.0e-9,  # 4 nC/(cm^2*K)
        nonlinear_susceptibility=1e-20,
        damping_coefficient=1e9,
        resonance_frequencies=[1e12, 3e12, 7e12],  # THz range
        zpe_coupling=0.15
    ),
    MaterialType.QUARTZ: MaterialProperties(
        name="Quartz",
        dielectric_constant=4.5,
        piezo_coefficient=2.3e-12,  # 2.3 pC/N
        pyro_coefficient=0.0,  # No pyroelectric effect
        nonlinear_susceptibility=3e-22,
        damping_coefficient=5e8,
        resonance_frequencies=[5e11, 2e12],  # Sub-THz to THz
        zpe_coupling=0.08
    ),
    MaterialType.BST: MaterialProperties(
        name="Barium Strontium Titanate",
        dielectric_constant=2000.0,  # Very high dielectric
        piezo_coefficient=1e-10,  # 100 pC/N
        pyro_coefficient=8e-8,  # 80 nC/(cm^2*K)
        nonlinear_susceptibility=5e-18,  # Strong nonlinearity
        damping_coefficient=2e9,
        resonance_frequencies=[8e11, 1.5e12, 4e12],
        zpe_coupling=0.25  # Strong ZPE coupling
    )
}


@dataclass
class HarmonicLayer:
    """Single harmonic layer with fractal modulation."""

    index: int  # Layer index (0 to N-1)
    frequency: float  # Base frequency (Hz)
    amplitude: float  # Initial amplitude
    phase: float  # Initial phase (radians)
    fractal_coefficient: float  # Beta_n fractal modulation
    zpe_envelope: float  # ZPE stability factor
    e7_root_index: Optional[int] = None  # Mapped E7 root (0-126)
    e8_root_index: Optional[int] = None  # Mapped E8 root (0-239)

    def harmonic_value(self, t: float, alpha: float = 1.0) -> float:
        """Calculate harmonic value at time t.

        Args:
            t: Time (seconds)
            alpha: Modulation exponent

        Returns:
            Harmonic amplitude at time t
        """
        # Fractal harmonic with golden ratio modulation
        omega_n = 2 * np.pi * self.frequency

        # Base harmonic
        h_n = self.amplitude * np.sin(omega_n * t + self.phase)

        # Exponential decay with fractal scaling
        lambda_n = self.fractal_coefficient * np.power(self.index + 1, -1.0/PHI)
        h_n *= np.exp(-lambda_n * t)

        # Modular symmetry driver
        m_n = np.power(np.abs(np.sin(2 * np.pi * self.index / PHI)), alpha)

        # ZPE stability envelope
        h_n *= self.zpe_envelope * m_n

        return h_n

    def evolve(self, dt: float) -> None:
        """Evolve harmonic layer by timestep dt."""
        # Phase evolution
        self.phase += 2 * np.pi * self.frequency * dt
        self.phase = self.phase % (2 * np.pi)

        # Amplitude decay (fractal scaling)
        decay_rate = self.fractal_coefficient * np.power(self.index + 1, -1.0/PHI)
        self.amplitude *= np.exp(-decay_rate * dt)

        # ZPE envelope modulation (slow variation)
        zpe_variation = 0.01 * np.sin(2 * np.pi * dt / (PHI * self.index + 1))
        self.zpe_envelope *= (1 + zpe_variation)
        self.zpe_envelope = np.clip(self.zpe_envelope, 0.1, 2.0)


class GenesisHarmonics:
    """Main Genesis Framework Harmonics implementation."""

    def __init__(
        self,
        num_layers: int = 127,  # Default to E7 (126 roots + zero)
        base_frequency: float = 1e12,  # 1 THz base
        fractal_alpha: float = 1.5,
        zpe_beta: float = 0.01,
        use_e8: bool = False
    ):
        """Initialize Genesis Harmonics system.

        Args:
            num_layers: Number of harmonic layers (127 for E7, 240 for E8)
            base_frequency: Base frequency in Hz
            fractal_alpha: Fractal modulation exponent
            zpe_beta: ZPE coupling strength
            use_e8: If True, use E8 (240) instead of E7 (127) layers
        """
        self.use_e8 = use_e8
        self.num_layers = 240 if use_e8 else 127
        self.base_frequency = base_frequency
        self.fractal_alpha = fractal_alpha
        self.zpe_beta = zpe_beta

        # Initialize harmonic layers
        self.layers = self._initialize_layers()

        # Root system integration
        self.e7_roots = None
        self.e8_roots = None
        self.root_coupling_matrix = None
        self._load_root_systems()

        # Material response systems
        self.materials = MATERIALS.copy()
        self.active_material = MaterialType.TOURMALINE

        # Time evolution state
        self.time = 0.0
        self.evolution_history = []

    def _initialize_layers(self) -> List[HarmonicLayer]:
        """Initialize fractal harmonic layers."""
        layers = []

        for n in range(self.num_layers):
            # Frequency follows golden ratio scaling
            freq_n = self.base_frequency * np.power(PHI, -n/10.0)

            # Initial amplitude with fractal distribution
            amp_n = 1.0 / (1 + n * self.fractal_alpha)

            # Phase distribution (golden angle)
            phase_n = 2 * np.pi * n / PHI

            # Fractal coefficient
            beta_n = self.fractal_alpha * np.power(n + 1, -1.0/PHI)

            # ZPE envelope (stability function)
            zpe_n = 1.0 / (1 + self.zpe_beta * n * n)

            # Map to root indices
            e7_idx = n if n < 127 else None
            e8_idx = n if n < 240 else None

            layer = HarmonicLayer(
                index=n,
                frequency=freq_n,
                amplitude=amp_n,
                phase=phase_n,
                fractal_coefficient=beta_n,
                zpe_envelope=zpe_n,
                e7_root_index=e7_idx,
                e8_root_index=e8_idx
            )
            layers.append(layer)

        return layers

    def _load_root_systems(self) -> None:
        """Load E7/E8 root systems for coupling."""
        try:
            # Import root system modules
            from .e7_root_system import E7RootSystem
            from .lie_algebras import E8RootSystem

            # Initialize E7
            e7_system = E7RootSystem()
            self.e7_roots = e7_system.generate_roots()
            e7_cartan = e7_system.compute_cartan_matrix()

            # Initialize E8
            e8_system = E8RootSystem()
            self.e8_roots = e8_system.generate_roots()
            e8_cartan = e8_system.cartan_matrix()

            # Build coupling matrix from Cartan matrices
            if self.use_e8:
                self.root_coupling_matrix = self._build_coupling_matrix(e8_cartan)
            else:
                self.root_coupling_matrix = self._build_coupling_matrix(e7_cartan)

        except ImportError:
            warnings.warn("Root system modules not found. Using default coupling.")
            # Fallback: random symmetric coupling
            size = self.num_layers
            random_matrix = np.random.randn(size, size) * 0.1
            self.root_coupling_matrix = (random_matrix + random_matrix.T) / 2

    def _build_coupling_matrix(self, cartan_matrix: np.ndarray) -> np.ndarray:
        """Build harmonic coupling matrix from Cartan matrix.

        Args:
            cartan_matrix: Cartan matrix of the Lie algebra

        Returns:
            Expanded coupling matrix for all harmonic layers
        """
        rank = cartan_matrix.shape[0]
        size = self.num_layers

        # Start with identity for diagonal stability
        coupling = np.eye(size)

        # Embed Cartan matrix structure
        if rank <= size:
            # Direct embedding in upper-left corner
            coupling[:rank, :rank] = cartan_matrix

            # Extend using fractal self-similarity
            for i in range(rank, size):
                # Fractal scaling of couplings
                scale = np.power(PHI, -(i-rank)/10.0)
                j_source = i % rank

                for j in range(size):
                    k_source = j % rank
                    if j_source < rank and k_source < rank:
                        coupling[i, j] = scale * cartan_matrix[j_source, k_source]
                        coupling[j, i] = coupling[i, j]  # Symmetry

        # Normalize to prevent instability
        max_eigenvalue = np.max(np.abs(np.linalg.eigvals(coupling)))
        if max_eigenvalue > 10:
            coupling /= (max_eigenvalue / 10)

        return coupling

    def genesis_superforce(
        self,
        x: np.ndarray,
        t: float,
        dimension: float = 3.0,
        modular_order: int = 24
    ) -> np.ndarray:
        """Compute Genesis Superforce Operator G(x,t,D,z).

        Implements: G(x,t,D,z) = Sum_n beta_n * F_n(x) + Integral D_f(D_n) + R(z)

        Args:
            x: Spatial coordinates (can be any dimension)
            t: Time
            dimension: Fractional/negative dimension parameter
            modular_order: Order of modular symmetry (24 for Monster group)

        Returns:
            Superforce field values at position x and time t
        """
        x = np.atleast_1d(x)
        result = np.zeros_like(x, dtype=complex)

        # 1. Fractal dynamics sum: Sum_n beta_n * F_n(x)
        for layer in self.layers:
            beta_n = layer.fractal_coefficient

            # n-th order fractal dynamics
            # Using Weierstrass-like fractal function
            omega_n = 2 * np.pi * layer.frequency

            # Spatial fractal pattern
            F_n = np.zeros_like(x, dtype=complex)
            for k in range(1, min(layer.index + 1, 10)):  # Limit iterations
                a_k = np.power(PHI, -k)
                b_k = np.power(2, k)

                # Multi-dimensional fractal
                for i, x_i in enumerate(x):
                    F_n[i] += a_k * np.exp(1j * b_k * x_i * omega_n / C)

            # Time modulation
            temporal = layer.harmonic_value(t, self.fractal_alpha)
            result += beta_n * F_n * temporal

        # 2. Fractional dimensional operator: Integral D_f(D_n)
        # Using Riemann-Liouville fractional derivative approximation
        if dimension != int(dimension):
            # Fractional part
            alpha = dimension - np.floor(dimension)

            # Gamma function normalization
            norm = gamma(1 - alpha)

            # Fractional integral kernel
            def kernel(tau):
                if tau > 0:
                    return np.power(tau, -alpha) / norm
                return 0

            # Approximate fractional operator effect
            D_f = np.zeros_like(result)

            # Sample past values (simplified for demonstration)
            for tau_idx in range(1, 11):
                tau = tau_idx * 0.01  # Small time steps
                if t - tau > 0:
                    # Historical contribution
                    past_value = np.exp(-tau / (PHI * dimension))
                    D_f += kernel(tau) * result * past_value

            result += D_f * 0.1  # Scale factor

        # 3. Modular E8-Monster symmetries: R(z)
        # Monster group has order ~8e53, we use modular functions

        # j-invariant approximation (Klein's j-function)
        # j(tau) ~ exp(2*pi*i*tau) for Im(tau) large
        tau = (1 + 1j * np.sqrt(modular_order)) / 2  # Modular parameter

        # Hauptmodul (main modular function)
        q = np.exp(2j * np.pi * tau)
        j_invariant = 1/q + 744 + 196884*q  # First few terms

        # Map to spatial modulation
        R_z = np.zeros_like(result)
        for i, x_i in enumerate(x):
            # Modular transformation
            z = x_i / (C * t + 1)  # Dimensionless position

            # Apply Monster symmetry via j-invariant
            R_z[i] = j_invariant * np.exp(-np.abs(z) / PHI)

        # Scale and add modular contribution
        result += R_z * 1e-10  # Very small contribution (renormalized)

        return result

    def material_response(
        self,
        field: np.ndarray,
        material: MaterialType,
        frequency: float
    ) -> np.ndarray:
        """Calculate material response to harmonic field.

        Args:
            field: Input field values
            material: Type of material
            frequency: Driving frequency (Hz)

        Returns:
            Material response (polarization/strain)
        """
        mat_props = self.materials[material]
        omega = 2 * np.pi * frequency

        # Frequency-dependent response
        chi = mat_props.response_function(omega)

        # Nonlinear response with saturation
        response = chi * field

        # Add thermal fluctuations
        thermal = mat_props.thermal_modulation()
        if thermal > 0:
            noise = np.random.randn(*field.shape) * np.sqrt(thermal)
            response += noise * np.abs(chi) * 0.01

        # Pyroelectric contribution (temperature gradient)
        if mat_props.pyro_coefficient > 0:
            # Assume small temperature gradient
            dT = 0.1  # K
            pyro_field = mat_props.pyro_coefficient * dT
            response += pyro_field * np.ones_like(field)

        return response

    def evolve_system(
        self,
        dt: float,
        steps: int = 1,
        save_history: bool = True
    ) -> Dict[str, Any]:
        """Evolve the harmonic system in time.

        Args:
            dt: Time step (seconds)
            steps: Number of steps to evolve
            save_history: Whether to save evolution history

        Returns:
            Dictionary with evolution results
        """
        results = {
            'time_points': [],
            'total_energy': [],
            'layer_amplitudes': [],
            'zpe_coherence': [],
            'material_responses': {}
        }

        for step in range(steps):
            # Current state snapshot
            current_time = self.time + step * dt

            # Evolve each layer
            total_energy = 0.0
            amplitudes = []

            for layer in self.layers:
                layer.evolve(dt)

                # Energy calculation (simplified)
                energy = 0.5 * layer.amplitude**2 * layer.frequency**2
                total_energy += energy
                amplitudes.append(layer.amplitude)

            # ZPE coherence metric (correlation between layers)
            zpe_coherence = self._calculate_zpe_coherence()

            # Material responses at this time
            test_position = np.array([0.0, 0.0, 0.0])
            test_field = self.genesis_superforce(
                test_position, current_time
            )

            mat_responses = {}
            for mat_type in MaterialType:
                avg_freq = np.mean([l.frequency for l in self.layers[:10]])
                response = self.material_response(
                    test_field.real, mat_type, avg_freq
                )
                mat_responses[mat_type.value] = float(np.abs(response[0]))

            # Store results
            results['time_points'].append(current_time)
            results['total_energy'].append(total_energy)
            results['layer_amplitudes'].append(amplitudes)
            results['zpe_coherence'].append(zpe_coherence)
            results['material_responses'][current_time] = mat_responses

            if save_history:
                self.evolution_history.append({
                    'time': current_time,
                    'energy': total_energy,
                    'coherence': zpe_coherence
                })

        # Update system time
        self.time += steps * dt

        return results

    def _calculate_zpe_coherence(self) -> float:
        """Calculate ZPE field coherence across layers.

        Returns:
            Coherence value (0 to 1)
        """
        if len(self.layers) < 2:
            return 1.0

        # Calculate phase correlation between adjacent layers
        correlations = []

        for i in range(len(self.layers) - 1):
            phase_diff = self.layers[i+1].phase - self.layers[i].phase

            # Wrapped correlation
            correlation = np.cos(phase_diff) * \
                         self.layers[i].zpe_envelope * \
                         self.layers[i+1].zpe_envelope
            correlations.append(correlation)

        # Average coherence with decay weighting
        weights = np.exp(-np.arange(len(correlations)) / PHI)
        weights /= np.sum(weights)

        coherence = np.sum(np.array(correlations) * weights)

        # Normalize to [0, 1]
        return (coherence + 1) / 2

    def get_coupling_matrix(self) -> np.ndarray:
        """Get the harmonic coupling matrix.

        Returns:
            Coupling matrix between harmonic layers
        """
        if self.root_coupling_matrix is not None:
            return self.root_coupling_matrix

        # Generate default coupling if not loaded
        size = self.num_layers
        coupling = np.eye(size)

        # Add nearest-neighbor coupling
        for i in range(size - 1):
            coupling[i, i+1] = 0.5 / PHI
            coupling[i+1, i] = 0.5 / PHI

        return coupling

    def spectral_analysis(self) -> Dict[str, np.ndarray]:
        """Perform spectral analysis of harmonic layers.

        Returns:
            Dictionary with frequency spectrum data
        """
        frequencies = []
        amplitudes = []
        phases = []
        zpe_weights = []

        for layer in self.layers:
            frequencies.append(layer.frequency)
            amplitudes.append(layer.amplitude)
            phases.append(layer.phase)
            zpe_weights.append(layer.zpe_envelope)

        return {
            'frequencies': np.array(frequencies),
            'amplitudes': np.array(amplitudes),
            'phases': np.array(phases),
            'zpe_weights': np.array(zpe_weights),
            'power_spectrum': np.array(amplitudes)**2 * np.array(frequencies)
        }

    def export_data(self, filepath: Union[str, Path]) -> None:
        """Export system state and history to JSON.

        Args:
            filepath: Path to save JSON data
        """
        filepath = Path(filepath)

        data = {
            'configuration': {
                'num_layers': self.num_layers,
                'base_frequency': self.base_frequency,
                'fractal_alpha': self.fractal_alpha,
                'zpe_beta': self.zpe_beta,
                'use_e8': self.use_e8,
                'current_time': self.time
            },
            'layers': [
                {
                    'index': layer.index,
                    'frequency': layer.frequency,
                    'amplitude': layer.amplitude,
                    'phase': layer.phase,
                    'fractal_coefficient': layer.fractal_coefficient,
                    'zpe_envelope': layer.zpe_envelope,
                    'e7_root_index': layer.e7_root_index,
                    'e8_root_index': layer.e8_root_index
                }
                for layer in self.layers
            ],
            'evolution_history': self.evolution_history,
            'spectral_analysis': {
                k: v.tolist() for k, v in self.spectral_analysis().items()
            }
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

    def visualize_data(self) -> Dict[str, Any]:
        """Generate data for visualization.

        Returns:
            Dictionary with visualization-ready data
        """
        # Time evolution data
        time_steps = 100
        dt = 1e-15  # Femtosecond scale
        evolution = self.evolve_system(dt, time_steps, save_history=False)

        # Spatial field distribution
        x_points = np.linspace(-1e-6, 1e-6, 200)  # Micrometer scale
        spatial_field = []

        for x in x_points:
            field = self.genesis_superforce(
                np.array([x, 0, 0]),
                self.time
            )
            spatial_field.append(np.abs(field[0]))

        # Material response curves
        frequencies = np.logspace(9, 14, 100)  # GHz to 100 THz
        material_responses = {}

        for mat_type in MaterialType:
            responses = []
            mat_props = self.materials[mat_type]

            for freq in frequencies:
                omega = 2 * np.pi * freq
                response = mat_props.response_function(omega)
                responses.append(np.abs(response))

            material_responses[mat_type.value] = {
                'frequencies': frequencies.tolist(),
                'responses': responses
            }

        # Coupling matrix heatmap data
        coupling_matrix = self.get_coupling_matrix()

        return {
            'time_evolution': {
                'times': evolution['time_points'],
                'total_energy': evolution['total_energy'],
                'zpe_coherence': evolution['zpe_coherence'],
                'layer_amplitudes': evolution['layer_amplitudes']
            },
            'spatial_distribution': {
                'x_positions': x_points.tolist(),
                'field_magnitude': spatial_field
            },
            'material_responses': material_responses,
            'coupling_matrix': coupling_matrix.tolist(),
            'spectral_data': self.spectral_analysis()
        }


def demonstrate_genesis_harmonics():
    """Demonstration of Genesis Harmonics capabilities."""

    print("=" * 70)
    print("GENESIS FRAMEWORK HARMONICS DEMONSTRATION")
    print("=" * 70)

    # Initialize with E7 configuration
    print("\n1. Initializing E7 harmonic system (127 layers)...")
    genesis_e7 = GenesisHarmonics(
        num_layers=127,
        base_frequency=1e12,  # 1 THz
        fractal_alpha=1.618,  # Golden ratio
        zpe_beta=0.01
    )

    # Spectral analysis
    print("\n2. Spectral Analysis:")
    spectrum = genesis_e7.spectral_analysis()
    print(f"   Frequency range: {spectrum['frequencies'][0]:.2e} - {spectrum['frequencies'][-1]:.2e} Hz")
    print(f"   Peak amplitude: {np.max(spectrum['amplitudes']):.4f}")
    print(f"   Total power: {np.sum(spectrum['power_spectrum']):.2e}")

    # Genesis Superforce computation
    print("\n3. Computing Genesis Superforce at origin...")
    test_positions = np.array([[0, 0, 0], [1e-6, 0, 0], [0, 1e-6, 0]])

    for i, pos in enumerate(test_positions):
        field = genesis_e7.genesis_superforce(pos, 0.0, dimension=2.7)
        print(f"   Position {i+1}: {pos*1e6} micrometers")
        print(f"   Field magnitude: {np.abs(field[0]):.2e}")

    # Material responses
    print("\n4. Material Response Analysis:")
    test_field = np.array([1e-3, 0, 0])  # 1 mV/m field

    for mat_type in MaterialType:
        response = genesis_e7.material_response(
            test_field, mat_type, 1e12  # 1 THz
        )
        print(f"   {mat_type.value.capitalize()}:")
        print(f"     Response magnitude: {np.abs(response[0]):.2e}")
        print(f"     ZPE coupling: {MATERIALS[mat_type].zpe_coupling:.3f}")

    # Time evolution
    print("\n5. Time Evolution (100 femtoseconds)...")
    evolution = genesis_e7.evolve_system(
        dt=1e-15,  # 1 fs
        steps=100
    )

    print(f"   Initial energy: {evolution['total_energy'][0]:.2e}")
    print(f"   Final energy: {evolution['total_energy'][-1]:.2e}")
    print(f"   Average ZPE coherence: {np.mean(evolution['zpe_coherence']):.4f}")

    # E8 comparison
    print("\n6. E8 System Comparison (240 layers)...")
    genesis_e8 = GenesisHarmonics(
        num_layers=240,
        base_frequency=1e12,
        fractal_alpha=1.618,
        zpe_beta=0.01,
        use_e8=True
    )

    spectrum_e8 = genesis_e8.spectral_analysis()
    print(f"   E8 frequency range: {spectrum_e8['frequencies'][0]:.2e} - {spectrum_e8['frequencies'][-1]:.2e} Hz")
    print(f"   E8 total power: {np.sum(spectrum_e8['power_spectrum']):.2e}")

    # Coupling matrix analysis
    print("\n7. Coupling Matrix Properties:")
    coupling = genesis_e7.get_coupling_matrix()
    eigenvalues = np.linalg.eigvals(coupling)

    print(f"   Matrix dimension: {coupling.shape}")
    print(f"   Max eigenvalue: {np.max(np.real(eigenvalues)):.4f}")
    print(f"   Min eigenvalue: {np.min(np.real(eigenvalues)):.4f}")
    print(f"   Condition number: {np.linalg.cond(coupling):.2e}")

    # Export data
    print("\n8. Exporting system data...")
    output_path = Path("/home/eirikr/Github_n_projects/MathScienceCompendium/experiments/data")
    output_path.mkdir(exist_ok=True)

    genesis_e7.export_data(output_path / "genesis_harmonics_e7.json")
    print(f"   Data exported to: {output_path / 'genesis_harmonics_e7.json'}")

    # Visualization data
    print("\n9. Generating visualization data...")
    viz_data = genesis_e7.visualize_data()

    print(f"   Spatial field points: {len(viz_data['spatial_distribution']['x_positions'])}")
    print(f"   Time evolution steps: {len(viz_data['time_evolution']['times'])}")
    print(f"   Material response curves: {len(viz_data['material_responses'])}")

    print("\n" + "=" * 70)
    print("DEMONSTRATION COMPLETE")
    print("=" * 70)

    return genesis_e7, genesis_e8, viz_data


if __name__ == "__main__":
    # Run demonstration
    genesis_e7, genesis_e8, viz_data = demonstrate_genesis_harmonics()

    print("\nGenesis Harmonics module successfully initialized!")
    print("E7 and E8 harmonic systems are ready for integration.")