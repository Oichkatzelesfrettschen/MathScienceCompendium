"""JAX-Accelerated Jordan Algebra (Albert Algebra) Implementation.

Implements Hermitian 3x3 matrices over octonions using block-vectorized
JAX operations for GPU offload.
"""

from __future__ import annotations

from typing import Any

import numpy as np


try:
    import jax.numpy as jnp
    from jax import jit

    HAS_JAX = True
except ImportError:
    jnp = np  # Fallback to numpy
    HAS_JAX = False

    def jit(func=None, **_kwargs):
        """Dummy jit decorator when JAX is not available."""
        if func is None:
            return lambda f: f
        return func


from ..algebra import JordanAlgebra
from .cayley_dickson import Octonion


def _build_octonion_multiplication_tensor() -> np.ndarray:
    """Return structure constants matching the canonical Octonion product."""
    tensor = np.zeros((8, 8, 8), dtype=np.float64)
    for left_index in range(8):
        left = Octonion.basis_element(left_index)
        for right_index in range(8):
            right = Octonion.basis_element(right_index)
            tensor[left_index, right_index, :] = (left * right).coeffs
    return tensor


OCTONION_MULTIPLICATION_TENSOR = jnp.asarray(_build_octonion_multiplication_tensor())


class AlbertAlgebraElement(JordanAlgebra):
    """An element of the 27-dimensional Albert algebra h3(O)."""

    def __init__(self, data: jnp.ndarray | np.ndarray | list) -> None:
        """Initialize with a (3, 3, 8) tensor representing 3x3 Octonions."""
        if isinstance(data, list):
            # Check if it's a list of Octonions
            if len(data) > 0 and isinstance(data[0], list) and isinstance(data[0][0], Octonion):
                flat_data = np.zeros((3, 3, 8))
                for i in range(3):
                    for j in range(3):
                        flat_data[i, j, :] = data[i][j].coeffs
                self.data = jnp.array(flat_data)
            else:
                self.data = jnp.array(data)
        else:
            self.data = jnp.array(data) if not isinstance(data, jnp.ndarray) else data
        if self.data.shape != (3, 3, 8):
            raise ValueError("Albert algebra data must have shape (3, 3, 8)")
        if not self.is_hermitian(tolerance=1e-6):
            raise ValueError("Albert algebra data must be Hermitian over the octonions")

    @staticmethod
    def from_octonions(matrix: list[list[Octonion]]) -> AlbertAlgebraElement:
        # Convert List[List[Octonion]] to (3, 3, 8) tensor
        flat_data = np.zeros((3, 3, 8))
        for i in range(3):
            for j in range(3):
                flat_data[i, j, :] = matrix[i][j].coeffs
        return AlbertAlgebraElement(jnp.array(flat_data))

    def jordan_product(self, other: AlbertAlgebraElement) -> AlbertAlgebraElement:
        """GPU-accelerated Jordan product."""
        # Call static JIT-compiled function with raw data tensors
        res_data = self._jordan_product_kernel(self.data, other.data)
        return AlbertAlgebraElement(res_data)

    @staticmethod
    @jit
    def _jordan_product_kernel(A: jnp.ndarray, B: jnp.ndarray) -> jnp.ndarray:
        """The core JAX-accelerated Jordan product kernel."""
        # Jordan product is (A*B + B*A) / 2
        # For CI, we ensure the kernel logic is valid for all tracers
        ab = AlbertAlgebraElement._mat_mul_oct(A, B)
        ba = AlbertAlgebraElement._mat_mul_oct(B, A)
        return (ab + ba) * 0.5

    @staticmethod
    @jit
    def _mat_mul_oct(A: jnp.ndarray, B: jnp.ndarray) -> jnp.ndarray:
        """Compute 3x3 matrix multiplication with octonion entries."""
        return jnp.einsum("ika,kjb,abc->ijc", A, B, OCTONION_MULTIPLICATION_TENSOR)

    @staticmethod
    def identity() -> AlbertAlgebraElement:
        data = jnp.zeros((3, 3, 8))
        for diagonal_index in range(3):
            data = data.at[diagonal_index, diagonal_index, 0].set(1.0) if HAS_JAX else data
            if not HAS_JAX:
                data[diagonal_index, diagonal_index, 0] = 1.0
        return AlbertAlgebraElement(data)

    def is_hermitian(self, tolerance: float = 1e-10) -> bool:
        """Check diagonal reality and conjugate symmetry."""
        values = np.asarray(self.data)
        for row_index in range(3):
            if np.max(np.abs(values[row_index, row_index, 1:])) > tolerance:
                return False
            for column_index in range(row_index + 1, 3):
                conjugate = values[row_index, column_index].copy()
                conjugate[1:] *= -1.0
                if not np.allclose(
                    conjugate,
                    values[column_index, row_index],
                    rtol=0.0,
                    atol=tolerance,
                ):
                    return False
        return True

    def trace(self) -> jnp.ndarray:
        # Return the (8,) sum of diagonal octonions
        return jnp.sum(jnp.diagonal(self.data, axis1=0, axis2=1), axis=1)

    def norm(self) -> float:
        return float(jnp.linalg.norm(self.data))

    def __add__(self, other: AlbertAlgebraElement) -> AlbertAlgebraElement:
        return AlbertAlgebraElement(self.data + other.data)

    def __sub__(self, other: AlbertAlgebraElement) -> AlbertAlgebraElement:
        return AlbertAlgebraElement(self.data - other.data)

    def __mul__(self, other: Any) -> AlbertAlgebraElement:
        if isinstance(other, (int, float, jnp.ndarray)):
            return AlbertAlgebraElement(self.data * other)
        raise NotImplementedError("Use jordan_product")
