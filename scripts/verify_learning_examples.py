#!/usr/bin/env python3
"""Check bounded printed learning examples with exact standard-library arithmetic.

The output records finite checks, manuscript hashes, and explicit claim limits.
Source parsing extracts named mathematical parameters, rather than judging prose.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import re
from fractions import Fraction
from pathlib import Path


CHAPTER_NAMES = (
    "proof",
    "linear_algebra",
    "calculus",
    "multivariable",
    "dynamics",
    "probability",
    "numerical",
    "algebra",
    "geometry",
    "advanced",
)
DEFAULT_CHAPTERS = Path(__file__).resolve().parents[1] / "papers/learning/chapters"


def require_equal(checks: list[dict], name: str, actual: object, expected: object) -> None:
    """Record a successful comparison or fail even under python -O."""
    if actual != expected:
        raise AssertionError(f"{name}: expected {expected!r}, observed {actual!r}")
    checks.append({"name": name, "status": "passed"})


def capture(source: str, pattern: str, name: str) -> tuple[str, ...]:
    """Extract one unambiguous named mathematical expression."""
    matches = list(re.finditer(pattern, source, flags=re.DOTALL))
    if len(matches) != 1:
        raise AssertionError(f"{name}: expected one source match, observed {len(matches)}")
    return matches[0].groups()


def determinant(matrix: list[list[Fraction]]) -> Fraction:
    """Evaluate a square determinant by exact elimination with row pivoting."""
    rows = [row[:] for row in matrix]
    result = Fraction(1)
    for column in range(len(rows)):
        pivot = next((index for index in range(column, len(rows)) if rows[index][column]), None)
        if pivot is None:
            return Fraction(0)
        if pivot != column:
            rows[column], rows[pivot] = rows[pivot], rows[column]
            result *= -1
        pivot_value = rows[column][column]
        result *= pivot_value
        for index in range(column + 1, len(rows)):
            factor = rows[index][column] / pivot_value
            for offset in range(column + 1, len(rows)):
                rows[index][offset] -= factor * rows[column][offset]
            rows[index][column] = Fraction(0)
    return result


def check_e8(source: str, checks: list[dict]) -> None:
    """Enumerate the printed eight-dimensional corpus and exact Cartan matrix."""
    dimension, positions, signs, count = map(
        int,
        capture(source, r"\\binom(\d+)(\d+)\\cdot(\d+)=(\d+)", "E8 first-family count"),
    )
    require_equal(
        checks, "e8_printed_dimension_positions_signs", (dimension, positions, signs), (8, 2, 4)
    )
    roots = set()
    for selected in itertools.combinations(range(dimension), positions):
        for values in itertools.product((-1, 1), repeat=positions):
            vector = [Fraction(0)] * dimension
            for index, value in zip(selected, values):
                vector[index] = Fraction(value)
            roots.add(tuple(vector))
    require_equal(checks, "e8_integer_family_count", len(roots), count)
    for values in itertools.product((-1, 1), repeat=dimension):
        if values.count(-1) % 2 == 0:
            roots.add(tuple(Fraction(value, 2) for value in values))
    require_equal(checks, "e8_total_count", len(roots), 240)
    require_equal(
        checks,
        "e8_exact_squared_norms",
        {sum(value * value for value in root) for root in roots},
        {Fraction(2)},
    )
    require_equal(
        checks, "e8_opposite_closure", {tuple(-value for value in root) for root in roots}, roots
    )
    cartan = [[Fraction(2 if row == column else 0) for column in range(8)] for row in range(8)]
    for left, right in ((0, 1), (0, 2), (2, 3), (0, 4), (4, 5), (5, 6), (6, 7)):
        cartan[left][right] = cartan[right][left] = Fraction(-1)
    printed_determinant = int(capture(source, r"\\frac45\\right\)=(\d+)", "E8 determinant")[0])
    require_equal(
        checks, "e8_cartan_determinant", determinant(cartan), Fraction(printed_determinant)
    )
    require_equal(checks, "e8_determinant_target", printed_determinant, 1)


def conjugate(vector: list[int]) -> list[int]:
    return [vector[0], *(-value for value in vector[1:])]


def cayley_product(left: list[int], right: list[int]) -> list[int]:
    """Use (a,b)(c,d)=(ac-conj(d)b, da+b conj(c)) with recursive basis order."""
    if len(left) != len(right) or not left or len(left) & (len(left) - 1):
        raise ValueError("Cayley-Dickson vectors require equal power-of-two dimensions")
    if len(left) == 1:
        return [left[0] * right[0]]
    midpoint = len(left) // 2
    first_left, second_left = left[:midpoint], left[midpoint:]
    first_right, second_right = right[:midpoint], right[midpoint:]
    first = [
        value - correction
        for value, correction in zip(
            cayley_product(first_left, first_right),
            cayley_product(conjugate(second_right), second_left),
        )
    ]
    second = [
        value + correction
        for value, correction in zip(
            cayley_product(second_right, first_left),
            cayley_product(second_left, conjugate(first_right)),
        )
    ]
    return first + second


def check_cayley(source: str, checks: list[dict]) -> None:
    left_first, left_second = map(
        int, capture(source, r"a=e_(\d+)\+e_\{(\d+)\}", "sedenion left witness")
    )
    right_first, right_second = map(
        int, capture(source, r"(?<![A-Za-z])b=e_(\d+)-e_\{(\d+)\}", "sedenion right witness")
    )
    require_equal(
        checks,
        "sedenion_printed_indices",
        (left_first, left_second, right_first, right_second),
        (3, 10, 6, 15),
    )
    left = [0] * 16
    right = [0] * 16
    left[left_first] = left[left_second] = 1
    right[right_first], right[right_second] = 1, -1
    require_equal(
        checks,
        "sedenion_nonzero_factor_norms_squared",
        (sum(value * value for value in left), sum(value * value for value in right)),
        (2, 2),
    )
    require_equal(checks, "sedenion_exact_zero_product", cayley_product(left, right), [0] * 16)
    for first, second, expected_index in ((3, 6, 5), (3, 15, 12), (10, 6, 12), (10, 15, 5)):
        basis_left, basis_right, expected = [0] * 16, [0] * 16, [0] * 16
        basis_left[first] = basis_right[second] = expected[expected_index] = 1
        require_equal(
            checks,
            f"sedenion_basis_product_{first}_{second}",
            cayley_product(basis_left, basis_right),
            expected,
        )


def check_d2q9(source: str, checks: list[dict]) -> None:
    compact = re.sub(r"\s+", "", source)
    linear, quadratic_numerator, quadratic_denominator, norm_numerator, norm_denominator = map(
        int,
        capture(
            compact,
            r"1\+(\d+)c_i\\cdotu\+\\frac(\d)(\d)\(c_i\\cdotu\)\^2-\\frac(\d)(\d)\|u\|\^2",
            "D2Q9 equilibrium coefficients",
        ),
    )
    quadratic = Fraction(quadratic_numerator, quadratic_denominator)
    norm = Fraction(norm_numerator, norm_denominator)
    require_equal(
        checks,
        "d2q9_printed_equilibrium_coefficients",
        (linear, quadratic, norm),
        (3, Fraction(9, 2), Fraction(3, 2)),
    )
    velocities = [(0, 0), (1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]
    weights = [Fraction(4, 9), *([Fraction(1, 9)] * 4), *([Fraction(1, 36)] * 4)]
    density, momentum_x, momentum_y = ([Fraction(0)] * 6 for _ in range(3))
    for (velocity_x, velocity_y), weight in zip(velocities, weights):
        coefficients = [
            Fraction(1),
            linear * velocity_x,
            linear * velocity_y,
            quadratic * velocity_x**2 - norm,
            2 * quadratic * velocity_x * velocity_y,
            quadratic * velocity_y**2 - norm,
        ]
        for index, coefficient in enumerate(coefficients):
            density[index] += weight * coefficient
            momentum_x[index] += weight * velocity_x * coefficient
            momentum_y[index] += weight * velocity_y * coefficient
    require_equal(checks, "d2q9_density_polynomial_coefficients", density, [1, 0, 0, 0, 0, 0])
    require_equal(checks, "d2q9_x_momentum_polynomial_coefficients", momentum_x, [0, 1, 0, 0, 0, 0])
    require_equal(checks, "d2q9_y_momentum_polynomial_coefficients", momentum_y, [0, 0, 1, 0, 0, 0])


def check_probability(source: str, checks: list[dict]) -> None:
    prevalence = Fraction(capture(source, r"P\(D\)=(0\.\d+)", "diagnostic prevalence")[0])
    sensitivity = Fraction(capture(source, r"P\(\+\\mid D\)=(0\.\d+)", "diagnostic sensitivity")[0])
    false_positive = Fraction(
        capture(source, r"P\(\+\\mid D\^c\)=(0\.\d+)", "diagnostic false-positive probability")[0]
    )
    positive = sensitivity * prevalence + false_positive * (1 - prevalence)
    require_equal(
        checks, "diagnostic_exact_posterior", sensitivity * prevalence / positive, Fraction(1, 6)
    )
    require_equal(checks, "diagnostic_positive_probability", positive, Fraction(594, 10000))


def check_approximation(sources: dict[str, str], checks: list[dict]) -> None:
    denominator = int(
        capture(
            sources["numerical"], r"=\\frac13\+\\frac1\{(\d+)n\^2\}", "trapezoid error denominator"
        )[0]
    )
    for pieces in (1, 2, 4, 10, 40, 41):
        estimate = (
            Fraction(1, 2) + sum(Fraction(index, pieces) ** 2 for index in range(1, pieces))
        ) / pieces
        require_equal(
            checks,
            f"quadratic_trapezoid_{pieces}_pieces",
            estimate - Fraction(1, 3),
            Fraction(1, denominator * pieces**2),
        )
    require_equal(
        checks,
        "quadratic_trapezoid_minimum_resolution",
        min(pieces for pieces in range(1, 100) if Fraction(1, 6 * pieces**2) <= Fraction(1, 10000)),
        41,
    )
    dynamics = re.sub(r"\s+", "", sources["dynamics"])
    amplitude = int(
        capture(dynamics, r"G\(\\theta\)=1-(\d+)r\\sin\^2", "heat amplification coefficient")[0]
    )
    require_equal(checks, "heat_amplification_coefficient", amplitude, 4)
    for ratio in (Fraction(0), Fraction(1, 4), Fraction(1, 2)):
        factors = [1 - amplitude * ratio * Fraction(index, 16) for index in range(17)]
        require_equal(
            checks,
            f"heat_stable_sample_r_{ratio}",
            all(abs(factor) <= 1 for factor in factors),
            True,
        )
    require_equal(
        checks, "heat_unstable_nyquist_r_3_over_5", abs(1 - amplitude * Fraction(3, 5)) > 1, True
    )
    require_equal(checks, "euler_decay_dt_2_over_5", 1 - 2 * Fraction(2, 5), Fraction(1, 5))
    require_equal(checks, "euler_growth_dt_11_over_10", 1 - 2 * Fraction(11, 10), Fraction(-6, 5))
    for degree in (0, 1, 9, 10, 20):
        partial = sum(Fraction(1, 2) ** index for index in range(degree + 1))
        require_equal(
            checks, f"geometric_remainder_degree_{degree}", 2 - partial, Fraction(1, 2) ** degree
        )
    require_equal(
        checks, "geometric_degree10_tolerance", Fraction(1, 2) ** 10 < Fraction(1, 1000), True
    )
    require_equal(
        checks,
        "sine_cubic_finite_error_bound",
        abs(math.sin(0.1) - (0.1 - 0.1**3 / 6)) <= 0.1**4 / 24,
        True,
    )
    smooth_coefficients = re.findall(r"e\^\{-(\d+)/x\^2\}", sources["calculus"])
    require_equal(
        checks, "smooth_example_printed_exponent_coefficients", set(smooth_coefficients), {"1"}
    )
    for power in range(5):
        values = [
            math.exp(-(float(argument) ** -2)) / float(argument) ** power
            for argument in (Fraction(1, 2), Fraction(1, 4), Fraction(1, 8))
        ]
        require_equal(
            checks,
            f"smooth_example_positive_decay_samples_power_{power}",
            values[0] > values[1] > values[2] > 0,
            True,
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chapters-dir", type=Path, default=DEFAULT_CHAPTERS)
    parser.add_argument("--output", type=Path, help="Optional JSON report path")
    arguments = parser.parse_args()
    sources = {
        name: (arguments.chapters_dir / f"{name}.tex").read_text(encoding="utf-8")
        for name in CHAPTER_NAMES
    }
    checks: list[dict] = []
    check_e8(sources["algebra"], checks)
    check_cayley(sources["advanced"], checks)
    check_d2q9(sources["advanced"], checks)
    check_probability(sources["probability"], checks)
    check_approximation(sources, checks)
    report = {
        "schema_version": 1,
        "status": "passed",
        "finite_check_count": len(checks),
        "checks": checks,
        "chapter_sha256": {
            name: hashlib.sha256(source.encode("utf-8")).hexdigest()
            for name, source in sources.items()
        },
        "scope": "Exact finite algebraic examples and explicitly sampled floating-point inequalities.",
        "limits": [
            "Finite checks do not prove universal analytic, classification, or physical claims.",
            "Source coupling covers named parsed equations and parameters; chapter hashes identify remaining text.",
            "Smooth-function samples illustrate positive decay; the manuscript supplies the limiting argument.",
            "Heat samples check specified amplification factors, not every scheme or boundary condition.",
            "Historical sources and page layout require separate review.",
        ],
    }
    if arguments.output is not None:
        arguments.output.parent.mkdir(parents=True, exist_ok=True)
        arguments.output.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    print(
        f"PASS: {len(checks)} bounded learning-example checks across {len(sources)} chapter snapshots"
    )


if __name__ == "__main__":
    main()
