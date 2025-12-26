"""Unit tests for quantum simulation modules.

Tests for quantum_encoding, quantum_e7_circuits, quantum_e8_circuits,
and quantum_simulation modules.

Author: Claude Code
Date: October 2025
"""

from __future__ import annotations
import unittest
import warnings

# Import modules to test
from mathphysics.quantum_encoding import (
    EncodingConfig, IndexEncoder
)

# Qiskit imports for testing

warnings.filterwarnings('ignore')

class TestQuantumEncoding(unittest.TestCase):
    """Test quantum encoding module."""

    def setUp(self):
        """Set up test configuration."""
        self.config = EncodingConfig(n_qubits=3)
        self.encoder = IndexEncoder(self.config)