#!/usr/bin/env python3
"""
Verify E7 Simple Roots and Cartan Matrix Determinant

This script implements and verifies the standard E7 simple roots following
Bourbaki conventions as used in SageMath and standard references.
"""

import numpy as np


def is_valid_e7_root(v):
    """Check if v is a valid E7 root."""
    # E7 roots must be either:
    # 1. Two +-1 entries, rest 0, sum=0
    # 2. Eight +-0.5 entries, even number of negatives, sum=0

    # Check if it's integer type
    if all(x == int(x) for x in v):
        # Integer root: exactly two non-zero entries that are +-1
        non_zeros = [x for x in v if x != 0]
        if len(non_zeros) == 2 and all(abs(x) == 1 for x in non_zeros) and sum(non_zeros) == 0:
            return True
    # Half-integer root: all entries are +-0.5
    elif all(abs(x) == 0.5 for x in v):
        negatives = sum(1 for x in v if x < 0)
        if negatives % 2 == 0 and abs(sum(v)) < 1e-10:
            return True
    return False


def compute_cartan_matrix(simple_roots):
    """Compute the Cartan matrix from simple roots."""
    n = len(simple_roots)
    cartan = np.zeros((n, n), dtype=int)

    for i in range(n):
        for j in range(n):
            # The Cartan entry is twice the root inner-product ratio.
            dot_ij = np.dot(simple_roots[i], simple_roots[j])
            dot_jj = np.dot(simple_roots[j], simple_roots[j])
            cartan[i, j] = round(2 * dot_ij / dot_jj)

    return cartan


# Standard E7 simple roots (Bourbaki convention)
# These are in an 8-dimensional embedding where E7 is embedded as
# vectors perpendicular to a fixed vector in E8

# Standard E7 simple roots (Bourbaki/Humphreys convention)
# These are the standard choice that gives det(Cartan) = 2

# Set 1: Following E8 embedding with perpendicularity constraint
alpha1 = np.array(
    [0.5, -0.5, -0.5, -0.5, -0.5, -0.5, -0.5, -0.5]
)  # Half-integer root (6 negatives - even)
alpha2 = np.array([1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])  # Sum != 0, not valid
alpha3 = np.array([-1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])  # Integer root
alpha4 = np.array([0.0, -1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0])  # Integer root
alpha5 = np.array([0.0, 0.0, -1.0, 1.0, 0.0, 0.0, 0.0, 0.0])  # Integer root
alpha6 = np.array([0.0, 0.0, 0.0, -1.0, 1.0, 0.0, 0.0, 0.0])  # Integer root
alpha7 = np.array([0.0, 0.0, 0.0, 0.0, -1.0, 1.0, 0.0, 0.0])  # Integer root

# Set 2: Standard E7 roots from literature (correct version)
# These satisfy the E7 constraint that alpha1 + alpha2 = 0 in first two coordinates
alt_alpha1 = np.array(
    [0.5, 0.5, -0.5, -0.5, -0.5, -0.5, 0.5, 0.5]
)  # Half-integer (4 negatives - even)
alt_alpha2 = np.array([0.0, 0.0, 1.0, -1.0, 0.0, 0.0, 0.0, 0.0])  # Integer root
alt_alpha3 = np.array([0.0, 0.0, -1.0, 0.0, 1.0, 0.0, 0.0, 0.0])  # Sum != 0, not valid
alt_alpha4 = np.array([0.0, 0.0, 0.0, 1.0, -1.0, 0.0, 0.0, 0.0])  # Integer root
alt_alpha5 = np.array([0.0, 0.0, 0.0, 0.0, 1.0, -1.0, 0.0, 0.0])  # Integer root
alt_alpha6 = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 1.0, -1.0, 0.0])  # Integer root
alt_alpha7 = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, -1.0])  # Integer root

# Set 3: Correct standard E7 simple roots (following Bourbaki)
# These are the actual standard simple roots that work
std_alpha1 = np.array(
    [0.5, -0.5, -0.5, -0.5, -0.5, -0.5, -0.5, -0.5]
)  # Half-integer (7 negatives - odd, need even!)
std_alpha2 = np.array([0.0, 1.0, -1.0, 0.0, 0.0, 0.0, 0.0, 0.0])  # Integer root
std_alpha3 = np.array([0.0, -1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0])  # Integer root
std_alpha4 = np.array([0.0, 0.0, 1.0, -1.0, 0.0, 0.0, 0.0, 0.0])  # Integer root
std_alpha5 = np.array([0.0, 0.0, 0.0, 1.0, -1.0, 0.0, 0.0, 0.0])  # Integer root
std_alpha6 = np.array([0.0, 0.0, 0.0, 0.0, 1.0, -1.0, 0.0, 0.0])  # Integer root
std_alpha7 = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 1.0, -1.0, 0.0])  # Integer root

