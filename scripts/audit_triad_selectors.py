#!/usr/bin/env python3
"""Generate the exact structural audit for barotropic triad selectors."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from mathphysics.triad_selectors import build_triad_selector_audit


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = REPO_ROOT / "data" / "registry" / "triad_selector_audit.json"
PREREGISTRATION_PATH = REPO_ROOT / "data" / "registry" / "e7_selector_preregistration.json"


def sha256_file(path: Path) -> str:
    """Return a file SHA-256 digest."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--radius", type=int, default=4)
    parser.add_argument("--evaluation-radii", type=int, nargs="+", default=[2, 4, 8])
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    arguments = parser.parse_args()
    if arguments.radius < 1:
        parser.error("--radius must be positive")
    if any(radius < 1 for radius in arguments.evaluation_radii):
        parser.error("--evaluation-radii values must be positive")
    output_path = arguments.output
    if not output_path.is_absolute():
        output_path = REPO_ROOT / output_path
    payload = build_triad_selector_audit(arguments.radius)
    payload["preregistration_relpath"] = str(PREREGISTRATION_PATH.relative_to(REPO_ROOT))
    payload["preregistration_sha256"] = sha256_file(PREREGISTRATION_PATH)
    payload["evaluation_domains"] = [
        {
            "square_domain_radius": radius,
            "ordered_nonzero_exact_triad_count": domain["ordered_nonzero_exact_triad_count"],
            "barotropic_active_channel_count": domain["barotropic_active_channel_count"],
            "quadratic_defect_admitted_triad_count": domain[
                "e7_quadratic_defect_admitted_triad_count"
            ],
            "quadratic_defect_active_admitted_count": domain[
                "e7_quadratic_defect_active_admitted_count"
            ],
            "checkerboard_kernel_exact_equivalence_pass": domain[
                "checkerboard_kernel_exact_equivalence_pass"
            ],
        }
        for radius in arguments.evaluation_radii
        for domain in [build_triad_selector_audit(radius)]
    ]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="ascii",
    )
    print(f"Wrote {output_path.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
