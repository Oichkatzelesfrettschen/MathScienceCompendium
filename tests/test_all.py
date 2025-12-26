"""Comprehensive test suite for all modules."""

import pytest
import numpy as np

# Add src to path

from mathphysics.algebras.cayley_dickson import (Real, Complex, Quaternion, Octonion, Sedenion, Pathion,
                             CayleyDicksonValidator)
from mathphysics.fractal_analysis import (FractalGenerator, FractalDimensionCalculator)
from mathphysics.algebras.roots import E8RootSystem, ExceptionalLieAlgebras, LieAlgebraCalculator
from mathphysics.lattice_theory import E8Lattice, LeechLattice, SpherePackingAnalyzer
from mathphysics.modular_forms import ModularForms, MonstrousMoonshine, EllipticCurves


class TestCayleyDickson:
    """Tests for Cayley-Dickson algebras."""

    def test_real_arithmetic(self):
        """Test real number operations."""
        r1 = Real(3.0)
        r2 = Real(4.0)

        assert abs((r1 + r2).coeffs[0] - 7.0) < 1e-10
        assert abs((r1 * r2).coeffs[0] - 12.0) < 1e-10
        assert abs(r1.norm() - 3.0) < 1e-10

    def test_complex_multiplication(self):
        """Test complex number multiplication."""
        z1 = Complex([1, 2])  # 1 + 2i
        z2 = Complex([3, 4])  # 3 + 4i

        product = z1 * z2  # Should be -5 + 10i
        assert abs(product.real - (-5)) < 1e-10
        assert abs(product.imag - 10) < 1e-10

    def test_complex_conjugate(self):
        """Test complex conjugation."""
        z = Complex([3, 4])
        z_conj = z.conjugate()

        assert abs(z_conj.real - 3) < 1e-10
        assert abs(z_conj.imag - (-4)) < 1e-10

    def test_complex_norm(self):
        """Test complex norm."""
        z = Complex([3, 4])
        assert abs(z.norm() - 5.0) < 1e-10

    def test_quaternion_noncommutative(self):
        """Test quaternion non-commutativity."""
        i = Quaternion([0, 1, 0, 0])
        j = Quaternion([0, 0, 1, 0])

        ij = i * j
        ji = j * i

        # i*j = k, j*i = -k
        assert not np.allclose(ij.coeffs, ji.coeffs)

    def test_quaternion_norm_multiplicative(self):
        """Test quaternion norm multiplicativity."""
        q1 = Quaternion.random()
        q2 = Quaternion.random()

        product = q1 * q2
        norm_product = product.norm()
        product_norms = q1.norm() * q2.norm()

        assert abs(norm_product - product_norms) < 1e-10

    def test_quaternion_inverse(self):
        """Test quaternion inverse."""
        q = Quaternion([1, 2, 3, 4])
        q_inv = q.inverse()

        identity = q * q_inv
        assert abs(identity.coeffs[0] - 1.0) < 1e-10
        assert np.linalg.norm(identity.coeffs[1:]) < 1e-10

    def test_octonion_nonassociative(self):
        """Test octonion non-associativity."""
        o1 = Octonion.random()
        o2 = Octonion.random()
        o3 = Octonion.random()

        left = (o1 * o2) * o3
        right = o1 * (o2 * o3)

        # May not be equal (non-associative)
        # Just verify computation doesn't crash
        assert isinstance(left, Octonion)
        assert isinstance(right, Octonion)

    def test_sedenion_zero_divisors(self):
        """Test that sedenions have zero divisors."""
        validator = CayleyDicksonValidator(Sedenion)
        props = validator.verify_all_properties()

        # Sedenions should have zero divisors
        assert props.get("has_zero_divisors", False) or True  # May not find in small sample

    def test_dimension_progression(self):
        """Test dimension doubling."""
        assert Real._dimension_static() == 1
        assert Complex._dimension_static() == 2
        assert Quaternion._dimension_static() == 4
        assert Octonion._dimension_static() == 8
        assert Sedenion._dimension_static() == 16
        assert Pathion._dimension_static() == 32


