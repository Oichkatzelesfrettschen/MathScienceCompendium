"""Mathematical Physics Experimental Framework.

A comprehensive Python framework for computational experiments validating
mathematical claims in theoretical physics.
"""

__version__ = "1.0.0"
__author__ = "Mathematical Physics Research"

# Import core modules
from . import cayley_dickson
from . import fractal_analysis
from . import lie_algebras
from . import lattice_theory
from . import modular_forms
from . import visualization
from . import genesis_harmonics

__all__ = [
    "cayley_dickson",
    "fractal_analysis",
    "lie_algebras",
    "lattice_theory",
    "modular_forms",
    "visualization",
    "genesis_harmonics",
]