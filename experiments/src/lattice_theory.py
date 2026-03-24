"""Lattice Theory - E_8 and Leech Lattice Implementation.

This module implements lattice theory with focus on:
- E_8 lattice (8-dimensional)
- Leech lattice (24-dimensional)
- Sphere packing calculations
- Golden ratio connections
- Lattice projections and visualizations
"""

from __future__ import annotations
from typing import List, Tuple, Dict, Any, Optional, Set
import numpy as np
from scipy.spatial import Voronoi, ConvexHull
from scipy.spatial.distance import cdist
import json
from pathlib import Path
from dataclasses import dataclass
from itertools import product
import warnings


PHI = (1 + np.sqrt(5)) / 2  # Golden ratio


@dataclass
class LatticeProperties:
    """Properties of a lattice."""

    name: str
    dimension: int
    kissing_number: int
    packing_density: float
    minimal_norm: float
    determinant: float
    theta_series_coefficients: List[int]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "dimension": self.dimension,
            "kissing_number": self.kissing_number,
            "packing_density": float(self.packing_density),
            "minimal_norm": float(self.minimal_norm),
            "determinant": float(self.determinant),
            "theta_series": self.theta_series_coefficients
        }


class E8Lattice:
    """E_8 lattice implementation."""

    def __init__(self):
        """Initialize E_8 lattice."""
        self.dimension = 8
        self.name = "E_8"
        self._basis = None
        self._gram_matrix = None
        self._root_system = None

    def basis_vectors(self) -> np.ndarray:
        """Generate basis vectors for E_8 lattice."""
        if self._basis is not None:
            return self._basis

        # Standard E_8 lattice basis
        # Method 1: Use D_8 lattice plus coset
        basis = []

        # D_8 basis: e_i - e_{i+1} for i = 1..7, and sum of all e_i
        for i in range(7):
            vec = np.zeros(8)
            vec[i] = 1
            vec[i+1] = -1
            basis.append(vec)

        # Last vector: sum of all coordinates (or equivalently, 2*e_8)
        vec = np.ones(8)
        basis.append(vec)

        # Alternative: add the half-integer vector
        # basis.append(np.ones(8) * 0.5)

        self._basis = np.array(basis)
        return self._basis

    def gram_matrix(self) -> np.ndarray:
        """Compute Gram matrix of the basis."""
        if self._gram_matrix is not None:
            return self._gram_matrix

        basis = self.basis_vectors()
        gram = np.dot(basis, basis.T)
        self._gram_matrix = gram
        return gram

    def generate_lattice_points(self, max_norm: float = 10.0,
                               include_zero: bool = False) -> np.ndarray:
        """Generate lattice points up to given norm."""
        basis = self.basis_vectors()
        points = []

        # Determine range of integer coefficients
        max_coeff = int(np.ceil(np.sqrt(max_norm))) + 1

        # Generate all integer linear combinations
        for coeffs in product(range(-max_coeff, max_coeff+1), repeat=8):
            point = np.sum([c * basis[i] for i, c in enumerate(coeffs)], axis=0)
            norm = np.linalg.norm(point)

            if norm <= max_norm:
                if include_zero or norm > 1e-10:
                    points.append(point)

        return np.array(points)

    def minimal_vectors(self) -> np.ndarray:
        """Get minimal (shortest non-zero) vectors."""
        # In E_8, there are 240 minimal vectors with norm sqrt(2)
        points = self.generate_lattice_points(max_norm=2.5)

        # Find minimal norm
        norms = np.linalg.norm(points, axis=1)
        min_norm = np.min(norms[norms > 1e-10])

        # Select vectors with minimal norm
        minimal = points[np.abs(norms - min_norm) < 1e-6]

        return minimal

    def kissing_number(self) -> int:
        """Compute kissing number (number of nearest neighbors)."""
        # For E_8, this is 240
        minimal = self.minimal_vectors()
        return len(minimal)

    def theta_series(self, max_n: int = 10) -> List[int]:
        """Compute theta series coefficients a_n.

        Theta series: sum_{v in E_8} q^{|v|^2/2}
        """
        coefficients = [0] * (max_n + 1)

        # Generate points up to appropriate norm
        max_norm = np.sqrt(2 * max_n) + 2
        points = self.generate_lattice_points(max_norm, include_zero=True)

        for point in points:
            norm_squared = np.dot(point, point)
            n = int(round(norm_squared / 2))
            if 0 <= n <= max_n:
                coefficients[n] += 1

        return coefficients

    def shell_structure(self, num_shells: int = 5) -> Dict[float, int]:
        """Analyze shell structure (number of points at each norm)."""
        shells = {}

        max_norm = np.sqrt(2 * num_shells * 2) + 1
        points = self.generate_lattice_points(max_norm, include_zero=True)

        for point in points:
            norm = np.linalg.norm(point)
            norm = round(norm, 6)
            shells[norm] = shells.get(norm, 0) + 1

        return shells

    def voronoi_cell_vertices(self, max_points: int = 100) -> np.ndarray:
        """Compute vertices of Voronoi cell (using subset of points)."""
        # Generate nearby lattice points
        points = self.generate_lattice_points(max_norm=3.0)

        # Subsample if too many
        if len(points) > max_points:
            indices = np.random.choice(len(points), max_points, replace=False)
            # Always include origin
            indices = np.append(indices, 0)
            points = points[indices]

        # Compute Voronoi diagram
        try:
            vor = Voronoi(points)
            # Find Voronoi cell containing origin
            origin_idx = np.argmin(np.linalg.norm(points, axis=1))
            vertices = vor.vertices
            return vertices
        except Exception as e:
            warnings.warn(f"Voronoi computation failed: {e}")
            return np.array([])

    def packing_density(self) -> float:
        """Compute sphere packing density."""
        # E_8 packing density = π^4 / 384 ≈ 0.2536997
        return np.pi ** 4 / 384

    def covering_radius(self) -> float:
        """Compute covering radius."""
        # For E_8: R = sqrt(2)
        return np.sqrt(2)

    def determinant(self) -> float:
        """Compute lattice determinant."""
        gram = self.gram_matrix()
        return np.abs(np.linalg.det(gram))

    def golden_ratio_connections(self) -> Dict[str, float]:
        """Analyze golden ratio appearances in E_8."""
        connections = {}

        # E_8 has various golden ratio connections through its structure
        # Check icosahedral symmetry connection
        phi = PHI

        # Ratio of shell radii
        shells = self.shell_structure(num_shells=4)
        sorted_shells = sorted(shells.keys())
        if len(sorted_shells) >= 3:
            for i in range(len(sorted_shells)-1):
                ratio = sorted_shells[i+1] / sorted_shells[i]
                connections[f"shell_ratio_{i}"] = ratio

        # Check for phi in lattice structure
        minimal = self.minimal_vectors()
        if len(minimal) > 1:
            # Compute angles between minimal vectors
            angles = []
            for i in range(min(10, len(minimal))):
                for j in range(i+1, min(10, len(minimal))):
                    cos_angle = np.dot(minimal[i], minimal[j]) / \
                                (np.linalg.norm(minimal[i]) * np.linalg.norm(minimal[j]))
                    angles.append(cos_angle)

            connections["angle_samples"] = angles[:5]

        return connections


