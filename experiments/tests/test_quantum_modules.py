"""Unit tests for quantum simulation modules.

Tests for quantum_encoding, quantum_e7_circuits, quantum_e8_circuits,
and quantum_simulation modules.

Author: Claude Code
Date: October 2025
"""

import unittest
import numpy as np
from pathlib import Path
import sys
import warnings
warnings.filterwarnings('ignore')

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

# Import modules to test
from e7_root_system import E7RootSystem
from lie_algebras import E8RootSystem
from quantum_encoding import (
    EncodingConfig, IndexEncoder, AmplitudeEncoder,
    BinaryEncoder, QROMEncoder, HybridEncoder, EncodingValidator
)
from quantum_e7_circuits import (
    E7CircuitConfig, E7OracleBuilder, E7GroverOperator,
    E7StatePreparation, E7MeasurementDecoder, E7QuantumAlgorithms
)
from quantum_e8_circuits import (
    E8CircuitConfig, E8RootStructure, E8OracleBuilder,
    E8GroverSearch, E8StatePreparation, E8MeasurementAnalysis,
    E8QuantumAlgorithms
)
from quantum_simulation import (
    SimulationConfig, QuantumSimulator, SimulationResult,
    E7E8SimulationSuite
)

# Qiskit imports for testing
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
from qiskit_aer import AerSimulator


class TestQuantumEncoding(unittest.TestCase):
    """Test quantum encoding module."""

    def setUp(self):
        """Set up test configuration."""
        self.config = EncodingConfig(
            encoding_type='index',
            num_qubits=7,
            precision_bits=4,
            error_tolerance=1e-6
        )
        self.e7_system = E7RootSystem()
        self.e8_system = E8RootSystem()

    def test_encoding_config(self):
        """Test encoding configuration."""
        self.config.validate()
        self.assertEqual(self.config.num_qubits, 7)
        self.assertEqual(self.config.precision_bits, 4)

        # Test invalid config
        with self.assertRaises(ValueError):
            bad_config = EncodingConfig(
                encoding_type='invalid',
                num_qubits=7
            )
            bad_config.validate()

    def test_index_encoder(self):
        """Test index encoding for roots."""
        encoder = IndexEncoder(self.config)

        # Test single index encoding
        circuit = encoder.encode_root_index(42, num_qubits=7)
        self.assertEqual(circuit.num_qubits, 7)

        # Test E7 index encoding
        e7_circuit = encoder.encode_e7_indices()
        self.assertEqual(e7_circuit.num_qubits, 7)

        # Test E8 index encoding
        e8_circuit = encoder.encode_e8_indices()
        self.assertEqual(e8_circuit.num_qubits, 8)

        # Test measurement decoding
        sample_counts = {'0101010': 100, '1010101': 50}
        decoded = encoder.decode_measurement(sample_counts, 'E7')
        self.assertIn(42, decoded)  # Binary 0101010 = 42

    def test_amplitude_encoder(self):
        """Test amplitude encoding."""
        encoder = AmplitudeEncoder(self.config)

        # Test single root encoding
        root = self.e7_system.generate_roots()[0]
        circuit = encoder.encode_root_amplitudes(root)
        self.assertEqual(circuit.num_qubits, 3)  # log2(8) = 3

        # Verify state preparation
        state = Statevector.from_instruction(circuit)
        self.assertAlmostEqual(np.linalg.norm(state.data), 1.0, places=6)

    def test_binary_encoder(self):
        """Test binary encoding."""
        encoder = BinaryEncoder(self.config)

        # Test float to binary conversion
        value = 0.5
        binary = encoder.float_to_binary(value, signed=True)
        decoded = encoder.binary_to_float(binary, signed=True)
        self.assertAlmostEqual(value, decoded, places=1)

        # Test root encoding
        root = np.array([1.0, -0.5, 0.0, 0.5, -1.0, 0.0, 0.0, 0.0])
        circuit = encoder.encode_root_binary(root)
        expected_qubits = 8 * self.config.precision_bits
        self.assertEqual(circuit.num_qubits, expected_qubits)

    def test_qrom_encoder(self):
        """Test QROM encoding."""
        encoder = QROMEncoder(self.config)

        # Test with small dataset
        test_data = [np.array([1, 0, 0]), np.array([0, 1, 0]), np.array([0, 0, 1])]
        circuit = encoder.build_qrom_circuit(test_data)

        self.assertGreater(circuit.num_qubits, 0)
        self.assertGreater(encoder.select_register_size, 0)

    def test_encoding_validator(self):
        """Test encoding validation."""
        validator = EncodingValidator()

        # Test statevector validation
        quantum_state = Statevector([0.6, 0.8])
        classical_data = np.array([0.6, 0.8])

        is_valid, fidelity = validator.validate_statevector(
            quantum_state, classical_data, tolerance=1e-6
        )

        self.assertTrue(is_valid)
        self.assertGreater(fidelity, 0.99)