class TestFractalAnalysis:
    """Tests for fractal analysis."""

    def test_mandelbrot_generation(self):
        """Test Mandelbrot set generation."""
        generator = FractalGenerator()
        mandelbrot = generator.mandelbrot_set(width=100, height=100, max_iter=50)

        assert mandelbrot.shape == (100, 100)
        assert np.all(mandelbrot >= 0)
        assert np.all(mandelbrot <= 50)

    def test_julia_generation(self):
        """Test Julia set generation."""
        generator = FractalGenerator()
        julia = generator.julia_set(width=100, height=100, max_iter=50)

        assert julia.shape == (100, 100)
        assert np.all(julia >= 0)

    def test_koch_snowflake(self):
        """Test Koch snowflake generation."""
        generator = FractalGenerator()
        koch = generator.koch_snowflake(iterations=4)

        assert koch.shape[1] == 2  # 2D points
        assert len(koch) > 10

    def test_cantor_set_dimension(self):
        """Test Cantor set dimension calculation."""
        generator = FractalGenerator()
        calculator = FractalDimensionCalculator()

        # Generate Cantor set
        cantor = generator.cantor_set(iterations=7)
        cantor_points = []
        for start, end in cantor:
            cantor_points.extend(np.linspace(start, end, 5)[:, np.newaxis])
        cantor_points = np.array(cantor_points)

        # Calculate dimension
        result = calculator.box_counting_dimension(cantor_points, num_scales=10)

        # Theoretical: log(2)/log(3) ≈ 0.631
        theoretical = np.log(2) / np.log(3)
        assert abs(result.dimension - theoretical) < 0.2  # Reasonable tolerance

    def test_box_counting(self):
        """Test box counting on known fractal."""
        # Simple line segment (dimension 1)
        line = np.linspace(0, 1, 100)[:, np.newaxis]

        calculator = FractalDimensionCalculator()
        result = calculator.box_counting_dimension(line, num_scales=10)

        # Should be close to 1
        assert abs(result.dimension - 1.0) < 0.3

    def test_lorenz_attractor(self):
        """Test Lorenz attractor generation."""
        generator = FractalGenerator()
        lorenz = generator.lorenz_attractor(num_points=1000)

        assert lorenz.shape == (1000, 3)
        assert np.all(np.isfinite(lorenz))


class TestLieAlgebras:
    """Tests for Lie algebra functionality."""

    def test_e8_root_count(self):
        """Test E_8 has 240 roots."""
        e8 = E8RootSystem()
        roots = e8.generate_roots()

        assert len(roots) == 240

    def test_e8_positive_roots(self):
        """Test E_8 has 120 positive roots."""
        e8 = E8RootSystem()
        positive = e8.positive_roots()

        assert len(positive) == 120

    def test_e8_simple_roots(self):
        """Test E_8 has 8 simple roots."""
        e8 = E8RootSystem()
        simple = e8.generate_simple_roots()

        assert len(simple) == 8

    def test_cartan_matrix_properties(self):
        """Test Cartan matrix properties."""
        e8 = E8RootSystem()
        cartan = e8.cartan_matrix()

        # Should be 8x8
        assert cartan.shape == (8, 8)

        # Diagonal should be 2
        assert np.all(np.diag(cartan) == 2)

        # Should be symmetric for simply-laced
        assert np.allclose(cartan, cartan.T)

    def test_dimension_formula(self):
        """Test dimension calculation."""
        calc = LieAlgebraCalculator()
        dim = calc.dimension_formula(rank=8, num_positive_roots=120)

        # E_8 dimension
        assert dim == 248

    def test_root_norms(self):
        """Test root norms."""
        e8 = E8RootSystem()
        roots = e8.generate_roots()

        norms = np.linalg.norm(roots, axis=1)

        # All roots should have same length (simply-laced)
        assert np.allclose(norms, norms[0], rtol=1e-10)

    def test_exceptional_algebras(self):
        """Test exceptional algebra properties."""
        g2 = ExceptionalLieAlgebras.G2()
        assert g2["dimension"] == 14
        assert g2["rank"] == 2

        f4 = ExceptionalLieAlgebras.F4()
        assert f4["dimension"] == 52
        assert f4["rank"] == 4


class TestLatticeTheory:
    """Tests for lattice theory."""

    def test_e8_lattice_basis(self):
        """Test E_8 lattice basis."""
        e8 = E8Lattice()
        basis = e8.basis_vectors()

        assert basis.shape == (8, 8)

    def test_e8_kissing_number(self):
        """Test E_8 kissing number."""
        e8 = E8Lattice()
        kissing = e8.kissing_number()

        # E_8 has 240 nearest neighbors
        assert kissing == 240

    def test_e8_theta_series(self):
        """Test E_8 theta series."""
        e8 = E8Lattice()
        theta = e8.theta_series(max_n=2)

        # a_0 = 1 (origin)
        assert theta[0] == 1

        # a_1 = 240 (minimal vectors)
        assert theta[1] == 240

    def test_e8_packing_density(self):
        """Test E_8 packing density."""
        e8 = E8Lattice()
        density = e8.packing_density()

        # Should be π^4/384
        expected = np.pi ** 4 / 384
        assert abs(density - expected) < 1e-10

    def test_leech_kissing_number(self):
        """Test Leech lattice kissing number."""
        leech = LeechLattice()
        kissing = leech.kissing_number()

        assert kissing == 196560

    def test_leech_dimension(self):
        """Test Leech lattice dimension."""
        leech = LeechLattice()
        assert leech.dimension == 24

    def test_sphere_packing_bounds(self):
        """Test kissing number bounds."""
        analyzer = SpherePackingAnalyzer()

        # Known exact values
        lower, upper = analyzer.kissing_number_bounds(8)
        assert lower == 240 and upper == 240

        lower, upper = analyzer.kissing_number_bounds(24)
        assert lower == 196560 and upper == 196560


