#!/usr/bin/env python3
"""Run the checkpointed preregistered beta-plane production sweep."""

from __future__ import annotations

import argparse
import hashlib
import io
import itertools
import json
import multiprocessing
import os
import subprocess
import sys
import tarfile
import zipfile
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import numpy as np


os.environ.setdefault("JAX_PLATFORMS", "cpu")
os.environ.setdefault("XLA_PYTHON_CLIENT_PREALLOCATE", "false")


REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from mathphysics.beta_plane import BarotropicBetaPlane, BetaPlaneConfig  # noqa: E402


PREREGISTRATION_PATH = REPO_ROOT / "data" / "registry" / "beta_plane_sweep_preregistration.json"
DEFAULT_OUTPUT = REPO_ROOT / "data" / "registry" / "beta_plane_sweep_results.json"
DEFAULT_WORK_ROOT = REPO_ROOT / "build" / "beta_plane_sweep"
REFINEMENT_AMENDMENT_PATH = (
    REPO_ROOT / "data" / "registry" / "beta_plane_refinement_protocol_amendment.json"
)
ENVIRONMENT_LOCK_PATH = REPO_ROOT / "requirements-lock.txt"
EVIDENCE_ROOT = REPO_ROOT / "data" / "evidence" / "beta_plane"


def sha256_bytes(data: bytes) -> str:
    """Return the SHA-256 digest of bytes."""
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    """Return the SHA-256 digest of a file."""
    digest = hashlib.sha256()
    with path.open("rb") as file_handle:
        while chunk := file_handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def display_path(path: Path) -> Path:
    """Render repository paths relatively and preserve external absolute paths."""
    return path.relative_to(REPO_ROOT) if path.is_relative_to(REPO_ROOT) else path


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


def checkpoint_binding(profile: str) -> dict[str, str]:
    """Bind resumable checkpoints to code, protocol, environment, and profile."""
    return {
        "source_commit": source_commit(),
        "preregistration_sha256": sha256_file(PREREGISTRATION_PATH),
        "environment_lock_sha256": sha256_file(ENVIRONMENT_LOCK_PATH),
        "profile": profile,
    }


