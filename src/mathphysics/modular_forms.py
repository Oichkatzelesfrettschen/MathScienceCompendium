"""Modular Forms and Affine Characters.

Provides Dedekind Eta, Jacobi Theta, and Eisenstein series for computing
characters of affine Lie algebra representations. Optimized via JAX when available.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

try:
    import jax.numpy as jnp
    from jax import jit

    HAS_JAX = True
except ImportError:
    jnp = np  # Fallback to numpy
    HAS_JAX = False

    def jit(func):  # noqa: ARG001
        """Dummy jit decorator when JAX is not available."""
        return lambda f: f


if TYPE_CHECKING:
    from pathlib import Path


class ModularForms:
    """Engine for modular forms and series computation."""

    @staticmethod
    def tau_to_q(tau: complex) -> complex:
        """Convert half-period ratio tau to nome q = exp(2*pi*i*tau)."""
        return np.exp(2j * np.pi * tau)

    @staticmethod
    def eisenstein_series_E4(tau: complex, num_terms: int = 100) -> complex:
        """Eisenstein series E4(tau) = 1 + 240 * sum sigma_3(n) * q^n."""
        q = ModularForms.tau_to_q(tau)
        return ModularForms.eisenstein_e4(q, num_terms)

    @staticmethod
    def eisenstein_e4(q: complex, num_terms: int = 100) -> complex:
        """Eisenstein series E4(q) = 1 + 240 * sum sigma_3(n) * q^n."""
        res = 1.0
        for n in range(1, num_terms + 1):
            sigma3 = sum(d**3 for d in range(1, n + 1) if n % d == 0)
            res += 240 * sigma3 * (q**n)
        return res

    @staticmethod
    def eisenstein_series_E6(tau: complex, num_terms: int = 100) -> complex:
        """Eisenstein series E6(tau) = 1 - 504 * sum sigma_5(n) * q^n."""
        q = ModularForms.tau_to_q(tau)
        return ModularForms.eisenstein_e6(q, num_terms)

    @staticmethod
    def eisenstein_e6(q: complex, num_terms: int = 100) -> complex:
        """Eisenstein series E6(q) = 1 - 504 * sum sigma_5(n) * q^n."""
        res = 1.0
        for n in range(1, num_terms + 1):
            sigma5 = sum(d**5 for d in range(1, n + 1) if n % d == 0)
            res -= 504 * sigma5 * (q**n)
        return res

    @staticmethod
    def j_invariant(tau: complex, num_terms: int = 100) -> complex:
        """Compute the j-invariant using E4 and E6."""
        e4 = ModularForms.eisenstein_series_E4(tau, num_terms)
        e6 = ModularForms.eisenstein_series_E6(tau, num_terms)
        delta = (e4**3 - e6**2) / 1728.0
        return (e4**3) / (delta if abs(delta) > 1e-10 else 1e-10)

    @staticmethod
    def klein_j_q_expansion(num_coeffs: int = 10) -> np.ndarray:
        """The j-function q-expansion coefficients."""
        coeffs = [1, 744, 196884, 21493760, 864299970, 20245856256]
        return np.array(coeffs[:num_coeffs])

    @staticmethod
    def ramanujan_tau(num_terms: int = 10) -> np.ndarray:
        """Ramanujan tau function values τ(n)."""
        vals = [1, -24, 252, -1472, 4830, -6048, -16744, 84480, -113643, -115920]
        return np.array(vals[:num_terms])

    @staticmethod
    def dedekind_eta(tau_or_q: complex, num_terms: int = 100) -> complex:
        """Dedekind Eta function. Detects if input is tau or q (nome)."""
        if abs(tau_or_q) >= 1.0 or tau_or_q.imag > 0:
            q = ModularForms.tau_to_q(tau_or_q)
        else:
            q = tau_or_q
        k = np.arange(-num_terms, num_terms + 1)
        res = np.sum(((-1.0) ** k) * (q ** (k * (3 * k - 1) / 2.0)))
        return (q ** (1.0 / 24.0)) * res

    @staticmethod
    def modular_discriminant(tau: complex, num_terms: int = 100) -> complex:
        """Modular discriminant Delta = (E4^3 - E6^2) / 1728."""
        e4 = ModularForms.eisenstein_series_E4(tau, num_terms)
        e6 = ModularForms.eisenstein_series_E6(tau, num_terms)
        return (e4**3 - e6**2) / 1728.0

    @staticmethod
    @jit
    def jacobi_theta(z: complex, q: complex, n_terms: int = 50) -> complex:
        """Jacobi Theta function theta_3(z, q)."""
        n = jnp.arange(-n_terms, n_terms + 1)
        return jnp.sum((q ** (n**2)) * jnp.exp(2j * n * z))


class AffineCharacterAnalyzer:
    """Character formulas for affine Lie algebras."""

    def __init__(self, algebra_name: str, rank: int) -> None:
        self.algebra_name = algebra_name
        self.rank = rank

    def vacuum_character(self, q: complex) -> complex:
        """Character ch(V_k) = 1 / eta(q)^rank."""
        eta_val = ModularForms.dedekind_eta(q)
        return 1.0 / (eta_val**self.rank)


class MonstrousMoonshine:
    """Links the Monster group to modular forms."""

    @staticmethod
    def monster_order() -> int:
        return 808017424794512875886459904961710757005754368000000000

    @staticmethod
    def monster_group_order() -> int:
        """Alias for monster_order required by tests."""
        return MonstrousMoonshine.monster_order()

    @staticmethod
    def q_expansion_j(tau: complex, n_terms: int = 10) -> complex:
        """The j-function q-expansion."""
        return ModularForms.j_invariant(tau, n_terms)


class EllipticCurves:
    """Analytic properties of elliptic curves."""

    @staticmethod
    def weierstrass_invariants(tau: complex, num_terms: int = 100) -> tuple[complex, complex]:
        """Compute g2 and g3 invariants from tau."""
        e4 = ModularForms.eisenstein_series_E4(tau, num_terms)
        e6 = ModularForms.eisenstein_series_E6(tau, num_terms)
        g2 = 60 * e4
        g3 = 140 * e6
        return g2, g3

    @staticmethod
    def compute_invariants(g2: float, g3: float) -> dict[str, float]:
        delta = g2**3 - 27 * g3**2
        j = 1728 * (g2**3) / (delta if abs(delta) > 1e-10 else 1e-10)
        return {"discriminant": delta, "j_invariant": j}


def analyze_modular_forms(output_dir: Path | None = None):
    """Production analysis of modular forms and j-invariant."""
    q = 0.1 + 0.1j
    results = {
        "e4": str(ModularForms.eisenstein_e4(q)),
        "j_inv": str(ModularForms.klein_j_q_expansion(1)[0]),
        "eta": str(ModularForms.dedekind_eta(q)),
    }
    if output_dir:
        import json

        with open(output_dir / "modular_analysis.json", "w") as f:
            json.dump(results, f, indent=2)
    return results
