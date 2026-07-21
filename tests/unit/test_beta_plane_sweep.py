"""Tests for the preregistered beta-plane production sweep runner."""

from __future__ import annotations

import json
import subprocess
import sys
import tarfile
from pathlib import Path

import numpy as np
from scripts.run_beta_plane_sweep import (
    PREREGISTRATION_PATH,
    aggregate_payload,
    build_primary_contrasts,
    build_refinement_checks,
    build_run_specs,
    checkpoint_binding,
    display_path,
    exact_cluster_sign_flip_p,
    load_checkpoint,
    run_id,
    shared_refinement_initial_vorticity,
    write_checkpoint,
)

from mathphysics.beta_plane import BarotropicBetaPlane, BetaPlaneConfig


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_production_matrix_has_preregistered_cardinality():
    preregistration = json.loads(PREREGISTRATION_PATH.read_text(encoding="ascii"))
    specifications = build_run_specs(preregistration, "production")
    assert len(specifications) == 540
    assert len({run_id(specification) for specification in specifications}) == 540


def test_smoke_matrix_is_explicitly_nonadmissible():
    preregistration = json.loads(PREREGISTRATION_PATH.read_text(encoding="ascii"))
    specifications = build_run_specs(preregistration, "smoke")
    assert len(specifications) == 4


def test_checkpoint_supports_work_root_outside_repository(tmp_path):
    preregistration = json.loads(PREREGISTRATION_PATH.read_text(encoding="ascii"))
    specification = build_run_specs(preregistration, "smoke")[0]
    record = {
        "run_id": run_id(specification),
        "specification": specification,
        "final_vorticity": np.asarray([[0.0, 1.0], [1.0, 0.0]], dtype=np.float64),
        "final_window_zonal_fractions": [0.1, 0.2],
        "final_window_jet_counts": [2, 2],
    }
    binding = checkpoint_binding("smoke")
    record["checkpoint_binding"] = binding
    checkpoint = write_checkpoint(record, tmp_path)
    assert "arrays_relpath" not in checkpoint
    assert load_checkpoint(specification, tmp_path, binding) == checkpoint
    stale_binding = {**binding, "source_commit": "0" * 40}
    assert load_checkpoint(specification, tmp_path, stale_binding) is None
    assert display_path(tmp_path / "result.json") == tmp_path / "result.json"


def test_smoke_cli_enforces_fresh_external_work_root(tmp_path):
    work_root = tmp_path / "checkpoints"
    result_path = tmp_path / "smoke_results.json"
    archive_path = tmp_path / "smoke_arrays.tar"
    command = [
        sys.executable,
        "scripts/run_beta_plane_sweep.py",
        "--profile",
        "smoke",
        "--workers",
        "2",
        "--work-root",
        str(work_root),
        "--require-empty-work-root",
        "--output",
        str(result_path),
        "--evidence-archive",
        str(archive_path),
    ]
    completed = subprocess.run(command, cwd=REPO_ROOT, check=False, capture_output=True)
    assert completed.returncode == 0, completed.stderr.decode("utf-8", errors="replace")
    payload = json.loads(result_path.read_text(encoding="ascii"))
    assert payload["execution_receipt"] == {
        "fresh_execution_required": True,
        "work_root_existed_before": False,
        "resumed_count": 0,
        "pending_count": 4,
        "total_count": 4,
    }
    with tarfile.open(archive_path, mode="r:") as archive:
        assert len(archive.getmembers()) == 4
    repeated = subprocess.run(command, cwd=REPO_ROOT, check=False, capture_output=True)
    assert repeated.returncode != 0
    assert b"required empty work root already exists" in repeated.stderr


def test_refinement_matrix_has_preregistered_cardinality():
    preregistration = json.loads(PREREGISTRATION_PATH.read_text(encoding="ascii"))
    specifications = build_run_specs(preregistration, "refinement")
    assert len(specifications) == 48
    assert len({run_id(specification) for specification in specifications}) == 48
    assert {specification["initial_condition_protocol"] for specification in specifications} == {
        "shared_n64_fourier_embedding"
    }


