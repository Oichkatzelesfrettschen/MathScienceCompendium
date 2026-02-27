"""Integration tests for algebraic-quantum framework."""

from __future__ import annotations
import unittest

# Import modules to test
from mathphysics.quantum_e8_circuits import E8QuantumAlgorithms
from mathphysics.quantum_simulation import UnifiedSimulation


class TestIntegration(unittest.TestCase):
    """Test full integration loop."""

    def test_e8_encoding_to_circuit(self):
        """Test encoding E8 roots into circuits."""
        algo = E8QuantumAlgorithms()
        qc = algo.prepare_e8_superposition()
        self.assertEqual(qc.num_qubits, 8)

    def test_end_to_end_e8_simulation(self):
        """Test end-to-end E8 simulation loop."""
        sim = UnifiedSimulation(n_qubits=8)
        res = sim.run_experiment("e8_search")
        self.assertEqual(res["experiment"], "e8_search")
        self.assertIn("counts", res)
        self.assertIn("top_measurement", res)
