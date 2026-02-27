"""Unified Quantum Physics Simulation Engine.

Integrates Lie algebraic structures with quantum circuit representations
to model fundamental symmetries and field interactions.
"""

from __future__ import annotations

import json
from typing import Any

from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

from .config import Config
from .quantum_e7_circuits import E7MeasurementDecoder, E7QuantumAlgorithms
from .quantum_e8_circuits import E8MeasurementAnalysis, E8QuantumAlgorithms
from .quantum_encoding import E8LatticeEncoder


class UnifiedSimulation:
    """Core simulator bridging abstract algebra and quantum execution."""

    def __init__(self, n_qubits: int = 8) -> None:
        self.config = Config()
        self.n_qubits = n_qubits
        self.encoder = E8LatticeEncoder(n_qubits)
        self.algorithms_e8 = E8QuantumAlgorithms()
        self.analysis_e8 = E8MeasurementAnalysis()
        self.algorithms_e7 = E7QuantumAlgorithms()
        self.decoder_e7 = E7MeasurementDecoder()
        self.backend = AerSimulator()

    def run_experiment(self, experiment_type: str = "e8_search") -> dict[str, Any]:
        """Execute a full algebraic-quantum simulation loop."""
        qc = QuantumCircuit(self.n_qubits)

        if experiment_type == "e8_search":
            qc = self.algorithms_e8.prepare_e8_superposition()
            # Simplified oracle marking
            qc.h(range(self.n_qubits))

        qc.measure_all()

        # Transpile and simulate
        t_qc = transpile(qc, self.backend)
        result = self.backend.run(t_qc, shots=1024).result()
        counts = result.get_counts()

        return {
            "experiment": experiment_type,
            "counts": counts,
            "top_measurement": max(counts, key=counts.get),
        }

    def save_results(self, results: dict[str, Any], filename: str) -> None:
        """Persist simulation results to disk."""
        path = self.config.RESULTS_DIR / filename
        with path.open("w") as f:
            json.dump(results, f, indent=2)
        print(f"Results saved to {path}")


def run_production_simulation() -> None:
    """Execute standard production simulation suite."""
    sim = UnifiedSimulation()
    res = sim.run_experiment("e8_search")
    sim.save_results(res, "quantum_search_results.json")
