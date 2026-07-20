"""Unit tests for quantum_simulation.py (UnifiedSimulation).

quantum_simulation.py performs bare `from qiskit import ...` at module level,
so every test that touches it uses pytest.importorskip to skip cleanly when
Qiskit is absent.

Covered surfaces:
- Module imports successfully when Qiskit is present
- UnifiedSimulation constructs with default and custom n_qubits
- UnifiedSimulation has expected attributes after construction
- run_experiment returns dict with required keys
- run_experiment 'e8_search' experiment type
- run_experiment 'counts' value is non-empty dict
- run_experiment 'top_measurement' is a string
- save_results writes JSON to the given path (uses tmp_path)
- save_results output is valid JSON
- save_results output round-trips through json.loads
- save_results does not clobber existing file content (overwrites intentionally)
- Config.RESULTS_DIR is used as default save location
- run_production_simulation executes without raising
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest


# ---------------------------------------------------------------------------
# Module import guard
# ---------------------------------------------------------------------------


qiskit = pytest.importorskip("qiskit", reason="Qiskit required for quantum_simulation tests")


# Re-import with Qiskit confirmed present
from mathphysics.config import Config  # noqa: E402
from mathphysics.quantum_simulation import (  # noqa: E402
    UnifiedSimulation,
    run_production_simulation,
)


if TYPE_CHECKING:
    from pathlib import Path


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


def test_unified_simulation_default_n_qubits():
    sim = UnifiedSimulation()
    assert sim.n_qubits == 8


def test_unified_simulation_custom_n_qubits():
    sim = UnifiedSimulation(n_qubits=4)
    assert sim.n_qubits == 4


def test_unified_simulation_has_backend():
    sim = UnifiedSimulation()
    assert sim.backend is not None


def test_unified_simulation_has_encoder():
    sim = UnifiedSimulation()
    assert sim.encoder is not None


def test_unified_simulation_has_algorithms_e8():
    sim = UnifiedSimulation()
    assert sim.algorithms_e8 is not None


def test_unified_simulation_has_algorithms_e7():
    sim = UnifiedSimulation()
    assert sim.algorithms_e7 is not None


def test_unified_simulation_has_analysis_e8():
    sim = UnifiedSimulation()
    assert sim.analysis_e8 is not None


def test_unified_simulation_has_decoder_e7():
    sim = UnifiedSimulation()
    assert sim.decoder_e7 is not None


def test_unified_simulation_has_config():
    sim = UnifiedSimulation()
    assert sim.config is not None


# ---------------------------------------------------------------------------
# run_experiment
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def sim_result() -> dict:
    """Run a single experiment and cache the result for all tests in module."""
    sim = UnifiedSimulation()
    return sim.run_experiment("e8_search")


def test_run_experiment_returns_dict(sim_result: dict):
    assert isinstance(sim_result, dict)


def test_run_experiment_has_experiment_key(sim_result: dict):
    assert "experiment" in sim_result


def test_run_experiment_has_counts_key(sim_result: dict):
    assert "counts" in sim_result


def test_run_experiment_has_top_measurement_key(sim_result: dict):
    assert "top_measurement" in sim_result


def test_run_experiment_experiment_value_matches_arg(sim_result: dict):
    assert sim_result["experiment"] == "e8_search"


def test_run_experiment_counts_is_non_empty_dict(sim_result: dict):
    assert isinstance(sim_result["counts"], dict)
    assert len(sim_result["counts"]) > 0


def test_run_experiment_top_measurement_is_string(sim_result: dict):
    assert isinstance(sim_result["top_measurement"], str)


def test_run_experiment_top_measurement_in_counts(sim_result: dict):
    top = sim_result["top_measurement"]
    assert top in sim_result["counts"]


def test_run_experiment_counts_values_are_positive_ints(sim_result: dict):
    for v in sim_result["counts"].values():
        assert isinstance(v, int)
        assert v > 0


# ---------------------------------------------------------------------------
# save_results
# ---------------------------------------------------------------------------


def test_save_results_creates_file(tmp_path: Path):
    sim = UnifiedSimulation()
    # Override RESULTS_DIR on the config instance to use tmp_path
    sim.config.RESULTS_DIR = tmp_path
    payload = {"experiment": "test", "counts": {"00": 512, "11": 512}}
    sim.save_results(payload, "test_output.json")
    assert (tmp_path / "test_output.json").exists()


def test_save_results_file_is_valid_json(tmp_path: Path):
    sim = UnifiedSimulation()
    sim.config.RESULTS_DIR = tmp_path
    payload = {"experiment": "json_check", "counts": {"0": 100}}
    sim.save_results(payload, "json_check.json")
    content = (tmp_path / "json_check.json").read_text()
    parsed = json.loads(content)
    assert isinstance(parsed, dict)


def test_save_results_round_trips_data(tmp_path: Path):
    sim = UnifiedSimulation()
    sim.config.RESULTS_DIR = tmp_path
    payload = {"x": 42, "nested": {"a": [1, 2, 3]}}
    sim.save_results(payload, "roundtrip.json")
    parsed = json.loads((tmp_path / "roundtrip.json").read_text())
    assert parsed["x"] == 42
    assert parsed["nested"]["a"] == [1, 2, 3]


def test_save_results_overwrites_on_second_call(tmp_path: Path):
    sim = UnifiedSimulation()
    sim.config.RESULTS_DIR = tmp_path
    sim.save_results({"v": 1}, "overwrite.json")
    sim.save_results({"v": 2}, "overwrite.json")
    parsed = json.loads((tmp_path / "overwrite.json").read_text())
    assert parsed["v"] == 2


def test_save_results_uses_results_dir(tmp_path: Path):
    # Confirm the file is placed under RESULTS_DIR, not cwd
    sim = UnifiedSimulation()
    sim.config.RESULTS_DIR = tmp_path
    sim.save_results({"check": True}, "location_check.json")
    assert (tmp_path / "location_check.json").is_file()


# ---------------------------------------------------------------------------
# run_production_simulation (smoke test)
# ---------------------------------------------------------------------------


def test_run_production_simulation_does_not_raise(tmp_path: Path):
    """run_production_simulation writes to Config.RESULTS_DIR; redirect via env."""

    original = Config.RESULTS_DIR
    try:
        Config.RESULTS_DIR = tmp_path
        # Patch the module-level sim's config as well
        run_production_simulation()
    finally:
        Config.RESULTS_DIR = original
