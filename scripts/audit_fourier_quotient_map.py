#!/usr/bin/env python3
"""Falsify the proposed E7 P/Q homomorphic Fourier-triad filter."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from mathphysics.fourier_quotient import build_fourier_quotient_audit  # noqa: E402


DEFAULT_OUTPUT = REPO_ROOT / "data" / "registry" / "fourier_quotient_audit.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--radius", type=int, default=4)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    arguments = parser.parse_args()
    if arguments.radius < 1:
        parser.error("--radius must be positive")

    output_path = arguments.output
    if not output_path.is_absolute():
        output_path = REPO_ROOT / output_path
    audit = build_fourier_quotient_audit(arguments.radius)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(audit, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="ascii",
    )
    print(f"Wrote {output_path.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
