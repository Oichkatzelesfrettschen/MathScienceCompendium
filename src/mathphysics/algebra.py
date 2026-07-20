"""Abstract Base Classes for Algebraic Structures.

Provides a unified interface for Lie, Jordan, and Clifford algebras,
ensuring consistent API design and hardware-agnostic execution.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from typing_extensions import Self


class AlgebraicStructure(ABC):
    """Base interface for all algebraic systems in the framework."""

    @abstractmethod
    def __add__(self, other: Any) -> AlgebraicStructure:
        pass

    @abstractmethod
    def __sub__(self, other: Any) -> AlgebraicStructure:
        pass

    @abstractmethod
    def __mul__(self, other: Any) -> AlgebraicStructure:
        pass

    @abstractmethod
    def norm(self) -> float:
        """Calculate the algebraic norm."""
        pass


class MultiplicativeAlgebra(AlgebraicStructure):
    """Interface for algebras with a defined unit and inverse."""

    @abstractmethod
    def inverse(self) -> MultiplicativeAlgebra:
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        pass


class LieAlgebra(AlgebraicStructure):
    """Interface for Lie algebras with commutator brackets."""

    @abstractmethod
    def bracket(self, other: LieAlgebra) -> LieAlgebra:
        """The Lie bracket [A, B]."""
        pass


class JordanAlgebra(AlgebraicStructure):
    """Interface for Jordan algebras with Jordan products."""

    @abstractmethod
    def jordan_product(self, other: Self) -> Self:
        """The Jordan product (A*B + B*A) / 2."""
        pass


class CliffordAlgebra(AlgebraicStructure):
    """Interface for Clifford (Geometric) algebras."""

    @abstractmethod
    def geometric_product(self, other: Self) -> Self:
        pass

    @abstractmethod
    def wedge(self, other: Self) -> Self:
        """The outer (Grassmann) product."""
        pass

    @abstractmethod
    def inner(self, other: Self) -> float:
        """The inner product."""
        pass
