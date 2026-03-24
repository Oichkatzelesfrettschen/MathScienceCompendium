"""Unified Quantum Simulation Framework for E7/E8 Lie Algebras.

This module provides a comprehensive simulation framework integrating E7 and E8
quantum circuits with Qiskit Aer simulators, noise models, error mitigation,
and result visualization capabilities.

Key Features:
1. Unified simulation interface for E7/E8 circuits
2. Integration with Qiskit Aer backends
3. IBM hardware noise modeling (FakeKyiv, FakeWashington)
4. Error mitigation strategies
5. Result analysis and visualization
6. Performance benchmarking

Author: Claude Code
Date: October 2025
"""

from __future__ import annotations
from typing import List, Tuple, Dict, Any, Optional, Union, Callable
import numpy as np
from datetime import datetime
import time
from dataclasses import dataclass, field
from pathlib import Path
import json
import pickle
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)

# Qiskit imports
from qiskit import QuantumCircuit, execute, transpile
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, thermal_relaxation_error, depolarizing_error
from qiskit.providers.fake_provider import FakeKyiv, FakeWashington, FakeMontreal
from qiskit.result import Result
from qiskit.quantum_info import (
    Statevector, DensityMatrix, state_fidelity,
    process_fidelity, hellinger_fidelity, Operator
)
from qiskit.visualization import plot_histogram, plot_state_city, plot_bloch_multivector
from qiskit.result.mitigation import CompleteMeasFitter, TensoredMeasFitter
from qiskit.utils.mitigation import complete_meas_cal, tensored_meas_cal

# Matplotlib for visualization
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.patches import Circle, Rectangle
import seaborn as sns
sns.set_style("whitegrid")

# Local imports
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from e7_root_system import E7RootSystem
from lie_algebras import E8RootSystem
from quantum_e7_circuits import (
    E7CircuitConfig, E7QuantumAlgorithms,
    E7MeasurementDecoder, E7CircuitOptimizer
)
from quantum_e8_circuits import (
    E8CircuitConfig, E8QuantumAlgorithms,
    E8MeasurementAnalysis, E8HardwareOptimization
)
from quantum_encoding import (
    EncodingConfig, IndexEncoder, AmplitudeEncoder,
    BinaryEncoder, QROMEncoder, HybridEncoder
)


@dataclass
class SimulationConfig:
    """Configuration for quantum simulation."""

    backend_type: str = 'aer_simulator'  # 'aer_simulator', 'statevector', 'density_matrix', 'fake_hardware'
    shots: int = 8192
    seed: Optional[int] = 42
    noise_model: Optional[str] = None  # None, 'FakeKyiv', 'FakeWashington', 'custom'
    error_mitigation: bool = True
    optimization_level: int = 2
    parallel_experiments: int = 1
    memory: bool = True
    max_parallel_threads: int = 4
    save_results: bool = True
    results_dir: Path = Path("/home/eirikr/Github_n_projects/MathScienceCompendium/experiments/results")
    visualization: bool = True
    verbose: bool = True

    def validate(self) -> None:
        """Validate configuration."""
        valid_backends = {'aer_simulator', 'statevector', 'density_matrix', 'fake_hardware'}
        if self.backend_type not in valid_backends:
            raise ValueError(f"Invalid backend type: {self.backend_type}")
        if self.shots < 1 or self.shots > 1000000:
            raise ValueError(f"Invalid shots: {self.shots}")
        if self.parallel_experiments < 1:
            raise ValueError("Parallel experiments must be >= 1")


@dataclass
class SimulationResult:
    """Container for simulation results."""

    circuit_name: str
    backend_name: str
    execution_time: float
    shots: int
    counts: Dict[str, int]
    memory: Optional[List[str]] = None
    statevector: Optional[Statevector] = None
    density_matrix: Optional[DensityMatrix] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    error_mitigation_applied: bool = False
    mitigated_counts: Optional[Dict[str, int]] = None
    analysis: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'circuit_name': self.circuit_name,
            'backend_name': self.backend_name,
            'execution_time': self.execution_time,
            'shots': self.shots,
            'counts': self.counts,
            'memory': self.memory,
            'metadata': self.metadata,
            'error_mitigation_applied': self.error_mitigation_applied,
            'mitigated_counts': self.mitigated_counts,
            'analysis': self.analysis,
            'timestamp': self.timestamp.isoformat()
        }

    def save(self, filepath: Path) -> None:
        """Save results to file."""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)


