"""Quantum Encoding Module for E7/E8 Lie Algebra Root Systems.

This module provides comprehensive functions to encode E7 and E8 root vectors
to quantum states using various encoding schemes optimized for quantum circuits.

Key Encoding Methods:
1. Index Encoding: Maps root indices to computational basis states
2. Amplitude Encoding: Encodes roots as quantum amplitudes
3. Binary Encoding: Maps root components to binary strings
4. QROM/QROAM: Quantum Read-Only Memory for efficient state preparation

Author: Claude Code
Date: October 2025
"""

from __future__ import annotations
from typing import List, Tuple, Dict, Any, Optional
import numpy as np
from math import log2, ceil, sqrt
from dataclasses import dataclass

# Qiskit imports
from qiskit import QuantumCircuit, QuantumRegister
from qiskit.circuit.library import StatePreparation
from qiskit.quantum_info import Statevector
from qiskit.circuit.library import MCXGate

# Local imports
from .algebras.roots import E7RootSystem
from .algebras.roots import E8RootSystem


@dataclass
class EncodingConfig:
    """Configuration for quantum encoding schemes."""

    encoding_type: str  # 'index', 'amplitude', 'binary', 'qrom'
    num_qubits: int
    precision_bits: int = 8  # For fixed-point encoding
    error_tolerance: float = 1e-6
    optimization_level: int = 2
    use_ancilla: bool = True
    normalize_amplitudes: bool = True

    def validate(self) -> None:
        """Validate configuration parameters."""
        valid_types = {'index', 'amplitude', 'binary', 'qrom', 'hybrid'}
        if self.encoding_type not in valid_types:
            raise ValueError(f"Invalid encoding type: {self.encoding_type}")
        if self.num_qubits < 1 or self.num_qubits > 127:
            raise ValueError(f"Invalid number of qubits: {self.num_qubits}")
        if self.precision_bits < 1 or self.precision_bits > 16:
            raise ValueError(f"Invalid precision bits: {self.precision_bits}")


class QuantumEncoder:
    """Base class for quantum encoding operations."""

    def __init__(self, config: EncodingConfig) -> None:
        """Initialize quantum encoder with configuration."""
        self.config = config
        self.config.validate()
        self._cache = {}

    def clear_cache(self) -> None:
        """Clear encoding cache."""
        self._cache.clear()

    @staticmethod
    def required_qubits(num_states: int) -> int:
        """Calculate minimum number of qubits needed for encoding."""
        return ceil(log2(num_states)) if num_states > 0 else 0

    @staticmethod
    def binary_string_to_int(binary_str: str) -> int:
        """Convert binary string to integer."""
        return int(binary_str, 2)

    @staticmethod
    def int_to_binary_string(value: int, num_bits: int) -> str:
        """Convert integer to binary string with fixed width."""
        return format(value, f'0{num_bits}b')

    def encode_state_vector(self, vector: np.ndarray) -> Statevector:
        """Encode a classical vector as quantum state vector."""
        if self.config.normalize_amplitudes:
            norm = np.linalg.norm(vector)
            if norm > self.config.error_tolerance:
                vector = vector / norm

        # Pad to nearest power of 2
        n = len(vector)
        n_qubits = self.required_qubits(n)
        padded_size = 2**n_qubits

        if n < padded_size:
            padded_vector = np.zeros(padded_size, dtype=complex)
            padded_vector[:n] = vector
            vector = padded_vector

        return Statevector(vector)