class TestE7QuantumCircuits(unittest.TestCase):
    """Test E7 quantum circuits module."""

    def setUp(self):
        """Set up E7 test configuration."""
        self.config = E7CircuitConfig(
            num_iterations=2,
            oracle_type='geometric',
            use_ancilla=True
        )
        self.e7_system = E7RootSystem()

    def test_e7_oracle_builder(self):
        """Test E7 oracle construction."""
        builder = E7OracleBuilder(self.config)

        # Test geometric oracle
        geo_oracle = builder.build_geometric_oracle()
        self.assertIn(geo_oracle.num_qubits, [7, 8])  # With or without ancilla

        # Test algebraic oracle
        alg_oracle = builder.build_algebraic_oracle()
        self.assertEqual(alg_oracle.num_qubits, 7)

        # Test hybrid oracle
        hybrid_oracle = builder.build_hybrid_oracle()
        self.assertGreaterEqual(hybrid_oracle.num_qubits, 7)

    def test_e7_grover_operator(self):
        """Test E7 Grover operator."""
        builder = E7OracleBuilder(self.config)
        oracle = builder.build_geometric_oracle()

        grover = E7GroverOperator(oracle, self.config)

        # Test diffusion operator
        diffusion = grover.build_diffusion_operator()
        self.assertEqual(diffusion.num_qubits, 7)

        # Test success probability calculation
        prob = grover.calculate_success_probability(n_marked=126, n_total=127)
        self.assertGreater(prob, 0)
        self.assertLessEqual(prob, 1)

        # Test complete Grover circuit
        grover_circuit = grover.build_grover_circuit()
        self.assertGreater(grover_circuit.num_qubits, 0)
        self.assertGreater(grover_circuit.num_clbits, 0)

    def test_e7_state_preparation(self):
        """Test E7 state preparation."""
        prep = E7StatePreparation(self.config)

        # Test uniform superposition
        uniform = prep.prepare_uniform_superposition()
        self.assertEqual(uniform.num_qubits, 7)

        # Verify state normalization
        state = Statevector.from_instruction(uniform)
        self.assertAlmostEqual(np.linalg.norm(state.data), 1.0)

        # Test type-specific superpositions
        type1 = prep.prepare_type1_superposition()
        type2 = prep.prepare_type2_superposition()

        self.assertEqual(type1.num_qubits, 7)
        self.assertEqual(type2.num_qubits, 7)

    def test_e7_measurement_decoder(self):
        """Test E7 measurement decoding."""
        decoder = E7MeasurementDecoder()

        # Test with sample measurements
        counts = {
            '0000000': 100,  # Index 0
            '0000001': 80,   # Index 1 (bit-reversed)
            '1111111': 60,   # Index 127 (invalid for E7 roots)
            '1111110': 40    # Index 126 (zero vector)
        }

        decoded = decoder.decode_index_measurement(counts)

        self.assertEqual(decoded['total_shots'], 280)
        self.assertIn('measured_roots', decoded)
        self.assertGreaterEqual(decoded['zero_probability'], 0)

        # Test top roots extraction
        top_roots = decoder.extract_top_roots(counts, top_k=2)
        self.assertLessEqual(len(top_roots), 2)

    def test_e7_quantum_algorithms(self):
        """Test E7 quantum algorithms."""
        algorithms = E7QuantumAlgorithms(self.config)

        # Test root search
        search_circuit = algorithms.root_search_algorithm('Type1')
        self.assertGreater(search_circuit.num_qubits, 0)

        # Test root validation
        validation_circuit = algorithms.root_validation_algorithm()
        self.assertGreater(validation_circuit.num_qubits, 0)

        # Test Cartan eigenvalue estimation
        qpe_circuit = algorithms.cartan_eigenvalue_estimation()
        self.assertGreater(qpe_circuit.num_qubits, 0)