class QuantumSimulator:
    """Main quantum simulation engine."""

    def __init__(self, config: SimulationConfig):
        """Initialize quantum simulator.

        Args:
            config: Simulation configuration
        """
        self.config = config
        self.config.validate()
        self.backend = self._initialize_backend()
        self.noise_model = self._initialize_noise_model()
        self.results_cache = {}

        # Create results directory
        self.config.results_dir.mkdir(parents=True, exist_ok=True)

    def _initialize_backend(self) -> Any:
        """Initialize simulation backend."""
        if self.config.backend_type == 'aer_simulator':
            return AerSimulator(
                method='automatic',
                device='CPU',
                precision='double',
                max_parallel_threads=self.config.max_parallel_threads,
                max_parallel_experiments=self.config.parallel_experiments,
                seed_simulator=self.config.seed
            )
        elif self.config.backend_type == 'statevector':
            return AerSimulator(
                method='statevector',
                seed_simulator=self.config.seed
            )
        elif self.config.backend_type == 'density_matrix':
            return AerSimulator(
                method='density_matrix',
                seed_simulator=self.config.seed
            )
        elif self.config.backend_type == 'fake_hardware':
            # Use fake backend for testing
            return FakeKyiv() if self.config.noise_model == 'FakeKyiv' else FakeWashington()
        else:
            return AerSimulator(seed_simulator=self.config.seed)

    def _initialize_noise_model(self) -> Optional[NoiseModel]:
        """Initialize noise model for simulation."""
        if self.config.noise_model is None:
            return None

        if self.config.noise_model == 'FakeKyiv':
            fake_backend = FakeKyiv()
            return NoiseModel.from_backend(fake_backend)
        elif self.config.noise_model == 'FakeWashington':
            fake_backend = FakeWashington()
            return NoiseModel.from_backend(fake_backend)
        elif self.config.noise_model == 'custom':
            return self._build_custom_noise_model()
        else:
            return None

    def _build_custom_noise_model(self) -> NoiseModel:
        """Build custom noise model."""
        noise_model = NoiseModel()

        # Single-qubit gate errors
        p_1q = 0.001  # 0.1% error rate
        error_1q = depolarizing_error(p_1q, 1)
        noise_model.add_all_qubit_quantum_error(error_1q, ['u1', 'u2', 'u3'])

        # Two-qubit gate errors
        p_2q = 0.01  # 1% error rate
        error_2q = depolarizing_error(p_2q, 2)
        noise_model.add_all_qubit_quantum_error(error_2q, ['cx'])

        # T1 and T2 relaxation
        t1 = 50e3  # 50 microseconds
        t2 = 70e3  # 70 microseconds
        gate_time = 50  # 50 nanoseconds

        for i in range(8):  # Up to 8 qubits
            thermal_error = thermal_relaxation_error(t1, t2, gate_time)
            noise_model.add_quantum_error(thermal_error, 'id', [i])

        return noise_model

    def simulate(self, circuit: QuantumCircuit,
                shots: Optional[int] = None,
                apply_mitigation: Optional[bool] = None) -> SimulationResult:
        """Run quantum simulation.

        Args:
            circuit: Quantum circuit to simulate
            shots: Number of shots (overrides config)
            apply_mitigation: Whether to apply error mitigation

        Returns:
            SimulationResult object
        """
        shots = shots or self.config.shots
        apply_mitigation = apply_mitigation if apply_mitigation is not None else self.config.error_mitigation

        if self.config.verbose:
            print(f"Simulating circuit: {circuit.name}")
            print(f"  Backend: {self.backend}")
            print(f"  Shots: {shots}")
            print(f"  Noise model: {self.config.noise_model}")

        start_time = time.time()

        # Transpile circuit
        transpiled = transpile(
            circuit,
            backend=self.backend,
            optimization_level=self.config.optimization_level,
            seed_transpiler=self.config.seed
        )

        # Execute simulation
        if self.noise_model:
            job = execute(
                transpiled,
                backend=self.backend,
                shots=shots,
                noise_model=self.noise_model,
                memory=self.config.memory,
                seed_simulator=self.config.seed
            )
        else:
            job = execute(
                transpiled,
                backend=self.backend,
                shots=shots,
                memory=self.config.memory,
                seed_simulator=self.config.seed
            )

        result = job.result()
        execution_time = time.time() - start_time

        # Extract results
        counts = result.get_counts()
        memory = result.get_memory() if self.config.memory else None

        # Create result object
        sim_result = SimulationResult(
            circuit_name=circuit.name,
            backend_name=str(self.backend),
            execution_time=execution_time,
            shots=shots,
            counts=counts,
            memory=memory,
            metadata={
                'circuit_depth': transpiled.depth(),
                'circuit_gates': transpiled.size(),
                'circuit_qubits': transpiled.num_qubits
            }
        )

        # Apply error mitigation if requested
        if apply_mitigation and self.noise_model:
            sim_result = self._apply_error_mitigation(circuit, sim_result)

        # Get statevector if backend supports it
        if self.config.backend_type in ['statevector', 'aer_simulator']:
            try:
                statevector = Statevector.from_instruction(transpiled)
                sim_result.statevector = statevector
            except:
                pass

        if self.config.verbose:
            print(f"  Execution time: {execution_time:.2f}s")
            print(f"  Unique outcomes: {len(counts)}")

        return sim_result

    def _apply_error_mitigation(self, circuit: QuantumCircuit,
                               result: SimulationResult) -> SimulationResult:
        """Apply measurement error mitigation.

        Args:
            circuit: Original circuit
            result: Simulation result

        Returns:
            Result with error mitigation applied
        """
        n_qubits = circuit.num_qubits

        # Build calibration circuits
        cal_circuits, state_labels = complete_meas_cal(
            qr=circuit.qregs[0],
            circlabel='cal'
        )

        # Execute calibration circuits
        cal_results = []
        for cal_circuit in cal_circuits:
            cal_job = execute(
                cal_circuit,
                backend=self.backend,
                shots=self.config.shots,
                noise_model=self.noise_model,
                seed_simulator=self.config.seed
            )
            cal_results.append(cal_job.result())

        # Create measurement filter
        meas_fitter = CompleteMeasFitter(cal_results[0], state_labels)
        meas_filter = meas_fitter.filter

        # Apply filter to results
        mitigated_counts = meas_filter.apply(result.counts)

        result.error_mitigation_applied = True
        result.mitigated_counts = mitigated_counts
        result.metadata['mitigation_fidelity'] = meas_fitter.readout_fidelity()

        return result

    def batch_simulate(self, circuits: List[QuantumCircuit],
                      parallel: bool = True) -> List[SimulationResult]:
        """Simulate multiple circuits.

        Args:
            circuits: List of circuits to simulate
            parallel: Whether to run in parallel

        Returns:
            List of simulation results
        """
        if self.config.verbose:
            print(f"Batch simulating {len(circuits)} circuits...")

        if parallel and len(circuits) > 1:
            with ThreadPoolExecutor(max_workers=self.config.max_parallel_threads) as executor:
                results = list(executor.map(self.simulate, circuits))
        else:
            results = [self.simulate(circuit) for circuit in circuits]

        return results

    def save_results(self, results: Union[SimulationResult, List[SimulationResult]],
                    prefix: str = "simulation") -> List[Path]:
        """Save simulation results.

        Args:
            results: Single result or list of results
            prefix: Filename prefix

        Returns:
            List of saved file paths
        """
        if not isinstance(results, list):
            results = [results]

        saved_paths = []
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        for i, result in enumerate(results):
            filename = f"{prefix}_{timestamp}_{i}.json"
            filepath = self.config.results_dir / filename
            result.save(filepath)
            saved_paths.append(filepath)

            if self.config.verbose:
                print(f"Saved result to: {filepath}")

        return saved_paths


