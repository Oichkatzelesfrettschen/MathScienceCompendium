"""Bridge for liesym (Rust-accelerated Lie algebra).

Provides a unified interface for root generation and multiplicity
calculations, with a fallback to native NumPy implementation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np


if TYPE_CHECKING:
    from collections.abc import Callable


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
        from .roots import (  # noqa: PLC0415
            BaseRootSystem,
            E6RootSystem,
            E7RootSystem,
            E8RootSystem,
            F4RootSystem,
        )

        mapping: dict[str, Callable[[], BaseRootSystem]] = {
            "E8": E8RootSystem,
            "E7": E7RootSystem,
            "E6": E6RootSystem,
            "F4": F4RootSystem,
        }
        key = f"{algebra_type}{rank}"
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
                elif algebra_type == "F" and rank == 4:
                    g = ls.F4()
                elif algebra_type == "G" and rank == 2:
                    g = ls.G2()
                else:
                    raise ValueError(f"Liesym orbit is unsupported for {algebra_type}{rank}")
                # orbit method takes a weight vector
                orbit = g.orbit(root.tolist())
                return [np.array(p) for p in orbit]
            except Exception as e:
                print(f"[LIESYM] Orbit calculation failed: {e}")

        roots = LiesymBridge.get_roots(algebra_type, rank)
        if not any(np.allclose(root, candidate) for candidate in roots):
            raise ValueError("The supplied vector is not a root of the requested algebra")
        target_norm = float(np.dot(root, root))
        orbit = [
            candidate
            for candidate in roots
            if np.isclose(float(np.dot(candidate, candidate)), target_norm)
        ]
        if not orbit:
            raise ValueError(f"No Weyl orbit found for {algebra_type}{rank} root")
        return orbit
