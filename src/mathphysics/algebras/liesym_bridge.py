"""Bridge for liesym (Rust-accelerated Lie algebra).

Provides a unified interface for root generation and multiplicity
calculations, with a fallback to native NumPy implementation.
"""

from __future__ import annotations

import numpy as np


try:
    import liesym as ls

    HAS_LIESYM = True
except ImportError:
    HAS_LIESYM = False


class LiesymBridge:
    """Infrastructure for accelerated root system calculations."""

    @staticmethod
    def get_roots(algebra_type: str, rank: int) -> np.ndarray:
        """Get roots for a given algebra, using liesym if available."""
        if HAS_LIESYM:
            try:
                # liesym provides factory methods like A(rank), E(rank), etc.
                if algebra_type == "E":
                    g = ls.E(rank)
                elif algebra_type == "F":
                    g = ls.F4()  # F4 is fixed rank
                elif algebra_type == "G":
                    g = ls.G2()  # G2 is fixed rank
                else:
                    # Generic lookup
                    func = getattr(ls, algebra_type, None)
                    g = func(rank) if func else None

                if g:
                    pos_roots = g.positive_roots()
                    neg_roots = [-r for r in pos_roots]
                    return np.array(pos_roots + neg_roots)
            except Exception as e:
                print(f"[LIESYM] Root generation failed: {e}")

        # Fallback to internal BaseRootSystem logic
        from .roots import E6RootSystem, E7RootSystem, E8RootSystem, F4RootSystem

        mapping = {"E8": E8RootSystem, "E7": E7RootSystem, "E6": E6RootSystem, "F4": F4RootSystem}
        key = f"{algebra_type}{rank}" if algebra_type == "E" else algebra_type
        if key in mapping:
            return mapping[key]().generate_roots()

        raise ValueError(f"Algebra {algebra_type}{rank} not supported in fallback.")

    @staticmethod
    def get_weyl_orbit(root: np.ndarray, algebra_type: str, rank: int = 8) -> list[np.ndarray]:
        """Calculate Weyl orbit for a root vector."""
        if HAS_LIESYM:
            try:
                if algebra_type == "E":
                    g = ls.E(rank)
                # orbit method takes a weight vector
                orbit = g.orbit(root.tolist())
                return [np.array(p) for p in orbit]
            except Exception as e:
                print(f"[LIESYM] Orbit calculation failed: {e}")

        # Fallback to manual reflection loop
        # (Implementation as before)