class E7E8SimulationSuite:
    """Complete simulation suite for E7 and E8 quantum circuits."""

    def __init__(self, sim_config: Optional[SimulationConfig] = None):
        """Initialize simulation suite.

        Args:
            sim_config: Simulation configuration
        """
        self.sim_config = sim_config or SimulationConfig()
        self.simulator = QuantumSimulator(self.sim_config)

        # Initialize algorithm instances
        self.e7_config = E7CircuitConfig()
        self.e8_config = E8CircuitConfig()
        self.e7_algorithms = E7QuantumAlgorithms(self.e7_config)
        self.e8_algorithms = E8QuantumAlgorithms(self.e8_config)

        # Analysis tools
        self.e7_decoder = E7MeasurementDecoder()
        self.e8_analyzer = E8MeasurementAnalysis()

    def run_e7_suite(self) -> Dict[str, SimulationResult]:
        """Run complete E7 simulation suite.

        Returns:
            Dictionary of simulation results
        """
        results = {}

        print("\n" + "=" * 80)
        print("E7 QUANTUM SIMULATION SUITE")
        print("=" * 80)

        # 1. Root search algorithms
        print("\n1. E7 Root Search Simulations")
        print("-" * 40)

        for root_type in ['Type1', 'Type2', 'all']:
            circuit = self.e7_algorithms.root_search_algorithm(root_type)
            result = self.simulator.simulate(circuit)
            results[f'e7_search_{root_type}'] = result

            # Analyze results
            decoded = self.e7_decoder.decode_index_measurement(result.counts)
            result.analysis = {
                'type1_probability': decoded['type1_probability'],
                'type2_probability': decoded['type2_probability'],
                'measured_roots': len(decoded['measured_roots'])
            }

            print(f"  {root_type} search: {len(decoded['measured_roots'])} roots found")

        # 2. Root validation
        print("\n2. E7 Root Validation")
        print("-" * 40)

        validation_circuit = self.e7_algorithms.root_validation_algorithm()
        val_result = self.simulator.simulate(validation_circuit)
        results['e7_validation'] = val_result

        # Calculate validation rate
        valid_count = sum(count for bitstring, count in val_result.counts.items()
                         if bitstring[-1] == '0')  # Last bit indicates validity
        validation_rate = valid_count / self.sim_config.shots
        val_result.analysis['validation_rate'] = validation_rate

        print(f"  Validation rate: {validation_rate:.3f}")

        # 3. Cartan eigenvalue estimation
        print("\n3. E7 Cartan Eigenvalue Estimation")
        print("-" * 40)

        cartan_circuit = self.e7_algorithms.cartan_eigenvalue_estimation()
        cartan_result = self.simulator.simulate(cartan_circuit)
        results['e7_cartan_qpe'] = cartan_result

        # Extract eigenvalue estimate
        top_measurement = max(cartan_result.counts.items(), key=lambda x: x[1])[0]
        eigenvalue_estimate = int(top_measurement[::-1], 2) / (2**len(top_measurement))
        cartan_result.analysis['eigenvalue_estimate'] = eigenvalue_estimate

        print(f"  Estimated eigenvalue: {eigenvalue_estimate:.4f}")

        # 4. Weyl group action
        print("\n4. E7 Weyl Group Action")
        print("-" * 40)

        weyl_circuit = self.e7_algorithms.weyl_group_action()
        weyl_result = self.simulator.simulate(weyl_circuit)
        results['e7_weyl_action'] = weyl_result

        print(f"  Weyl action executed: {len(weyl_result.counts)} unique outcomes")

        return results

    def run_e8_suite(self) -> Dict[str, SimulationResult]:
        """Run complete E8 simulation suite.

        Returns:
            Dictionary of simulation results
        """
        results = {}

        print("\n" + "=" * 80)
        print("E8 QUANTUM SIMULATION SUITE")
        print("=" * 80)

        # 1. Root counting
        print("\n1. E8 Root Counting")
        print("-" * 40)

        counting_circuit = self.e8_algorithms.root_counting_algorithm()
        count_result = self.simulator.simulate(counting_circuit)
        results['e8_counting'] = count_result

        # Extract count estimate
        top_count = max(count_result.counts.items(), key=lambda x: x[1])[0]
        count_estimate = int(top_count[::-1], 2) * (256 / 8)  # Scale to full space
        count_result.analysis['root_count_estimate'] = count_estimate

        print(f"  Estimated root count: {count_estimate:.0f} (actual: 240)")

        # 2. Root classification
        print("\n2. E8 Root Classification")
        print("-" * 40)

        classification_circuit = self.e8_algorithms.root_classification_algorithm()
        class_result = self.simulator.simulate(classification_circuit)
        results['e8_classification'] = class_result

        # Analyze classification
        type1_count = sum(count for bitstring, count in class_result.counts.items()
                         if bitstring.split()[-1][-1] == '0')  # Type bit
        type1_ratio = type1_count / self.sim_config.shots
        class_result.analysis['type1_ratio'] = type1_ratio

        print(f"  Type 1 ratio: {type1_ratio:.3f} (expected: {112/240:.3f})")

        # 3. Cartan time evolution
        print("\n3. E8 Cartan Time Evolution")
        print("-" * 40)

        evolution_circuit = self.e8_algorithms.cartan_simulation(time=1.0)
        evo_result = self.simulator.simulate(evolution_circuit)
        results['e8_evolution'] = evo_result

        print(f"  Evolution completed: {len(evo_result.counts)} final states")

        # 4. Dynkin diagram encoding
        print("\n4. E8 Dynkin Diagram")
        print("-" * 40)

        dynkin_circuit = self.e8_algorithms.dynkin_diagram_encoding()
        dynkin_result = self.simulator.simulate(dynkin_circuit)
        results['e8_dynkin'] = dynkin_result

        # Analyze entanglement structure
        decoded = self.e8_analyzer.decode_measurement(dynkin_result.counts)
        dynkin_result.analysis = decoded

        print(f"  Dynkin encoding: {decoded['measured_root_count']} distinct states")

        # 5. Exceptional symmetry test
        print("\n5. E8 Exceptional Symmetry")
        print("-" * 40)

        symmetry_circuit = self.e8_algorithms.exceptional_symmetry_test()
        sym_result = self.simulator.simulate(symmetry_circuit)
        results['e8_symmetry'] = sym_result

        # Check symmetry preservation
        initial_state = '00000000'
        if initial_state in sym_result.counts:
            symmetry_preserved = sym_result.counts[initial_state] / self.sim_config.shots
        else:
            symmetry_preserved = 0.0
        sym_result.analysis['symmetry_preserved'] = symmetry_preserved

        print(f"  Symmetry preservation: {symmetry_preserved:.3f}")

        return results

    def run_noise_comparison(self) -> Dict[str, Any]:
        """Compare results with different noise models.

        Returns:
            Comparison results
        """
        print("\n" + "=" * 80)
        print("NOISE MODEL COMPARISON")
        print("=" * 80)

        # Test circuit: E7 root search
        test_circuit = self.e7_algorithms.root_search_algorithm('Type1')

        comparison = {}
        noise_models = [None, 'FakeKyiv', 'custom']

        for noise_model in noise_models:
            print(f"\nTesting noise model: {noise_model or 'Ideal'}")

            # Update simulator config
            self.simulator.config.noise_model = noise_model
            self.simulator.noise_model = self.simulator._initialize_noise_model()

            # Run simulation
            result = self.simulator.simulate(test_circuit, shots=1024)

            # Analyze
            decoded = self.e7_decoder.decode_index_measurement(result.counts)

            comparison[noise_model or 'ideal'] = {
                'execution_time': result.execution_time,
                'unique_outcomes': len(result.counts),
                'type1_probability': decoded['type1_probability'],
                'type2_probability': decoded['type2_probability'],
                'measured_roots': len(decoded['measured_roots'])
            }

            print(f"  Measured roots: {len(decoded['measured_roots'])}")
            print(f"  Type 1 probability: {decoded['type1_probability']:.3f}")

        return comparison

    def benchmark_performance(self) -> Dict[str, Any]:
        """Benchmark simulation performance.

        Returns:
            Benchmark results
        """
        print("\n" + "=" * 80)
        print("PERFORMANCE BENCHMARKING")
        print("=" * 80)

        benchmarks = {}

        # Test different circuit sizes
        test_configs = [
            ('E7_small', self.e7_algorithms.root_validation_algorithm()),
            ('E7_medium', self.e7_algorithms.root_search_algorithm('all')),
            ('E8_small', self.e8_algorithms.root_classification_algorithm()),
            ('E8_large', self.e8_algorithms.cartan_simulation(time=2.0))
        ]

        for name, circuit in test_configs:
            print(f"\nBenchmarking: {name}")
            print(f"  Circuit depth: {circuit.depth()}")
            print(f"  Circuit gates: {circuit.size()}")

            # Run multiple times for average
            times = []
            for _ in range(3):
                result = self.simulator.simulate(circuit, shots=1024)
                times.append(result.execution_time)

            avg_time = np.mean(times)
            std_time = np.std(times)

            benchmarks[name] = {
                'circuit_depth': circuit.depth(),
                'circuit_gates': circuit.size(),
                'avg_time': avg_time,
                'std_time': std_time,
                'throughput': 1024 / avg_time  # shots per second
            }

            print(f"  Avg time: {avg_time:.3f}±{std_time:.3f}s")
            print(f"  Throughput: {benchmarks[name]['throughput']:.1f} shots/s")

        return benchmarks

    def visualize_results(self, results: Dict[str, SimulationResult]) -> None:
        """Visualize simulation results.

        Args:
            results: Dictionary of simulation results
        """
        if not self.sim_config.visualization:
            return

        print("\n" + "=" * 80)
        print("VISUALIZATION")
        print("=" * 80)

        # Create figure with subplots
        fig = plt.figure(figsize=(16, 12))
        gs = gridspec.GridSpec(3, 3, figure=fig)

        # 1. E7 Root Distribution
        ax1 = fig.add_subplot(gs[0, :2])
        if 'e7_search_all' in results:
            result = results['e7_search_all']
            decoded = self.e7_decoder.decode_index_measurement(result.counts)

            # Extract top roots
            top_roots = self.e7_decoder.extract_top_roots(result.counts, top_k=20)
            indices = [r['index'] for r in top_roots]
            probs = [r['probability'] for r in top_roots]
            colors = ['blue' if r['type'] == 'Type 1' else 'red' for r in top_roots]

            ax1.bar(range(len(indices)), probs, color=colors, alpha=0.7)
            ax1.set_xlabel('Root Index')
            ax1.set_ylabel('Probability')
            ax1.set_title('E7 Root Distribution (Top 20)')
            ax1.set_xticks(range(len(indices)))
            ax1.set_xticklabels(indices, rotation=45)

        # 2. E8 Classification
        ax2 = fig.add_subplot(gs[0, 2])
        if 'e8_classification' in results:
            result = results['e8_classification']
            type1_ratio = result.analysis.get('type1_ratio', 0.5)

            sizes = [type1_ratio, 1 - type1_ratio]
            labels = ['Type 1', 'Type 2']
            colors = ['#3498db', '#e74c3c']

            ax2.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%')
            ax2.set_title('E8 Root Classification')

        # 3. Noise Comparison (if available)
        ax3 = fig.add_subplot(gs[1, :])
        # Placeholder for noise comparison visualization

        # 4. Execution Times
        ax4 = fig.add_subplot(gs[2, :2])
        circuit_names = []
        exec_times = []
        for name, result in results.items():
            if 'e7' in name.lower():
                circuit_names.append(name.replace('e7_', 'E7:'))
                exec_times.append(result.execution_time)
            elif 'e8' in name.lower():
                circuit_names.append(name.replace('e8_', 'E8:'))
                exec_times.append(result.execution_time)

        if circuit_names:
            colors = ['blue' if 'E7' in n else 'green' for n in circuit_names]
            ax4.barh(circuit_names, exec_times, color=colors, alpha=0.6)
            ax4.set_xlabel('Execution Time (seconds)')
            ax4.set_title('Circuit Execution Times')
            ax4.grid(True, alpha=0.3)

        # 5. Circuit Metrics
        ax5 = fig.add_subplot(gs[2, 2])
        depths = []
        gates = []
        labels = []

        for name, result in results.items():
            if 'metadata' in result.__dict__ and result.metadata:
                depths.append(result.metadata.get('circuit_depth', 0))
                gates.append(result.metadata.get('circuit_gates', 0))
                labels.append(name.split('_')[0].upper())

        if depths and gates:
            scatter = ax5.scatter(depths, gates, s=100, alpha=0.6, c=range(len(depths)))
            ax5.set_xlabel('Circuit Depth')
            ax5.set_ylabel('Gate Count')
            ax5.set_title('Circuit Complexity')

            for i, label in enumerate(labels):
                ax5.annotate(label, (depths[i], gates[i]), fontsize=8)

        plt.suptitle('E7/E8 Quantum Simulation Results', fontsize=16, y=1.02)
        plt.tight_layout()

        # Save figure
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = self.sim_config.results_dir / f"visualization_{timestamp}.png"
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        print(f"\nVisualization saved to: {filepath}")

        if self.sim_config.verbose:
            plt.show()


