#!/usr/bin/env python3
"""Quantify sensitivity of the LBM density scaffold to E7 root ordering."""

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

from mathphysics.algebras.roots import E7RootSystem  # noqa: E402
from mathphysics.quantum_lattice_boltzmann import PHI_INV  # noqa: E402


DEFAULT_OUTPUT = REPO_ROOT / "data" / "registry" / "lbm_root_order_audit.json"


def ordered_root_digest(roots: np.ndarray) -> str:
    contiguous_roots = np.ascontiguousarray(roots, dtype=np.float64)
    return hashlib.sha256(contiguous_roots.tobytes()).hexdigest()


def density_scaffold(
    roots: np.ndarray,
    grid_shape: tuple[int, int],
    harmonic_count: int,
    harmonic_amplitude: float,
) -> np.ndarray:
    """Reproduce the root-indexed density initializer for an explicit order."""
    x_coordinates = np.linspace(0.0, 2.0 * np.pi, grid_shape[0])
    y_coordinates = np.linspace(0.0, 2.0 * np.pi, grid_shape[1])
    x_grid, y_grid = np.meshgrid(x_coordinates, y_coordinates, indexing="ij")
    density = np.ones(grid_shape, dtype=np.float64)
    for root_index, root in enumerate(roots[:harmonic_count]):
        frequency_x = abs(root[0]) * (root_index + 1)
        frequency_y = abs(root[1]) * (root_index + 1)
        amplitude = harmonic_amplitude * (PHI_INV ** (root_index / 10.0)) / (root_index + 1)
        density += amplitude * np.sin(frequency_x * x_grid) * np.cos(frequency_y * y_grid)
    return density


def compare_orders(
    reference_roots: np.ndarray,
    comparison_roots: np.ndarray,
    grid_shape: tuple[int, int],
    harmonic_count: int,
    harmonic_amplitude: float,
) -> dict[str, Any]:
    reference_density = density_scaffold(
        reference_roots, grid_shape, harmonic_count, harmonic_amplitude
    )
    comparison_density = density_scaffold(
        comparison_roots, grid_shape, harmonic_count, harmonic_amplitude
    )
    difference = comparison_density - reference_density
    reference_perturbation = reference_density - 1.0
    perturbation_norm = float(np.linalg.norm(reference_perturbation))
    return {
        "reference_order_sha256": ordered_root_digest(reference_roots),
        "comparison_order_sha256": ordered_root_digest(comparison_roots),
        "relative_perturbation_l2_difference": (
            float(np.linalg.norm(difference)) / perturbation_norm
            if perturbation_norm > 0.0
            else None
        ),
        "maximum_absolute_density_difference": float(np.max(np.abs(difference))),
        "reference_density_minimum": float(np.min(reference_density)),
        "reference_density_maximum": float(np.max(reference_density)),
        "comparison_density_minimum": float(np.min(comparison_density)),
        "comparison_density_maximum": float(np.max(comparison_density)),
    }


def build_audit(
    grid_shape: tuple[int, int], harmonic_count: int, harmonic_amplitude: float
) -> dict[str, Any]:
    roots = E7RootSystem().generate_roots()
    effective_harmonic_count = min(harmonic_count, len(roots))
    return {
        "schema_version": 1,
        "generator": "scripts/audit_lbm_root_order.py",
        "root_order": "lexicographic coordinate order",
        "root_count": len(roots),
        "grid_shape": list(grid_shape),
        "requested_harmonic_count": harmonic_count,
        "effective_harmonic_count": effective_harmonic_count,
        "harmonic_amplitude": harmonic_amplitude,
        "interpretation": (
            "Ordering is deterministic, but selecting and index-weighting the first roots "
            "is a load-bearing modeling choice rather than a Weyl-invariant operation."
        ),
        "comparisons": {
            "reverse_order": compare_orders(
                roots,
                roots[::-1],
                grid_shape,
                effective_harmonic_count,
                harmonic_amplitude,
            ),
            "cyclic_shift_by_one": compare_orders(
                roots,
                np.roll(roots, 1, axis=0),
                grid_shape,
                effective_harmonic_count,
                harmonic_amplitude,
            ),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--grid-size", type=int, default=32)
    parser.add_argument("--harmonic-count", type=int, default=127)
    parser.add_argument("--harmonic-amplitude", type=float, default=0.01)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    arguments = parser.parse_args()
    if arguments.grid_size <= 1:
        parser.error("--grid-size must exceed one")
    if arguments.harmonic_count <= 0:
        parser.error("--harmonic-count must be positive")
    if arguments.harmonic_amplitude < 0.0:
        parser.error("--harmonic-amplitude must be nonnegative")

    output_path = arguments.output
    if not output_path.is_absolute():
        output_path = REPO_ROOT / output_path
    audit = build_audit(
        (arguments.grid_size, arguments.grid_size),
        arguments.harmonic_count,
        arguments.harmonic_amplitude,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(audit, indent=2, sort_keys=True, allow_nan=False, ensure_ascii=True) + "\n",
        encoding="ascii",
    )
    print(f"Wrote {output_path.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
