#!/usr/bin/env python3
"""Audit the Albert exceptional-group ladder, Kac-Moody boundary, and moonshine scope."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np


REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from mathphysics.algebras.jordan import AlbertAlgebraElement  # noqa: E402
from mathphysics.algebras.roots import (  # noqa: E402
    E9RootSystem,
    E10RootSystem,
    E11RootSystem,
)
from mathphysics.modular_forms import MonstrousMoonshine  # noqa: E402


DEFAULT_OUTPUT = REPO_ROOT / "data" / "registry" / "exceptional_group_scope_audit.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file_handle:
        while chunk := file_handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def hermitian_element(scale: float) -> AlbertAlgebraElement:
    data = np.zeros((3, 3, 8), dtype=np.float64)
    data[0, 0, 0] = scale
    data[1, 1, 0] = -2.0 * scale
    data[2, 2, 0] = 0.5 * scale
    data[0, 1, [1, 3]] = [0.25 * scale, -0.5 * scale]
    data[1, 0] = data[0, 1]
    data[1, 0, 1:] *= -1.0
    data[0, 2, [2, 5]] = [0.75 * scale, 0.125 * scale]
    data[2, 0] = data[0, 2]
    data[2, 0, 1:] *= -1.0
    return AlbertAlgebraElement(data)


def albert_implementation_metrics() -> dict[str, Any]:
    identity = AlbertAlgebraElement.identity()
    left = hermitian_element(0.6)
    right = hermitian_element(-0.35) + identity
    product = left.jordan_product(right)
    commutator = np.asarray(product.data) - np.asarray(right.jordan_product(left).data)
    left_squared = left.jordan_product(left)
    jordan_left = left.jordan_product(right.jordan_product(left_squared))
    jordan_right = left.jordan_product(right).jordan_product(left_squared)
    jordan_residual = np.asarray(jordan_left.data) - np.asarray(jordan_right.data)
    unit_residual = np.asarray(identity.jordan_product(left).data) - np.asarray(left.data)
    return {
        "coordinate_dimension": 27,
        "identity_residual_maximum_absolute": float(np.max(np.abs(unit_residual))),
        "commutativity_residual_maximum_absolute": float(np.max(np.abs(commutator))),
        "jordan_identity_residual_maximum_absolute": float(np.max(np.abs(jordan_residual))),
        "nonzero_product_norm": float(np.linalg.norm(np.asarray(product.data))),
        "inputs_are_hermitian": left.is_hermitian() and right.is_hermitian(),
    }


def kac_moody_metrics() -> list[dict[str, Any]]:
    records = []
    for root_system in (E9RootSystem(), E10RootSystem(), E11RootSystem()):
        matrix = root_system.generalized_cartan_matrix()
        eigenvalues = np.linalg.eigvalsh(matrix)
        records.append(
            {
                "name": root_system.name,
                "rank": root_system.rank,
                "determinant": round(float(np.linalg.det(matrix))),
                "negative_eigenvalue_count": int(np.count_nonzero(eigenvalues < -1e-10)),
                "null_eigenvalue_count": int(np.count_nonzero(np.abs(eigenvalues) <= 1e-10)),
            }
        )
    return records


def build_audit() -> dict[str, Any]:
    baez_path = REPO_ROOT / "source_materials" / "pdfs" / "math_0105155.pdf"
    borcherds_path = (
        REPO_ROOT / "source_materials" / "pdfs" / "borcherds_monstrous_moonshine_1992.pdf"
    )
    moonshine_survey_path = REPO_ROOT / "source_materials" / "pdfs" / "arxiv_1411.6571.pdf"
    return {
        "schema_version": 1,
        "generator": "scripts/audit_exceptional_group_scope.py",
        "source_evidence": [
            {"relpath": str(baez_path.relative_to(REPO_ROOT)), "sha256": sha256_file(baez_path)},
            {
                "relpath": str(borcherds_path.relative_to(REPO_ROOT)),
                "sha256": sha256_file(borcherds_path),
            },
            {
                "relpath": str(moonshine_survey_path.relative_to(REPO_ROOT)),
                "sha256": sha256_file(moonshine_survey_path),
            },
        ],
        "albert_ladder": [
            {
                "group": "F4",
                "dimension": 52,
                "role": "automorphism group of the Albert algebra h3(O)",
                "status": "established",
            },
            {
                "group": "E6(-26)",
                "dimension": 78,
                "role": "determinant-preserving reduced structure group of h3(O)",
                "status": "established",
            },
            {
                "group": "E7(-25)",
                "dimension": 133,
                "role": "conformal/Freudenthal symmetry built from h3(O), not its automorphism group",
                "status": "established",
            },
            {
                "group": "E7 as Aut(J3(S))",
                "dimension": 133,
                "role": "source-framework claim",
                "status": "rejected",
            },
        ],
        "dimension_identities": {
            "albert_dimension": 27,
            "e6_dimension_from_f4_plus_traceless_albert": 52 + 26,
            "e7_dimension_from_f4_plus_three_albert_copies": 52 + 3 * 27,
        },
        "albert_implementation": albert_implementation_metrics(),
        "kac_moody_extensions": kac_moody_metrics(),
        "moonshine_scope": {
            "monster_order": MonstrousMoonshine.monster_order(),
            "established": (
                "Monster graded traces on the moonshine module are specific genus-zero "
                "modular functions proved using the monster Lie algebra."
            ),
            "repository_implementation": (
                "The code stores the Monster order and evaluates j; it defines no Monster "
                "representation, graded module, physical state action, or stability operator."
            ),
            "physical_stability_claim_status": "rejected",
            "rejection_criterion": (
                "Reject generic stability claims until a Monster representation, state "
                "space, evolution operator, invariant, and matched control are defined."
            ),
        },
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
    print(f"Wrote {output_path.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