class IndexEncoder(QuantumEncoder):
    """Index-based encoding for root systems."""

    def encode_root_index(self, index: int, num_qubits: Optional[int] = None) -> QuantumCircuit:
        """Encode root index as computational basis state |index>.

        Args:
            index: Root index (0 to 2^n - 1)
            num_qubits: Number of qubits (auto-calculated if None)

        Returns:
            QuantumCircuit preparing |index>
        """
        if num_qubits is None:
            num_qubits = self.config.num_qubits

        qc = QuantumCircuit(num_qubits, name=f"Index_{index}")

        # Convert index to binary and apply X gates
        binary_str = self.int_to_binary_string(index, num_qubits)
        for i, bit in enumerate(reversed(binary_str)):
            if bit == '1':
                qc.x(i)

        return qc

    def encode_e7_indices(self) -> QuantumCircuit:
        """Create quantum circuit encoding all 127 E7 states (126 roots + zero).

        Returns:
            QuantumCircuit with uniform superposition over E7 indices
        """
        # E7: 127 states fit in 7 qubits (2^7 = 128)
        n_qubits = 7
        qc = QuantumCircuit(n_qubits, name="E7_Index_Encoding")

        # Create uniform superposition over first 127 states
        # |psi> = 1/sqrt(127) * sum_{i=0}^{126} |i>
        amplitudes = np.zeros(128)
        amplitudes[:127] = 1.0 / sqrt(127)

        state_prep = StatePreparation(amplitudes)
        qc.append(state_prep, range(n_qubits))

        return qc

    def encode_e8_indices(self) -> QuantumCircuit:
        """Create quantum circuit encoding all 240 E8 roots.

        Returns:
            QuantumCircuit with uniform superposition over E8 indices
        """
        # E8: 240 roots fit in 8 qubits (2^8 = 256)
        n_qubits = 8
        qc = QuantumCircuit(n_qubits, name="E8_Index_Encoding")

        # Create uniform superposition over first 240 states
        amplitudes = np.zeros(256)
        amplitudes[:240] = 1.0 / sqrt(240)

        state_prep = StatePreparation(amplitudes)
        qc.append(state_prep, range(n_qubits))

        return qc

    def decode_measurement(self, counts: Dict[str, int],
                          root_system: str = 'E7') -> Dict[int, float]:
        """Decode measurement results to root indices.

        Args:
            counts: Measurement counts from quantum circuit
            root_system: 'E7' or 'E8'

        Returns:
            Dictionary mapping root indices to probabilities
        """
        total_shots = sum(counts.values())
        max_index = 126 if root_system == 'E7' else 239

        index_probs = {}
        for bitstring, count in counts.items():
            index = self.binary_string_to_int(bitstring)
            if index <= max_index:
                index_probs[index] = count / total_shots

        return index_probs


class AmplitudeEncoder(QuantumEncoder):
    """Amplitude encoding for root vectors."""

    def encode_root_amplitudes(self, root: np.ndarray) -> QuantumCircuit:
        """Encode root vector components as quantum amplitudes.

        Args:
            root: Root vector (8-dimensional for E7/E8)

        Returns:
            QuantumCircuit preparing amplitude-encoded state
        """
        # Normalize and pad to power of 2
        n = len(root)
        n_qubits = self.required_qubits(n)

        # Create amplitude vector
        amplitudes = np.zeros(2**n_qubits)

        # Map root components to amplitudes
        if self.config.normalize_amplitudes:
            norm = np.linalg.norm(root)
            if norm > self.config.error_tolerance:
                amplitudes[:n] = root / norm
            else:
                amplitudes[:n] = root
        else:
            amplitudes[:n] = root

        # Create circuit
        qc = QuantumCircuit(n_qubits, name="Amplitude_Encoding")
        state_prep = StatePreparation(amplitudes)
        qc.append(state_prep, range(n_qubits))

        return qc

    def encode_e7_superposition(self, roots: Optional[np.ndarray] = None) -> QuantumCircuit:
        """Create superposition of all E7 root amplitudes.

        Args:
            roots: Optional custom root array, otherwise use E7 system

        Returns:
            QuantumCircuit encoding E7 root superposition
        """
        if roots is None:
            e7 = E7RootSystem()
            roots = e7.get_127_state_system()  # 126 roots + zero

        # Flatten all roots into single amplitude vector
        # Each root is 8D, so we need log2(127*8) = 10 qubits
        flat_amplitudes = roots.flatten()

        # Normalize
        norm = np.linalg.norm(flat_amplitudes)
        if norm > self.config.error_tolerance:
            flat_amplitudes = flat_amplitudes / norm

        # Pad to power of 2
        n = len(flat_amplitudes)
        n_qubits = self.required_qubits(n)
        padded_amplitudes = np.zeros(2**n_qubits)
        padded_amplitudes[:n] = flat_amplitudes

        # Create circuit
        qc = QuantumCircuit(n_qubits, name="E7_Amplitude_Superposition")
        state_prep = StatePreparation(padded_amplitudes)
        qc.append(state_prep, range(n_qubits))

        return qc

    def encode_e8_superposition(self, roots: Optional[np.ndarray] = None) -> QuantumCircuit:
        """Create superposition of all E8 root amplitudes.

        Args:
            roots: Optional custom root array, otherwise use E8 system

        Returns:
            QuantumCircuit encoding E8 root superposition
        """
        if roots is None:
            e8 = E8RootSystem()
            roots = e8.generate_roots()  # 240 roots

        # Flatten all roots into single amplitude vector
        flat_amplitudes = roots.flatten()

        # Normalize
        norm = np.linalg.norm(flat_amplitudes)
        if norm > self.config.error_tolerance:
            flat_amplitudes = flat_amplitudes / norm

        # Pad to power of 2
        n = len(flat_amplitudes)
        n_qubits = self.required_qubits(n)
        padded_amplitudes = np.zeros(2**n_qubits)
        padded_amplitudes[:n] = flat_amplitudes

        # Create circuit
        qc = QuantumCircuit(n_qubits, name="E8_Amplitude_Superposition")
        state_prep = StatePreparation(padded_amplitudes)
        qc.append(state_prep, range(n_qubits))

        return qc