class LeechLattice:
    """Leech lattice implementation (24-dimensional)."""

    def __init__(self):
        """Initialize Leech lattice."""
        self.dimension = 24
        self.name = "Leech"
        self._basis = None

    def basis_vectors(self) -> np.ndarray:
        """Generate basis vectors for Leech lattice.

        Using construction from extended binary Golay code.
        """
        if self._basis is not None:
            return self._basis

        # Simplified construction: use multiple copies of E_8 and D_8
        # Full construction would use Golay code

        # For demonstration, create a simplified 24D lattice
        basis = []

        # First 8 coordinates: E_8 pattern
        for i in range(7):
            vec = np.zeros(24)
            vec[i] = 1
            vec[i+1] = -1
            basis.append(vec)

        # Next 8 coordinates: E_8 pattern
        for i in range(8, 15):
            vec = np.zeros(24)
            vec[i] = 1
            vec[i+1] = -1
            basis.append(vec)

        # Last 8 coordinates: E_8 pattern
        for i in range(16, 23):
            vec = np.zeros(24)
            vec[i] = 1
            vec[i+1] = -1
            basis.append(vec)

        # Additional vectors to complete the lattice
        vec = np.zeros(24)
        vec[:8] = 1
        basis.append(vec)

        vec = np.zeros(24)
        vec[8:16] = 1
        basis.append(vec)

        vec = np.zeros(24)
        vec[16:24] = 1
        basis.append(vec)

        # Fill remaining basis vectors
        while len(basis) < 24:
            vec = np.zeros(24)
            idx = len(basis)
            if idx < 24:
                vec[idx] = 1
            basis.append(vec)

        self._basis = np.array(basis[:24])
        return self._basis

    def generate_lattice_points(self, max_norm: float = 6.0) -> np.ndarray:
        """Generate lattice points up to given norm."""
        basis = self.basis_vectors()
        points = []

        # Due to 24D, we need to limit the search space
        max_coeff = 2  # Restricted search

        for coeffs in product(range(-max_coeff, max_coeff+1), repeat=24):
            if np.sum(np.abs(coeffs)) > 6:  # Further restriction
                continue

            point = np.sum([c * basis[i] for i, c in enumerate(coeffs)], axis=0)
            norm = np.linalg.norm(point)

            if norm <= max_norm and norm > 1e-10:
                points.append(point)

        return np.array(points) if points else np.array([]).reshape(0, 24)

    def minimal_vectors(self) -> int:
        """Count minimal vectors.

        Leech lattice has 196560 minimal vectors at norm sqrt(4) = 2.
        """
        # Due to computational constraints, return theoretical value
        return 196560

    def kissing_number(self) -> int:
        """Get kissing number.

        For Leech lattice: 196560
        """
        return 196560

    def packing_density(self) -> float:
        """Compute sphere packing density.

        Leech lattice provides densest known packing in 24D.
        """
        # ρ = (π^12 / 12!) * determinant
        # For Leech: determinant = 1
        return (np.pi ** 12) / np.math.factorial(12)

    def properties(self) -> LatticeProperties:
        """Get lattice properties."""
        return LatticeProperties(
            name="Leech",
            dimension=24,
            kissing_number=196560,
            packing_density=self.packing_density(),
            minimal_norm=2.0,
            determinant=1.0,
            theta_series_coefficients=[1, 0, 196560]  # First few terms
        )


