# E7 Cartan Basis Audit

## Result

The former `E7RootSystem.generate_simple_roots()` basis was invalid. It
generated 126 roots and had Cartan determinant 2, but its Cartan matrix had a
positive off-diagonal entry. A generalized Cartan matrix must have diagonal
entries 2 and nonpositive integral off-diagonal entries. Root count and
determinant alone did not detect the defect.

The canonical implementation now uses seven E8 roots in the subsystem
orthogonal to `e7 + e8`:

```text
( 1/2, -1/2, -1/2, -1/2, -1/2, -1/2, -1/2,  1/2)
(   1,    1,    0,    0,    0,    0,    0,    0)
(  -1,    1,    0,    0,    0,    0,    0,    0)
(   0,   -1,    1,    0,    0,    0,    0,    0)
(   0,    0,   -1,    1,    0,    0,    0,    0)
(   0,    0,    0,   -1,    1,    0,    0,    0)
(   0,    0,    0,    0,   -1,    1,    0,    0)
```

Its Cartan matrix is:

```text
[[ 2,  0, -1,  0,  0,  0,  0],
 [ 0,  2,  0, -1,  0,  0,  0],
 [-1,  0,  2, -1,  0,  0,  0],
 [ 0, -1, -1,  2, -1,  0,  0],
 [ 0,  0,  0, -1,  2, -1,  0],
 [ 0,  0,  0,  0, -1,  2, -1],
 [ 0,  0,  0,  0,  0, -1,  2]]
```

## Executable acceptance criteria

- The simple roots have rank 7 and squared norm 2.
- The Cartan matrix is symmetric and integral.
- Its diagonal is 2 and every off-diagonal entry is 0 or -1.
- Its Dynkin graph is connected.
- Its determinant is 2 and all eigenvalues are positive.
- Weyl reflection closure produces exactly 126 roots.

The determinant 2 is an invariant of the E7 Cartan matrix. It is the order of
the quotient of the weight lattice by the root lattice, `P/Q`. It is not a
normalization accident and cannot be changed to 1 by choosing another valid
simple-root basis.

## E9-E11 consequence

The E9 affine node must attach to node zero in the repository's E8 node
ordering. The old node-seven attachment produced determinant -2 and therefore
did not construct affine E8. The corrected extension has determinants 0, -1,
and -2 for E9, E10, and E11, respectively. Tests also require one null
direction for E9 and one negative direction for E10 and E11.

## Reproduction

```sh
pytest -q tests/unit/test_roots.py tests/unit/test_e6_e7_roots.py
ruff check src/mathphysics/algebras/roots.py tests/unit/test_roots.py \
  tests/unit/test_e6_e7_roots.py
```

The executable implementation and tests are authoritative. Standalone search
scripts under `experiments/` are exploratory records and must not override
these invariants.
