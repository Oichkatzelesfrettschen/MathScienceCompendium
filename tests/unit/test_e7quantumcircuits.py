"""Unit tests for E7 quantum circuits."""

from __future__ import annotations
import unittest
import numpy as np
from qiskit.quantum_info import Statevector

# Import modules to test
from mathphysics.quantum_e7_circuits import (
    E7CircuitConfig,
    E7OracleBuilder,
    E7GroverOperator,
    E7StatePreparation,
    E7MeasurementDecoder,
    E7QuantumAlgorithms,
)


class TestE7QuantumCircuits(unittest.TestCase):
    """Test E7 quantum circuit module."""

    def setUp(self):
        """Set up test configuration."""
        self.config = E7CircuitConfig()
        self.algorithms = E7QuantumAlgorithms()

    def test_e7_oracle_construction(self):
        """Test E7 oracle builder."""
        builder = E7OracleBuilder(self.config)
        oracle = builder.build_algebraic_oracle()
        self.assertIsNotNone(oracle)
        # E7 rank is 7
        self.assertEqual(oracle.num_qubits, 7)

    def test_e7_grover_operator(self):
        """Test E7 Grover operator."""
        builder = E7OracleBuilder(self.config)
        oracle = builder.build_algebraic_oracle()
        grover = E7GroverOperator(oracle, self.config)
        op = grover.build_diffusion_operator()
        self.assertIsNotNone(op)

    def test_e7_state_preparation(self):
        """Test E7 state preparation."""
        prep = E7StatePreparation(self.config)
        qc = prep.prepare_uniform_superposition()
        self.assertIsNotNone(qc)

        # Verify uniform superposition over 127 states
        sv = Statevector.from_instruction(qc)
        self.assertAlmostEqual(sv.data[0], 1.0 / np.sqrt(127))

    def test_e7_quantum_algorithms(self):
        """Test high-level E7 quantum algorithms."""
        qc = self.algorithms.root_search_algorithm()
        self.assertIsNotNone(qc)
        # May be transpiled to 27+ qubits depending on backend
        self.assertGreaterEqual(qc.num_qubits, 7)

    def test_e7_measurement_decoding(self):
        """Test decoding of E7 measurements."""
        decoder = E7MeasurementDecoder()
        res = decoder.decode_index_measurement({"0000000": 1024})
        self.assertIn("total_shots", res)
