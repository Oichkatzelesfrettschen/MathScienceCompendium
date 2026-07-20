#!/usr/bin/env python3
"""
E7 Simple Roots Solution
========================

This file contains the CORRECT E7 simple roots that:
1. Are all valid E7 roots
2. Form a linearly independent basis
3. Give Cartan matrix with det = 2
4. Follow standard conventions
"""

import numpy as np


def print_solution():
    """Print the correct E7 simple roots solution."""

    print("=" * 70)
    print("E7 SIMPLE ROOTS - CORRECT SOLUTION")
    print("=" * 70)
    print()

    # The correct E7 simple roots in 8-dimensional embedding
    # These satisfy all requirements and give det(Cartan) = 2
    alpha = [
        np.array([0.5, -0.5, -0.5, -0.5, -0.5, -0.5, -0.5, 0.5]),
        np.array([1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
        np.array([-1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
        np.array([0.0, -1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
        np.array([0.0, 0.0, -1.0, 1.0, 0.0, 0.0, 0.0, 0.0]),
        np.array([0.0, 0.0, 0.0, -1.0, 1.0, 0.0, 0.0, 0.0]),
        np.array([0.0, 0.0, 0.0, 0.0, -1.0, 1.0, 0.0, 0.0]),
    ]

    print("CORRECT E7 SIMPLE ROOTS:")
    print("-" * 50)
    for i, root in enumerate(alpha, 1):
        print(f"alpha{i} = {root}")

    print()
    print("VERIFICATION:")
    print("-" * 50)

    # Verify each root
    e7_normal = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0])
    for i, root in enumerate(alpha, 1):
        # E7 is the E8 root subsystem orthogonal to e7 + e8.
        non_zeros = [x for x in root if x != 0]
        if len(non_zeros) == 2:
            is_valid = all(abs(x) == 1 for x in non_zeros) and np.dot(root, e7_normal) == 0.0
            root_type = "Integer"
        elif all(abs(x) == 0.5 for x in root):
            negatives = sum(1 for x in root if x < 0)
            is_valid = negatives % 2 == 0 and np.dot(root, e7_normal) == 0.0
            root_type = "Half-integer"
        else:
            is_valid = False
            root_type = "Invalid"

        status = "VALID" if is_valid else "INVALID"
        print(f"alpha{i}: {root_type} root - {status}")

    # Compute Cartan matrix
    n = len(alpha)
    cartan = np.zeros((n, n), dtype=int)
    for i in range(n):
        for j in range(n):
            dot_ij = np.dot(alpha[i], alpha[j])
            dot_jj = np.dot(alpha[j], alpha[j])
            cartan[i, j] = round(2 * dot_ij / dot_jj)

    print()
    print("CARTAN MATRIX:")
    print("-" * 50)
    print(cartan)

    det = np.linalg.det(cartan)
    print()
    print(f"Determinant: {det:.0f}")

    # Check rank
    rank = np.linalg.matrix_rank(np.array(alpha))
    print(f"Rank of simple roots: {rank}/7")

    print()
    print("=" * 70)
    print("MATHEMATICAL EXPLANATION")
    print("=" * 70)
    print("""
The E7 root system is one of the five exceptional Lie algebras (along with
G2, F4, E6, and E8). It has the following key properties:

1. ROOT STRUCTURE:
   - Total of 126 roots in a 7-dimensional space
   - Embedded in 8 dimensions for computational convenience
   - Two types of roots:
     * Integer roots: E8 integer roots orthogonal to e7 + e8
     * Half-integer roots: all eight entries +-0.5, even number of
       negative entries, and orthogonal to e7 + e8

2. SIMPLE ROOTS:
   - 7 linearly independent roots that generate all 126 roots
   - The choice above follows standard conventions
   - The half-integer root (alpha1) creates the exceptional structure

3. CARTAN MATRIX:
   - Encodes angles between simple roots
   - Entry A_ij = 2(alpha_i . alpha_j)/(alpha_j . alpha_j)
   - For E7, det(Cartan) = 2 in standard normalization
   - Every off-diagonal entry is 0 or -1

4. DYNKIN DIAGRAM:
   The E7 Dynkin diagram has the structure:

        1---3---4---5---6---7
                |
                2

   Node 4 connects to nodes 2, 3, and 5. Node 1 is the half-integer
   simple root in this ordering.

5. DETERMINANT VALUE:
   The determinant equals 2, which is correct for E7. This value appears
   in standard references and indicates that the index of the root
   lattice in the weight lattice is 2.

REFERENCES:
- Bourbaki, "Groupes et Algebres de Lie", Chapters 4-6, Planche VII
- Humphreys, "Introduction to Lie Algebras and Representation Theory"
- SageMath documentation for E-type root systems
- Wikipedia articles on E7 and root systems
""")

    print("=" * 70)
    print("CONCLUSION")
    print("=" * 70)
    print("""
This set of simple roots is CORRECT and standard. It:
- Contains only valid E7 roots
- Forms a linearly independent basis (rank 7)
- Gives the correct Cartan determinant (2)
- Follows established mathematical conventions

Every off-diagonal Cartan entry is nonpositive. A positive off-diagonal
entry invalidates a proposed simple-root basis even when the determinant
and generated-root count happen to match E7.
""")


if __name__ == "__main__":
    print_solution()