class TestE8QuantumCircuits(unittest.TestCase):
    """Test E8 quantum circuits module."""

    def setUp(self):
        """Set up E8 test configuration."""
        self.config = E8CircuitConfig(
            num_iterations=2,
            oracle_type='algebraic',
            use_ancilla=True
        )

    def test_e8_root_structure(self):
        """Test E8 root structure analysis."""
        structure = E8RootStructure()

        # Check root counts
        self.assertEqual(len(structure.roots), 240)
        self.assertEqual(len(structure.type1_indices) + len(structure.type2_indices), 240)

        # Test root neighbors
        neighbors = structure.get_root_neighbors(0, max_distance=1)
        self.assertIsInstance(neighbors, set)

        # Test Weyl orbit
        orbit = structure.get_weyl_orbit(0)
        self.assertIsInstance(orbit, set)
        self.assertGreater(len(orbit), 0)

    def test_e8_oracle_builder(self):
        """Test E8 oracle construction."""
        builder = E8OracleBuilder(self.config)

        # Test algebraic oracle
        alg_oracle = builder.build_algebraic_oracle()
        self.assertEqual(alg_oracle.num_qubits, 8)

        # Test geometric oracle
        geo_oracle = builder.build_geometric_oracle()
        self.assertEqual(geo_oracle.num_qubits, 8)

        # Test Weyl oracle
        weyl_oracle = builder.build_weyl_oracle(0)
        self.assertEqual(weyl_oracle.num_qubits, 8)

    def test_e8_grover_search(self):
        """Test E8 Grover search."""
        builder = E8OracleBuilder(self.config)
        oracle = builder.build_algebraic_oracle()

        grover = E8GroverSearch(oracle, self.config)

        # Test optimal iterations
        optimal = grover.calculate_optimal_iterations(240)
        self.assertGreater(optimal, 0)

        # Test Grover circuit
        grover_circuit = grover.build_grover_circuit()
        self.assertEqual(grover_circuit.num_qubits, 8)

        # Test fixed-point Grover
        fp_grover = grover.build_fixed_point_grover()
        self.assertEqual(fp_grover.num_qubits, 8)

    def test_e8_state_preparation(self):
        """Test E8 state preparation."""
        prep = E8StatePreparation(self.config)

        # Test uniform superposition
        uniform = prep.prepare_uniform_superposition()
        self.assertEqual(uniform.num_qubits, 8)

        # Test root type superposition
        type1 = prep.prepare_root_type_superposition('Type1')
        self.assertEqual(type1.num_qubits, 8)

        # Test Cartan eigenstate
        cartan = prep.prepare_cartan_eigenstate(0)
        self.assertEqual(cartan.num_qubits, 8)

    def test_e8_measurement_analysis(self):
        """Test E8 measurement analysis."""
        analyzer = E8MeasurementAnalysis()

        # Test with sample measurements
        counts = {
            '00000000': 100,
            '11110000': 80,
            '10101010': 60,
            '11111111': 40  # Index 255 (invalid)
        }

        decoded = analyzer.decode_measurement(counts)
        self.assertEqual(decoded['total_shots'], 280)
        self.assertIn('type1_probability', decoded)
        self.assertIn('type2_probability', decoded)

        # Test correlation analysis
        correlations = analyzer.analyze_correlations(counts)
        self.assertIsInstance(correlations, dict)

        # Test invariant extraction
        invariants = analyzer.extract_algebraic_invariants(counts)
        self.assertIn('average_root_norm', invariants)

    def test_e8_quantum_algorithms(self):
        """Test E8 quantum algorithms."""
        algorithms = E8QuantumAlgorithms(self.config)

        # Test root counting
        counting = algorithms.root_counting_algorithm()
        self.assertGreater(counting.num_qubits, 0)

        # Test classification
        classification = algorithms.root_classification_algorithm()
        self.assertGreater(classification.num_qubits, 0)

        # Test Cartan simulation
        evolution = algorithms.cartan_simulation(time=0.5)
        self.assertEqual(evolution.num_qubits, 8)

        # Test Dynkin diagram
        dynkin = algorithms.dynkin_diagram_encoding()
        self.assertEqual(dynkin.num_qubits, 8)


