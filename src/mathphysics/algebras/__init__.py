"""Exceptional and Geometric Algebras Subpackage.

Provides unified implementations of Lie, Jordan, and Clifford algebras
optimized for SM89 compute.
"""

from ..algebras.roots import (
    E4RootSystem, E5RootSystem, E6RootSystem, E7RootSystem, E8RootSystem,
    E9RootSystem, E10RootSystem, E11RootSystem, ExceptionalLieAlgebras,
    LieAlgebraCalculator, E7Properties
)
from .jordan import AlbertAlgebraElement
from .clifford import Multivector, CliffordEngine
from .cayley_dickson import (
    Real, Complex, Quaternion, Octonion, Sedenion, Pathion,
    Chingon, Rouxion, Polyxon, run_comprehensive_validation
)

__all__ = [
    "E4RootSystem", "E5RootSystem", "E6RootSystem", "E7RootSystem", "E8RootSystem",
    "E9RootSystem", "E10RootSystem", "E11RootSystem", "ExceptionalLieAlgebras",
    "LieAlgebraCalculator", "E7Properties",
    "AlbertAlgebraElement",
    "Multivector", "CliffordEngine",
    "Real", "Complex", "Quaternion", "Octonion", "Sedenion", "Pathion",
    "Chingon", "Rouxion", "Polyxon", "run_comprehensive_validation"
]
