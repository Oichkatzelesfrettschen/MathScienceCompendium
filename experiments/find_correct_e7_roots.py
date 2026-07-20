#!/usr/bin/env python3
"""Find the correct E7 simple roots that give determinant 1."""

import numpy as np


def test_simple_roots(roots):
    """Test if a set of simple roots gives correct E7 Cartan matrix."""
    n = len(roots)

    # Check they sum to zero
    for i, root in enumerate(roots):
        if abs(np.sum(root)) > 1e-10:
            return None, f"Root {i + 1} doesn't sum to zero"

    # Check squared lengths
    for i, root in enumerate(roots):
        if abs(np.sum(root**2) - 2.0) > 1e-10:
            return None, f"Root {i + 1} has wrong length"

    # Compute Cartan matrix
    cartan = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            cartan[i, j] = np.dot(roots[i], roots[j])

    det = np.linalg.det(cartan)
    return det, cartan


# Standard E7 simple roots (from E8 restriction)
# Based on the standard construction where E7 = E8 \ {alpha_1}
# where alpha_1 is removed from E8 simple roots

print("FINDING CORRECT E7 SIMPLE ROOTS")
print("=" * 80)
print()

# E8 simple roots (standard)
e8_roots = np.array(
    [
        [0.5, -0.5, -0.5, -0.5, -0.5, -0.5, -0.5, 0.5],  # alpha_1 (to be removed for E7)
        [1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # alpha_2
        [-1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # alpha_3
        [0.0, -1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # alpha_4
        [0.0, 0.0, -1.0, 1.0, 0.0, 0.0, 0.0, 0.0],  # alpha_5
        [0.0, 0.0, 0.0, -1.0, 1.0, 0.0, 0.0, 0.0],  # alpha_6
        [0.0, 0.0, 0.0, 0.0, -1.0, 1.0, 0.0, 0.0],  # alpha_7
        [0.0, 0.0, 0.0, 0.0, 0.0, -1.0, 1.0, 0.0],  # alpha_8
    ]
)

# E7 is obtained by removing alpha_1 and projecting to the orthogonal complement
# But we need to be more careful about the construction

# Correct E7 simple roots (standard mathematical convention)
# These are the roots that give the correct Dynkin diagram and det = 1
e7_roots_correct = np.array(
    [
        [0.5, -0.5, -0.5, -0.5, -0.5, -0.5, -0.5, 0.5],  # alpha_1
        [0.0, 1.0, -1.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # alpha_2
        [0.0, 0.0, 1.0, -1.0, 0.0, 0.0, 0.0, 0.0],  # alpha_3
        [0.0, 0.0, 0.0, 1.0, -1.0, 0.0, 0.0, 0.0],  # alpha_4
        [0.0, 0.0, 0.0, 0.0, 1.0, -1.0, 0.0, 0.0],  # alpha_5
        [0.0, 0.0, 0.0, 0.0, 0.0, 1.0, -1.0, 0.0],  # alpha_6
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, -1.0],  # alpha_7
    ]
)

print("Testing Standard E7 Construction (7 roots from E8):")
det, cartan = test_simple_roots(e7_roots_correct)
if det is not None:
    print(f"  Determinant: {det:.10f}")
    if abs(det - 1.0) < 1e-10:
        print("  [DONE] SUCCESS! Determinant = 1")
        print("\n  Cartan Matrix:")
        print(cartan)
        print("\n  CORRECT E7 SIMPLE ROOTS FOUND:")
        for i, root in enumerate(e7_roots_correct):
            print(f"    alpha{i + 1} = {root}")
    else:
        print(f"  [FAILED] Determinant = {det}, not 1")
else:
    print(f"  Error: {cartan}")

print("\n" + "=" * 80)

# Try alternative orderings to get the correct Dynkin diagram
# The E7 Dynkin diagram should have:
#   alpha_1 -- alpha_3 -- alpha_4 -- alpha_5 -- alpha_6 -- alpha_7
#        |
#       alpha_2

# Let's construct E7 roots that match this Dynkin diagram
e7_alt = np.array(
    [
        [1.0, -1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # alpha_1
        [0.0, 1.0, -1.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # alpha_2
        [-0.5, -0.5, -0.5, -0.5, 0.5, 0.5, 0.5, 0.5],  # alpha_3
        [0.0, 0.0, 1.0, -1.0, 0.0, 0.0, 0.0, 0.0],  # alpha_4
        [0.0, 0.0, 0.0, 1.0, -1.0, 0.0, 0.0, 0.0],  # alpha_5
        [0.0, 0.0, 0.0, 0.0, 1.0, -1.0, 0.0, 0.0],  # alpha_6
        [0.0, 0.0, 0.0, 0.0, 0.0, 1.0, -1.0, 0.0],  # alpha_7
    ]
)

print("\nTesting Alternative E7 with correct Dynkin structure:")
det, cartan = test_simple_roots(e7_alt)
if det is not None:
    print(f"  Determinant: {det:.10f}")
    if abs(det - 1.0) < 1e-10:
        print("  [DONE] SUCCESS! Determinant = 1")
        print("\n  Cartan Matrix:")
        print(cartan)
        print("\n  CORRECT E7 SIMPLE ROOTS FOUND:")
        for i, root in enumerate(e7_alt):
            print(f"    alpha{i + 1} = {root}")
    else:
        print(f"  [FAILED] Determinant = {det}, not 1")
else:
    print(f"  Error: {cartan}")

print("\n" + "=" * 80)
print("FINAL RECOMMENDATION:")
print("=" * 80)

# The canonical E7 simple roots
canonical_e7 = np.array(
    [
        [0.5, -0.5, -0.5, -0.5, -0.5, -0.5, -0.5, 0.5],  # alpha_1
        [0.0, 1.0, -1.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # alpha_2
        [0.0, -1.0, -1.0, 0.0, 0.0, 0.0, 0.0, 2.0],  # alpha_3 - needs correction
        [1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, -2.0],  # alpha_4 - needs correction
        [0.0, 0.0, 1.0, -1.0, 0.0, 0.0, 0.0, 0.0],  # alpha_5
        [0.0, 0.0, 0.0, 1.0, -1.0, 0.0, 0.0, 0.0],  # alpha_6
        [0.0, 0.0, 0.0, 0.0, 1.0, -1.0, 0.0, 0.0],  # alpha_7
    ]
)

# Actually, let's use the correct canonical form
canonical_e7_correct = np.array(
    [
        [-0.5, -0.5, -0.5, 0.5, 0.5, 0.5, 0.5, -0.5],  # alpha_1
        [1.0, -1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # alpha_2
        [-1.0, -1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0],  # alpha_3
        [0.0, 1.0, -1.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # alpha_4
        [0.0, 0.0, 1.0, -1.0, 0.0, 0.0, 0.0, 0.0],  # alpha_5
        [0.0, 0.0, 0.0, 1.0, -1.0, 0.0, 0.0, 0.0],  # alpha_6
        [0.0, 0.0, 0.0, 0.0, 1.0, -1.0, 0.0, 0.0],  # alpha_7
    ]
)

print("\nUsing well-known E7 simple roots:")
# These are the actual correct E7 simple roots
e7_final = np.array(
    [
        [1.0, -1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # alpha_1 = e_1 - e_2
        [-0.5, -0.5, -0.5, -0.5, -0.5, 0.5, 0.5, 0.5],  # alpha_2
        [0.0, 1.0, -1.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # alpha_3 = e_2 - e_3
        [0.0, 0.0, 1.0, -1.0, 0.0, 0.0, 0.0, 0.0],  # alpha_4 = e_3 - e_4
        [0.0, 0.0, 0.0, 1.0, -1.0, 0.0, 0.0, 0.0],  # alpha_5 = e_4 - e_5
        [0.0, 0.0, 0.0, 0.0, 1.0, -1.0, 0.0, 0.0],  # alpha_6 = e_5 - e_6
        [0.0, 0.0, 0.0, 0.0, 0.0, 1.0, -1.0, 0.0],  # alpha_7 = e_6 - e_7
    ]
)

det, cartan = test_simple_roots(e7_final)
if det is not None:
    print(f"  Determinant: {det:.10f}")
    if abs(det - 1.0) < 1e-10:
        print("  [DONE] SUCCESS! Determinant = 1\n")
        print("  Cartan Matrix:")
        print(cartan)
        print("\n  THESE ARE THE CORRECT E7 SIMPLE ROOTS:")
        for i, root in enumerate(e7_final):
            print(f"    alpha{i + 1} = {root}")

        # Check Dynkin diagram
        print("\n  Dynkin Diagram Connections (where A[i,j] = -1):")
        for i in range(7):
            for j in range(i + 1, 7):
                if abs(cartan[i, j] + 1.0) < 1e-10:
                    print(f"    alpha{i + 1} -- alpha{j + 1}")
    else:
        print(f"  [FAILED] Determinant = {det}, not 1")
else:
    print(f"  Error: {cartan}")
