"""Exact structural selectors for barotropic Fourier triads.

The E7 quadratic-defect selector is a new nonhomomorphic construction. It is
not root charge conservation and has no admitted physical interpretation. The
PDE-support and Rossby-resonance selectors provide equation-derived references
against which the E7-targeted construction must be tested.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Any

from .fourier_quotient import Mode, Triad, enumerate_exact_triads


E7_CARTAN_MATRIX = (
    (2, 0, -1, 0, 0, 0, 0),
    (0, 2, 0, -1, 0, 0, 0),
    (-1, 0, 2, -1, 0, 0, 0),
    (0, -1, -1, 2, -1, 0, 0),
    (0, 0, 0, -1, 2, -1, 0),
    (0, 0, 0, 0, -1, 2, -1),
    (0, 0, 0, 0, 0, -1, 2),
)


def exact_determinant(matrix: tuple[tuple[int, ...], ...]) -> Fraction:
    """Return a square integer matrix determinant by exact elimination."""
    size = len(matrix)
    if size == 0 or any(len(row) != size for row in matrix):
        raise ValueError("matrix must be nonempty and square")
    work = [[Fraction(value) for value in row] for row in matrix]
    determinant = Fraction(1)
    for column_index in range(size):
        pivot_index = next(
            (index for index in range(column_index, size) if work[index][column_index]),
            None,
        )
        if pivot_index is None:
            return Fraction(0)
        if pivot_index != column_index:
            work[column_index], work[pivot_index] = work[pivot_index], work[column_index]
            determinant = -determinant
        pivot = work[column_index][column_index]
        determinant *= pivot
        for row_index in range(column_index + 1, size):
            factor = work[row_index][column_index] / pivot
            for entry_index in range(column_index + 1, size):
                work[row_index][entry_index] -= factor * work[column_index][entry_index]
    return determinant


def exact_inverse(matrix: tuple[tuple[int, ...], ...]) -> tuple[tuple[Fraction, ...], ...]:
    """Invert a square integer matrix using exact row reduction."""
    size = len(matrix)
    if size == 0 or any(len(row) != size for row in matrix):
        raise ValueError("matrix must be nonempty and square")
    augmented = [
        [Fraction(value) for value in row]
        + [Fraction(int(row_index == column_index)) for column_index in range(size)]
        for row_index, row in enumerate(matrix)
    ]
    for column_index in range(size):
        pivot_index = next(
            (index for index in range(column_index, size) if augmented[index][column_index]),
            None,
        )
        if pivot_index is None:
            raise ValueError("matrix is singular")
        augmented[column_index], augmented[pivot_index] = (
            augmented[pivot_index],
            augmented[column_index],
        )
        pivot = augmented[column_index][column_index]
        augmented[column_index] = [value / pivot for value in augmented[column_index]]
        for row_index in range(size):
            if row_index == column_index:
                continue
            factor = augmented[row_index][column_index]
            augmented[row_index] = [
                value - factor * augmented[column_index][value_index]
                for value_index, value in enumerate(augmented[row_index])
            ]
    return tuple(tuple(row[size:]) for row in augmented)


def e7_discriminant_form_audit() -> dict[str, Any]:
    """Derive the nonzero E7 discriminant quadratic value exactly."""
    inverse = exact_inverse(E7_CARTAN_MATRIX)
    generator_index = 6
    generator_coordinates = tuple(row[generator_index] for row in inverse)
    generator_norm = inverse[generator_index][generator_index]
    quadratic_value = generator_norm / 2 % 1
    cartan_determinant = exact_determinant(E7_CARTAN_MATRIX)
    doubled_coordinates_integral = all((2 * value).denominator == 1 for value in generator_coordinates)
    return {
        "cartan_determinant": int(cartan_determinant),
        "discriminant_group_order": abs(int(cartan_determinant)),
        "generator_fundamental_weight_index": generator_index + 1,
        "generator_coordinates": [str(value) for value in generator_coordinates],
        "generator_norm_squared": str(generator_norm),
        "half_normalized_quadratic_value_mod_one": str(quadratic_value),
        "generator_is_outside_root_lattice": any(value.denominator != 1 for value in generator_coordinates),
        "doubled_generator_is_in_root_lattice": doubled_coordinates_integral,
        "quadratic_form_is_nonadditive": (2 * quadratic_value) % 1 != 0,
    }


def mode_norm_squared(mode: Mode) -> int:
    """Return the exact squared Euclidean norm of an integer mode."""
    mode_x, mode_y = mode
    return mode_x * mode_x + mode_y * mode_y


def is_nonzero_triad(triad: Triad) -> bool:
    """Return whether every member of a triad is nonzero."""
    return all(mode != (0, 0) for mode in triad)


def barotropic_channel_is_active(triad: Triad) -> bool:
    """Return whether the symmetrized barotropic interaction is nonzero.

    For receiver k and sources p and q, the coefficient is proportional to
    cross(p, q) times (1/|q|^2 - 1/|p|^2). Only exact zero support is tested;
    no floating-point threshold enters this structural audit.
    """
    _, first_source, second_source = triad
    determinant = first_source[0] * second_source[1] - first_source[1] * second_source[0]
    return determinant != 0 and mode_norm_squared(first_source) != mode_norm_squared(second_source)


def rossby_frequency(mode: Mode, beta: int = 1) -> Fraction:
    """Return the exact Rossby frequency -beta*k_x/|k|^2."""
    norm_squared = mode_norm_squared(mode)
    if norm_squared == 0:
        raise ValueError("Rossby frequency is undefined for the zero mode")
    return Fraction(-beta * mode[0], norm_squared)


def rossby_exact_resonance(triad: Triad, beta: int = 1) -> bool:
    """Return whether a nonzero exact triad also closes in frequency."""
    if not is_nonzero_triad(triad):
        return False
    return sum((rossby_frequency(mode, beta) for mode in triad), start=Fraction()) == 0


def e7_discriminant_label(mode: Mode) -> int:
    """Map a Fourier mode to the external nonzero E7 P/Q parity label."""
    return (mode[0] + mode[1]) % 2


def e7_quadratic_defect_mod_four(triad: Triad) -> int:
    """Return four times the E7 discriminant quadratic defect modulo four.

    The nonzero class of the E7 discriminant group has quadratic value 3/4
    modulo one in the half-normalized convention. Exact closure forces zero or
    two odd external labels, so a nonzero defect rejects the two-odd class.
    """
    return 3 * sum(e7_discriminant_label(mode) for mode in triad) % 4


def e7_quadratic_defect_admits(triad: Triad) -> bool:
    """Admit an exact triad only when its E7 quadratic defect vanishes."""
    return e7_quadratic_defect_mod_four(triad) == 0


def checkerboard_kernel_admits(triad: Triad) -> bool:
    """Admit only triads wholly inside the even checkerboard sublattice."""
    return all(e7_discriminant_label(mode) == 0 for mode in triad)


def transform_triad(triad: Triad, transform: str) -> Triad:
    """Apply a named square-lattice symmetry to a triad."""
    operations = {
        "identity": lambda mode_x, mode_y: (mode_x, mode_y),
        "invert": lambda mode_x, mode_y: (-mode_x, -mode_y),
        "reflect_x": lambda mode_x, mode_y: (-mode_x, mode_y),
        "reflect_y": lambda mode_x, mode_y: (mode_x, -mode_y),
        "swap": lambda mode_x, mode_y: (mode_y, mode_x),
        "rotate_90": lambda mode_x, mode_y: (-mode_y, mode_x),
        "rotate_180": lambda mode_x, mode_y: (-mode_x, -mode_y),
        "rotate_270": lambda mode_x, mode_y: (mode_y, -mode_x),
        "reflect_diagonal": lambda mode_x, mode_y: (mode_y, mode_x),
        "reflect_antidiagonal": lambda mode_x, mode_y: (-mode_y, -mode_x),
    }
    try:
        operation = operations[transform]
    except KeyError as error:
        raise ValueError(f"unknown triad transform {transform!r}") from error
    return tuple(operation(*mode) for mode in triad)  # type: ignore[return-value]


def build_triad_selector_audit(radius: int = 4) -> dict[str, Any]:
    """Build exact counts and invariance checks for selector candidates."""
    triads = tuple(triad for triad in enumerate_exact_triads(radius) if is_nonzero_triad(triad))
    active_triads = tuple(triad for triad in triads if barotropic_channel_is_active(triad))
    resonant_triads = tuple(triad for triad in triads if rossby_exact_resonance(triad))
    active_resonant = tuple(triad for triad in active_triads if rossby_exact_resonance(triad))
    e7_admitted = tuple(triad for triad in triads if e7_quadratic_defect_admits(triad))
    e7_active_admitted = tuple(
        triad for triad in active_triads if e7_quadratic_defect_admits(triad)
    )
    transforms = (
        "identity",
        "rotate_90",
        "rotate_180",
        "rotate_270",
        "reflect_x",
        "reflect_y",
        "reflect_diagonal",
        "reflect_antidiagonal",
    )
    e7_symmetry_pass = all(
        e7_quadratic_defect_admits(transform_triad(triad, transform))
        == e7_quadratic_defect_admits(triad)
        for triad in triads
        for transform in transforms
    )
    permutation_pass = all(
        e7_quadratic_defect_admits((triad[1], triad[0], triad[2]))
        == e7_quadratic_defect_admits(triad)
        and e7_quadratic_defect_admits((triad[1], triad[2], triad[0]))
        == e7_quadratic_defect_admits(triad)
        for triad in triads
    )
    checkerboard_equivalence_pass = all(
        e7_quadratic_defect_admits(triad) == checkerboard_kernel_admits(triad)
        for triad in triads
    )
    return {
        "schema_version": 1,
        "generator": "scripts/audit_triad_selectors.py",
        "square_shell_radius": radius,
        "ordered_exact_triad_count_including_zero_modes": len(enumerate_exact_triads(radius)),
        "ordered_nonzero_exact_triad_count": len(triads),
        "barotropic_active_channel_count": len(active_triads),
        "barotropic_zero_support_channel_count": len(triads) - len(active_triads),
        "rossby_exact_resonant_triad_count": len(resonant_triads),
        "rossby_active_exact_resonant_channel_count": len(active_resonant),
        "e7_quadratic_defect_admitted_triad_count": len(e7_admitted),
        "e7_quadratic_defect_rejected_triad_count": len(triads) - len(e7_admitted),
        "e7_quadratic_defect_active_admitted_count": len(e7_active_admitted),
        "e7_quadratic_defect_active_rejected_count": len(active_triads) - len(e7_active_admitted),
        "e7_square_symmetry_pass": e7_symmetry_pass,
        "e7_permutation_closure_pass": permutation_pass,
        "e7_selector_nontrivial": 0 < len(e7_admitted) < len(triads),
        "e7_discriminant_form": e7_discriminant_form_audit(),
        "checkerboard_kernel_exact_equivalence_pass": checkerboard_equivalence_pass,
        "e7_specificity_falsified": checkerboard_equivalence_pass,
        "scientific_outcome": "e7_specificity_falsified_generic_parity_kernel_retained",
        "interpretation_boundary": (
            "The quadratic-defect mask is exactly the generic even-checkerboard kernel. "
            "The arithmetic is valid, but it supplies no E7-specific selector. Generic "
            "parity-kernel dynamics remains a separate conjecture with conservation and "
            "independent-reproduction gates still pending."
        ),
    }
