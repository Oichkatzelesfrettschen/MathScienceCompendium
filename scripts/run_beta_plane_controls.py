#!/usr/bin/env python3
"""Run quotient-sentinel and f-plane rotation-covariance controls."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import multiprocessing
import os
import subprocess
import sys
import tarfile
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np


os.environ.setdefault("JAX_PLATFORMS", "cpu")
os.environ.setdefault("XLA_PYTHON_CLIENT_PREALLOCATE", "false")

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from mathphysics.beta_plane import (  # noqa: E402
    BarotropicBetaPlane,
    BetaPlaneConfig,
    NonlinearFilter,
    classify_final_window,
)


PREREGISTRATION_PATH = REPO_ROOT / "data" / "registry" / "beta_plane_sweep_preregistration.json"
DEFAULT_OUTPUT = REPO_ROOT / "data" / "registry" / "beta_plane_control_results.json"
LBM_AUDIT_PATH = REPO_ROOT / "data" / "registry" / "lbm_evidence_audit.json"
ENVIRONMENT_LOCK_PATH = REPO_ROOT / "requirements-lock.txt"
DEFAULT_EVIDENCE_ARCHIVE = (
    REPO_ROOT / "data" / "evidence" / "beta_plane" / "control_final_states.tar"
)


def array_sha256(values: np.ndarray) -> str:
    """Hash a float64 array in contiguous row-major order."""
    data = np.ascontiguousarray(values, dtype=np.float64).tobytes()
    return hashlib.sha256(data).hexdigest()


def file_sha256(path: Path) -> str:
    """Hash a retained evidence file."""
    digest = hashlib.sha256()
    with path.open("rb") as file_handle:
        while chunk := file_handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def source_commit() -> str:
    """Return the committed protocol and implementation revision."""
    declared_commit = os.environ.get("EVIDENCE_SOURCE_COMMIT")
    if declared_commit is not None:
        if len(declared_commit) != 40 or any(
            character not in "0123456789abcdef" for character in declared_commit
        ):
            raise ValueError("EVIDENCE_SOURCE_COMMIT must be a lowercase Git digest")
        return declared_commit
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def write_control_archive(records: list[dict[str, Any]], archive_path: Path) -> dict[str, str]:
    """Retain every control final state in a deterministic tracked archive."""
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive_path, mode="w", format=tarfile.PAX_FORMAT) as archive:
        for record in sorted(records, key=lambda item: item["seed"]):
            arrays = record.pop("_arrays")
            record["array_shape"] = list(next(iter(arrays.values())).shape)
            record["array_dtype"] = "float64_row_major"
            record["archive_members"] = {}
            for arm_name in sorted(arrays):
                data = np.ascontiguousarray(arrays[arm_name], dtype=np.float64).tobytes()
                member_name = f"seed_{record['seed']:03d}/{arm_name}.f64"
                member = tarfile.TarInfo(member_name)
                member.size = len(data)
                member.mode = 0o644
                member.mtime = 0
                member.uid = 0
                member.gid = 0
                member.uname = ""
                member.gname = ""
                archive.addfile(member, io.BytesIO(data))
                record["archive_members"][arm_name] = member_name
    return {
        "relpath": str(archive_path.relative_to(REPO_ROOT)),
        "sha256": file_sha256(archive_path),
        "format": "deterministic_uncompressed_tar_of_float64_arrays",
    }


def prescribed_zonal_diagnostic_control(model: dict[str, Any]) -> dict[str, Any]:
    """Verify that the locked diagnostics recognize a known four-wave jet field."""
    config = BetaPlaneConfig(
        grid_size=int(model["production_grid_size"]),
        initial_energy=float(model["initial_kinetic_energy"]),
        initial_wavenumber_minimum=float(model["initial_shell"][0]),
        initial_wavenumber_maximum=float(model["initial_shell"][1]),
    )
    solver = BarotropicBetaPlane(config)
    vorticity_hat = np.zeros((config.grid_size, config.grid_size), dtype=np.complex128)
    prescribed_wavenumber = 4
    vorticity_hat[0, prescribed_wavenumber] = 1.0
    vorticity_hat[0, -prescribed_wavenumber] = 1.0
    vorticity_hat *= np.sqrt(config.initial_energy / solver.kinetic_energy(vorticity_hat))
    zonal_fraction, spectral_fraction, jet_count, prominence = solver.zonal_diagnostics(
        vorticity_hat
    )
    window_classification = classify_final_window(
        [zonal_fraction] * 10,
        [jet_count] * 10,
    )
    passed = (
        abs(zonal_fraction - 1.0) <= 1e-12
        and abs(spectral_fraction - 1.0) <= 1e-12
        and jet_count == 2 * prescribed_wavenumber
        and window_classification["persistent_jet"] is True
    )
    return {
        "prescribed_zonal_wavenumber": prescribed_wavenumber,
        "expected_total_jet_count": 2 * prescribed_wavenumber,
        "observed_total_jet_count": jet_count,
        "zonal_kinetic_energy_fraction": zonal_fraction,
        "spectral_zonal_energy_fraction": spectral_fraction,
        "prominence_threshold": prominence,
        "full_window_classification": window_classification,
        "passed": passed,
    }


def retained_lbm_null_control() -> dict[str, Any]:
    """Verify that the independent high-resolution LBM corpus stays non-zonal."""
    audit = json.loads(LBM_AUDIT_PATH.read_text(encoding="ascii"))
    ratios = [float(snapshot["zonal_to_total_rms_ratio"]) for snapshot in audit["snapshots"]]
    threshold = 0.01
    return {
        "audit_relpath": str(LBM_AUDIT_PATH.relative_to(REPO_ROOT)),
        "audit_sha256": file_sha256(LBM_AUDIT_PATH),
        "snapshot_count": len(ratios),
        "maximum_zonal_to_total_rms_ratio": max(ratios),
        "maximum_allowed_ratio": threshold,
        "passed": max(ratios) < threshold,
    }


def execute_seed(seed: int, model: dict[str, Any]) -> dict[str, Any]:
    """Run all locked controls for one seed."""
    time_step = float(model["production_time_step"])
    duration = float(model["duration"])
    base = BetaPlaneConfig(
        grid_size=int(model["production_grid_size"]),
        time_step=time_step,
        steps=round(duration / time_step),
        beta=5.0,
        linear_drag=0.02,
        viscosity=0.0005,
        initial_wavenumber_minimum=float(model["initial_shell"][0]),
        initial_wavenumber_maximum=float(model["initial_shell"][1]),
        initial_energy=float(model["initial_kinetic_energy"]),
        seed=seed,
        sample_interval_steps=int(model["sample_interval_steps"]),
        analysis_window_fraction=float(model["analysis_window_fraction"]),
    )
    identity = BarotropicBetaPlane(base).run()
    quotient = BarotropicBetaPlane(
        replace(base, nonlinear_filter=NonlinearFilter.E7_PQ_HOMOMORPHISM)
    ).run()
    quotient_error = float(np.max(np.abs(identity.final_vorticity - quotient.final_vorticity)))

    f_plane_config = replace(base, beta=0.0)
    f_plane_solver = BarotropicBetaPlane(f_plane_config)
    initial_hat = f_plane_solver.initial_vorticity()
    initial_physical = np.fft.ifft2(initial_hat).real
    rotated_initial = np.rot90(initial_physical)
    rotated_initial_hat = np.fft.fft2(rotated_initial)
    f_plane = f_plane_solver.run(initial_hat)
    rotated_f_plane = f_plane_solver.run(rotated_initial_hat)
    expected_rotated_final = np.rot90(f_plane.final_vorticity)
    denominator = max(float(np.linalg.norm(expected_rotated_final)), 1e-15)
    rotation_error = float(
        np.linalg.norm(rotated_f_plane.final_vorticity - expected_rotated_final) / denominator
    )
    maximum_budget_residual = max(
        abs(identity.energy_budget_residual),
        abs(identity.enstrophy_budget_residual),
        abs(quotient.energy_budget_residual),
        abs(quotient.enstrophy_budget_residual),
        abs(f_plane.energy_budget_residual),
        abs(f_plane.enstrophy_budget_residual),
        abs(rotated_f_plane.energy_budget_residual),
        abs(rotated_f_plane.enstrophy_budget_residual),
    )
    return {
        "seed": seed,
        "quotient_to_identity_maximum_vorticity_error": quotient_error,
        "f_plane_rotation_relative_vorticity_error": rotation_error,
        "maximum_absolute_budget_residual": maximum_budget_residual,
        "identity_final_sha256": array_sha256(identity.final_vorticity),
        "quotient_final_sha256": array_sha256(quotient.final_vorticity),
        "f_plane_final_sha256": array_sha256(f_plane.final_vorticity),
        "rotated_f_plane_final_sha256": array_sha256(rotated_f_plane.final_vorticity),
        "_arrays": {
            "identity": identity.final_vorticity,
            "quotient": quotient.final_vorticity,
            "f_plane": f_plane.final_vorticity,
            "rotated_f_plane": rotated_f_plane.final_vorticity,
        },
        "quotient_sentinel_passed": quotient_error <= 1e-12,
        "rotation_covariance_passed": rotation_error <= 1e-10,
        "budget_passed": maximum_budget_residual <= 1e-6,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=max(1, min(8, os.cpu_count() or 1)))
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--evidence-archive", type=Path, default=DEFAULT_EVIDENCE_ARCHIVE)
    arguments = parser.parse_args()
    if arguments.workers < 1:
        parser.error("--workers must be positive")
    preregistration = json.loads(PREREGISTRATION_PATH.read_text(encoding="ascii"))
    seeds = [int(seed) for seed in preregistration["production_matrix"]["seeds"]]
    with ProcessPoolExecutor(
        max_workers=arguments.workers,
        mp_context=multiprocessing.get_context("spawn"),
    ) as executor:
        records = list(
            executor.map(
                execute_seed,
                seeds,
                [preregistration["model"]] * len(seeds),
            )
        )
    all_controls_passed = all(
        record["quotient_sentinel_passed"]
        and record["rotation_covariance_passed"]
        and record["budget_passed"]
        for record in records
    )
    prescribed_zonal_control = prescribed_zonal_diagnostic_control(preregistration["model"])
    lbm_null_control = retained_lbm_null_control()
    all_controls_passed = (
        all_controls_passed and prescribed_zonal_control["passed"] and lbm_null_control["passed"]
    )
    payload = {
        "schema_version": 1,
        "generator": "scripts/run_beta_plane_controls.py",
        "preregistration_relpath": str(PREREGISTRATION_PATH.relative_to(REPO_ROOT)),
        "preregistration_sha256": file_sha256(PREREGISTRATION_PATH),
        "source_commit": source_commit(),
        "environment_lock_relpath": str(ENVIRONMENT_LOCK_PATH.relative_to(REPO_ROOT)),
        "environment_lock_sha256": file_sha256(ENVIRONMENT_LOCK_PATH),
        "seed_count": len(seeds),
        "arm_run_count": 4 * len(seeds),
        "records": records,
        "prescribed_zonal_diagnostic_control": prescribed_zonal_control,
        "retained_lbm_null_control": lbm_null_control,
        "all_controls_passed": all_controls_passed,
    }
    evidence_archive = arguments.evidence_archive
    if not evidence_archive.is_absolute():
        evidence_archive = REPO_ROOT / evidence_archive
    payload["evidence_archive"] = write_control_archive(records, evidence_archive)
    output_path = arguments.output
    if not output_path.is_absolute():
        output_path = REPO_ROOT / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="ascii",
    )
    print(
        f"Wrote {output_path.relative_to(REPO_ROOT)}: controls_passed={all_controls_passed}",
        flush=True,
    )
    return 0 if all_controls_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
