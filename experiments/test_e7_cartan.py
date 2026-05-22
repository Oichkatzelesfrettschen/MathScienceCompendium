#!/usr/bin/env python3
"""Test script to verify E7 Cartan matrix computation and simple roots."""

import sys

import numpy as np


def verify_e7_simple_roots():
    """Verify the E7 simple roots and Cartan matrix."""

    print("=" * 80)
    print("E7 CARTAN MATRIX VERIFICATION")
    print("=" * 80)
    print()

    # Standard E7 simple roots (Bourbaki convention)
    # The E7 simple roots embedded in R^8 with sum = 0 constraint
    # Following the standard E7 Dynkin diagram:
    #   α₁ — α₃ — α₄ — α₅ — α₆ — α₇
    #        |
    #       α₂
    simple_roots = np.array(
        [
            [0.5, -0.5, -0.5, -0.5, -0.5, -0.5, 0.5, 0.5],  # α₁
            [0.0, 0.0, 1.0, -1.0, 0.0, 0.0, 0.0, 0.0],  # α₂
            [0.0, 0.0, -1.0, 0.0, 1.0, 0.0, 0.0, 0.0],  # α₃
            [0.0, 0.0, 0.0, 1.0, -1.0, 0.0, 0.0, 0.0],  # α₄
            [0.0, 0.0, 0.0, 0.0, 1.0, -1.0, 0.0, 0.0],  # α₅
            [0.0, 0.0, 0.0, 0.0, 0.0, 1.0, -1.0, 0.0],  # α₆
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, -1.0],  # α₇
        ]
    )

    # Verification 1: All roots sum to zero
    print("1. Checking if all simple roots sum to zero:")
    for i, root in enumerate(simple_roots):
        root_sum = np.sum(root)
        print(f"   α{i + 1} sum = {root_sum:.10f}")
        assert abs(root_sum) < 1e-10, f"Root α{i + 1} does not sum to zero!"
    print("   [DONE] All simple roots sum to zero\n")

    # Verification 2: All roots have squared length 2
    print("2. Checking squared lengths of simple roots:")
    for i, root in enumerate(simple_roots):
        squared_length = np.sum(root**2)
        print(f"   ||α{i + 1}||² = {squared_length:.10f}")
        assert abs(squared_length - 2.0) < 1e-10, f"Root α{i + 1} has incorrect length!"
    print("   [DONE] All simple roots have squared length 2\n")

    # Verification 3: Compute Cartan matrix
    print("3. Computing Cartan matrix:")
    n = len(simple_roots)
    cartan = np.zeros((n, n))

    for i in range(n):
        for j in range(n):
            # For simply-laced algebras like E7:
            # A_ij = 2 * <α_i, α_j> / <α_j, α_j>
            # Since all roots have length 2: <α_j, α_j> = 2
            # So: A_ij = <α_i, α_j>
            inner_prod = np.dot(simple_roots[i], simple_roots[j])
            cartan[i, j] = inner_prod

    print("\nCartan Matrix A:")
    print(cartan)
    print()

    # Verification 4: Check Cartan matrix properties
    print("4. Verifying Cartan matrix properties:")

    # Diagonal elements should be 2
    print("   a) Diagonal elements (should all be 2):")
    for i in range(n):
        print(f"      A[{i},{i}] = {cartan[i, i]:.1f}")
        assert abs(cartan[i, i] - 2.0) < 1e-10, f"Diagonal element A[{i},{i}] is not 2!"
    print("      [DONE] All diagonal elements equal 2\n")

    # Off-diagonal elements should be 0 or -1
    print("   b) Off-diagonal elements (should be 0 or -1):")
    for i in range(n):
        for j in range(n):
            if i != j:
                val = cartan[i, j]
                if abs(val) > 1e-10:  # Non-zero
                    print(f"      A[{i},{j}] = {val:.1f}")
                    assert abs(val + 1.0) < 1e-10, (
                        f"Off-diagonal element A[{i},{j}] = {val} is not 0 or -1!"
                    )
    print("      [DONE] All off-diagonal elements are 0 or -1\n")

    # Check E7 Dynkin diagram structure
    print("   c) E7 Dynkin diagram connections:")
    print("      Expected structure:")
    print("      α₁ — α₃ — α₄ — α₅ — α₆ — α₇")
    print("           |")
    print("          α₂")
    print()
    print("      Actual connections (where A[i,j] = -1):")

    connections = []
    for i in range(n):
        for j in range(i + 1, n):
            if abs(cartan[i, j] + 1.0) < 1e-10:
                connections.append((i + 1, j + 1))
                print(f"      α{i + 1} — α{j + 1}")

    expected_connections = [(1, 3), (2, 4), (3, 4), (4, 5), (5, 6), (6, 7)]
    print(f"\n      Expected connections: {expected_connections}")
    print(f"      Actual connections: {connections}")

    if set(connections) == set(expected_connections):
        print("      [DONE] Dynkin diagram structure is correct!\n")
    else:
        print("      [FAILED] Dynkin diagram structure is INCORRECT!\n")

    # Verification 5: Compute determinant
    print("5. Computing Cartan matrix determinant:")
    det = np.linalg.det(cartan)
    print(f"   det(A) = {det:.10f}")
    print(f"   Expected: 1.0")

    if abs(det - 1.0) < 1e-10:
        print("   [DONE] Determinant equals 1 (CORRECT!)")
    else:
        print(f"   [FAILED] Determinant = {det:.10f}, expected 1.0 (INCORRECT!)")
        print("\n   ROOT CAUSE: The simple roots are not the correct set.")
        print("   The Dynkin diagram structure is correct, but we need")
        print("   different simple roots from the E7 root system.\n")

    print("\n" + "=" * 80)
    print("ANALYSIS SUMMARY")
    print("=" * 80)

    if abs(det - 1.0) > 1e-10:
        print("\nPROBLEM IDENTIFIED:")
        print("  The current simple roots give the correct Dynkin diagram")
        print("  structure but wrong Cartan determinant.")
        print("\n  This suggests we need to use a different embedding or")
        print("  different selection of simple roots from the E7 root system.")

        # Try alternative simple roots
        print("\n" + "=" * 80)
        print("TRYING ALTERNATIVE E7 SIMPLE ROOTS")
        print("=" * 80)

        # Alternative set based on standard E8 restriction
        alt_simple_roots = np.array(
            [
                [1.0, -1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # α₁
                [0.0, 1.0, -1.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # α₂
                [0.0, 0.0, 1.0, -1.0, 0.0, 0.0, 0.0, 0.0],  # α₃
                [0.0, 0.0, 0.0, 1.0, -1.0, 0.0, 0.0, 0.0],  # α₄
                [0.0, 0.0, 0.0, 0.0, 1.0, -1.0, 0.0, 0.0],  # α₅
                [0.0, 0.0, 0.0, 0.0, 0.0, 1.0, -1.0, 0.0],  # α₆
                [
                    -0.5,
                    -0.5,
                    -0.5,
                    -0.5,
                    -0.5,
                    -0.5,
                    -0.5,
                    -0.5,
                ],  # α₇ (incorrect - doesn't sum to 0!)
            ]
        )

        # Fix α₇ to sum to zero
        alt_simple_roots[6] = [0.5, 0.5, 0.5, -0.5, -0.5, -0.5, -0.5, 0.5]

        print("\nTrying alternative simple roots...")
        alt_cartan = np.zeros((7, 7))
        for i in range(7):
            for j in range(7):
                inner_prod = np.dot(alt_simple_roots[i], alt_simple_roots[j])
                alt_cartan[i, j] = inner_prod

        print("\nAlternative Cartan Matrix:")
        print(alt_cartan)
        alt_det = np.linalg.det(alt_cartan)
        print(f"\nDeterminant: {alt_det:.10f}")

        if abs(alt_det - 1.0) < 1e-10:
            print("[DONE] SUCCESS! This set gives determinant 1!\n")
            print("CORRECT SIMPLE ROOTS:")
            for i, root in enumerate(alt_simple_roots):
                print(f"  α{i + 1} = {root}")
        else:
            print(f"[FAILED] Still incorrect: det = {alt_det}")

    return cartan, det


if __name__ == "__main__":
    cartan, det = verify_e7_simple_roots()

    # Return exit code based on success
    if abs(det - 1.0) < 1e-10:
        sys.exit(0)
    else:
        sys.exit(1)