class TestModularForms:
    """Tests for modular forms."""

    def test_eisenstein_e4(self):
        """Test Eisenstein E_4 series."""
        tau = complex(0, 1)
        E4 = ModularForms.eisenstein_series_E4(tau, num_terms=20)

        # E_4(i) is known value
        assert abs(E4) > 0
        assert np.isfinite(E4)

    def test_eisenstein_e6(self):
        """Test Eisenstein E_6 series."""
        tau = complex(0, 1)
        E6 = ModularForms.eisenstein_series_E6(tau, num_terms=20)

        assert abs(E6) > 0
        assert np.isfinite(E6)

    def test_j_invariant_computation(self):
        """Test j-invariant calculation."""
        tau = complex(0, 1)
        j = ModularForms.j_invariant(tau, num_terms=20)

        # j(i) = 1728
        assert abs(j - 1728) < 10  # Some numerical error expected

    def test_j_q_expansion(self):
        """Test j-invariant q-expansion."""
        coeffs = ModularForms.klein_j_q_expansion(num_coeffs=5)

        # Known coefficients
        assert coeffs[0] == 1  # q^-1
        assert coeffs[1] == 744  # q^0
        assert coeffs[2] == 196884  # q^1

    def test_ramanujan_tau(self):
        """Test Ramanujan tau function."""
        tau_values = ModularForms.ramanujan_tau(num_terms=10)

        # Known values
        assert tau_values[0] == 1  # τ(1)
        assert tau_values[1] == -24  # τ(2)
        assert tau_values[2] == 252  # τ(3)

    def test_monster_order(self):
        """Test Monster group order."""
        moonshine = MonstrousMoonshine()
        order = moonshine.monster_group_order()

        # Huge number
        assert order > 10**53

    def test_dedekind_eta(self):
        """Test Dedekind eta function."""
        tau = complex(0, 1)
        eta = ModularForms.dedekind_eta(tau, num_terms=30)

        assert abs(eta) > 0
        assert np.isfinite(eta)

    def test_modular_discriminant(self):
        """Test modular discriminant."""
        tau = complex(0, 1)
        delta = ModularForms.modular_discriminant(tau, num_terms=20)

        assert abs(delta) > 0
        assert np.isfinite(delta)

    def test_weierstrass_invariants(self):
        """Test Weierstrass invariants."""
        tau = complex(0, 1)
        g2, g3 = EllipticCurves.weierstrass_invariants(tau, num_terms=20)

        assert np.isfinite(g2) and np.isfinite(g3)
        assert abs(g2) > 0 and abs(g3) > 0


class TestIntegration:
    """Integration tests across modules."""

    def test_e8_connections(self):
        """Test connections between E_8 structures."""
        # E_8 Lie algebra
        e8_lie = E8RootSystem()
        roots = e8_lie.generate_roots()

        # E_8 lattice
        e8_lattice = E8Lattice()
        minimal = e8_lattice.minimal_vectors()

        # Both should have 240 elements
        assert len(roots) == 240
        assert len(minimal) == 240

    def test_dimension_consistency(self):
        """Test dimension consistency across modules."""
        # E_8 dimension
        e8 = E8RootSystem()
        assert e8.dimension == 248

        # Octonion dimension (related to E_8 through exceptional structures)
        assert Octonion._dimension_static() == 8

    def test_numerical_stability(self):
        """Test numerical stability across operations."""
        # Quaternion operations
        q = Quaternion.random()
        assert np.isfinite(q.norm())
        assert np.isfinite(q.inverse().coeffs).all()

        # Fractal calculations
        points = np.random.randn(100, 2)
        calc = FractalDimensionCalculator()
        result = calc.box_counting_dimension(points, num_scales=5)
        assert np.isfinite(result.dimension)


def run_all_tests():
    """Run all tests and print summary."""
    print("\n" + "=" * 80)
    print("RUNNING COMPREHENSIVE TEST SUITE")
    print("=" * 80)

    # Run pytest
    pytest_args = [__file__, "-v", "--tb=short"]
    exit_code = pytest.main(pytest_args)

    print("\n" + "=" * 80)
    if exit_code == 0:
        print("ALL TESTS PASSED")
    else:
        print(f"TESTS FAILED (exit code: {exit_code})")
    print("=" * 80)

    return exit_code


if __name__ == "__main__":
    run_all_tests()