"""Mathematical Physics Experimental Framework.

A comprehensive Python framework for computational experiments validating
mathematical claims in theoretical physics.
"""

from __future__ import annotations


__version__ = "1.0.0"
__author__ = "Mathematical Physics Research"

# Import optional dependency tracking first
from . import optional_deps

# Import unified core modules (these should have minimal dependencies)
from . import (
    config,
    data_handler,
    fractal_analysis,
    lattice_theory,
    modular_forms,
    viz,
)
from .algebras import cayley_dickson, roots

# Optional modules that may require extra dependencies
_optional_modules = []

# Try to import modules with optional dependencies
try:
    from . import accelerated_lbm

    _optional_modules.append("accelerated_lbm")
except ImportError:
    accelerated_lbm = None  # type: ignore

try:
    from . import genesis_harmonics

    _optional_modules.append("genesis_harmonics")
except ImportError:
    genesis_harmonics = None  # type: ignore


__all__ = [
    "cayley_dickson",
    "config",
    "data_handler",
    "fractal_analysis",
    "lattice_theory",
    "modular_forms",
    "optional_deps",
    "roots",
    "viz",
] + _optional_modules

