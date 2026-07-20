"""Fourier-lattice homomorphisms into the E7 quotient P/Q.

The E7 Cartan determinant is two, so its weight-lattice quotient P/Q is
isomorphic to Z/2. This module enumerates homomorphisms from the square Fourier
lattice Z^2 into that quotient and tests whether charge conservation can reject
exact convolution triads.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from .algebras.roots import E7RootSystem


Mode = tuple[int, int]
Triad = tuple[Mode, Mode, Mode]


@dataclass(frozen=True)
class Z2FourierHomomorphism:
    """A homomorphism h(kx, ky) = ax*kx + ay*ky modulo two."""

    coefficient_x: int
    coefficient_y: int

    def __post_init__(self) -> None:
        if self.coefficient_x not in {0, 1} or self.coefficient_y not in {0, 1}:
            raise ValueError("Z/2 coefficients must be zero or one")

    def charge(self, mode: Mode) -> int:
        """Return the mode's charge in Z/2."""
        mode_x, mode_y = mode
        return (self.coefficient_x * mode_x + self.coefficient_y * mode_y) % 2

    @property
    def is_nontrivial(self) -> bool:
        return bool(self.coefficient_x or self.coefficient_y)

    @property
    def is_square_symmetry_invariant(self) -> bool:
        """Return whether the map is invariant under the square D4 action.

        Sign changes are invisible modulo two. Coordinate exchange requires
        equal coefficients, which is also sufficient for the full D4 action.
        """
        return self.coefficient_x == self.coefficient_y

    def admits_exact_triad(self, triad: Triad) -> bool:
        return sum(self.charge(mode) for mode in triad) % 2 == 0


def all_z2_fourier_homomorphisms() -> tuple[Z2FourierHomomorphism, ...]:
    """Enumerate every homomorphism from Z^2 to Z/2."""
    return tuple(
        Z2FourierHomomorphism(coefficient_x, coefficient_y)
        for coefficient_x in (0, 1)
        for coefficient_y in (0, 1)
    )


def square_symmetry_orbit(mode: Mode) -> frozenset[Mode]:
    """Return the orbit of a Fourier mode under rotations and reflections."""
    mode_x, mode_y = mode
    return frozenset(
        {
            (mode_x, mode_y),
            (-mode_x, mode_y),
            (mode_x, -mode_y),
            (-mode_x, -mode_y),
            (mode_y, mode_x),
            (-mode_y, mode_x),
            (mode_y, -mode_x),
            (-mode_y, -mode_x),
        }
    )


def square_modes(radius: int) -> tuple[Mode, ...]:
    """Enumerate the integer modes in a closed square Fourier shell."""
    if radius < 1:
        raise ValueError("radius must be positive")
    return tuple(
        (mode_x, mode_y)
        for mode_x in range(-radius, radius + 1)
        for mode_y in range(-radius, radius + 1)
    )


def enumerate_exact_triads(radius: int) -> tuple[Triad, ...]:
    """Enumerate ordered triads k + p + q = 0 contained in a square shell."""
    modes = square_modes(radius)
    mode_set = set(modes)
    triads: list[Triad] = []
    for first_mode in modes:
        for second_mode in modes:
            third_mode = (
                -first_mode[0] - second_mode[0],
                -first_mode[1] - second_mode[1],
            )
            if third_mode in mode_set:
                triads.append((first_mode, second_mode, third_mode))
    return tuple(triads)


def e7_weight_root_quotient_order() -> int:
    """Return |P/Q| from the determinant of the E7 Cartan matrix."""
    cartan = E7RootSystem().compute_cartan_matrix()
    determinant = round(float(np.linalg.det(cartan)))
    if determinant != 2:
        raise ValueError(f"E7 Cartan determinant must be 2, received {determinant}")
    return determinant


def build_fourier_quotient_audit(radius: int = 4) -> dict[str, Any]:
    """Build a deterministic falsification audit for the proposed triad filter."""
    quotient_order = e7_weight_root_quotient_order()
    triads = enumerate_exact_triads(radius)
    homomorphism_records: list[dict[str, Any]] = []
    for homomorphism in all_z2_fourier_homomorphisms():
        rejected_count = sum(
            not homomorphism.admits_exact_triad(triad) for triad in triads
        )
        homomorphism_records.append(
            {
                "coefficients": [
                    homomorphism.coefficient_x,
                    homomorphism.coefficient_y,
                ],
                "nontrivial": homomorphism.is_nontrivial,
                "square_symmetry_invariant": (
                    homomorphism.is_square_symmetry_invariant
                ),
                "rejected_exact_triad_count": rejected_count,
            }
        )

    symmetry_compatible_nontrivial = [
        record
        for record in homomorphism_records
        if record["nontrivial"] and record["square_symmetry_invariant"]
    ]
    maximum_rejected_count = max(
        int(record["rejected_exact_triad_count"])
        for record in symmetry_compatible_nontrivial
    )
    return {
        "schema_version": 1,
        "generator": "scripts/audit_fourier_quotient_map.py",
        "fourier_lattice": "Z^2 square lattice",
        "target_quotient": "E7 weight lattice/root lattice P/Q isomorphic to Z/2",
        "target_quotient_order": quotient_order,
        "square_shell_radius": radius,
        "mode_count": len(square_modes(radius)),
        "ordered_exact_triad_count": len(triads),
        "homomorphisms": homomorphism_records,
        "nontrivial_square_symmetry_map_exists": bool(symmetry_compatible_nontrivial),
        "maximum_rejected_exact_triad_count": maximum_rejected_count,
        "map_existence_outcome": "established",
        "triad_filter_outcome": "falsified",
        "proof": (
            "The nontrivial D4-invariant map h(kx,ky)=(kx+ky) mod 2 exists. "
            "For every exact triad k+p+q=0, homomorphism additivity gives "
            "h(k)+h(p)+h(q)=h(0)=0, so no exact triad is rejected."
        ),
        "rejection_criterion": (
            "Reject a nontrivial homomorphic triad-filter mechanism when every "
            "symmetry-compatible nontrivial map rejects zero exact triads."
        ),
    }