def test_refinement_embedding_preserves_active_modes_and_energy():
    base = BetaPlaneConfig(grid_size=64, seed=29)
    refined = BetaPlaneConfig(grid_size=96, seed=29)
    base_hat = shared_refinement_initial_vorticity(base)
    refined_hat = shared_refinement_initial_vorticity(refined)
    base_solver = BarotropicBetaPlane(base)
    refined_solver = BarotropicBetaPlane(refined)
    assert abs(base_solver.kinetic_energy(base_hat) - base.initial_energy) <= 1e-14
    assert abs(refined_solver.kinetic_energy(refined_hat) - refined.initial_energy) <= 1e-14
    for wavenumber_x in range(-6, 7):
        for wavenumber_y in range(-6, 7):
            base_value = base_hat[wavenumber_x % 64, wavenumber_y % 64] / (64**2)
            refined_value = refined_hat[wavenumber_x % 96, wavenumber_y % 96] / (96**2)
            assert abs(base_value - refined_value) <= 1e-14


def test_smoke_aggregate_cannot_support_hypothesis():
    preregistration = json.loads(PREREGISTRATION_PATH.read_text(encoding="ascii"))
    record = {
        "run_id": "smoke",
        "final_energy": 0.01,
        "final_enstrophy": 0.1,
        "final_window_mean_zonal_fraction": 1.0,
        "rms_speed": 0.1,
        "energy_budget_residual": 0.0,
        "enstrophy_budget_residual": 0.0,
        "normalized_energy_budget_residual": 0.0,
        "normalized_enstrophy_budget_residual": 0.0,
    }
    payload = aggregate_payload(preregistration, "smoke", [record])
    assert payload["numerical_gate_passed"]
    assert payload["primary_hypothesis_passed"] is False
    assert payload["aggregate_decision"] == "smoke_only_not_admissible"


def test_exact_cluster_sign_flip_p_uses_seed_clusters():
    all_positive = {seed: [1.0, 2.0] for seed in range(12)}
    balanced = {seed: [1.0 if seed % 2 == 0 else -1.0] for seed in range(12)}
    assert exact_cluster_sign_flip_p(all_positive) == 2.0 / (2**12)
    assert exact_cluster_sign_flip_p(balanced) == 1.0


def test_primary_contrasts_are_exactly_invariant_to_completion_order():
    records = []
    contrast_values = {0.01: 1e16, 0.02: -1e16, 0.05: 1.0}
    for beta in (0.0, 1.25, 2.5, 5.0, 10.0):
        for linear_drag in sorted(contrast_values):
            for seed in (11, 29):
                value = 0.0 if beta == 0.0 else contrast_values[linear_drag]
                records.append(
                    {
                        "specification": {
                            "beta": beta,
                            "linear_drag": linear_drag,
                            "viscosity": 0.0005,
                            "seed": seed,
                        },
                        "final_window_mean_zonal_fraction": value,
                        "persistent_jet": value,
                    }
                )
    assert build_primary_contrasts(records) == build_primary_contrasts(list(reversed(records)))


def test_refinement_check_enforces_locked_thresholds():
    records = []
    for beta in (0.0, 5.0, 10.0):
        for seed in (11, 29, 47, 71):
            for grid_size in (64, 96):
                for time_step in (0.005, 0.0025):
                    records.append(
                        {
                            "specification": {
                                "beta": beta,
                                "seed": seed,
                                "grid_size": grid_size,
                                "time_step": time_step,
                            },
                            "final_energy": 1.0,
                            "final_enstrophy": 1.0,
                            "final_window_mean_zonal_fraction": 0.2,
                            "final_window_modal_jet_count": 2,
                        }
                    )
    checks = build_refinement_checks(records)
    assert len(checks) == 12
    assert all(check["time_step_passed"] for check in checks)
    assert all(check["grid_passed"] for check in checks)
    assert all(check["jet_count_passed"] for check in checks)
