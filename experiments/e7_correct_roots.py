#!/usr/bin/env python3
"""Derive the correct E7 simple roots mathematically."""

import numpy as np


print("=" * 80)
print("E7 SIMPLE ROOTS DERIVATION")
print("=" * 80)
print()

# The correct E7 simple roots (Bourbaki convention)
# These are well-established in the literature
# E7 is embedded in R^8 with the constraint sum(x_i) = 0

# The standard E7 simple roots are:
e7_simple_roots = np.array(
    [
        # Six roots of the form e_i - e_{i+1}
        [1.0, -1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # alpha_1 = e_1 - e_2
        [0.0, 1.0, -1.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # alpha_2 = e_2 - e_3
        [0.0, 0.0, 1.0, -1.0, 0.0, 0.0, 0.0, 0.0],  # alpha_3 = e_3 - e_4
        [0.0, 0.0, 0.0, 1.0, -1.0, 0.0, 0.0, 0.0],  # alpha_4 = e_4 - e_5
        [0.0, 0.0, 0.0, 0.0, 1.0, -1.0, 0.0, 0.0],  # alpha_5 = e_5 - e_6
        [0.0, 0.0, 0.0, 0.0, 0.0, 1.0, -1.0, 0.0],  # alpha_6 = e_6 - e_7
        # One special root (half-integer coordinates)
        # This must sum to 0 and have squared length 2
        # Standard choice: (-1/2, -1/2, -1/2, -1/2, 1/2, 1/2, 1/2, 1/2)
        [-0.5, -0.5, -0.5, -0.5, 0.5, 0.5, 0.5, 0.5],  # alpha_7
    ]
)

print("Standard E7 Simple Roots (Chain + Special Root):")
print("-" * 50)

# Verify properties
all_valid = True
for i, root in enumerate(e7_simple_roots):
    root_sum = np.sum(root)
    squared_length = np.sum(root**2)
    print(f"alpha{i + 1} = {root}")
    print(f"     Sum: {root_sum:.6f}, ||alpha||^2 = {squared_length:.6f}")

    if abs(root_sum) > 1e-10:
        print("     ERROR: Root doesn't sum to 0!")
        all_valid = False
    if abs(squared_length - 2.0) > 1e-10:
        print("     ERROR: Root doesn't have squared length 2!")
        all_valid = False

print()

if all_valid:
    # Compute Cartan matrix
    n = 7
    cartan = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            cartan[i, j] = np.dot(e7_simple_roots[i], e7_simple_roots[j])

    print("Cartan Matrix:")
    print(cartan)
    print()

    det = np.linalg.det(cartan)
    print(f"Determinant: {det:.10f}")

    if abs(det - 1.0) < 1e-10:
        print("[DONE] SUCCESS! Determinant = 1")
    else:
        print(f"[FAILED] PROBLEM: Determinant = {det}, expected 1")

    # Check Dynkin diagram
    print("\nDynkin Diagram Connections (where A[i,j] = -1):")
    connections = []
    for i in range(n):
        for j in range(i + 1, n):
            if abs(cartan[i, j] + 1.0) < 1e-10:
                connections.append((i + 1, j + 1))
                print(f"  alpha{i + 1} -- alpha{j + 1}")

    # Expected E7 Dynkin diagram:
    #   alpha_1 -- alpha_2 -- alpha_3 -- alpha_4 -- alpha_5 -- alpha_6
    #                   |
    #                  alpha_7
    # Connections: (1,2), (2,3), (3,4), (4,5), (4,7), (5,6)

    expected = [(1, 2), (2, 3), (3, 4), (4, 5), (4, 7), (5, 6)]
    print(f"\nExpected connections: {expected}")
    print(f"Actual connections:   {connections}")

    # But wait, this gives A_6 + A_1, not E7!
    # The correct E7 has a different structure

print("\n" + "=" * 80)
print("CORRECTED E7 SIMPLE ROOTS (Proper E7 Dynkin Diagram)")
print("=" * 80)
print()

# The CORRECT E7 simple roots for the proper Dynkin diagram:
# E7 Dynkin diagram:
#   alpha_1 -- alpha_3 -- alpha_4 -- alpha_5 -- alpha_6 -- alpha_7
#        |
#       alpha_2

# We need to reorder/modify to get the correct branching
e7_correct = np.array(
    [
        # alpha_1 connects only to alpha_3
        [-0.5, -0.5, -0.5, -0.5, -0.5, 0.5, 0.5, 0.5],  # alpha_1
        # alpha_2 connects only to alpha_3 (branch)
        [1.0, 1.0, 0.0, 0.0, 0.0, 0.0, -1.0, -1.0],  # alpha_2
        # alpha_3 connects to alpha_1, alpha_2, alpha_4 (central node)
        [0.0, -1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # alpha_3
        # alpha_4 connects to alpha_3, alpha_5
        [0.0, 0.0, -1.0, 1.0, 0.0, 0.0, 0.0, 0.0],  # alpha_4
        # alpha_5 connects to alpha_4, alpha_6
        [0.0, 0.0, 0.0, -1.0, 1.0, 0.0, 0.0, 0.0],  # alpha_5
        # alpha_6 connects to alpha_5, alpha_7
        [0.0, 0.0, 0.0, 0.0, -1.0, 1.0, 0.0, 0.0],  # alpha_6
        # alpha_7 connects only to alpha_6
        [0.0, 0.0, 0.0, 0.0, 0.0, -1.0, 1.0, 0.0],  # alpha_7
    ]
)

print("E7 Simple Roots (Correct Dynkin Diagram):")
print("-" * 50)

# Verify properties
all_valid = True
for i, root in enumerate(e7_correct):
    root_sum = np.sum(root)
    squared_length = np.sum(root**2)
    print(f"alpha{i + 1} = {root}")
    print(f"     Sum: {root_sum:.6f}, ||alpha||^2 = {squared_length:.6f}")

    if abs(root_sum) > 1e-10:
        print("     ERROR: Root doesn't sum to 0!")
        all_valid = False
    if abs(squared_length - 2.0) > 1e-10:
        print("     ERROR: Root doesn't have squared length 2!")
        all_valid = False

print()

if all_valid:
    # Compute Cartan matrix
    n = 7
    cartan = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            cartan[i, j] = np.dot(e7_correct[i], e7_correct[j])

    print("Cartan Matrix:")
    print(cartan)
    print()

    det = np.linalg.det(cartan)
    print(f"Determinant: {det:.10f}")

    if abs(det - 1.0) < 1e-10:
        print("[DONE] SUCCESS! Determinant = 1")
        print("\n" + "=" * 80)
        print("SOLUTION FOUND!")
        print("=" * 80)
        print("\nThe correct E7 simple roots are:")
        for i, root in enumerate(e7_correct):
            print(f"  alpha{i + 1} = {root}")
    else:
        print(f"[FAILED] PROBLEM: Determinant = {det}, expected 1")

    # Check Dynkin diagram
    print("\nDynkin Diagram Connections (where A[i,j] = -1):")
    connections = []
    for i in range(n):
        for j in range(i + 1, n):
            if abs(cartan[i, j] + 1.0) < 1e-10:
                connections.append((i + 1, j + 1))
                print(f"  alpha{i + 1} -- alpha{j + 1}")

    print("\nExpected E7 Dynkin diagram:")
    print("  alpha_1 -- alpha_3 -- alpha_4 -- alpha_5 -- alpha_6 -- alpha_7")
    print("       |")
    print("      alpha_2")

    expected = [(1, 3), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7)]
    print(f"\nExpected connections: {expected}")
    print(f"Actual connections:   {connections}")
