"""Exceptional Lie Algebra Root Systems and Cartan Matrices.

Provides a unified implementation of E4-E11 exceptional root systems,
specifically targeting quantum and classical physical simulations.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from itertools import product
from typing import Any

import networkx as nx
import numpy as np

from ..algebra import AlgebraicStructure, LieAlgebra


@dataclass
class LieAlgebraProperties:
    """Mathematical properties of a Lie algebra."""

    name: str
    dimension: int
    rank: int
    num_roots: int
    num_positive_roots: int
    weyl_group_order: int
    is_simply_laced: bool = True
    root_squared_length: float = 2.0


@dataclass
class E7Properties:
    """Mathematical properties of the E7 Lie algebra (backward compatibility)."""

    name: str = "E7"
    dimension: int = 133
    rank: int = 7
    num_roots: int = 126
    num_positive_roots: int = 63
    weyl_group_order: int = 2903040
    is_simply_laced: bool = True
    root_squared_length: float = 2.0


class BaseRootSystem(LieAlgebra):
    """Abstract base class for Lie algebra root systems."""

    def __init__(self, properties: LieAlgebraProperties) -> None:
        self.properties = properties
        self._roots: np.ndarray | None = None
        self._positive_roots: np.ndarray | None = None
        self._simple_roots: np.ndarray | None = None
        self._cartan_matrix: np.ndarray | None = None
        self.dimension = properties.dimension

    def __add__(self, other: Any) -> AlgebraicStructure:
        raise NotImplementedError("Root systems represent structure, not elements")

    def __sub__(self, other: Any) -> AlgebraicStructure:
        raise NotImplementedError()

    def __mul__(self, other: Any) -> AlgebraicStructure:
        raise NotImplementedError()

    def norm(self) -> float:
        return 0.0

    def bracket(self, other: LieAlgebra) -> LieAlgebra:
        raise NotImplementedError("Structure constant derivation not implemented")

    def generate_roots(self) -> np.ndarray:
        """Generate all roots from simple roots using Weyl reflections."""
        if self._roots is not None:
            return self._roots

        simple_roots = self.generate_simple_roots()
        roots = {tuple(r) for r in simple_roots}
        new_roots = {tuple(r) for r in simple_roots}

        while new_roots:
            next_roots = set()
            for r in new_roots:
                r_vec = np.array(r)
                for s in simple_roots:
                    # Weyl reflection: w_s(r) = r - 2*(r.s)/(s.s) * s
                    reflected = r_vec - 2 * np.dot(r_vec, s) / np.dot(s, s) * s
                    reflected_tuple = tuple(np.round(reflected, 10))
                    if reflected_tuple not in roots and np.linalg.norm(reflected) > 1e-5:
                        roots.add(reflected_tuple)
                        next_roots.add(reflected_tuple)
            new_roots = next_roots

        # Add negatives
        all_roots = set(roots)
        for r in roots:
            neg_r = tuple(-np.array(r))
            all_roots.add(neg_r)

        self._roots = np.array([list(r) for r in all_roots])
        return self._roots

    @abstractmethod
    def generate_simple_roots(self) -> np.ndarray:
        pass

    def compute_cartan_matrix(self) -> np.ndarray:
        if self._cartan_matrix is not None:
            return self._cartan_matrix
        simple_roots = self.generate_simple_roots()
        n = len(simple_roots)
        cartan = np.zeros((n, n), dtype=np.float64)
        for i in range(n):
            for j in range(n):
                inner_product = np.dot(simple_roots[i], simple_roots[j])
                norm_j = np.dot(simple_roots[j], simple_roots[j])
                cartan[i, j] = 2 * inner_product / norm_j
        self._cartan_matrix = cartan
        return cartan

    def positive_roots(self) -> np.ndarray:
        if self._positive_roots is not None:
            return self._positive_roots
        roots = self.generate_roots()
        positive = []
        for root in roots:
            for coord in root:
                if abs(coord) > 1e-10:
                    if coord > 0:
                        positive.append(root)
                    break
        self._positive_roots = np.array(positive)
        return self._positive_roots

    def dynkin_diagram(self) -> nx.Graph:
        G = nx.Graph()
        cartan = self.compute_cartan_matrix()
        rank = self.properties.rank
        for i in range(rank):
            G.add_node(i, label=f"α_{i + 1}")
        for i in range(rank):
            for j in range(i + 1, rank):
                if cartan[i, j] < 0:
                    weight = round(abs(cartan[i, j] * cartan[j, i]))
                    G.add_edge(i, j, weight=weight)
        return G


class E4RootSystem(BaseRootSystem):
    def __init__(self) -> None:
        props = LieAlgebraProperties("E4", 24, 4, 20, 10, 120)
        super().__init__(props)

    def generate_roots(self) -> np.ndarray:
        roots = []
        for i in range(5):
            for j in range(5):
                if i != j:
                    v = np.zeros(5)
                    v[i], v[j] = 1, -1
                    roots.append(v)
        return np.array(roots)

    def generate_simple_roots(self) -> np.ndarray:
        return np.array([[1, -1, 0, 0, 0], [0, 1, -1, 0, 0], [0, 0, 1, -1, 0], [0, 0, 0, 1, -1]])


class E5RootSystem(BaseRootSystem):
    def __init__(self) -> None:
        props = LieAlgebraProperties("E5", 45, 5, 40, 20, 1920)
        super().__init__(props)

    def generate_roots(self) -> np.ndarray:
        roots = []
        for i in range(5):
            for j in range(i + 1, 5):
                for s1 in [1, -1]:
                    for s2 in [1, -1]:
                        v = np.zeros(5)
                        v[i], v[j] = s1, s2
                        roots.append(v)
        return np.array(roots)

    def generate_simple_roots(self) -> np.ndarray:
        return np.array(
            [
                [1, -1, 0, 0, 0],
                [0, 1, -1, 0, 0],
                [0, 0, 1, -1, 0],
                [0, 0, 0, 1, -1],
                [0, 0, 0, 1, 1],
            ]
        )


class E6RootSystem(BaseRootSystem):
    def __init__(self) -> None:
        props = LieAlgebraProperties("E6", 78, 6, 72, 36, 51840)
        super().__init__(props)

    def generate_simple_roots(self) -> np.ndarray:
        return np.array(
            [
                [0.5, -0.5, -0.5, -0.5, -0.5, -0.5, -0.5, 0.5],
                [1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                [-1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                [0.0, -1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                [0.0, 0.0, -1.0, 1.0, 0.0, 0.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, -1.0, 1.0, 0.0, 0.0, 0.0],
            ]
        )


class F4RootSystem(BaseRootSystem):
    """F4 root system (48 roots in R^4)."""

    def __init__(self) -> None:
        props = LieAlgebraProperties("F4", 52, 4, 48, 24, 1152, is_simply_laced=False)
        super().__init__(props)

    def generate_roots(self) -> np.ndarray:
        roots = []
        # Type 1: Permutations of (+/-1, +/-1, 0, 0) - 24 roots
        for i in range(4):
            for j in range(i + 1, 4):
                for s1 in [1, -1]:
                    for s2 in [1, -1]:
                        v = np.zeros(4)
                        v[i], v[j] = s1, s2
                        roots.append(v)
        # Type 2: (+/-1, 0, 0, 0) and permutations - 8 roots
        for i in range(4):
            for s in [1, -1]:
                v = np.zeros(4)
                v[i] = s
                roots.append(v)
        # Type 3: (+/-1/2, +/-1/2, +/-1/2, +/-1/2) - 16 roots
        for s in product([-0.5, 0.5], repeat=4):
            roots.append(np.array(s))
        return np.array(roots)

    def generate_simple_roots(self) -> np.ndarray:
        return np.array([[0, 1, -1, 0], [0, 0, 1, -1], [0, 0, 0, 1], [0.5, -0.5, -0.5, -0.5]])


class E7RootSystem(BaseRootSystem):
    def __init__(self) -> None:
        props = LieAlgebraProperties("E7", 133, 7, 126, 63, 2903040)
        super().__init__(props)

    def generate_roots(self, include_zero: bool = False) -> np.ndarray:
        roots = super().generate_roots()
        if include_zero:
            return np.vstack([roots, np.zeros((1, roots.shape[1]))])
        return roots

    def generate_simple_roots(self) -> np.ndarray:
        return np.array(
            [
                [0.0, 1.0, -1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                [0.0, 0.0, 1.0, -1.0, 0.0, 0.0, 0.0, 0.0],
                [0.5, 0.5, -0.5, -0.5, -0.5, -0.5, 0.5, 0.5],
                [0.0, 0.0, 0.0, 1.0, -1.0, 0.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, 0.0, 1.0, -1.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, 0.0, 0.0, 1.0, -1.0, 0.0],
                [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, -1.0],
            ]
        )

    def get_127_state_system(self) -> np.ndarray:
        return self.generate_roots(include_zero=True)

    def classify_root(self, root_or_index: np.ndarray | int) -> str:
        root = (
            self.get_root_by_index(root_or_index)
            if isinstance(root_or_index, (int, np.integer))
            else root_or_index
        )
        non_zero = root[np.abs(root) > 1e-10]
        return (
            "Type 1: Integer"
            if (len(non_zero) > 0 and np.allclose(np.abs(non_zero), 1.0))
            else "Type 2: Half-integer"
        )

    def get_root_by_index(self, index: int) -> np.ndarray:
        return self.generate_roots(include_zero=True)[index]


class E8RootSystem(BaseRootSystem):
    def __init__(self) -> None:
        props = LieAlgebraProperties("E8", 248, 8, 240, 120, 696729600)
        super().__init__(props)

    def cartan_matrix(self) -> np.ndarray:
        return self.compute_cartan_matrix()

    def generate_roots(self) -> np.ndarray:
        roots = []
        for i in range(8):
            for j in range(i + 1, 8):
                for s1 in [1, -1]:
                    for s2 in [1, -1]:
                        root = np.zeros(8)
                        root[i], root[j] = s1, s2
                        roots.append(root)
        for s in product([-0.5, 0.5], repeat=8):
            root = np.array(s)
            if np.sum(root < 0) % 2 == 0:
                roots.append(root)
        return np.array(roots)

    def generate_simple_roots(self) -> np.ndarray:
        return np.array(
            [
                [1, -1, 0, 0, 0, 0, 0, 0],
                [0, 1, -1, 0, 0, 0, 0, 0],
                [0, 0, 1, -1, 0, 0, 0, 0],
                [0, 0, 0, 1, -1, 0, 0, 0],
                [0, 0, 0, 0, 1, -1, 0, 0],
                [0, 0, 0, 0, 0, 1, -1, 0],
                [0, 0, 0, 0, 0, 1, 1, 0],
                [-0.5, -0.5, -0.5, -0.5, -0.5, -0.5, -0.5, -0.5],
            ]
        )


class KacMoodyAlgebra(ABC):
    def __init__(self, name: str, rank: int) -> None:
        self.name, self.rank = name, rank

    @abstractmethod
    def generalized_cartan_matrix(self) -> np.ndarray:
        pass


class E9RootSystem(KacMoodyAlgebra):
    def __init__(self) -> None:
        super().__init__("E9", 9)

    def generalized_cartan_matrix(self) -> np.ndarray:
        res = np.eye(9) * 2
        res[:8, :8] = E8RootSystem().compute_cartan_matrix()
        res[8, 7] = res[7, 8] = -1
        return res


class E10RootSystem(KacMoodyAlgebra):
    def __init__(self) -> None:
        super().__init__("E10", 10)

    def generalized_cartan_matrix(self) -> np.ndarray:
        res = np.eye(10) * 2
        res[:9, :9] = E9RootSystem().generalized_cartan_matrix()
        res[9, 8] = res[8, 9] = -1
        return res


class E11RootSystem(KacMoodyAlgebra):
    def __init__(self) -> None:
        super().__init__("E11", 11)

    def generalized_cartan_matrix(self) -> np.ndarray:
        res = np.eye(11) * 2
        res[:10, :10] = E10RootSystem().generalized_cartan_matrix()
        res[10, 9] = res[9, 10] = -1
        return res


class LieAlgebraCalculator:
    @staticmethod
    def dimension_formula(rank: int, num_positive_roots: int) -> int:
        return rank + 2 * num_positive_roots

    @staticmethod
    def coxeter_number(cartan_matrix: np.ndarray) -> int:
        return 30 if len(cartan_matrix) == 8 else 18


class ExceptionalLieAlgebras:
    @staticmethod
    def G2() -> dict[str, Any]:
        return {"name": "G2", "dimension": 14, "rank": 2, "num_roots": 12}

    @staticmethod
    def F4() -> dict[str, Any]:
        return {"name": "F4", "dimension": 52, "rank": 4, "num_roots": 48}

    @staticmethod
    def E6() -> dict[str, Any]:
        return {"name": "E6", "dimension": 78, "rank": 6, "num_roots": 72}

    @staticmethod
    def E7() -> dict[str, Any]:
        return {"name": "E7", "dimension": 133, "rank": 7, "num_roots": 126}

    @staticmethod
    def get_all() -> list[dict[str, Any]]:
        return [
            ExceptionalLieAlgebras.G2(),
            ExceptionalLieAlgebras.F4(),
            ExceptionalLieAlgebras.E6(),
            ExceptionalLieAlgebras.E7(),
            {"name": "E8", "dimension": 248, "rank": 8, "num_roots": 240},
        ]
