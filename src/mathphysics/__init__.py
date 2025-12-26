"""Mathematical Physics Experimental Framework.

A comprehensive Python framework for computational experiments validating
mathematical claims in theoretical physics.
"""

from __future__ import annotations

__version__ = "1.0.0"
__author__ = "Mathematical Physics Research"

# Import unified core modules
from .algebras import roots
from . import viz
from .algebras import cayley_dickson
from . import fractal_analysis
from . import modular_forms
from . import lattice_theory
from . import genesis_harmonics
from . import config
from . import data_handler
from . import accelerated_lbm

__all__ = [
    "roots",
    "viz",
    "cayley_dickson",
    "fractal_analysis",
    "modular_forms",
    "lattice_theory",
    "genesis_harmonics",
    "config",
    "data_handler",
    "accelerated_lbm",
]
