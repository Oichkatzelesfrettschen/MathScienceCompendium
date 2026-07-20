"""Configuration management for the Mathematical Physics Experimental Framework.

This module handles path resolution and configuration settings, eliminating hardcoded paths.
"""

import os
from pathlib import Path


# Base project directory (assuming this file is in src/mathphysics/config.py)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Data directories
DATA_DIR = Path(os.environ.get("MATHPHYSICS_DATA_DIR", str(PROJECT_ROOT / "data")))
RESULTS_DIR = Path(os.environ.get("MATHPHYSICS_RESULTS_DIR", str(PROJECT_ROOT / "results")))
FIGURES_DIR = Path(os.environ.get("MATHPHYSICS_FIGURES_DIR", str(PROJECT_ROOT / "figures")))

# Ensure directories exist
for directory in [DATA_DIR, RESULTS_DIR, FIGURES_DIR]:
    directory.mkdir(parents=True, exist_ok=True)


class Config:
    """Global configuration."""

    PROJECT_ROOT = PROJECT_ROOT
    DATA_DIR = DATA_DIR
    RESULTS_DIR = RESULTS_DIR
    FIGURES_DIR = FIGURES_DIR

    @staticmethod
    def get_data_path(filename: str) -> Path:
        """Get path for a data file."""
        return Path(Config.DATA_DIR) / filename

    @staticmethod
    def get_results_path(filename: str) -> Path:
        """Get path for a results file."""
        return Path(Config.RESULTS_DIR) / filename

    @staticmethod
    def get_figure_path(filename: str) -> Path:
        """Get path for a figure file."""
        return Path(Config.FIGURES_DIR) / filename

    @staticmethod
    def get_jax_backend():
        """Get the active JAX backend using modern jax.extend API."""
        try:
            import jax.extend  # noqa: PLC0415

            return jax.extend.backend.get_backend()
        except (ImportError, AttributeError):
            import jax.lib.xla_bridge as xb  # noqa: PLC0415

            return xb.get_backend()
