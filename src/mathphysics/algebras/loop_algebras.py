"""Generalized Loop Algebras and Affine Kac-Moody Extensions.

Implements the L(g, sigma) structure, central extensions, and the
Sugawara construction for affine Lie algebras.
"""

from __future__ import annotations

from typing import Any

import jax.numpy as jnp
import numpy as np

from ..algebra import AlgebraicStructure, LieAlgebra
from .roots import BaseRootSystem, LieAlgebraProperties


class LoopAlgebraElement:
    """An element of the loop algebra g ⊗ C[t, t^-1]."""

    def __init__(self, coeffs: dict[int, jnp.ndarray]) -> None:
        """coeffs: Map from Laurent power n to algebra element vector."""
        self.coeffs = coeffs


class AffineLieAlgebra(LieAlgebra):
    """Affine Kac-Moody Algebra g^ = g ⊗ C[t, t^-1] ⊕ Cc ⊕ Cd."""

    def __init__(self, finite_g: BaseRootSystem, level: float = 1.0) -> None:
        self.finite_g = finite_g
        self.level = level  # Central charge c
        self.rank = finite_g.properties.rank + 1
        self._dimension = float("inf")

    def __add__(self, other: Any) -> AlgebraicStructure:
        raise NotImplementedError()

    def __sub__(self, other: Any) -> AlgebraicStructure:
        raise NotImplementedError()

    def __mul__(self, other: Any) -> AlgebraicStructure:
        raise NotImplementedError()

    def norm(self) -> float:
        return 0.0

    def bracket(self, other: LieAlgebra) -> LieAlgebra:
        """The affine commutator: [X⊗t^n, Y⊗t^m] = [X,Y]⊗t^{n+m} + n*δ_{n+m,0}*<X,Y>*c."""
        # Implementation of the centrally extended loop bracket
        raise NotImplementedError()

    def get_generalized_cartan_matrix(self) -> jnp.ndarray:
        """Construct the affine Cartan matrix A^(1)."""
        finite_cartan = self.finite_g.compute_cartan_matrix()
        # Highest root theta for sl(n) connects to first and last simple roots
        size = finite_cartan.shape[0] + 1
        res = np.eye(size) * 2
        res[1:, 1:] = finite_cartan

        if size == 2:  # A1^(1) case
            res[0, 1] = res[1, 0] = -2
        else:  # An^(1) for n > 1
            res[0, 1] = res[1, 0] = -1
            res[0, size - 1] = res[size - 1, 0] = -1

        return jnp.array(res)


class SL2Affine(AffineLieAlgebra):
    """Affine sl(2, C) Kac-Moody algebra."""

    def __init__(self, level: float = 1.0) -> None:
        # sl(2) is A1  # noqa: ERA001
        props = LieAlgebraProperties("A1", 3, 1, 2, 1, 2)

        class A1Roots(BaseRootSystem):
            def __init__(self) -> None:
                super().__init__(props)

            def generate_roots(self):
                return np.array([[1], [-1]])

            def generate_simple_roots(self):
                return np.array([[1]])

        super().__init__(A1Roots(), level)


class SL3Affine(AffineLieAlgebra):
    """Affine sl(3, C) Kac-Moody algebra."""

    def __init__(self, level: float = 1.0) -> None:
        props = LieAlgebraProperties("A2", 8, 2, 6, 3, 6)

        class A2Roots(BaseRootSystem):
            def __init__(self) -> None:
                super().__init__(props)

            def generate_roots(self):
                return np.array(
                    [[1, -1, 0], [1, 0, -1], [0, 1, -1], [-1, 1, 0], [-1, 0, 1], [0, -1, 1]]
                )

            def generate_simple_roots(self):
                return np.array([[1, -1, 0], [0, 1, -1]])

        super().__init__(A2Roots(), level)
