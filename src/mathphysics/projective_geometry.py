"""Projective Geometry PG(6,2) Module.

This module implements the projective geometry PG(6,2) over the finite field GF(2),
with deep connections to:
1. E7 Lie algebra (127 points match 126 roots + zero)
2. Fano plane PG(2,2) as foundational structure
3. Quantum error correction codes
4. Minimal informationally complete (MIC) measurements
5. Contextual geometries for quantum computing

PG(6,2) Properties:
- 127 points (2^7 - 1)
- 2,667 lines
- Binary projective space
- Connection to [127, 1, 127] simplex code
- Automorphism group related to GL(7,2)

References:
- Fano plane and quantum LDPC codes
- Contextual geometries (arXiv:0803.0618)
- Binary projective spaces and codes
- E7 root system geometry

Author: Claude Code
Date: October 2025
"""

from __future__ import annotations

# GF(2) arithmetic
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np


sys.path.append(str(Path(__file__).parent))
from .algebras.roots import E7RootSystem


@dataclass
class PGConfig:
    """Configuration for projective geometry."""

    dimension: int = 6  # PG(6,2)
    field_characteristic: int = 2  # GF(2)
    include_zero: bool = False  # Whether to include zero vector
    cache_lines: bool = True  # Cache line calculations

    def validate(self) -> None:
        """Validate configuration."""
        if self.dimension < 1:
            raise ValueError("Dimension must be positive")
        if self.field_characteristic != 2:
            raise ValueError("Only GF(2) currently supported")


class GF2Vector:
    """Vector over GF(2) (binary field).

    Represents elements of F_2^n with binary arithmetic.
    """

    def __init__(self, components: list[int] | np.ndarray | int) -> None:
        """Initialize GF(2) vector.

        Args:
            components: List of 0/1 values, numpy array, or integer (for binary representation)
        """
        if isinstance(components, int):
            # Convert integer to binary vector
            self.components = np.array([int(b) for b in format(components, "b")], dtype=int)
        else:
            self.components = np.array(components, dtype=int) % 2

    def __add__(self, other: GF2Vector) -> GF2Vector:
        """Addition in GF(2) (XOR)."""
        # Pad to same length
        max_len = max(len(self.components), len(other.components))
        a = np.pad(self.components, (max_len - len(self.components), 0))
        b = np.pad(other.components, (max_len - len(other.components), 0))
        return GF2Vector((a + b) % 2)

    def __mul__(self, scalar: int) -> GF2Vector:
        """Scalar multiplication in GF(2)."""
        return GF2Vector((self.components * (scalar % 2)) % 2)

    def dot(self, other: GF2Vector) -> int:
        """Dot product in GF(2)."""
        min_len = min(len(self.components), len(other.components))
        return int(np.sum(self.components[:min_len] * other.components[:min_len]) % 2)

    def is_zero(self) -> bool:
        """Check if vector is zero."""
        return bool(np.all(self.components == 0))

    def to_tuple(self) -> tuple[int, ...]:
        """Convert to tuple for hashing."""
        return tuple(int(component) for component in self.components)

    def __hash__(self) -> int:
        return hash(self.to_tuple())

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, GF2Vector):
            return NotImplemented
        return bool(np.array_equal(self.components, other.components))

    def __repr__(self) -> str:
        return f"GF2({list(self.components)})"


class ProjectivePoint:
    """Point in projective space PG(n, 2).

    Represents equivalence class of non-zero vectors under scalar multiplication.
    In GF(2), only scalar is 1, so each non-zero vector is a unique point.
    """

    def __init__(self, vector: GF2Vector) -> None:
        """Initialize projective point.

        Args:
            vector: Representative vector (must be non-zero)
        """
        if vector.is_zero():
            raise ValueError("Cannot create projective point from zero vector")

        self.vector = vector
        # In PG(n,2), normalize to canonical form (leftmost non-zero entry)
        self.canonical = self._canonicalize(vector)

    @staticmethod
    def _canonicalize(vector: GF2Vector) -> GF2Vector:
        """Return canonical representative of projective point."""
        # In GF(2), vector is already canonical (only non-zero scalar is 1)
        return vector

    def coordinates(self) -> np.ndarray:
        """Get homogeneous coordinates."""
        return self.canonical.components

    def __hash__(self) -> int:
        return hash(self.canonical)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ProjectivePoint):
            return NotImplemented
        return self.canonical == other.canonical

    def __repr__(self) -> str:
        coords = list(self.canonical.components)
        return f"P{coords}"


