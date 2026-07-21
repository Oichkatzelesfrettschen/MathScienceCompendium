#!/usr/bin/env python3
"""Reproduce promoted computational outcomes without primary run caches."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
from pathlib import Path

import numpy as np
import scipy


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_ROOT = REPO_ROOT / "data" / "reproduction"


def sha256_file(path: Path) -> str:
    """Return a file digest."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(command: list[str]) -> None:
    """Run one locked reproduction command at repository root."""
    subprocess.run(command, cwd=REPO_ROOT, check=True)


def main() -> int:
    source_commit = os.environ.get("EVIDENCE_SOURCE_COMMIT", "")
    if len(source_commit) != 40 or any(character not in "0123456789abcdef" for character in source_commit):
        raise ValueError("EVIDENCE_SOURCE_COMMIT must be a lowercase 40-character Git digest")
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    commands = [
        [
            sys.executable,
            "scripts/audit_triad_selectors.py",
            "--output",
            "data/reproduction/triad_selector_audit.json",
        ],
        [
            sys.executable,
            "scripts/run_beta_plane_sweep.py",
            "--profile",
            "production",
            "--work-root",
            "/tmp/beta_plane_reproduction",
            "--output",
            "data/reproduction/beta_plane_sweep_results.json",
            "--evidence-archive",
            "data/reproduction/beta_plane_production_arrays.tar",
        ],
        [
            sys.executable,
            "scripts/run_beta_plane_sweep.py",
            "--profile",
            "refinement",
            "--work-root",
            "/tmp/beta_plane_reproduction",
            "--output",
            "data/reproduction/beta_plane_refinement_results.json",
            "--evidence-archive",
            "data/reproduction/beta_plane_refinement_arrays.tar",
        ],
        [
            sys.executable,
            "scripts/run_beta_plane_controls.py",
            "--output",
            "data/reproduction/beta_plane_control_results.json",
            "--evidence-archive",
            "data/reproduction/beta_plane_control_arrays.tar",
        ],
    ]
    for command in commands:
        run(command)
    result_paths = sorted(
        path for path in OUTPUT_ROOT.iterdir() if path.name != "environment_report.json"
    )
    production = json.loads(
        (OUTPUT_ROOT / "beta_plane_sweep_results.json").read_text(encoding="ascii")
    )
    selector = json.loads(
        (OUTPUT_ROOT / "triad_selector_audit.json").read_text(encoding="ascii")
    )
    report = {
        "schema_version": 1,
        "source_commit": source_commit,
        "python_version": platform.python_version(),
        "numpy_version": np.__version__,
        "scipy_version": scipy.__version__,
        "commands": commands,
        "beta_plane_outcome": production["aggregate_decision"],
        "selector_outcome": selector["scientific_outcome"],
        "outputs": [
            {
                "relpath": str(path.relative_to(REPO_ROOT)),
                "sha256": sha256_file(path),
                "size_bytes": path.stat().st_size,
            }
            for path in result_paths
        ],
    }
    (OUTPUT_ROOT / "environment_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="ascii",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