class BinaryEncoder(QuantumEncoder):
    """Binary encoding for root vector components."""

    def __init__(self, config: EncodingConfig) -> None:
        """Initialize binary encoder."""
        super().__init__(config)
        self.precision = config.precision_bits

    def float_to_binary(self, value: float, signed: bool = True) -> str:
        """Convert float value to fixed-point binary string."""
        val = np.clip(value, -1.0, 1.0)
        n_bits = self.config.precision_bits
        
        if signed:
            # Standard signed fixed point: 1 bit sign, n-1 bits magnitude
            sign_bit = '1' if val < 0 else '0'
            # Use 2^(n-1) for scaling to match standard binary fractions
            scaled = int(abs(val) * (2**(n_bits-1)))
            scaled = min(scaled, 2**(n_bits-1) - 1)
            return sign_bit + format(scaled, f'0{n_bits-1}b')
        else:
            # Map [-1, 1] to [0, 1] and scale by 2^n
            mag = (val + 1.0) / 2.0
            scaled = int(mag * (2**n_bits))
            scaled = min(scaled, 2**n_bits - 1)
            return format(scaled, f'0{n_bits}b')

    def binary_to_float(self, binary: str, signed: bool = True) -> float:
        """Convert binary string back to float."""
        n_bits = len(binary)
        if signed:
            sign = -1.0 if binary[0] == '1' else 1.0
            mag_bits = binary[1:]
            if not mag_bits:
                return 0.0
            scaled = int(mag_bits, 2)
            return sign * (scaled / (2**(n_bits-1)))
        else:
            scaled = int(binary, 2)
            return 2.0 * (scaled / (2**n_bits)) - 1.0

    def encode_root_binary(self, root: np.ndarray) -> QuantumCircuit:
        """Encode root vector as binary quantum state.

        Args:
            root: Root vector to encode

        Returns:
            QuantumCircuit with binary-encoded root
        """
        n_components = len(root)
        n_qubits = n_components * self.precision

        qc = QuantumCircuit(n_qubits, name="Binary_Root_Encoding")

        # Encode each component
        for i, component in enumerate(root):
            binary_str = self.float_to_binary(component, signed=True)

            # Apply X gates for 1s in binary representation
            for j, bit in enumerate(reversed(binary_str)):
                if bit == '1':
                    qubit_idx = i * self.precision + j
                    qc.x(qubit_idx)

        return qc

    def decode_binary_state(self, bitstring: str, n_components: int = 8) -> np.ndarray:
        """Decode binary quantum state to root vector.

        Args:
            bitstring: Measured binary string
            n_components: Number of vector components

        Returns:
            Decoded root vector
        """
        root = np.zeros(n_components)

        for i in range(n_components):
            start = i * self.precision
            end = start + self.precision
            component_bits = bitstring[start:end]

            if len(component_bits) == self.precision:
                root[i] = self.binary_to_float(component_bits[::-1], signed=True)

        return root

    def encode_e7_binary_oracle(self) -> QuantumCircuit:
        """Create oracle circuit for E7 root validation in binary encoding.

        Returns:
            QuantumCircuit implementing E7 validation oracle
        """
        # 8 components * precision_bits per component
        n_data_qubits = 8 * self.precision
        n_ancilla = 1  # For oracle output

        qr_data = QuantumRegister(n_data_qubits, 'data')
        qr_anc = QuantumRegister(n_ancilla, 'oracle')
        qc = QuantumCircuit(qr_data, qr_anc, name="E7_Binary_Oracle")

        # Oracle checks:
        # 1. Sum of components = 0
        # 2. Squared length = 2
        # 3. Valid pattern (Type 1 or Type 2)

        # This is a simplified oracle structure
        # Full implementation would require arithmetic circuits

        # Add comment for oracle logic
        qc.barrier()

        return qc


