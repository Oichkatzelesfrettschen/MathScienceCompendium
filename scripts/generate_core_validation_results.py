#!/usr/bin/env python3
"""Regenerate deterministic Cayley-Dickson and E8 validation artifacts."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

import numpy as np


REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from mathphysics.algebras.cayley_dickson import (  # noqa: E402
    CayleyDicksonValidator,
    Real,
    _NumpyEncoder,
)
from mathphysics.algebras.roots import E8RootSystem  # noqa: E402


DEFAULT_OUTPUT_DIR = REPO_ROOT / "experiments" / "results"
GENERATOR_RELPATH = "scripts/generate_core_validation_results.py"


def atomic_write_json(output_path: Path, payload: dict[str, Any]) -> None:
    """Write JSON through a same-directory temporary file and atomic rename."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=output_path.parent,
            prefix=f".{output_path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            json.dump(
                payload,
                temporary_file,
                cls=_NumpyEncoder,
                indent=2,
                sort_keys=True,
                allow_nan=False,
            )
            temporary_file.write("\n")
            temporary_file.flush()
            os.fsync(temporary_file.fileno())
        temporary_path.replace(output_path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def build_real_validation() -> dict[str, Any]:
    """Evaluate the implemented real-number Cayley-Dickson base case."""
    np.random.seed(0)
    result = CayleyDicksonValidator(Real).verify_all_properties()
    return {
        "schema_version": 1,
        "generator": GENERATOR_RELPATH,
        "method": "implemented property checks with numpy seed 0",
        "result": result,
    }


def build_e8_validation() -> dict[str, Any]:
    """Evaluate exact finite invariants of the implemented E8 root system."""
    root_system = E8RootSystem()
    roots = root_system.generate_roots()
    positive_roots = root_system.positive_roots()
    simple_roots = root_system.generate_simple_roots()
    cartan_matrix = np.rint(root_system.cartan_matrix()).astype(int)
    squared_norms, squared_norm_counts = np.unique(
        np.round(np.sum(roots * roots, axis=1), decimals=12),
        return_counts=True,
    )
    if squared_norms.shape != squared_norm_counts.shape:
        raise RuntimeError("NumPy returned misaligned E8 norm values and counts")
    root_tuples = {tuple(root.tolist()) for root in roots}
    opposite_closed = all(tuple((-root).tolist()) in root_tuples for root in roots)

    return {
        "schema_version": 1,
        "generator": GENERATOR_RELPATH,
        "method": "direct enumeration of the implemented E8 roots",
        "root_count": int(roots.shape[0]),
        "positive_root_count": int(positive_roots.shape[0]),
        "rank": int(simple_roots.shape[0]),
        "dimension_from_rank_and_roots": int(simple_roots.shape[0] + roots.shape[0]),
        "squared_root_norm_multiplicities": {
            f"{float(squared_norm):.12g}": int(count)
            for squared_norm, count in zip(squared_norms, squared_norm_counts)
        },
        "opposite_root_closure": opposite_closed,
        "simple_roots": simple_roots.tolist(),
        "cartan_matrix": cartan_matrix.tolist(),
        "cartan_determinant": round(float(np.linalg.det(cartan_matrix))),
        "weyl_group_order": int(root_system.properties.weyl_group_order),
    }


def generate_results(output_dir: Path) -> list[Path]:
    """Generate both core validation artifacts and return their paths."""
    output_paths = [
        output_dir / "cayley_dickson_real_validation.json",
        output_dir / "e8_analysis.json",
    ]
    atomic_write_json(output_paths[0], build_real_validation())
    atomic_write_json(output_paths[1], build_e8_validation())
    return output_paths


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    arguments = parser.parse_args()

    output_dir = arguments.output_dir
    if not output_dir.is_absolute():
        output_dir = REPO_ROOT / output_dir
    for output_path in generate_results(output_dir):
        print(f"Wrote {output_path.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