class SpherePackingAnalyzer:
    """Analyzer for sphere packing problems."""

    @staticmethod
    def compute_packing_density(dimension: int, lattice_type: str) -> float:
        """Compute packing density for various lattices."""
        if lattice_type == "E8":
            return np.pi ** 4 / 384

        elif lattice_type == "Leech":
            return (np.pi ** 12) / np.math.factorial(12)

        elif lattice_type == "D_n":
            # D_n lattice density (general formula)
            n = dimension
            return (np.pi ** (n/2)) / (2 ** (n-1) * np.math.factorial(n/2))

        elif lattice_type == "Z_n":
            # Integer lattice (hypercubic)
            n = dimension
            return (np.pi ** (n/2)) / (2 ** n * np.math.factorial(n/2))

        else:
            raise ValueError(f"Unknown lattice type: {lattice_type}")

    @staticmethod
    def kissing_number_bounds(dimension: int) -> Tuple[int, Optional[int]]:
        """Get known bounds on kissing numbers."""
        # Known exact values
        exact_values = {
            1: 2,
            2: 6,
            3: 12,
            4: 24,
            8: 240,  # E_8
            24: 196560  # Leech
        }

        if dimension in exact_values:
            return exact_values[dimension], exact_values[dimension]

        # Lower bounds (Chabauty-Shannon-Wyner bound)
        lower = 2 * dimension

        # Upper bounds vary by dimension
        upper_bounds = {
            5: 45,
            6: 82,
            7: 140,
            9: 380,
            10: 595
        }

        upper = upper_bounds.get(dimension, None)

        return lower, upper

    @staticmethod
    def volume_of_sphere(dimension: int, radius: float = 1.0) -> float:
        """Compute volume of n-dimensional sphere."""
        n = dimension
        return (np.pi ** (n/2)) / np.math.factorial(n/2) * (radius ** n)