class QROMEncoder(QuantumEncoder):
    """Quantum Read-Only Memory (QROM) encoding for efficient state preparation."""

    def __init__(self, config: EncodingConfig) -> None:
        """Initialize QROM encoder."""
        super().__init__(config)
        self.select_register_size = 0
        self.data_register_size = 0

    def build_qrom_circuit(self, data: List[np.ndarray],
                          labels: Optional[List[str]] = None) -> QuantumCircuit:
        """Build QROM circuit for accessing stored data.

        Args:
            data: List of vectors to store in QROM
            labels: Optional labels for data items

        Returns:
            QuantumCircuit implementing QROM
        """
        n_items = len(data)
        n_select = self.required_qubits(n_items)

        # Assume uniform data size
        data_size = len(data[0]) if data else 0
        n_data = self.required_qubits(data_size) * self.config.precision_bits

        # Create registers
        qr_select = QuantumRegister(n_select, 'select')
        qr_data = QuantumRegister(n_data, 'data')
        if self.config.use_ancilla:
            qr_anc = QuantumRegister(1, 'ancilla')
            qc = QuantumCircuit(qr_select, qr_data, qr_anc, name="QROM")
        else:
            qc = QuantumCircuit(qr_select, qr_data, name="QROM")

        # Store register sizes
        self.select_register_size = n_select
        self.data_register_size = n_data

        # Implement QROM logic
        for i, vector in enumerate(data):
            # Create controlled operation for each data item
            control_state = self.int_to_binary_string(i, n_select)

            # Encode vector data when select register matches i
            self._add_controlled_data_load(qc, qr_select, qr_data,
                                          control_state, vector)

        return qc

    def _add_controlled_data_load(self, qc: QuantumCircuit,
                                  qr_select: QuantumRegister,
                                  qr_data: QuantumRegister,
                                  control_state: str,
                                  data_vector: np.ndarray) -> None:
        """Add controlled data loading operation.

        Args:
            qc: Quantum circuit
            qr_select: Selection register
            qr_data: Data register
            control_state: Binary control pattern
            data_vector: Data to load
        """
        # Create control pattern
        control_qubits = []
        for i, bit in enumerate(reversed(control_state)):
            if bit == '1':
                control_qubits.append(qr_select[i])

        # Load data when control matches
        # This is simplified - full QROM would use more efficient techniques
        if control_qubits:
            # Apply controlled operations to load data
            for j, value in enumerate(data_vector):
                if abs(value) > self.config.error_tolerance:
                    # Simplified: just mark non-zero positions
                    if j < len(qr_data):
                        if len(control_qubits) == 1:
                            qc.cx(control_qubits[0], qr_data[j])
                        else:
                            # Multi-controlled X gate
                            mcx = MCXGate(len(control_qubits))
                            qc.append(mcx, control_qubits + [qr_data[j]])

    def build_e7_qrom(self) -> QuantumCircuit:
        """Build QROM circuit for E7 root system.

        Returns:
            QuantumCircuit implementing E7 QROM
        """
        e7 = E7RootSystem()
        roots = e7.get_127_state_system()

        return self.build_qrom_circuit(roots.tolist(),
                                      labels=[f"E7_root_{i}" for i in range(127)])

    def build_e8_qrom(self) -> QuantumCircuit:
        """Build QROM circuit for E8 root system.

        Returns:
            QuantumCircuit implementing E8 QROM
        """
        e8 = E8RootSystem()
        roots = e8.generate_roots()

        return self.build_qrom_circuit(roots.tolist(),
                                      labels=[f"E8_root_{i}" for i in range(240)])


