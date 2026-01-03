"""Mathematical Physics Experimental Framework.

A comprehensive Python framework for computational experiments validating
mathematical claims in theoretical physics.
"""

from __future__ import annotations


__version__ = "1.0.0"
__author__ = "Mathematical Physics Research"

# Import unified core modules
from . import (
    accelerated_lbm,
    config,
    data_handler,
    fractal_analysis,
    genesis_harmonics,
    lattice_theory,
    modular_forms,
    viz,
)
from .algebras import cayley_dickson, roots


__all__ = [
    "accelerated_lbm",
    "cayley_dickson",
    "config",
    "data_handler",
    "fractal_analysis",
    "genesis_harmonics",
    "lattice_theory",
    "modular_forms",
    "roots",
    "viz",
]
