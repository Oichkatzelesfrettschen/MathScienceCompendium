#!/usr/bin/env python3
"""Generate reproducible diagnostics for retained high-resolution LBM states."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from mathphysics.diagnostics import calculate_vorticity


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_RESULTS_GLOB = "results/highres_lbm_*.parquet"
DEFAULT_OUTPUT = REPO_ROOT / "data" / "registry" / "lbm_evidence_audit.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as input_file:
        for chunk in iter(lambda: input_file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def analyze_arrays(
    density: np.ndarray, velocity_x: np.ndarray, velocity_y: np.ndarray
) -> dict[str, Any]:
    """Compute mass, speed, zonal-flow, and spectral-anisotropy diagnostics."""
    if density.shape != velocity_x.shape or density.shape != velocity_y.shape:
        raise ValueError("density and velocity arrays must have identical shapes")
    if density.ndim != 2:
        raise ValueError("retained LBM arrays must be two-dimensional")

    speed = np.sqrt(velocity_x * velocity_x + velocity_y * velocity_y)
    zonal_mean_velocity = np.mean(velocity_x, axis=0)
    zonal_anomaly = zonal_mean_velocity - np.mean(zonal_mean_velocity)
    zonal_spectrum = np.abs(np.fft.rfft(zonal_anomaly)) ** 2
    dominant_zonal_mode = int(np.argmax(zonal_spectrum[1:]) + 1) if zonal_spectrum.size > 1 else 0

    velocity = np.stack((velocity_x, velocity_y), axis=-1)
    vorticity = calculate_vorticity(velocity)
    vorticity_power = np.abs(np.fft.fft2(vorticity)) ** 2
    x_wavenumbers = np.fft.fftfreq(density.shape[0])[:, np.newaxis]
    y_wavenumbers = np.fft.fftfreq(density.shape[1])[np.newaxis, :]
    x_second_moment = float(np.sum((x_wavenumbers**2) * vorticity_power))
    y_second_moment = float(np.sum((y_wavenumbers**2) * vorticity_power))
    anisotropy_ratio = x_second_moment / y_second_moment if y_second_moment > 0.0 else None

    speed_rms = float(np.sqrt(np.mean(speed * speed)))
    zonal_rms = float(np.sqrt(np.mean(zonal_anomaly * zonal_anomaly)))
    return {
        "grid_shape": list(density.shape),
        "mass": float(np.sum(density)),
        "nominal_initial_mass": int(density.size),
        "relative_mass_drift_from_unit_density": float(
            abs(np.sum(density) - density.size) / density.size
        ),
        "mean_speed": float(np.mean(speed)),
        "rms_speed": speed_rms,
        "maximum_speed": float(np.max(speed)),
        "dominant_zonal_mode": dominant_zonal_mode,
        "zonal_mean_rms": zonal_rms,
        "zonal_to_total_rms_ratio": zonal_rms / speed_rms if speed_rms > 0.0 else None,
        "vorticity_spectral_second_moment_ratio_x_to_y": anisotropy_ratio,
    }


def analyze_snapshot(path: Path) -> dict[str, Any]:
    frame = pd.read_parquet(path)
    if len(frame) != 1:
        raise ValueError(f"expected one retained state row in {path}, found {len(frame)}")
    row = frame.iloc[0]
    diagnostics = analyze_arrays(
        np.stack(row["density"]).astype(np.float64),
        np.stack(row["velocity_x"]).astype(np.float64),
        np.stack(row["velocity_y"]).astype(np.float64),
    )
    return {
        "source_relpath": path.relative_to(REPO_ROOT).as_posix(),
        "source_sha256": sha256_file(path),
        "iteration": int(row["iteration"]),
        **diagnostics,
    }


def render_snapshot_figures(path: Path, figure_root: Path) -> None:
    """Regenerate vorticity figures from one retained snapshot."""
    import matplotlib.pyplot as plt  # noqa: PLC0415

    frame = pd.read_parquet(path)
    if len(frame) != 1:
        raise ValueError(f"expected one retained state row in {path}, found {len(frame)}")
    row = frame.iloc[0]
    velocity = np.stack(
        (
            np.stack(row["velocity_x"]).astype(np.float64),
            np.stack(row["velocity_y"]).astype(np.float64),
        ),
        axis=-1,
    )
    vorticity = calculate_vorticity(velocity)
    vorticity_power = np.abs(np.fft.fft2(vorticity)) ** 2
    iteration = int(row["iteration"])
    source_digest = sha256_file(path)[:12]
    figure_root.mkdir(parents=True, exist_ok=True)

    figure, axis = plt.subplots(figsize=(10, 8))
    image = axis.imshow(vorticity, cmap="RdBu_r", origin="lower")
    figure.colorbar(image, ax=axis, label="Scalar vorticity")
    axis.set_title(f"Retained LBM vorticity, step {iteration}")
    axis.set_xlabel("y index")
    axis.set_ylabel("x index")
    figure.text(0.01, 0.01, f"source SHA-256 prefix: {source_digest}", fontsize=7)
    figure.savefig(figure_root / "vorticity_map_highres.png", dpi=180, bbox_inches="tight")
    plt.close(figure)

    figure, axis = plt.subplots(figsize=(10, 7))
    image = axis.imshow(
        np.log10(np.fft.fftshift(vorticity_power) + 1e-30),
        cmap="viridis",
        origin="lower",
    )
    figure.colorbar(image, ax=axis, label="log10 vorticity power")
    axis.set_title(f"Retained LBM vorticity spectrum, step {iteration}")
    axis.set_xlabel("shifted y mode")
    axis.set_ylabel("shifted x mode")
    figure.text(0.01, 0.01, f"source SHA-256 prefix: {source_digest}", fontsize=7)
    figure.savefig(figure_root / "vorticity_psd_highres.png", dpi=180, bbox_inches="tight")
    plt.close(figure)


def build_audit(pattern: str) -> dict[str, Any]:
    snapshots = [analyze_snapshot(path) for path in sorted(REPO_ROOT.glob(pattern))]
    return {
        "schema_version": 1,
        "generator": "scripts/analyze_retained_lbm.py",
        "method": {
            "zonal_profile": "mean x-velocity over axis 0, then remove profile mean",
            "dominant_mode": "largest nonzero real-FFT power of zonal profile",
            "coordinate_convention": "axis 0 is x; axis 1 is y",
            "vorticity": "gradient(velocity_y, axis=0) - gradient(velocity_x, axis=1)",
            "anisotropy": "vorticity-power second moment in x divided by y",
        },
        "snapshot_count": len(snapshots),
        "snapshots": snapshots,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pattern", default=DEFAULT_RESULTS_GLOB)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--figure-root",
        type=Path,
        help="Regenerate final-state vorticity figures in this directory.",
    )
    arguments = parser.parse_args()

    output_path = arguments.output
    if not output_path.is_absolute():
        output_path = REPO_ROOT / output_path
    audit = build_audit(arguments.pattern)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(audit, indent=2, sort_keys=True, allow_nan=False, ensure_ascii=True) + "\n",
        encoding="ascii",
    )
    print(f"Wrote {output_path.relative_to(REPO_ROOT)} ({audit['snapshot_count']} snapshots)")
    if arguments.figure_root is not None:
        figure_root = arguments.figure_root
        if not figure_root.is_absolute():
            figure_root = REPO_ROOT / figure_root
        snapshot_paths = sorted(REPO_ROOT.glob(arguments.pattern))
        if not snapshot_paths:
            raise ValueError(f"no snapshots match {arguments.pattern}")
        render_snapshot_figures(snapshot_paths[-1], figure_root)
        print(f"Wrote vorticity figures under {figure_root.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