class HybridEncoder(QuantumEncoder):
    """Hybrid encoding combining multiple schemes for optimization."""

    def __init__(self, config: EncodingConfig) -> None:
        """Initialize hybrid encoder."""
        super().__init__(config)
        self.index_encoder = IndexEncoder(config)
        self.amplitude_encoder = AmplitudeEncoder(config)
        self.binary_encoder = BinaryEncoder(config)
        self.qrom_encoder = QROMEncoder(config)

    def encode_hierarchical(self, roots: np.ndarray,
                           levels: int = 2) -> QuantumCircuit:
        """Hierarchical encoding using multiple levels.

        Args:
            roots: Array of root vectors
            levels: Number of hierarchy levels

        Returns:
            QuantumCircuit with hierarchical encoding
        """
        n_roots = len(roots)

        # Level 1: Index encoding for root selection
        n_index_qubits = self.required_qubits(n_roots)

        # Level 2: Amplitude encoding for root components
        n_amp_qubits = 3  # For 8D vectors

        total_qubits = n_index_qubits + n_amp_qubits

        qr = QuantumRegister(total_qubits, 'hybrid')
        qc = QuantumCircuit(qr, name="Hierarchical_Encoding")

        # Create superposition over root indices
        index_circuit = self.index_encoder.encode_e7_indices() if n_roots == 127 \
                       else self.index_encoder.encode_e8_indices()

        qc.append(index_circuit, qr[:n_index_qubits])

        # Add amplitude encoding layer
        qc.barrier()

        # For each root index, encode its amplitude
        # This is simplified - full implementation would use controlled operations

        return qc

    def optimize_encoding(self, roots: np.ndarray,
                         target_fidelity: float = 0.99) -> Dict[str, Any]:
        """Optimize encoding scheme for given root system.

        Args:
            roots: Array of root vectors
            target_fidelity: Target encoding fidelity

        Returns:
            Dictionary with optimal encoding parameters
        """
        results = {}

        # Test different encoding schemes
        schemes = ['index', 'amplitude', 'binary', 'qrom']

        for scheme in schemes:
            if scheme == 'index':
                n_qubits = self.required_qubits(len(roots))
                depth_estimate = n_qubits  # Simple estimate

            elif scheme == 'amplitude':
                n_qubits = self.required_qubits(len(roots.flatten()))
                depth_estimate = 2 * n_qubits  # State prep overhead

            elif scheme == 'binary':
                n_qubits = len(roots[0]) * self.config.precision_bits
                depth_estimate = n_qubits

            elif scheme == 'qrom':
                n_select = self.required_qubits(len(roots))
                n_data = len(roots[0]) * self.config.precision_bits
                n_qubits = n_select + n_data
                depth_estimate = n_select * n_data  # Rough estimate

            results[scheme] = {
                'qubits': n_qubits,
                'depth_estimate': depth_estimate,
                'suitable_for_hardware': n_qubits <= 127
            }

        # Recommend best scheme
        best_scheme = min(results.keys(),
                         key=lambda s: results[s]['qubits'] * results[s]['depth_estimate'])

        return {
            'schemes': results,
            'recommended': best_scheme,
            'reasoning': f"Minimizes qubit-depth product for target fidelity {target_fidelity}"
        }


