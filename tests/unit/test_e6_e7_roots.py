"""Unit tests for E6 and E7 root systems."""

import unittest

import numpy as np
from src.mathphysics.algebras.roots import E6RootSystem, E7RootSystem


class TestE6E7Roots(unittest.TestCase):
    def test_e6_properties(self):
        e6 = E6RootSystem()
        roots = e6.generate_roots()
        self.assertEqual(len(roots), 72)

        cartan = e6.compute_cartan_matrix()
        det = np.linalg.det(cartan)
        self.assertAlmostEqual(det, 3.0)

        # Verify rank
        self.assertEqual(e6.properties.rank, 6)
        # Verify dimension
        self.assertEqual(e6.properties.dimension, 78)

    def test_e7_properties(self):
        e7 = E7RootSystem()
        roots = e7.generate_roots()
        self.assertEqual(len(roots), 126)

        cartan = e7.compute_cartan_matrix()
        det = np.linalg.det(cartan)
        self.assertAlmostEqual(det, 2.0)
        off_diagonal = cartan.copy()
        np.fill_diagonal(off_diagonal, 0.0)
        self.assertTrue(np.all(off_diagonal <= 0.0))
        self.assertTrue(np.all(np.linalg.eigvalsh(cartan) > 0.0))

        # Verify rank
        self.assertEqual(e7.properties.rank, 7)
        # Verify dimension
        self.assertEqual(e7.properties.dimension, 133)

    def test_e7_127_states(self):
        e7 = E7RootSystem()
        roots = e7.generate_roots(include_zero=True)
        self.assertEqual(len(roots), 127)
        # Last root should be zero
        self.assertTrue(np.allclose(roots[-1], 0.0))


if __name__ == "__main__":
    unittest.main()