class TestQuantumSimulation(unittest.TestCase):
    """Test quantum simulation framework."""

    def setUp(self):
        """Set up simulation configuration."""
        self.config = SimulationConfig(
            backend_type='aer_simulator',
            shots=1024,
            noise_model=None,
            error_mitigation=False,
            verbose=False
        )

    def test_simulation_config(self):
        """Test simulation configuration."""
        self.config.validate()
        self.assertEqual(self.config.shots, 1024)
        self.assertEqual(self.config.backend_type, 'aer_simulator')

        # Test invalid config
        with self.assertRaises(ValueError):
            bad_config = SimulationConfig(backend_type='invalid')
            bad_config.validate()

    def test_quantum_simulator(self):
        """Test quantum simulator."""
        simulator = QuantumSimulator(self.config)

        # Create simple test circuit
        qc = QuantumCircuit(2, 2)
        qc.h(0)
        qc.cx(0, 1)
        qc.measure([0, 1], [0, 1])

        # Run simulation
        result = simulator.simulate(qc, shots=100)

        self.assertIsInstance(result, SimulationResult)
        self.assertEqual(result.shots, 100)
        self.assertIn('counts', result.__dict__)
        self.assertGreater(len(result.counts), 0)

    def test_batch_simulation(self):
        """Test batch simulation."""
        simulator = QuantumSimulator(self.config)

        # Create multiple test circuits
        circuits = []
        for i in range(3):
            qc = QuantumCircuit(2, 2, name=f'test_{i}')
            qc.h(0)
            if i > 0:
                qc.x(1)
            qc.measure([0, 1], [0, 1])
            circuits.append(qc)

        # Run batch simulation
        results = simulator.batch_simulate(circuits, parallel=False)

        self.assertEqual(len(results), 3)
        for result in results:
            self.assertIsInstance(result, SimulationResult)

    def test_e7e8_simulation_suite(self):
        """Test E7/E8 simulation suite."""
        suite = E7E8SimulationSuite(self.config)

        # Test E7 algorithm creation
        self.assertIsNotNone(suite.e7_algorithms)
        self.assertIsNotNone(suite.e7_decoder)

        # Test E8 algorithm creation
        self.assertIsNotNone(suite.e8_algorithms)
        self.assertIsNotNone(suite.e8_analyzer)

        # Create simple test circuit
        qc = QuantumCircuit(7, 7)
        qc.h(range(7))
        qc.measure(range(7), range(7))

        # Run simulation through suite
        result = suite.simulator.simulate(qc, shots=100)
        self.assertIsInstance(result, SimulationResult)


class TestIntegration(unittest.TestCase):
    """Integration tests for complete quantum system."""

    def test_e7_encoding_to_circuit(self):
        """Test E7 encoding to circuit integration."""
        # Create encoding
        config = EncodingConfig(encoding_type='index', num_qubits=7)
        encoder = IndexEncoder(config)

        # Create E7 circuit
        e7_config = E7CircuitConfig()
        algorithms = E7QuantumAlgorithms(e7_config)

        # Encode and create circuit
        encoding_circuit = encoder.encode_e7_indices()
        search_circuit = algorithms.root_search_algorithm('all')

        # Both should be compatible
        self.assertEqual(encoding_circuit.num_qubits, 7)
        self.assertGreaterEqual(search_circuit.num_qubits, 7)

    def test_e8_encoding_to_circuit(self):
        """Test E8 encoding to circuit integration."""
        # Create encoding
        config = EncodingConfig(encoding_type='index', num_qubits=8)
        encoder = IndexEncoder(config)

        # Create E8 circuit
        e8_config = E8CircuitConfig()
        algorithms = E8QuantumAlgorithms(e8_config)

        # Encode and create circuit
        encoding_circuit = encoder.encode_e8_indices()
        counting_circuit = algorithms.root_counting_algorithm()

        # Both should be compatible
        self.assertEqual(encoding_circuit.num_qubits, 8)
        self.assertGreaterEqual(counting_circuit.num_qubits, 8)

    def test_end_to_end_e7_simulation(self):
        """Test end-to-end E7 simulation."""
        # Configure
        sim_config = SimulationConfig(shots=100, verbose=False)
        suite = E7E8SimulationSuite(sim_config)

        # Create E7 validation circuit
        circuit = suite.e7_algorithms.root_validation_algorithm()

        # Simulate
        result = suite.simulator.simulate(circuit)

        # Decode results
        decoded = suite.e7_decoder.decode_index_measurement(result.counts)

        # Verify
        self.assertIn('measured_roots', decoded)
        self.assertEqual(decoded['total_shots'], 100)

    def test_end_to_end_e8_simulation(self):
        """Test end-to-end E8 simulation."""
        # Configure
        sim_config = SimulationConfig(shots=100, verbose=False)
        suite = E7E8SimulationSuite(sim_config)

        # Create E8 classification circuit
        circuit = suite.e8_algorithms.root_classification_algorithm()

        # Simulate
        result = suite.simulator.simulate(circuit)

        # Analyze results
        analysis = suite.e8_analyzer.decode_measurement(result.counts)

        # Verify
        self.assertIn('type1_probability', analysis)
        self.assertIn('type2_probability', analysis)
        self.assertEqual(analysis['total_shots'], 100)


def run_all_tests():
    """Run all unit tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test cases
    suite.addTests(loader.loadTestsFromTestCase(TestQuantumEncoding))
    suite.addTests(loader.loadTestsFromTestCase(TestE7QuantumCircuits))
    suite.addTests(loader.loadTestsFromTestCase(TestE8QuantumCircuits))
    suite.addTests(loader.loadTestsFromTestCase(TestQuantumSimulation))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {(result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100:.1f}%")
    print("=" * 80)

    return result


if __name__ == "__main__":
    result = run_all_tests()