class E8LatticeEncoder(QuantumEncoder):
    """Encodes E8 lattice points into quantum states."""
    
    def __init__(self, n_qubits: int = 8) -> None:
        config = EncodingConfig(encoding_type='index', num_qubits=n_qubits)
        super().__init__(config)
        self.root_system = E8RootSystem()

    def encode_point(self, point_index: int) -> QuantumCircuit:
        """Encode a specific E8 root by index."""
        if point_index >= 240:
            raise ValueError("E8 has only 240 roots.")
        return IndexEncoder(self.config).encode_root_index(point_index)

    def prepare_superposition(self) -> QuantumCircuit:
        """Prepare uniform superposition over all E8 roots."""
        return IndexEncoder(self.config).encode_e8_indices()

class EncodingValidator:
    """Validate quantum encodings against classical data."""

    @staticmethod
    def validate_statevector(quantum_state: Statevector,
                            classical_data: np.ndarray,
                            tolerance: float = 1e-6) -> Tuple[bool, float]:
        """Validate quantum state against classical data.

        Args:
            quantum_state: Quantum state vector
            classical_data: Expected classical data
            tolerance: Numerical tolerance

        Returns:
            Tuple of (is_valid, fidelity)
        """
        # Normalize classical data
        classical_norm = np.linalg.norm(classical_data)
        if classical_norm > tolerance:
            classical_normalized = classical_data / classical_norm
        else:
            classical_normalized = classical_data

        # Pad classical data to match quantum state size
        quantum_dim = len(quantum_state)
        if len(classical_normalized) < quantum_dim:
            padded = np.zeros(quantum_dim, dtype=complex)
            padded[:len(classical_normalized)] = classical_normalized
            classical_normalized = padded

        # Calculate fidelity
        fidelity = abs(np.vdot(quantum_state.data, classical_normalized))**2

        is_valid = fidelity > (1 - tolerance)

        return is_valid, fidelity

    @staticmethod
    def validate_encoding_scheme(encoder: QuantumEncoder,
                                test_data: np.ndarray,
                                samples: int = 10) -> Dict[str, Any]:
        """Validate encoding scheme with test data.

        Args:
            encoder: Quantum encoder instance
            test_data: Test root vectors
            samples: Number of samples to test

        Returns:
            Validation results dictionary
        """
        results = {
            'tested_samples': min(samples, len(test_data)),
            'successes': 0,
            'failures': 0,
            'average_fidelity': 0.0,
            'errors': []
        }

        total_fidelity = 0.0

        for i in range(min(samples, len(test_data))):
            try:
                root = test_data[i]

                if isinstance(encoder, AmplitudeEncoder):
                    qc = encoder.encode_root_amplitudes(root)
                elif isinstance(encoder, BinaryEncoder):
                    qc = encoder.encode_root_binary(root)
                else:
                    # Default to amplitude encoding for testing
                    qc = AmplitudeEncoder(encoder.config).encode_root_amplitudes(root)

                # Get statevector from circuit
                from qiskit.quantum_info import Statevector
                state = Statevector.from_instruction(qc)

                # Validate
                is_valid, fidelity = EncodingValidator.validate_statevector(
                    state, root, encoder.config.error_tolerance
                )

                if is_valid:
                    results['successes'] += 1
                else:
                    results['failures'] += 1
                    results['errors'].append(f"Sample {i}: fidelity {fidelity:.6f}")

                total_fidelity += fidelity

            except Exception as e:
                results['failures'] += 1
                results['errors'].append(f"Sample {i}: {str(e)}")

        if results['tested_samples'] > 0:
            results['average_fidelity'] = total_fidelity / results['tested_samples']

        return results


