"""JAX-Accelerated Clifford (Geometric) Algebra Engine.

Provides high-performance multivector operations by pre-computing
multiplication tables and utilizing JIT-compiled tensor contractions.
Optimized for NVIDIA SM89 (RTX 4070 Ti).
"""

from __future__ import annotations

from functools import partial
from typing import Any, ClassVar

import jax
import jax.numpy as jnp
import numpy as np

from ..algebra import CliffordAlgebra


class CliffordEngine:
    """Singleton engine to manage JIT-compiled GA tables."""

    _instance = None

    def __init__(self, signature: tuple[int, int, int]) -> None:
        if len(signature) != 3 or any(component < 0 for component in signature):
            raise ValueError("Clifford signature must contain three nonnegative integers")
        self.signature = signature
        self.size = 2 ** (sum(signature))
        self.mt_idx, self.mt_sign = self._precompute_multiplication_table()

        # Move tables to GPU
        self.mt_idx = jnp.array(self.mt_idx)
        self.mt_sign = jnp.array(self.mt_sign)
        basis_indices = np.arange(self.size, dtype=np.int32)
        disjoint_mask = (basis_indices[:, None] & basis_indices[None, :]) == 0
        self.wedge_sign = jnp.array(np.asarray(self.mt_sign) * disjoint_mask)

    def _precompute_multiplication_table(self):
        p, q, r = self.signature
        size = 2 ** (p + q + r)
        mt_idx = np.zeros((size, size), dtype=np.int32)
        mt_sign = np.zeros((size, size), dtype=np.float32)

        for i in range(size):
            for j in range(size):
                res_idx = i ^ j
                res_sign = 1.0
                # Standard GA sign logic
                for bit in range(p + q + r):
                    if (j >> bit) & 1:
                        if bin(i >> (bit + 1)).count("1") % 2:
                            res_sign *= -1.0
                        if (i >> bit) & 1:
                            if bit < p:
                                pass
                            elif bit < p + q:
                                res_sign *= -1.0
                            else:
                                res_sign = 0.0
                mt_idx[i, j] = res_idx
                mt_sign[i, j] = res_sign
        return mt_idx, mt_sign

    @partial(jax.jit, static_argnums=(0,))
    def gp(self, a_coeffs: jnp.ndarray, b_coeffs: jnp.ndarray) -> jnp.ndarray:
        """Geometric product via JIT-compiled tensor mapping."""
        # a_coeffs: (size,), b_coeffs: (size,)
        # res[k] = sum(a[i] * b[j] * mt_sign[i,j]) where mt_idx[i,j] == k

        # 1. Compute all pairwise products: (size, size)
        terms = a_coeffs[:, None] * b_coeffs[None, :] * self.mt_sign

        # 2. Vectorized aggregation into result vector
        # We flatten the (size, size) arrays and use segment_sum or scatter_add
        res = jnp.zeros(self.size)
        res = res.at[self.mt_idx.ravel()].add(terms.ravel())
        return res

    @partial(jax.jit, static_argnums=(0,))
    def exterior_product(self, a_coeffs: jnp.ndarray, b_coeffs: jnp.ndarray) -> jnp.ndarray:
        """Exterior product using only disjoint basis blades."""
        terms = a_coeffs[:, None] * b_coeffs[None, :] * self.wedge_sign
        result = jnp.zeros(self.size)
        return result.at[self.mt_idx.ravel()].add(terms.ravel())


class Multivector(CliffordAlgebra):
    """Production-grade Multivector utilizing JIT-accelerated kernels."""

    _engines: ClassVar[dict[tuple[int, int, int], CliffordEngine]] = {}

    def __init__(self, coeffs: np.ndarray | jnp.ndarray, signature: tuple[int, int, int]) -> None:
        if signature not in Multivector._engines:
            Multivector._engines[signature] = CliffordEngine(signature)
        self.engine = Multivector._engines[signature]
        if tuple(coeffs.shape) != (self.engine.size,):
            raise ValueError(
                f"Clifford coefficients must have shape ({self.engine.size},), "
                f"got {tuple(coeffs.shape)}"
            )
        self.coeffs = jnp.array(coeffs) if not isinstance(coeffs, jnp.ndarray) else coeffs
        self.signature = signature
        self.n_dims = round(np.log2(self.coeffs.shape[0]))

    def _require_matching_signature(self, other: Multivector) -> None:
        if self.signature != other.signature:
            raise ValueError(f"Clifford signatures differ: {self.signature} and {other.signature}")

    def geometric_product(self, other: Multivector) -> Multivector:
        self._require_matching_signature(other)
        res_coeffs = self.engine.gp(self.coeffs, other.coeffs)
        return Multivector(res_coeffs, self.signature)

    def wedge(self, other: Multivector) -> Multivector:
        """Return the exterior product of two multivectors."""
        self._require_matching_signature(other)
        result_coefficients = self.engine.exterior_product(self.coeffs, other.coeffs)
        return Multivector(result_coefficients, self.signature)

    def inner(self, other: Multivector) -> float:
        """Return the scalar product, the grade-zero part of the geometric product."""
        self._require_matching_signature(other)
        return float(self.geometric_product(other).coeffs[0])

    def __add__(self, other: Multivector) -> Multivector:
        self._require_matching_signature(other)
        return Multivector(self.coeffs + other.coeffs, self.signature)

    def __sub__(self, other: Multivector) -> Multivector:
        self._require_matching_signature(other)
        return Multivector(self.coeffs - other.coeffs, self.signature)

    def __mul__(self, other: Any) -> Multivector:
        if isinstance(other, (int, float, complex, jnp.ndarray)):
            return Multivector(self.coeffs * other, self.signature)
        return self.geometric_product(other)

    def norm(self) -> float:
        return float(jnp.sqrt(jnp.sum(jnp.square(self.coeffs))))
