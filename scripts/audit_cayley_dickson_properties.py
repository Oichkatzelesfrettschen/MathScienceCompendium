#!/usr/bin/env python3
"""Generate a theorem-bounded Cayley-Dickson property and witness table."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np


REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from mathphysics.algebras.cayley_dickson import (  # noqa: E402
    CayleyDickson,
    Complex,
    Octonion,
    Pathion,
    Quaternion,
    Real,
    Sedenion,
)


DEFAULT_OUTPUT = REPO_ROOT / "data" / "registry" / "cayley_dickson_property_audit.json"
ALGEBRAS = (Real, Complex, Quaternion, Octonion, Sedenion, Pathion)


def maximum_absolute(element: CayleyDickson) -> float:
    return float(np.max(np.abs(element.coeffs)))


def dense_elements(algebra_class: Any) -> tuple[CayleyDickson, CayleyDickson]:
    dimension = algebra_class._dimension_static()
    left = algebra_class(np.arange(1, dimension + 1) % 5 - 2)
    right = algebra_class(np.arange(dimension, 0, -1) % 7 - 3)
    return left, right


def zero_divisor_witness(algebra_class: Any) -> dict[str, Any] | None:
    dimension = algebra_class._dimension_static()
    if dimension < 16:
        return None
    left_coefficients = np.zeros(dimension)
    right_coefficients = np.zeros(dimension)
    left_coefficients[[3, 10]] = 1.0
    right_coefficients[6] = 1.0
    right_coefficients[15] = -1.0
    left = algebra_class(left_coefficients)
    right = algebra_class(right_coefficients)
    return {
        "left_nonzero_indices": {"3": 1.0, "10": 1.0},
        "right_nonzero_indices": {"6": 1.0, "15": -1.0},
        "left_norm_squared": left.norm_squared(),
        "right_norm_squared": right.norm_squared(),
        "product_norm_squared": (left * right).norm_squared(),
    }


def algebra_record(algebra_class: Any) -> dict[str, Any]:
    properties = algebra_class.properties()
    dimension = properties.dimension
    left, right = dense_elements(algebra_class)
    quadratic_residual = left * left - 2.0 * left.coeffs[0] * left + left.norm_squared()
    left_alternative_residual = (left * left) * right - left * (left * right)
    right_alternative_residual = (right * left) * left - right * (left * left)
    flexibility_residual = (left * right) * left - left * (right * left)
    norm_composition_residual = abs(
        (left * right).norm_squared() - left.norm_squared() * right.norm_squared()
    )
    if dimension >= 4:
        basis_one = algebra_class.basis_element(1)
        basis_two = algebra_class.basis_element(2)
        commutator_residual = maximum_absolute(basis_one * basis_two - basis_two * basis_one)
    else:
        commutator_residual = maximum_absolute(left * right - right * left)
    if dimension >= 8:
        basis_one = algebra_class.basis_element(1)
        basis_two = algebra_class.basis_element(2)
        basis_four = algebra_class.basis_element(4)
        associator_residual = maximum_absolute(
            (basis_one * basis_two) * basis_four - basis_one * (basis_two * basis_four)
        )
    else:
        associator_residual = maximum_absolute((left * right) * left - left * (right * left))
    return {
        "name": properties.name,
        "dimension": dimension,
        "properties": properties.to_dict(),
        "witnesses": {
            "commutator_maximum_absolute": commutator_residual,
            "associator_maximum_absolute": associator_residual,
            "left_alternative_residual_maximum_absolute": maximum_absolute(
                left_alternative_residual
            ),
            "right_alternative_residual_maximum_absolute": maximum_absolute(
                right_alternative_residual
            ),
            "flexibility_residual_maximum_absolute": maximum_absolute(flexibility_residual),
            "quadratic_identity_residual_maximum_absolute": maximum_absolute(quadratic_residual),
            "norm_composition_absolute_residual": norm_composition_residual,
            "zero_divisor": zero_divisor_witness(algebra_class),
        },
    }


def build_audit() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "generator": "scripts/audit_cayley_dickson_properties.py",
        "construction": "standard real Cayley-Dickson algebras with negative doubling parameter",
        "source_evidence": [
            {
                "relpath": "source_materials/pdfs/math_0105155.pdf",
                "scope": "R, C, H, O division, associativity, alternativity, and norm-composition boundary",
            },
            {
                "relpath": "source_materials/pdfs/math_0512517.pdf",
                "scope": "higher algebras are flexible, nonalternative, non-normed, and have zero divisors",
            },
        ],
        "interpretation": (
            "The source theorems establish universal properties. Executable residuals "
            "guard the implementation and provide counterexamples for properties that fail."
        ),
        "algebras": [algebra_record(algebra_class) for algebra_class in ALGEBRAS],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    arguments = parser.parse_args()
    output_path = arguments.output
    if not output_path.is_absolute():
        output_path = REPO_ROOT / output_path
    payload = build_audit()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="ascii",
    )
    print(f"Wrote {output_path.relative_to(REPO_ROOT)} ({len(payload['algebras'])} algebras)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