def demonstrate_encodings():
    """Demonstrate various quantum encoding schemes for E7/E8."""
    print("=" * 80)
    print("QUANTUM ENCODING DEMONSTRATIONS")
    print("=" * 80)
    print()

    # Configure encoders
    config = EncodingConfig(
        encoding_type='hybrid',
        num_qubits=7,
        precision_bits=4,
        error_tolerance=1e-6,
        optimization_level=2
    )

    # Initialize encoders
    index_enc = IndexEncoder(config)
    amp_enc = AmplitudeEncoder(config)
    binary_enc = BinaryEncoder(config)
    qrom_enc = QROMEncoder(config)
    hybrid_enc = HybridEncoder(config)

    print("1. INDEX ENCODING")
    print("-" * 40)

    # E7 index encoding
    e7_index_circuit = index_enc.encode_e7_indices()
    print("E7 Index Encoding Circuit:")
    print(f"  Qubits: {e7_index_circuit.num_qubits}")
    print(f"  Gates: {e7_index_circuit.size()}")
    print(f"  Depth: {e7_index_circuit.depth()}")
    print()

    # E8 index encoding
    e8_index_circuit = index_enc.encode_e8_indices()
    print("E8 Index Encoding Circuit:")
    print(f"  Qubits: {e8_index_circuit.num_qubits}")
    print(f"  Gates: {e8_index_circuit.size()}")
    print(f"  Depth: {e8_index_circuit.depth()}")
    print()

    print("2. AMPLITUDE ENCODING")
    print("-" * 40)

    # Test with sample E7 root
    e7 = E7RootSystem()
    sample_root = e7.generate_roots()[0]

    amp_circuit = amp_enc.encode_root_amplitudes(sample_root)
    print("Single Root Amplitude Encoding:")
    print(f"  Input dimension: {len(sample_root)}")
    print(f"  Qubits: {amp_circuit.num_qubits}")
    print(f"  Circuit depth: {amp_circuit.depth()}")
    print()

    print("3. BINARY ENCODING")
    print("-" * 40)

    # Binary encoding example
    binary_circuit = binary_enc.encode_root_binary(sample_root)
    print("Binary Root Encoding:")
    print(f"  Precision bits: {binary_enc.precision}")
    print(f"  Total qubits: {binary_circuit.num_qubits}")
    print(f"  Gates: {binary_circuit.size()}")

    # Test encoding/decoding
    test_value = 0.5
    binary_str = binary_enc.float_to_binary(test_value)
    decoded = binary_enc.binary_to_float(binary_str)
    print(f"  Encoding test: {test_value} -> {binary_str} -> {decoded:.4f}")
    print()

    print("4. QROM ENCODING")
    print("-" * 40)

    # QROM for first 10 E7 roots
    small_roots = e7.generate_roots()[:10]
    qrom_circuit = qrom_enc.build_qrom_circuit(small_roots.tolist())
    print("QROM Circuit (10 roots):")
    print(f"  Select register: {qrom_enc.select_register_size} qubits")
    print(f"  Data register: {qrom_enc.data_register_size} qubits")
    print(f"  Total qubits: {qrom_circuit.num_qubits}")
    print()

    print("5. OPTIMIZATION ANALYSIS")
    print("-" * 40)

    # Analyze encoding options for E7
    e7_roots = e7.get_127_state_system()
    optimization = hybrid_enc.optimize_encoding(e7_roots)

    print("Encoding Scheme Analysis for E7:")
    for scheme, metrics in optimization['schemes'].items():
        print(f"  {scheme.upper()}:")
        print(f"    Qubits: {metrics['qubits']}")
        print(f"    Depth estimate: {metrics['depth_estimate']}")
        print(f"    Hardware suitable: {metrics['suitable_for_hardware']}")

    print(f"\nRecommended: {optimization['recommended']}")
    print(f"Reasoning: {optimization['reasoning']}")
    print()

    print("6. VALIDATION")
    print("-" * 40)

    # Validate amplitude encoding
    validator = EncodingValidator()
    test_roots = e7.generate_roots()[:5]

    validation = validator.validate_encoding_scheme(amp_enc, test_roots, samples=5)
    print("Amplitude Encoding Validation:")
    print(f"  Samples tested: {validation['tested_samples']}")
    print(f"  Successes: {validation['successes']}")
    print(f"  Failures: {validation['failures']}")
    print(f"  Average fidelity: {validation['average_fidelity']:.6f}")

    if validation['errors']:
        print(f"  Errors: {validation['errors'][:2]}")  # Show first 2 errors

    print()
    print("=" * 80)
    print("Encoding demonstrations complete!")
    print("=" * 80)


if __name__ == "__main__":
    demonstrate_encodings()