def write_deterministic_npz(path: Path, arrays: dict[str, np.ndarray]) -> None:
    """Write a compressed NumPy archive without wall-clock ZIP metadata."""
    with zipfile.ZipFile(path, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        for array_name in sorted(arrays):
            buffer = io.BytesIO()
            np.lib.format.write_array(buffer, arrays[array_name], allow_pickle=False)
            member = zipfile.ZipInfo(f"{array_name}.npy", date_time=(1980, 1, 1, 0, 0, 0))
            member.compress_type = zipfile.ZIP_DEFLATED
            member.external_attr = 0o600 << 16
            archive.writestr(member, buffer.getvalue(), compress_type=zipfile.ZIP_DEFLATED)


def run_id(specification: dict[str, Any]) -> str:
    """Build a deterministic mechanism-first run identifier."""
    return (
        f"beta_{specification['beta']:05.2f}"
        f"_drag_{specification['linear_drag']:.5f}"
        f"_nu_{specification['viscosity']:.6f}"
        f"_seed_{specification['seed']:03d}"
        f"_n_{specification['grid_size']:03d}"
        f"_dt_{specification['time_step']:.4f}"
    ).replace(".", "p")


def build_run_specs(preregistration: dict[str, Any], profile: str) -> list[dict[str, Any]]:
    """Expand the locked production matrix or a non-admissible smoke subset."""
    model = preregistration["model"]
    matrix = preregistration["production_matrix"]
    if profile == "production":
        beta_values = matrix["beta"]
        drag_values = matrix["linear_drag"]
        viscosity_values = matrix["viscosity"]
        seeds = matrix["seeds"]
        grid_size = model["production_grid_size"]
        time_step = model["production_time_step"]
        duration = model["duration"]
    elif profile == "refinement":
        refinement = preregistration["refinement_matrix"]
        beta_values = refinement["beta"]
        drag_values = refinement["linear_drag"]
        viscosity_values = refinement["viscosity"]
        seeds = refinement["seeds"]
        duration = model["duration"]
        return [
            {
                "beta": float(beta),
                "linear_drag": float(linear_drag),
                "viscosity": float(viscosity),
                "seed": int(seed),
                "grid_size": int(grid_size),
                "time_step": float(time_step),
                "steps": round(duration / float(time_step)),
                "duration": float(duration),
                "initial_wavenumber_minimum": float(model["initial_shell"][0]),
                "initial_wavenumber_maximum": float(model["initial_shell"][1]),
                "initial_energy": float(model["initial_kinetic_energy"]),
                "sample_interval_steps": int(model["sample_interval_steps"]),
                "analysis_window_fraction": float(model["analysis_window_fraction"]),
                "initial_condition_protocol": "shared_n64_fourier_embedding",
            }
            for beta, linear_drag, viscosity, seed, grid_size, time_step in itertools.product(
                beta_values,
                drag_values,
                viscosity_values,
                seeds,
                refinement["grid_sizes"],
                refinement["time_steps"],
            )
        ]
    else:
        beta_values = [0.0, 5.0]
        drag_values = [0.02]
        viscosity_values = [0.0005]
        seeds = [11, 29]
        grid_size = 24
        time_step = 0.01
        duration = 0.5
    steps = round(duration / time_step)
    if not np.isclose(steps * time_step, duration, rtol=0.0, atol=1e-14):
        raise ValueError("duration must be an integer multiple of the time step")
    return [
        {
            "beta": float(beta),
            "linear_drag": float(linear_drag),
            "viscosity": float(viscosity),
            "seed": int(seed),
            "grid_size": int(grid_size),
            "time_step": float(time_step),
            "steps": steps,
            "duration": float(duration),
            "initial_wavenumber_minimum": float(model["initial_shell"][0]),
            "initial_wavenumber_maximum": float(model["initial_shell"][1]),
            "initial_energy": float(model["initial_kinetic_energy"]),
            "sample_interval_steps": int(model["sample_interval_steps"]),
            "analysis_window_fraction": float(model["analysis_window_fraction"]),
        }
        for beta, linear_drag, viscosity, seed in itertools.product(
            beta_values, drag_values, viscosity_values, seeds
        )
    ]


def execute_run(specification: dict[str, Any]) -> dict[str, Any]:
    """Execute one independent matrix cell and return serializable evidence."""
    config = BetaPlaneConfig(
        grid_size=specification["grid_size"],
        time_step=specification["time_step"],
        steps=specification["steps"],
        beta=specification["beta"],
        linear_drag=specification["linear_drag"],
        viscosity=specification["viscosity"],
        initial_wavenumber_minimum=specification["initial_wavenumber_minimum"],
        initial_wavenumber_maximum=specification["initial_wavenumber_maximum"],
        initial_energy=specification["initial_energy"],
        seed=specification["seed"],
        sample_interval_steps=specification["sample_interval_steps"],
        analysis_window_fraction=specification["analysis_window_fraction"],
    )
    solver = BarotropicBetaPlane(config)
    initial_vorticity_hat = None
    if specification.get("initial_condition_protocol") == "shared_n64_fourier_embedding":
        initial_vorticity_hat = shared_refinement_initial_vorticity(config)
    result = solver.run(initial_vorticity_hat)
    final_hat = np.fft.fft2(result.final_vorticity)
    _, _, velocity_x, velocity_y = solver.physical_fields(final_hat)
    rms_speed = float(np.sqrt(np.mean(velocity_x**2 + velocity_y**2)))
    zonal_profile = np.mean(velocity_x, axis=0)
    zonal_profile -= np.mean(zonal_profile)
    zonal_rms = float(np.sqrt(np.mean(zonal_profile**2)))
    profile_spectrum = np.abs(np.fft.fft(zonal_profile)) ** 2
    profile_spectrum[0] = 0.0
    dominant_zonal_wavenumber = int(
        abs(np.fft.fftfreq(config.grid_size) * config.grid_size)[int(np.argmax(profile_spectrum))]
    )
    rhines_wavenumber = (
        float(np.sqrt(config.beta / rms_speed)) if config.beta > 0.0 and rms_speed > 0.0 else 0.0
    )
    final_bytes = np.ascontiguousarray(result.final_vorticity, dtype=np.float64).tobytes()
    initial_bytes = np.ascontiguousarray(result.initial_vorticity, dtype=np.float64).tobytes()
    return {
        "run_id": run_id(specification),
        "specification": specification,
        "initial_vorticity_sha256": sha256_bytes(initial_bytes),
        "final_vorticity_sha256": sha256_bytes(final_bytes),
        "initial_energy": result.initial_energy,
        "final_energy": result.final_energy,
        "initial_enstrophy": result.initial_enstrophy,
        "final_enstrophy": result.final_enstrophy,
        "energy_budget_residual": result.energy_budget_residual,
        "enstrophy_budget_residual": result.enstrophy_budget_residual,
        "normalized_energy_budget_residual": result.energy_budget_residual
        / max(abs(result.initial_energy), 1e-15),
        "normalized_enstrophy_budget_residual": result.enstrophy_budget_residual
        / max(abs(result.initial_enstrophy), 1e-15),
        "final_zonal_fraction": result.zonal_kinetic_energy_fraction,
        "final_spectral_zonal_fraction": result.spectral_zonal_energy_fraction,
        "final_window_mean_zonal_fraction": result.final_window_mean_zonal_fraction,
        "final_window_tenth_percentile_zonal_fraction": (
            result.final_window_tenth_percentile_zonal_fraction
        ),
        "final_window_modal_jet_count": result.final_window_modal_jet_count,
        "final_window_modal_jet_count_occupancy": (result.final_window_modal_jet_count_occupancy),
        "persistent_jet": result.jet_claim_admitted,
        "jet_prominence_threshold": result.jet_prominence_threshold,
        "rms_speed": rms_speed,
        "zonal_rms_to_initial_speed": zonal_rms / np.sqrt(2.0 * config.initial_energy),
        "rhines_wavenumber": rhines_wavenumber,
        "dominant_zonal_wavenumber": dominant_zonal_wavenumber,
        "final_window_zonal_fractions": list(result.final_window_zonal_fractions),
        "final_window_jet_counts": list(result.final_window_jet_counts),
        "final_vorticity": result.final_vorticity,
    }


def shared_refinement_initial_vorticity(
    target_config: BetaPlaneConfig, reference_grid_size: int = 64
) -> np.ndarray:
    """Embed one reference Fourier realization into every refinement grid."""
    reference_config = BetaPlaneConfig(
        grid_size=reference_grid_size,
        time_step=target_config.time_step,
        steps=target_config.steps,
        beta=target_config.beta,
        linear_drag=target_config.linear_drag,
        viscosity=target_config.viscosity,
        initial_wavenumber_minimum=target_config.initial_wavenumber_minimum,
        initial_wavenumber_maximum=target_config.initial_wavenumber_maximum,
        initial_energy=target_config.initial_energy,
        seed=target_config.seed,
        sample_interval_steps=target_config.sample_interval_steps,
        analysis_window_fraction=target_config.analysis_window_fraction,
    )
    reference_solver = BarotropicBetaPlane(reference_config)
    reference_hat = reference_solver.initial_vorticity()
    target_hat = np.zeros((target_config.grid_size, target_config.grid_size), dtype=np.complex128)
    transform_scale = (target_config.grid_size / reference_grid_size) ** 2
    active_indices = np.argwhere(np.abs(reference_hat) > 0.0)
    for reference_x_index, reference_y_index in active_indices:
        wavenumber_x = round(reference_solver.wavenumber_x[reference_x_index, reference_y_index])
        wavenumber_y = round(reference_solver.wavenumber_y[reference_x_index, reference_y_index])
        target_x_index = wavenumber_x % target_config.grid_size
        target_y_index = wavenumber_y % target_config.grid_size
        target_hat[target_x_index, target_y_index] = (
            reference_hat[reference_x_index, reference_y_index] * transform_scale
        )
    target_solver = BarotropicBetaPlane(target_config)
    embedded_energy = target_solver.kinetic_energy(target_hat)
    target_hat *= np.sqrt(target_config.initial_energy / embedded_energy)
    return target_hat


def write_checkpoint(record: dict[str, Any], work_root: Path) -> dict[str, Any]:
    """Retain one run's arrays and JSON summary atomically enough for resume."""
    run_name = record["run_id"]
    run_root = work_root / "runs"
    run_root.mkdir(parents=True, exist_ok=True)
    array_path = run_root / f"{run_name}.npz"
    final_vorticity = record.pop("final_vorticity")
    final_window_zonal_fractions = np.asarray(
        record.pop("final_window_zonal_fractions"), dtype=np.float64
    )
    final_window_jet_counts = np.asarray(record.pop("final_window_jet_counts"), dtype=np.int64)
    if not (
        np.isfinite(final_vorticity).all()
        and np.isfinite(final_window_zonal_fractions).all()
        and np.isfinite(final_window_jet_counts).all()
    ):
        raise FloatingPointError(f"nonfinite retained array in {run_name}")
    write_deterministic_npz(
        array_path,
        {
            "final_vorticity": final_vorticity,
            "final_window_jet_counts": final_window_jet_counts,
            "final_window_zonal_fractions": final_window_zonal_fractions,
        },
    )
    record["arrays_sha256"] = sha256_file(array_path)
    summary_path = run_root / f"{run_name}.json"
    temporary_path = summary_path.with_suffix(".json.tmp")
    temporary_path.write_text(
        json.dumps(record, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="ascii",
    )
    temporary_path.replace(summary_path)
    return record


def write_evidence_archive(
    records: list[dict[str, Any]], profile: str, archive_path: Path, work_root: Path
) -> dict[str, str]:
    """Write deterministic tracked evidence and bind each record to its member."""
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive_path, mode="w", format=tarfile.PAX_FORMAT) as archive:
        for record in sorted(records, key=lambda item: item["run_id"]):
            arrays_path = work_root / "runs" / f"{record['run_id']}.npz"
            data = arrays_path.read_bytes()
            if sha256_bytes(data) != record["arrays_sha256"]:
                raise ValueError(f"checkpoint digest mismatch for {record['run_id']}")
            member_name = f"{profile}/{record['run_id']}.npz"
            member = tarfile.TarInfo(member_name)
            member.size = len(data)
            member.mode = 0o644
            member.mtime = 0
            member.uid = 0
            member.gid = 0
            member.uname = ""
            member.gname = ""
            archive.addfile(member, io.BytesIO(data))
            record["arrays_archive_member"] = member_name
            record.pop("checkpoint_binding", None)
    return {
        "relpath": str(display_path(archive_path)),
        "sha256": sha256_file(archive_path),
        "format": "deterministic_uncompressed_tar_of_npz",
    }


def load_checkpoint(
    specification: dict[str, Any],
    work_root: Path,
    expected_binding: dict[str, str],
) -> dict[str, Any] | None:
    """Load a completed run only when its locked specification and arrays match."""
    summary_path = work_root / "runs" / f"{run_id(specification)}.json"
    if not summary_path.is_file():
        return None
    record = json.loads(summary_path.read_text(encoding="ascii"))
    if record.get("specification") != specification:
        return None
    if record.get("checkpoint_binding") != expected_binding:
        return None
    arrays_path = work_root / "runs" / f"{run_id(specification)}.npz"
    if not arrays_path.is_file() or sha256_file(arrays_path) != record["arrays_sha256"]:
        return None
    return record


def bootstrap_differences(
    paired_differences: dict[int, list[float]], seed: int, draws: int = 10000
) -> np.ndarray:
    """Bootstrap seed clusters while preserving all cells within each seed."""
    seed_values = sorted(paired_differences)
    generator = np.random.default_rng(seed)
    bootstrapped = np.empty(draws, dtype=np.float64)
    for draw_index in range(draws):
        sampled_seeds = generator.choice(seed_values, size=len(seed_values), replace=True)
        selected = [value for item in sampled_seeds for value in paired_differences[int(item)]]
        bootstrapped[draw_index] = float(np.mean(selected))
    return bootstrapped


def exact_cluster_sign_flip_p(paired_differences: dict[int, list[float]]) -> float:
    """Return an exact two-sided sign-flip p-value over independent seed clusters."""
    cluster_means = np.asarray(
        [np.mean(paired_differences[seed]) for seed in sorted(paired_differences)],
        dtype=np.float64,
    )
    observed = abs(float(np.mean(cluster_means)))
    null_statistics = [
        abs(float(np.mean(cluster_means * np.asarray(signs, dtype=np.float64))))
        for signs in itertools.product((-1.0, 1.0), repeat=len(cluster_means))
    ]
    return float(np.mean(np.asarray(null_statistics) >= observed - 1e-15))


def build_primary_contrasts(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Evaluate the eight preregistered paired primary contrasts."""
    record_lookup = {
        (
            record["specification"]["beta"],
            record["specification"]["linear_drag"],
            record["specification"]["viscosity"],
            record["specification"]["seed"],
        ): record
        for record in records
    }
    contrast_work: list[tuple[dict[str, Any], np.ndarray]] = []
    metric_specs = (
        ("final_window_mean_zonal_fraction", 0.05),
        ("persistent_jet", 0.50),
    )
    for beta in (1.25, 2.5, 5.0, 10.0):
        for metric, minimum_effect in metric_specs:
            paired_by_seed: dict[int, list[float]] = {}
            for (_, drag, viscosity, seed), beta_record in record_lookup.items():
                if beta_record["specification"]["beta"] != beta:
                    continue
                control = record_lookup[(0.0, drag, viscosity, seed)]
                difference = float(beta_record[metric]) - float(control[metric])
                paired_by_seed.setdefault(int(seed), []).append(difference)
            values = [value for seed_values in paired_by_seed.values() for value in seed_values]
            distribution = bootstrap_differences(
                paired_by_seed,
                seed=20260720 + round(100 * beta) + (1 if metric == "persistent_jet" else 0),
            )
            raw_p = exact_cluster_sign_flip_p(paired_by_seed)
            contrast_work.append(
                (
                    {
                        "metric": metric,
                        "beta": beta,
                        "control_beta": 0.0,
                        "cluster_count": len(paired_by_seed),
                        "cell_pair_count": len(values),
                        "effect_estimate": float(np.mean(values)),
                        "raw_p": float(raw_p),
                        "minimum_effect": minimum_effect,
                    },
                    distribution,
                )
            )
    ordered_indices = sorted(
        range(len(contrast_work)), key=lambda index: contrast_work[index][0]["raw_p"]
    )
    running_adjusted_p = 0.0
    for rank, index in enumerate(ordered_indices):
        record, distribution = contrast_work[index]
        remaining = len(contrast_work) - rank
        running_adjusted_p = max(running_adjusted_p, min(1.0, remaining * record["raw_p"]))
        record["holm_adjusted_p"] = running_adjusted_p
        simultaneous_alpha = 0.05 / len(contrast_work)
        record["familywise_ci_lower"] = float(np.quantile(distribution, simultaneous_alpha / 2.0))
        record["familywise_ci_upper"] = float(
            np.quantile(distribution, 1.0 - simultaneous_alpha / 2.0)
        )
        record["statistical_pass"] = (
            record["holm_adjusted_p"] < 0.05 and record["familywise_ci_lower"] > 0.0
        )
        record["minimum_effect_pass"] = record["effect_estimate"] >= record["minimum_effect"]
    return [record for record, _ in contrast_work]


def relative_change(left: float, right: float) -> float:
    """Return absolute relative change with a stable zero denominator."""
    return abs(left - right) / max(abs(right), 1e-15)


def build_refinement_checks(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Compare locked time-step and grid refinements for every beta-seed pair."""
    record_lookup = {
        (
            record["specification"]["beta"],
            record["specification"]["seed"],
            record["specification"]["grid_size"],
            record["specification"]["time_step"],
        ): record
        for record in records
    }
    checks: list[dict[str, Any]] = []
    for beta in (0.0, 5.0, 10.0):
        for seed in (11, 29, 47, 71):
            base = record_lookup[(beta, seed, 64, 0.005)]
            fine_time = record_lookup[(beta, seed, 64, 0.0025)]
            fine_grid = record_lookup[(beta, seed, 96, 0.0025)]
            metrics = (
                "final_energy",
                "final_enstrophy",
                "final_window_mean_zonal_fraction",
            )
            time_step_changes = {
                metric: relative_change(float(base[metric]), float(fine_time[metric]))
                for metric in metrics
            }
            grid_changes = {
                metric: relative_change(float(fine_time[metric]), float(fine_grid[metric]))
                for metric in metrics
            }
            jet_count_difference = abs(
                int(fine_time["final_window_modal_jet_count"])
                - int(fine_grid["final_window_modal_jet_count"])
            )
            checks.append(
                {
                    "beta": beta,
                    "seed": seed,
                    "time_step_relative_changes": time_step_changes,
                    "grid_relative_changes": grid_changes,
                    "refined_modal_jet_count_difference": jet_count_difference,
                    "time_step_passed": max(time_step_changes.values()) < 0.02,
                    "grid_passed": max(grid_changes.values()) < 0.05,
                    "jet_count_passed": jet_count_difference <= 1,
                }
            )
    return checks


def aggregate_payload(
    preregistration: dict[str, Any], profile: str, records: list[dict[str, Any]]
) -> dict[str, Any]:
    """Build the final sweep ledger and preregistered decision."""
    contrasts = build_primary_contrasts(records) if profile == "production" else []
    required = [contrast for contrast in contrasts if contrast["beta"] in {5.0, 10.0}]
    numerical_pass = all(
        all(
            np.isfinite(value)
            for value in record.values()
            if isinstance(value, int | float) and not isinstance(value, bool)
        )
        and abs(record["normalized_energy_budget_residual"]) <= 1e-6
        and abs(record["normalized_enstrophy_budget_residual"]) <= 1e-6
        for record in records
    )
    primary_pass = bool(required) and all(
        contrast["statistical_pass"] and contrast["minimum_effect_pass"] for contrast in required
    )
    refinement_checks = build_refinement_checks(records) if profile == "refinement" else []
    refinement_pass = bool(refinement_checks) and all(
        check["time_step_passed"] and check["grid_passed"] and check["jet_count_passed"]
        for check in refinement_checks
    )
    payload = {
        "schema_version": 1,
        "generator": "scripts/run_beta_plane_sweep.py",
        "profile": profile,
        "scientifically_admissible_profile": profile == "production",
        "preregistration_relpath": str(PREREGISTRATION_PATH.relative_to(REPO_ROOT)),
        "preregistration_sha256": sha256_file(PREREGISTRATION_PATH),
        "source_commit": source_commit(),
        "environment_lock_relpath": str(ENVIRONMENT_LOCK_PATH.relative_to(REPO_ROOT)),
        "environment_lock_sha256": sha256_file(ENVIRONMENT_LOCK_PATH),
        "run_count": len(records),
        "records": sorted(records, key=lambda record: record["run_id"]),
        "primary_contrasts": contrasts,
        "numerical_gate_passed": numerical_pass,
        "primary_hypothesis_passed": primary_pass,
        "aggregate_decision": (
            "primary_supported_pending_refinement_and_reproduction"
            if profile == "production" and numerical_pass and primary_pass
            else "not_supported"
            if profile == "production"
            else "refinement_complete"
            if profile == "refinement" and numerical_pass and refinement_pass
            else "refinement_failed"
            if profile == "refinement"
            else "smoke_only_not_admissible"
        ),
        "claim_scope": preregistration["claim_scope"],
    }
    if profile == "refinement":
        payload["refinement_checks"] = refinement_checks
        payload["refinement_gate_passed"] = refinement_pass
        payload["protocol_amendment_relpath"] = str(
            REFINEMENT_AMENDMENT_PATH.relative_to(REPO_ROOT)
        )
        payload["protocol_amendment_sha256"] = sha256_file(REFINEMENT_AMENDMENT_PATH)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--profile",
        choices=("smoke", "production", "refinement"),
        default="production",
    )
    parser.add_argument("--workers", type=int, default=max(1, min(8, os.cpu_count() or 1)))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--work-root", type=Path, default=DEFAULT_WORK_ROOT)
    parser.add_argument("--evidence-archive", type=Path)
    parser.add_argument("--require-empty-work-root", action="store_true")
    arguments = parser.parse_args()
    if arguments.workers < 1:
        parser.error("--workers must be positive")
    preregistration = json.loads(PREREGISTRATION_PATH.read_text(encoding="ascii"))
    specifications = build_run_specs(preregistration, arguments.profile)
    expected_count = preregistration["production_matrix"]["run_count"]
    if arguments.profile == "production" and len(specifications) != expected_count:
        raise ValueError(
            f"production matrix expanded to {len(specifications)}, expected {expected_count}"
        )
    if arguments.profile == "refinement":
        refinement_count = preregistration["refinement_matrix"]["run_count"]
        if len(specifications) != refinement_count:
            raise ValueError(
                f"refinement matrix expanded to {len(specifications)}, expected {refinement_count}"
            )
    work_root = arguments.work_root
    if not work_root.is_absolute():
        work_root = REPO_ROOT / work_root
    work_root = work_root / arguments.profile
    work_root_existed_before = work_root.exists()
    if arguments.require_empty_work_root and work_root_existed_before:
        raise FileExistsError(f"required empty work root already exists: {work_root}")
    binding = checkpoint_binding(arguments.profile)
    records: list[dict[str, Any]] = []
    pending: list[dict[str, Any]] = []
    for specification in specifications:
        checkpoint = load_checkpoint(specification, work_root, binding)
        if checkpoint is None:
            pending.append(specification)
        else:
            records.append(checkpoint)
    print(
        f"profile={arguments.profile} total={len(specifications)} "
        f"resumed={len(records)} pending={len(pending)} workers={arguments.workers}",
        flush=True,
    )
    with ProcessPoolExecutor(
        max_workers=arguments.workers,
        mp_context=multiprocessing.get_context("spawn"),
    ) as executor:
        future_to_specification = {
            executor.submit(execute_run, specification): specification for specification in pending
        }
        for future in as_completed(future_to_specification):
            completed_record = future.result()
            completed_record["checkpoint_binding"] = binding
            record = write_checkpoint(completed_record, work_root)
            records.append(record)
            print(
                f"completed={len(records)}/{len(specifications)} run_id={record['run_id']}",
                flush=True,
            )
    payload = aggregate_payload(preregistration, arguments.profile, records)
    payload["execution_receipt"] = {
        "fresh_execution_required": arguments.require_empty_work_root,
        "work_root_existed_before": work_root_existed_before,
        "resumed_count": len(records) - len(pending),
        "pending_count": len(pending),
        "total_count": len(specifications),
    }
    evidence_archive = arguments.evidence_archive
    if evidence_archive is None:
        evidence_archive = (
            EVIDENCE_ROOT / f"{arguments.profile}_run_arrays.tar"
            if arguments.profile in {"production", "refinement"}
            else work_root / "smoke_run_arrays.tar"
        )
    if not evidence_archive.is_absolute():
        evidence_archive = REPO_ROOT / evidence_archive
    payload["evidence_archive"] = write_evidence_archive(
        records, arguments.profile, evidence_archive, work_root
    )
    output_path = arguments.output
    if output_path is None:
        output_path = (
            DEFAULT_OUTPUT
            if arguments.profile == "production"
            else REPO_ROOT / "data/registry/beta_plane_refinement_results.json"
            if arguments.profile == "refinement"
            else work_root / "smoke_results.json"
        )
    if not output_path.is_absolute():
        output_path = REPO_ROOT / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="ascii",
    )
    print(
        f"Wrote {display_path(output_path)}: decision={payload['aggregate_decision']}",
        flush=True,
    )
    return 0 if payload["numerical_gate_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
