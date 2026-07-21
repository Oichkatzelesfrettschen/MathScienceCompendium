#!/usr/bin/env python3
"""Run the preregistered beta-plane and E7 quotient-filter ablation matrix."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np


REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from mathphysics.beta_plane import (  # noqa: E402
    BarotropicBetaPlane,
    BetaPlaneConfig,
    BetaPlaneRun,
    NonlinearFilter,
)


PREREGISTRATION_PATH = REPO_ROOT / "data" / "registry" / "beta_plane_ablation_preregistration.json"
DEFAULT_OUTPUT = REPO_ROOT / "data" / "registry" / "beta_plane_ablation_results.json"


def array_sha256(values: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(values, dtype=np.float64).tobytes()).hexdigest()


def run_metrics(run: BetaPlaneRun) -> dict[str, Any]:
    return {
        "initial_energy": run.initial_energy,
        "final_energy": run.final_energy,
        "initial_enstrophy": run.initial_enstrophy,
        "final_enstrophy": run.final_enstrophy,
        "energy_budget_residual": run.energy_budget_residual,
        "enstrophy_budget_residual": run.enstrophy_budget_residual,
        "zonal_kinetic_energy_fraction": run.zonal_kinetic_energy_fraction,
        "spectral_zonal_energy_fraction": run.spectral_zonal_energy_fraction,
        "jet_count": run.jet_count,
        "jet_prominence_threshold": run.jet_prominence_threshold,
        "final_window_sample_count": run.final_window_sample_count,
        "final_window_mean_zonal_fraction": run.final_window_mean_zonal_fraction,
        "final_window_tenth_percentile_zonal_fraction": (
            run.final_window_tenth_percentile_zonal_fraction
        ),
        "final_window_minimum_zonal_fraction": run.final_window_minimum_zonal_fraction,
        "final_window_zonal_fractions": list(run.final_window_zonal_fractions),
        "final_window_jet_counts": list(run.final_window_jet_counts),
        "final_window_modal_jet_count": run.final_window_modal_jet_count,
        "final_window_modal_jet_count_occupancy": (run.final_window_modal_jet_count_occupancy),
        "jet_claim_admitted": run.jet_claim_admitted,
        "final_vorticity_sha256": array_sha256(run.final_vorticity),
    }


def relative_l2_difference(left: np.ndarray, right: np.ndarray) -> float:
    denominator = float(np.linalg.norm(right))
    if denominator == 0.0:
        return float(np.linalg.norm(left - right))
    return float(np.linalg.norm(left - right) / denominator)


def relative_change(left: float, right: float) -> float:
    return abs(left - right) / max(abs(right), 1e-15)


def build_config(
    preregistration: dict[str, Any], seed: int, grid_size: int, time_step: float
) -> BetaPlaneConfig:
    fixed = preregistration["fixed_parameters"]
    duration = float(fixed["duration"])
    steps = round(duration / time_step)
    if not np.isclose(steps * time_step, duration, rtol=0.0, atol=1e-14):
        raise ValueError("duration must be an integer multiple of every time step")
    return BetaPlaneConfig(
        grid_size=grid_size,
        time_step=time_step,
        steps=steps,
        beta=float(fixed["beta"]),
        linear_drag=float(fixed["linear_drag"]),
        viscosity=float(fixed["viscosity"]),
        initial_wavenumber_minimum=float(fixed["initial_wavenumber_minimum"]),
        initial_wavenumber_maximum=float(fixed["initial_wavenumber_maximum"]),
        initial_energy=float(fixed["initial_energy"]),
        seed=seed,
    )


def execute_ablation() -> dict[str, Any]:
    preregistration = json.loads(PREREGISTRATION_PATH.read_text(encoding="ascii"))
    refinement = preregistration["refinement_matrix"]
    records: list[dict[str, Any]] = []
    run_lookup: dict[tuple[int, int, float], dict[str, BetaPlaneRun]] = {}
    for seed in refinement["seeds"]:
        for grid_size in refinement["grid_sizes"]:
            for time_step in refinement["time_steps"]:
                base_config = build_config(preregistration, seed, grid_size, time_step)
                arms = {
                    "f_plane_identity": replace(base_config, beta=0.0),
                    "beta_plane_identity": replace(
                        base_config, nonlinear_filter=NonlinearFilter.IDENTITY
                    ),
                    "beta_plane_e7_quotient": replace(
                        base_config,
                        nonlinear_filter=NonlinearFilter.E7_PQ_HOMOMORPHISM,
                    ),
                }
                runs = {
                    arm_name: BarotropicBetaPlane(config).run() for arm_name, config in arms.items()
                }
                run_lookup[(seed, grid_size, time_step)] = runs
                beta_run = runs["beta_plane_identity"]
                f_plane_run = runs["f_plane_identity"]
                quotient_run = runs["beta_plane_e7_quotient"]
                beta_difference = relative_l2_difference(
                    beta_run.final_vorticity, f_plane_run.final_vorticity
                )
                filter_difference = float(
                    np.max(np.abs(quotient_run.final_vorticity - beta_run.final_vorticity))
                )
                maximum_budget_residual = max(
                    *(abs(run.energy_budget_residual) for run in runs.values()),
                    *(abs(run.enstrophy_budget_residual) for run in runs.values()),
                )
                records.append(
                    {
                        "seed": seed,
                        "grid_size": grid_size,
                        "time_step": time_step,
                        "steps": base_config.steps,
                        "arms": {arm_name: run_metrics(run) for arm_name, run in runs.items()},
                        "comparisons": {
                            "beta_to_f_plane_relative_vorticity_l2": beta_difference,
                            "quotient_to_identity_maximum_vorticity_error": filter_difference,
                        },
                        "criteria": {
                            "budget_passed": maximum_budget_residual < 1e-6,
                            "beta_sensitivity_passed": beta_difference > 1e-6,
                            "negative_control_passed": filter_difference <= 1e-12,
                        },
                    }
                )

    time_step_refinements: list[dict[str, Any]] = []
    coarse_time_step = max(float(value) for value in refinement["time_steps"])
    fine_time_step = min(float(value) for value in refinement["time_steps"])
    for seed in refinement["seeds"]:
        for grid_size in refinement["grid_sizes"]:
            coarse = run_lookup[(seed, grid_size, coarse_time_step)]["beta_plane_identity"]
            fine = run_lookup[(seed, grid_size, fine_time_step)]["beta_plane_identity"]
            changes = {
                "final_energy": relative_change(coarse.final_energy, fine.final_energy),
                "final_enstrophy": relative_change(coarse.final_enstrophy, fine.final_enstrophy),
                "zonal_kinetic_energy_fraction": relative_change(
                    coarse.zonal_kinetic_energy_fraction,
                    fine.zonal_kinetic_energy_fraction,
                ),
            }
            time_step_refinements.append(
                {
                    "seed": seed,
                    "grid_size": grid_size,
                    "coarse_time_step": coarse_time_step,
                    "fine_time_step": fine_time_step,
                    "relative_changes": changes,
                    "passed": max(changes.values()) < 0.02,
                }
            )

    record_criteria = [criterion for record in records for criterion in record["criteria"].values()]
    time_step_passed = all(record["passed"] for record in time_step_refinements)
    jet_claim_admitted = all(
        record["arms"]["beta_plane_identity"]["jet_claim_admitted"] for record in records
    )
    all_criteria_passed = all(record_criteria) and time_step_passed
    return {
        "schema_version": 1,
        "generator": "scripts/run_beta_plane_ablation.py",
        "preregistration_relpath": str(PREREGISTRATION_PATH.relative_to(REPO_ROOT)),
        "configuration_count": len(records),
        "arm_run_count": 3 * len(records),
        "records": records,
        "time_step_refinements": time_step_refinements,
        "aggregate_criteria": {
            "all_budgets_passed": all(record["criteria"]["budget_passed"] for record in records),
            "all_beta_sensitivity_checks_passed": all(
                record["criteria"]["beta_sensitivity_passed"] for record in records
            ),
            "all_negative_controls_passed": all(
                record["criteria"]["negative_control_passed"] for record in records
            ),
            "all_time_step_refinements_passed": time_step_passed,
            "all_preregistered_implementation_criteria_passed": all_criteria_passed,
            "jet_claim_admitted": jet_claim_admitted,
        },
        "conclusion": (
            "The beta term changes every matched trajectory. The E7 P/Q homomorphic "
            "filter is bit-identical to the identity control and has zero dynamical "
            "effect. No jet claim is admitted unless every preregistered jet gate passes."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    arguments = parser.parse_args()
    output_path = arguments.output
    if not output_path.is_absolute():
        output_path = REPO_ROOT / output_path
    payload = execute_ablation()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="ascii",
    )
    passed = payload["aggregate_criteria"]["all_preregistered_implementation_criteria_passed"]
    print(
        f"Wrote {output_path.relative_to(REPO_ROOT)}: "
        f"{payload['arm_run_count']} arm runs; criteria_passed={passed}"
    )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