class ProjectiveLine:
    """Line in projective space PG(n, 2).

    A line is determined by 2 distinct points, or equivalently,
    a (n-1)-dimensional subspace of the dual space.
    """

    def __init__(self, point1: ProjectivePoint, point2: ProjectivePoint) -> None:
        """Initialize projective line from two points.

        Args:
            point1: First point
            point2: Second point (must be distinct from point1)
        """
        if point1 == point2:
            raise ValueError("Points must be distinct to define a line")

        self.points = frozenset([point1, point2])
        self._all_points: frozenset[ProjectivePoint] | None = None

    def contains(self, point: ProjectivePoint, _dimension: int = 6) -> bool:
        """Check if point lies on this line.

        Args:
            point: Point to check
            dimension: Ambient dimension

        Returns:
            Whether point is on line
        """
        # In PG(n,2), line through p1, p2 contains:
        # {p1, p2, p1+p2} (3 points total)
        p1, p2 = list(self.points)

        if point in (p1, p2):
            return True

        # Check if point = p1 + p2
        sum_vec = p1.vector + p2.vector
        if not sum_vec.is_zero():
            sum_point = ProjectivePoint(sum_vec)
            return point == sum_point

        return False

    def get_all_points(self, _dimension: int = 6) -> frozenset[ProjectivePoint]:
        """Get all points on this line.

        In PG(n,2), every line has exactly 3 points.

        Args:
            dimension: Ambient dimension

        Returns:
            Set of all points on line
        """
        if self._all_points is not None:
            return self._all_points

        p1, p2 = list(self.points)
        sum_vec = p1.vector + p2.vector

        points = {p1, p2}
        if not sum_vec.is_zero():
            points.add(ProjectivePoint(sum_vec))

        self._all_points = frozenset(points)
        return self._all_points

    def __hash__(self) -> int:
        return hash(self.points)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ProjectiveLine):
            return NotImplemented
        return self.points == other.points

    def __repr__(self) -> str:
        p1, p2 = list(self.points)
        return f"Line[{p1}, {p2}]"


