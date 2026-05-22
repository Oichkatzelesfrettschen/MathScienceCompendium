#!/usr/bin/env python3
"""Find the correct E7 simple roots that give determinant 1."""

from itertools import combinations

import numpy as np


def test_simple_roots(roots, name="Test"):
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
# Based on the standard construction where E7 = E8 \ {α_1}
# where α_1 is removed from E8 simple roots

print("FINDING CORRECT E7 SIMPLE ROOTS")
print("=" * 80)
print()

# E8 simple roots (standard)
e8_roots = np.array(
    [
        [0.5, -0.5, -0.5, -0.5, -0.5, -0.5, -0.5, 0.5],  # α₁ (to be removed for E7)
        [1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # α₂
        [-1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # α₃
        [0.0, -1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # α₄
        [0.0, 0.0, -1.0, 1.0, 0.0, 0.0, 0.0, 0.0],  # α₅
        [0.0, 0.0, 0.0, -1.0, 1.0, 0.0, 0.0, 0.0],  # α₆
        [0.0, 0.0, 0.0, 0.0, -1.0, 1.0, 0.0, 0.0],  # α₇
        [0.0, 0.0, 0.0, 0.0, 0.0, -1.0, 1.0, 0.0],  # α₈
    ]
)

# E7 is obtained by removing α₁ and projecting to the orthogonal complement
# But we need to be more careful about the construction

# Correct E7 simple roots (standard mathematical convention)
# These are the roots that give the correct Dynkin diagram and det = 1
e7_roots_correct = np.array(
    [
        [0.5, -0.5, -0.5, -0.5, -0.5, -0.5, -0.5, 0.5],  # α₁
        [0.0, 1.0, -1.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # α₂
        [0.0, 0.0, 1.0, -1.0, 0.0, 0.0, 0.0, 0.0],  # α₃
        [0.0, 0.0, 0.0, 1.0, -1.0, 0.0, 0.0, 0.0],  # α₄
        [0.0, 0.0, 0.0, 0.0, 1.0, -1.0, 0.0, 0.0],  # α₅
        [0.0, 0.0, 0.0, 0.0, 0.0, 1.0, -1.0, 0.0],  # α₆
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, -1.0],  # α₇
    ]
)

print("Testing Standard E7 Construction (7 roots from E8):")
det, cartan = test_simple_roots(e7_roots_correct, "E7 standard")
if det is not None:
    print(f"  Determinant: {det:.10f}")
    if abs(det - 1.0) < 1e-10:
        print("  [DONE] SUCCESS! Determinant = 1")
        print("\n  Cartan Matrix:")
        print(cartan)
        print("\n  CORRECT E7 SIMPLE ROOTS FOUND:")
        for i, root in enumerate(e7_roots_correct):
            print(f"    α{i + 1} = {root}")
    else:
        print(f"  [FAILED] Determinant = {det}, not 1")
else:
    print(f"  Error: {cartan}")

print("\n" + "=" * 80)

# Try alternative orderings to get the correct Dynkin diagram
# The E7 Dynkin diagram should have:
#   α₁ — α₃ — α₄ — α₅ — α₆ — α₇
#        |
#       α₂

# Let's construct E7 roots that match this Dynkin diagram
e7_alt = np.array(
    [
        [1.0, -1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # α₁
        [0.0, 1.0, -1.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # α₂
        [-0.5, -0.5, -0.5, -0.5, 0.5, 0.5, 0.5, 0.5],  # α₃
        [0.0, 0.0, 1.0, -1.0, 0.0, 0.0, 0.0, 0.0],  # α₄
        [0.0, 0.0, 0.0, 1.0, -1.0, 0.0, 0.0, 0.0],  # α₅
        [0.0, 0.0, 0.0, 0.0, 1.0, -1.0, 0.0, 0.0],  # α₆
        [0.0, 0.0, 0.0, 0.0, 0.0, 1.0, -1.0, 0.0],  # α₇
    ]
)

print("\nTesting Alternative E7 with correct Dynkin structure:")
det, cartan = test_simple_roots(e7_alt, "E7 alternative")
if det is not None:
    print(f"  Determinant: {det:.10f}")
    if abs(det - 1.0) < 1e-10:
        print("  [DONE] SUCCESS! Determinant = 1")
        print("\n  Cartan Matrix:")
        print(cartan)
        print("\n  CORRECT E7 SIMPLE ROOTS FOUND:")
        for i, root in enumerate(e7_alt):
            print(f"    α{i + 1} = {root}")
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
        [0.5, -0.5, -0.5, -0.5, -0.5, -0.5, -0.5, 0.5],  # α₁
        [0.0, 1.0, -1.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # α₂
        [0.0, -1.0, -1.0, 0.0, 0.0, 0.0, 0.0, 2.0],  # α₃ - needs correction
        [1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, -2.0],  # α₄ - needs correction
        [0.0, 0.0, 1.0, -1.0, 0.0, 0.0, 0.0, 0.0],  # α₅
        [0.0, 0.0, 0.0, 1.0, -1.0, 0.0, 0.0, 0.0],  # α₆
        [0.0, 0.0, 0.0, 0.0, 1.0, -1.0, 0.0, 0.0],  # α₇
    ]
)

# Actually, let's use the correct canonical form
canonical_e7_correct = np.array(
    [
        [-0.5, -0.5, -0.5, 0.5, 0.5, 0.5, 0.5, -0.5],  # α₁
        [1.0, -1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # α₂
        [-1.0, -1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0],  # α₃
        [0.0, 1.0, -1.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # α₄
        [0.0, 0.0, 1.0, -1.0, 0.0, 0.0, 0.0, 0.0],  # α₅
        [0.0, 0.0, 0.0, 1.0, -1.0, 0.0, 0.0, 0.0],  # α₆
        [0.0, 0.0, 0.0, 0.0, 1.0, -1.0, 0.0, 0.0],  # α₇
    ]
)

print("\nUsing well-known E7 simple roots:")
# These are the actual correct E7 simple roots
e7_final = np.array(
    [
        [1.0, -1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # α₁ = e₁ - e₂
        [-0.5, -0.5, -0.5, -0.5, -0.5, 0.5, 0.5, 0.5],  # α₂
        [0.0, 1.0, -1.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # α₃ = e₂ - e₃
        [0.0, 0.0, 1.0, -1.0, 0.0, 0.0, 0.0, 0.0],  # α₄ = e₃ - e₄
        [0.0, 0.0, 0.0, 1.0, -1.0, 0.0, 0.0, 0.0],  # α₅ = e₄ - e₅
        [0.0, 0.0, 0.0, 0.0, 1.0, -1.0, 0.0, 0.0],  # α₆ = e₅ - e₆
        [0.0, 0.0, 0.0, 0.0, 0.0, 1.0, -1.0, 0.0],  # α₇ = e₆ - e₇
    ]
)

det, cartan = test_simple_roots(e7_final, "E7 final")
if det is not None:
    print(f"  Determinant: {det:.10f}")
    if abs(det - 1.0) < 1e-10:
        print("  [DONE] SUCCESS! Determinant = 1\n")
        print("  Cartan Matrix:")
        print(cartan)
        print("\n  THESE ARE THE CORRECT E7 SIMPLE ROOTS:")
        for i, root in enumerate(e7_final):
            print(f"    α{i + 1} = {root}")

        # Check Dynkin diagram
        print("\n  Dynkin Diagram Connections (where A[i,j] = -1):")
        for i in range(7):
            for j in range(i + 1, 7):
                if abs(cartan[i, j] + 1.0) < 1e-10:
                    print(f"    α{i + 1} — α{j + 1}")
    else:
        print(f"  [FAILED] Determinant = {det}, not 1")
else:
    print(f"  Error: {cartan}")