# Set 4: Corrected standard E7 roots (proper half-integer with even negatives)
# Following the E7 Dynkin diagram structure where node 1 connects to node 3
correct_alpha1 = np.array([0.0, 1.0, -1.0, 0.0, 0.0, 0.0, 0.0, 0.0])  # Integer root
correct_alpha2 = np.array([0.0, 0.0, 1.0, -1.0, 0.0, 0.0, 0.0, 0.0])  # Integer root
correct_alpha3 = np.array(
    [0.5, 0.5, -0.5, -0.5, -0.5, -0.5, 0.5, 0.5]
)  # Half-integer (4 negatives - even!)
correct_alpha4 = np.array([0.0, 0.0, 0.0, 1.0, -1.0, 0.0, 0.0, 0.0])  # Integer root
correct_alpha5 = np.array([0.0, 0.0, 0.0, 0.0, 1.0, -1.0, 0.0, 0.0])  # Integer root
correct_alpha6 = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 1.0, -1.0, 0.0])  # Integer root
correct_alpha7 = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, -1.0])  # Integer root

# Try all sets
print("=" * 60)
print("E7 SIMPLE ROOTS VERIFICATION")
print("=" * 60)

for name, roots in [
    ("Set 1 (E8 embedding)", [alpha1, alpha2, alpha3, alpha4, alpha5, alpha6, alpha7]),
    (
        "Set 2 (Literature variant)",
        [alt_alpha1, alt_alpha2, alt_alpha3, alt_alpha4, alt_alpha5, alt_alpha6, alt_alpha7],
    ),
    (
        "Set 3 (Bourbaki attempt)",
        [std_alpha1, std_alpha2, std_alpha3, std_alpha4, std_alpha5, std_alpha6, std_alpha7],
    ),
    (
        "Set 4 (Corrected)",
        [
            correct_alpha1,
            correct_alpha2,
            correct_alpha3,
            correct_alpha4,
            correct_alpha5,
            correct_alpha6,
            correct_alpha7,
        ],
    ),
]:
    print(f"\n{name}:")
    print("-" * 40)

    # Verify all are valid E7 roots
    all_valid = True
    for i, root in enumerate(roots, 1):
        valid = is_valid_e7_root(root)
        print(f"  alpha{i}: {root} - Valid: {valid}")
        if not valid:
            all_valid = False

    if all_valid:
        print("\n  All roots are VALID E7 roots!")

        # Check linear independence
        rank = np.linalg.matrix_rank(np.array(roots))
        print(f"  Rank of root matrix: {rank}/7")

        if rank == 7:
            # Compute Cartan matrix
            cartan = compute_cartan_matrix(roots)
            print("\n  Cartan Matrix:")
            print(cartan)

            # Compute determinant
            det = np.linalg.det(cartan)
            print(f"\n  Determinant of Cartan matrix: {det:.0f}")

            # Verify it's a valid Cartan matrix (diagonal entries should be 2)
            if all(cartan[i, i] == 2 for i in range(7)):
                print("  Cartan matrix has correct diagonal entries (all 2)")

            # Check off-diagonal entries are non-positive integers
            valid_cartan = True
            for i in range(7):
                for j in range(7):
                    if i != j and cartan[i, j] > 0:
                        valid_cartan = False

            if valid_cartan:
                print("  Cartan matrix has valid off-diagonal entries (non-positive)")
            else:
                print("  WARNING: Cartan matrix has invalid positive off-diagonal entries")
    else:
        print("\n  ERROR: Not all vectors are valid E7 roots!")

print("\n" + "=" * 60)
print("MATHEMATICAL EXPLANATION")
print("=" * 60)
print("""
The E7 root system has 126 roots in a 7-dimensional space.
It can be embedded in 8 dimensions for computational convenience.

Key Properties:
1. E7 roots come in two types:
   - Integer roots: exactly two +-1 entries, rest 0, sum = 0
   - Half-integer roots: all eight entries are +-0.5, even number
     of negatives, sum = 0

2. Simple roots are a basis of 7 linearly independent roots from
   which all 126 roots can be generated.

3. The Cartan matrix A_ij = 2(alpha_i . alpha_j)/(alpha_j . alpha_j)
   encodes the angles between simple roots.

4. For E7, the determinant of the Cartan matrix equals 2 in the
   standard normalization (where all roots have squared length 2).

References:
- Bourbaki, "Groupes et Algebres de Lie", Ch. 4-6
- Humphreys, "Introduction to Lie Algebras and Representation Theory"
- SageMath documentation on E-type root systems
""")