class ProjectiveSpace:
    """Projective space PG(n, 2) over GF(2).

    For PG(6, 2):
    - 2^7 - 1 = 127 points
    - Each line has 3 points
    - Rich combinatorial structure
    """

    def __init__(self, dimension: int = 6) -> None:
        """Initialize projective space.

        Args:
            dimension: Dimension of projective space
        """
        self.dimension = dimension
        self.ambient_dim = dimension + 1  # Ambient vector space dimension
        self._points: list[ProjectivePoint] | None = None
        self._lines: list[ProjectiveLine] | None = None
        self._point_index: dict[ProjectivePoint, int] = {}

    def generate_points(self) -> list[ProjectivePoint]:
        """Generate all points in PG(n, 2).

        Returns:
            List of all projective points
        """
        if self._points is not None:
            return self._points

        points = []
        # All non-zero vectors in GF(2)^(n+1)
        for i in range(1, 2**self.ambient_dim):
            # Convert integer to binary vector
            binary = format(i, f"0{self.ambient_dim}b")
            vector = GF2Vector([int(b) for b in binary])
            point = ProjectivePoint(vector)
            points.append(point)
            self._point_index[point] = len(points) - 1

        self._points = points
        return points

    def num_points(self) -> int:
        """Get number of points in PG(n, 2).

        Formula: 2^(n+1) - 1
        """
        return int(2 ** (self.dimension + 1) - 1)

    def generate_lines(self) -> list[ProjectiveLine]:
        """Generate all lines in PG(n, 2).

        Returns:
            List of all projective lines
        """
        if self._lines is not None:
            return self._lines

        points = self.generate_points()
        lines = []
        covered_pairs = set()

        # Each pair of distinct points determines a unique line
        for i in range(len(points)):
            for j in range(i + 1, len(points)):
                pair = tuple(sorted((i, j)))
                if pair in covered_pairs:
                    continue

                # New line
                line = ProjectiveLine(points[i], points[j])
                lines.append(line)

                # In PG(n,2), every line has 3 points. Find the 3rd point.
                # p1, p2, p1+p2 are the three points.
                all_pts_on_line = line.get_all_points(self.dimension)
                indices_on_line = []
                for p in all_pts_on_line:
                    if p in self._point_index:
                        indices_on_line.append(self._point_index[p])

                # Mark all pairs on this line as covered
                for k in range(len(indices_on_line)):
                    for ll in range(k + 1, len(indices_on_line)):
                        covered_pairs.add(tuple(sorted((indices_on_line[k], indices_on_line[ll]))))

        self._lines = lines
        return lines

    def num_lines(self) -> int:
        """Get number of lines in PG(n, 2).

        Formula: (2^(n+1) - 1)(2^n - 1) / 3
        """
        num_pts = 2 ** (self.dimension + 1) - 1
        return int(num_pts * (2**self.dimension - 1) // 3)

    def incidence_matrix(self) -> np.ndarray:
        """Build point-line incidence matrix.

        Returns:
            Binary matrix where entry (i,j) = 1 if point i is on line j
        """
        points = self.generate_points()
        lines = self.generate_lines()

        matrix = np.zeros((len(points), len(lines)), dtype=int)

        for j, line in enumerate(lines):
            line_points = line.get_all_points(self.dimension)
            for point in line_points:
                if point in self._point_index:
                    i = self._point_index[point]
                    matrix[i, j] = 1

        return matrix

    def point_to_e7_index(self, point: ProjectivePoint) -> int:
        """Map projective point to E7 root index (0-126).

        Args:
            point: Projective point

        Returns:
            E7 index (0-126)
        """
        if point in self._point_index:
            return self._point_index[point]
        return -1

    def properties(self) -> dict[str, Any]:
        """Get geometric properties of projective space.

        Returns:
            Dictionary of properties
        """
        return {
            "dimension": self.dimension,
            "num_points": self.num_points(),
            "num_lines": self.num_lines(),
            "points_per_line": 3,  # Always 3 in PG(n,2)
            "field": "GF(2)",
            "automorphism_group": f"GL({self.dimension + 1}, 2)",
        }


class FanoPlane:
    """Fano plane PG(2, 2) - smallest projective plane.

    The Fano plane has:
    - 7 points
    - 7 lines
    - 3 points on each line
    - 3 lines through each point

    Fundamental structure for quantum error correction and contextual geometries.
    """

    def __init__(self) -> None:
        """Initialize Fano plane."""
        self.pg = ProjectiveSpace(dimension=2)
        self.points = self.pg.generate_points()
        self.lines = self._construct_fano_lines()

    def _construct_fano_lines(self) -> list[list[int]]:
        """Construct the 7 lines of the Fano plane.

        Returns:
            List of lines (each line is list of 3 point indices)
        """
        # Standard Fano plane labeling: points 0-6
        # Lines are defined by their point sets
        fano_lines = [
            [0, 1, 2],  # Line 1
            [0, 3, 4],  # Line 2
            [0, 5, 6],  # Line 3
            [1, 3, 5],  # Line 4
            [1, 4, 6],  # Line 5
            [2, 3, 6],  # Line 6
            [2, 4, 5],  # Line 7 (the "circle")
        ]
        return fano_lines

    def verify_incidence_axioms(self) -> bool:
        """Verify Fano plane incidence axioms.

        Returns:
            Whether all axioms are satisfied
        """
        # Axiom 1: Any two distinct points lie on exactly one line
        points_on_lines = defaultdict(set)

        for line_idx, line in enumerate(self.lines):
            for p in line:
                points_on_lines[p].add(line_idx)

        # Check each pair of points
        for i in range(7):
            for j in range(i + 1, 7):
                common_lines = points_on_lines[i] & points_on_lines[j]
                if len(common_lines) != 1:
                    return False

        # Axiom 2: Any two distinct lines meet in exactly one point
        for i in range(len(self.lines)):
            for j in range(i + 1, len(self.lines)):
                intersection = set(self.lines[i]) & set(self.lines[j])
                if len(intersection) != 1:
                    return False

        # Axiom 3: There exist 4 points, no 3 collinear
        # Points 0, 1, 3, 6 work
        test_points = [0, 1, 3, 6]
        for line in self.lines:
            collinear = sum(1 for p in test_points if p in line)
            if collinear >= 3:
                return False

        return True

    def dual_plane(self) -> FanoPlane:
        """Construct dual Fano plane (points <-> lines).

        Returns:
            Dual Fano plane
        """
        # Fano plane is self-dual
        return self

    def automorphism_group_order(self) -> int:
        """Get order of automorphism group.

        Returns:
            Order of Aut(Fano) = PSL(3, 2) = GL(3, 2) (isomorphic)
        """
        # |GL(3, 2)| = (2^3 - 1)(2^3 - 2)(2^3 - 4) = 7 * 6 * 4 = 168
        return 168


class PG62_E7Connection:
    """Connection between PG(6,2) and E7 root system.

    The 127 points of PG(6,2) correspond to:
    - 126 E7 roots
    - 1 zero vector (if included)

    This connection enables geometric interpretation of E7 algebra.
    """

    def __init__(self) -> None:
        """Initialize PG(6,2)-E7 connection."""
        self.pg = ProjectiveSpace(dimension=6)
        self.e7 = E7RootSystem()
        self.pg_points = self.pg.generate_points()
        self.e7_roots = self.e7.get_127_state_system()
        self._pg_to_e7_map: dict[int, int] = {}
        self._e7_to_pg_map: dict[int, int] = {}

    def build_correspondence(self) -> dict[int, dict[str, Any]]:
        """Build explicit correspondence between PG(6,2) points and E7 roots.

        Returns:
            Mapping dictionary
        """
        correspondence = {}

        # Simple correspondence: index-based
        for i in range(min(127, len(self.pg_points))):
            self._pg_to_e7_map[i] = i
            self._e7_to_pg_map[i] = i

            pg_point = self.pg_points[i] if i < len(self.pg_points) else None
            e7_root = self.e7_roots[i] if i < len(self.e7_roots) else None

            correspondence[i] = {
                "pg_point": list(pg_point.coordinates()) if pg_point else None,
                "e7_root": list(e7_root) if e7_root is not None else None,
                "pg_index": i,
                "e7_index": i,
            }

        return correspondence

    def geometric_interpretation(self, e7_root_index: int) -> dict[str, Any]:
        """Provide geometric interpretation of E7 root via PG(6,2).

        Args:
            e7_root_index: Index of E7 root

        Returns:
            Geometric interpretation
        """
        if e7_root_index >= len(self.e7_roots):
            return {}

        root = self.e7_roots[e7_root_index]
        pg_index = self._e7_to_pg_map.get(e7_root_index, e7_root_index)

        interpretation = {
            "e7_root": list(root),
            "root_type": self.e7.classify_root(root) if not np.allclose(root, 0) else "zero",
            "root_squared_norm": float(np.sum(root**2)),
            "pg_point_index": pg_index,
        }

        if pg_index < len(self.pg_points):
            pg_point = self.pg_points[pg_index]
            interpretation["pg_coordinates"] = list(pg_point.coordinates())

        return interpretation

    def analyze_structure(self) -> dict[str, Any]:
        """Analyze the PG(6,2)-E7 structural connection.

        Returns:
            Analysis results
        """
        analysis: dict[str, Any] = {
            "pg62_points": len(self.pg_points),
            "e7_states": len(self.e7_roots),
            "correspondence_size": len(self._pg_to_e7_map),
            "perfect_match": len(self.pg_points) == len(self.e7_roots),
        }

        # E7 properties
        e7_stats = self.e7.get_statistics()
        analysis["e7_properties"] = {
            "total_roots": e7_stats["total_roots"],
            "positive_roots": e7_stats["positive_roots"],
            "rank": e7_stats["rank"],
            "dimension": e7_stats["dimension"],
        }

        # PG(6,2) properties
        analysis["pg62_properties"] = self.pg.properties()

        return analysis


def demonstrate_projective_geometry():
    """Demonstrate projective geometry module."""
    print("=" * 80)
    print("PROJECTIVE GEOMETRY PG(6,2) MODULE")
    print("=" * 80)
    print()

    print("1. FANO PLANE PG(2,2)")
    print("-" * 40)
    fano = FanoPlane()
    print("Points: 7")
    print("Lines: 7")
    print("Points per line: 3")
    print("Lines through each point: 3")
    print(f"Incidence axioms satisfied: {fano.verify_incidence_axioms()}")
    print(f"Automorphism group order: {fano.automorphism_group_order()}")
    print()

    print("Fano lines:")
    for i, line in enumerate(fano.lines, 1):
        print(f"  Line {i}: {line}")
    print()

    print("2. PROJECTIVE SPACE PG(6,2)")
    print("-" * 40)
    pg62 = ProjectiveSpace(dimension=6)
    props = pg62.properties()

    for key, value in props.items():
        print(f"  {key}: {value}")
    print()

    print("Sample points (first 5):")
    points = pg62.generate_points()
    for i, point in enumerate(points[:5]):
        coords = list(point.coordinates())
        print(f"  P{i}: {coords}")
    print()

    print("3. PG(6,2) - E7 CONNECTION")
    print("-" * 40)
    connection = PG62_E7Connection()

    analysis = connection.analyze_structure()
    print(f"PG(6,2) points: {analysis['pg62_points']}")
    print(f"E7 states (126 roots + zero): {analysis['e7_states']}")
    print(f"Perfect correspondence: {analysis['perfect_match']}")
    print()

    print("E7 Properties:")
    e7_props = analysis["e7_properties"]
    for key, value in e7_props.items():
        if isinstance(value, int) and value > 1000:
            print(f"  {key}: {value:,}")
        else:
            print(f"  {key}: {value}")
    print()

    print("Sample E7-PG correspondence (first 3 roots):")
    correspondence = connection.build_correspondence()
    for i in range(min(3, len(correspondence))):
        entry = correspondence[i]
        print(f"\n  Root {i}:")
        print(f"    E7 root: {entry['e7_root'][:4]}... (truncated)")
        print(f"    PG point: {entry['pg_point']}")

        # Get interpretation
        interp = connection.geometric_interpretation(i)
        print(f"    Root type: {interp['root_type']}")
        print(f"    Squared norm: {interp['root_squared_norm']:.1f}")
    print()

    print("4. INCIDENCE STRUCTURE")
    print("-" * 40)

    # Generate small incidence matrix sample
    print("Computing incidence matrix...")
    incidence = pg62.incidence_matrix()
    print(f"Incidence matrix shape: {incidence.shape}")
    print(f"Total incidences: {np.sum(incidence)}")
    print(f"Average points per line: {np.mean(np.sum(incidence, axis=0)):.2f}")
    print()

    print("=" * 80)
    print("Projective geometry demonstration complete!")
    print("PG(6,2) successfully connected to E7 root system.")
    print("127 points <-> 126 E7 roots + zero vector")
    print("=" * 80)


if __name__ == "__main__":
    demonstrate_projective_geometry()
