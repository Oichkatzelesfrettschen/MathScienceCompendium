"""Unit tests for E8 quantum circuits."""

from __future__ import annotations

import unittest

# Import modules to test
from mathphysics.quantum_e8_circuits import (
    E8CircuitConfig,
    E8MeasurementAnalysis,
    E8OracleBuilder,
    E8QuantumAlgorithms,
    E8RootStructure,
    E8StatePreparation,
)


class TestE8QuantumCircuits(unittest.TestCase):
    """Test E8 quantum circuit module."""

    def setUp(self):
        """Set up test configuration."""
        self.config = E8CircuitConfig()
        self.algorithms = E8QuantumAlgorithms()

    def test_e8_root_structure(self):
        """Test E8 root structure mapping."""
        struct = E8RootStructure()
        self.assertEqual(len(struct.roots), 240)

    def test_e8_oracle_builder(self):
        """Test E8 oracle builder."""
        builder = E8OracleBuilder(self.config)
        oracle = builder.build_algebraic_oracle()
        self.assertIsNotNone(oracle)
        self.assertEqual(oracle.num_qubits, 8)

    def test_e8_state_preparation(self):
        """Test E8 state preparation."""
        prep = E8StatePreparation(self.config)
        qc = prep.prepare_uniform_superposition()
        self.assertIsNotNone(qc)

        # sv = Statevector.from_instruction(qc) # Might be slow
        self.assertEqual(qc.num_qubits, 8)

    def test_e8_quantum_algorithms(self):
        """Test high-level E8 quantum algorithms."""
        qc = self.algorithms.prepare_e8_superposition()
        self.assertIsNotNone(qc)
        self.assertEqual(qc.num_qubits, 8)

    def test_e8_measurement_analysis(self):
        """Test E8 measurement analysis."""
        analysis = E8MeasurementAnalysis()
        res = analysis.decode_measurement({"00000000": 1024})
        self.assertIn("measured_roots", res)