def run_complete_simulation():
    """Run complete E7/E8 quantum simulation demonstration."""
    print("=" * 80)
    print("E7/E8 QUANTUM SIMULATION FRAMEWORK")
    print("=" * 80)
    print()

    # Configure simulation
    sim_config = SimulationConfig(
        backend_type='aer_simulator',
        shots=4096,
        noise_model=None,  # Start with ideal simulation
        error_mitigation=False,
        optimization_level=2,
        visualization=True,
        verbose=True
    )

    # Initialize simulation suite
    suite = E7E8SimulationSuite(sim_config)

    # Run E7 simulations
    e7_results = suite.run_e7_suite()

    # Run E8 simulations
    e8_results = suite.run_e8_suite()

    # Combine results
    all_results = {**e7_results, **e8_results}

    # Run noise comparison
    noise_comparison = suite.run_noise_comparison()

    print("\n" + "=" * 80)
    print("NOISE MODEL COMPARISON SUMMARY")
    print("=" * 80)
    for model, metrics in noise_comparison.items():
        print(f"\n{model.upper()}:")
        for key, value in metrics.items():
            if isinstance(value, float):
                print(f"  {key}: {value:.3f}")
            else:
                print(f"  {key}: {value}")

    # Run performance benchmarks
    benchmarks = suite.benchmark_performance()

    print("\n" + "=" * 80)
    print("PERFORMANCE SUMMARY")
    print("=" * 80)
    for circuit, metrics in benchmarks.items():
        print(f"\n{circuit}:")
        print(f"  Depth: {metrics['circuit_depth']}")
        print(f"  Gates: {metrics['circuit_gates']}")
        print(f"  Avg time: {metrics['avg_time']:.3f}s")
        print(f"  Throughput: {metrics['throughput']:.1f} shots/s")

    # Visualize results
    suite.visualize_results(all_results)

    # Save all results
    if sim_config.save_results:
        saved_paths = suite.simulator.save_results(list(all_results.values()))
        print(f"\nSaved {len(saved_paths)} result files")

    print("\n" + "=" * 80)
    print("SIMULATION COMPLETE")
    print("=" * 80)
    print(f"Total E7 circuits simulated: {len(e7_results)}")
    print(f"Total E8 circuits simulated: {len(e8_results)}")
    print(f"Results directory: {sim_config.results_dir}")
    print("=" * 80)

    return all_results, noise_comparison, benchmarks


if __name__ == "__main__":
    results, noise, benchmarks = run_complete_simulation()