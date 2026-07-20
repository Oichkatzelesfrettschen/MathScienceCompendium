"""Pytest configuration and shared fixtures."""

from __future__ import annotations

import importlib
from pathlib import Path

import numpy as np
import pytest


def _qiskit_available() -> bool:
    return importlib.util.find_spec("qiskit") is not None


# Skip entire test files that unconditionally import qiskit at module level.
# pytest collect_ignore is evaluated before collection so it prevents ImportError.
if not _qiskit_available():
    _TESTS_DIR = Path(__file__).parent
    collect_ignore = [
        str(_TESTS_DIR / "test_quantum_modules.py"),
        str(_TESTS_DIR / "unit" / "test_e7quantumcircuits.py"),
        str(_TESTS_DIR / "unit" / "test_e8quantumcircuits.py"),
        str(_TESTS_DIR / "unit" / "test_integration.py"),
    ]


@pytest.fixture(autouse=True)
def seed_random():
    """Fix random seed for reproducible tests."""
    np.random.seed(42)
    yield