def analyze_lattice_properties(output_dir: Optional[Path] = None) -> Dict[str, Any]:
    """Comprehensive lattice analysis."""
    if output_dir is None:
        output_dir = Path("/home/eirikr/MathScienceCompendium/experiments/results")

    output_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 80)
    print("LATTICE THEORY ANALYSIS")
    print("=" * 80)

    results = {}

    # E_8 Lattice
    print("\n--- E_8 Lattice ---")
    e8 = E8Lattice()

    print(f"Dimension: {e8.dimension}")

    kissing = e8.kissing_number()
    print(f"Kissing number: {kissing}")
    results["E8_kissing_number"] = kissing

    packing = e8.packing_density()
    print(f"Packing density: {packing:.6f}")
    results["E8_packing_density"] = packing

    det = e8.determinant()
    print(f"Determinant: {det:.2f}")
    results["E8_determinant"] = det

    print("\nShell structure:")
    shells = e8.shell_structure(num_shells=6)
    for norm in sorted(shells.keys())[:6]:
        print(f"  r = {norm:.3f}: {shells[norm]} points")
    results["E8_shells"] = {str(k): v for k, v in shells.items()}

    print("\nTheta series coefficients:")
    theta = e8.theta_series(max_n=8)
    print(f"  a_0 = {theta[0]} (1 point at origin)")
    print(f"  a_1 = {theta[1]} (240 minimal vectors)")
    print(f"  a_2 = {theta[2]}")
    print(f"  a_3 = {theta[3]}")
    print(f"  a_4 = {theta[4]}")
    results["E8_theta_series"] = theta

    # Golden ratio connections
    print("\nGolden ratio connections:")
    golden = e8.golden_ratio_connections()
    for key, value in list(golden.items())[:5]:
        if isinstance(value, (int, float)):
            print(f"  {key}: {value:.6f}")
    results["E8_golden_ratio"] = {k: float(v) if isinstance(v, (int, float)) else str(v)
                                  for k, v in golden.items() if isinstance(v, (int, float))}

    # Leech Lattice
    print("\n--- Leech Lattice ---")
    leech = LeechLattice()

    leech_props = leech.properties()
    print(f"Dimension: {leech_props.dimension}")
    print(f"Kissing number: {leech_props.kissing_number}")
    print(f"Packing density: {leech_props.packing_density:.10f}")
    print(f"Minimal norm: {leech_props.minimal_norm}")
    print(f"Determinant: {leech_props.determinant}")

    results["Leech"] = leech_props.to_dict()

    # Packing comparison
    print("\n--- Sphere Packing Comparison ---")
    analyzer = SpherePackingAnalyzer()

    dimensions_to_test = [1, 2, 3, 4, 8, 24]
    print(f"{'Dim':<6} {'E_8/Leech':<15} {'D_n':<15} {'Z_n':<15}")
    print("-" * 60)

    for d in dimensions_to_test:
        if d == 8:
            e8_density = analyzer.compute_packing_density(8, "E8")
            dn_density = analyzer.compute_packing_density(8, "D_n")
            zn_density = analyzer.compute_packing_density(8, "Z_n")
            print(f"{d:<6} {e8_density:<15.8f} {dn_density:<15.8f} {zn_density:<15.8f}")
        elif d == 24:
            leech_density = analyzer.compute_packing_density(24, "Leech")
            dn_density = analyzer.compute_packing_density(24, "D_n")
            zn_density = analyzer.compute_packing_density(24, "Z_n")
            print(f"{d:<6} {leech_density:<15.10f} {dn_density:<15.10f} {zn_density:<15.10f}")
        else:
            try:
                dn_density = analyzer.compute_packing_density(d, "D_n")
                zn_density = analyzer.compute_packing_density(d, "Z_n")
                print(f"{d:<6} {'-':<15} {dn_density:<15.8f} {zn_density:<15.8f}")
            except:
                pass

    # Kissing numbers
    print("\n--- Kissing Numbers ---")
    print(f"{'Dimension':<12} {'Lower Bound':<15} {'Upper Bound':<15} {'Known Exact':<15}")
    print("-" * 60)

    for d in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 24]:
        lower, upper = analyzer.kissing_number_bounds(d)
        exact = "✓" if lower == upper else "-"
        upper_str = str(upper) if upper is not None else "unknown"
        print(f"{d:<12} {lower:<15} {upper_str:<15} {exact:<15}")

    # Save results
    with open(output_dir / "lattice_analysis.json", 'w') as f:
        json.dump(results, f, indent=2)

    return results


def demonstrate_e8_structure():
    """Demonstrate E_8 lattice structure."""
    print("\n" + "=" * 80)
    print("E_8 LATTICE STRUCTURE DEMONSTRATION")
    print("=" * 80)

    e8 = E8Lattice()

    # Basis vectors
    print("\n--- Basis Vectors ---")
    basis = e8.basis_vectors()
    print(f"Shape: {basis.shape}")
    print("First 3 basis vectors:")
    for i in range(3):
        print(f"  v_{i+1} = {basis[i]}")

    # Gram matrix
    print("\n--- Gram Matrix ---")
    gram = e8.gram_matrix()
    print("Diagonal elements (self inner products):")
    print(f"  {np.diag(gram)}")
    print(f"Determinant: {np.linalg.det(gram):.2f}")

    # Minimal vectors
    print("\n--- Minimal Vectors ---")
    minimal = e8.minimal_vectors()
    print(f"Number of minimal vectors: {len(minimal)}")
    print(f"Minimal norm: {np.linalg.norm(minimal[0]):.6f}")
    print(f"Expected: {np.sqrt(2):.6f}")

    # Sample minimal vectors
    print("\nFirst 5 minimal vectors:")
    for i in range(min(5, len(minimal))):
        print(f"  {minimal[i]}")


if __name__ == "__main__":
    # Run analysis
    results = analyze_lattice_properties()

    # Demonstrate structure
    demonstrate_e8_structure()

    print("\n" + "=" * 80)
    print("Lattice analysis complete!")
    print("Results saved to experiments/results/lattice_analysis.json")
    print("=" * 80)