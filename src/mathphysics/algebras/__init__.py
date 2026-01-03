"""Exceptional and Geometric Algebras Subpackage.

Provides unified implementations of Lie, Jordan, and Clifford algebras
optimized for SM89 compute.
"""

from ..algebras.roots import (
    E4RootSystem,
    E5RootSystem,
    E6RootSystem,
    E7Properties,
    E7RootSystem,
    E8RootSystem,
    E9RootSystem,
    E10RootSystem,
    E11RootSystem,
    ExceptionalLieAlgebras,
    LieAlgebraCalculator,
)
from .cayley_dickson import (
    Chingon,
    Complex,
    Octonion,
    Pathion,
    Polyxon,
    Quaternion,
    Real,
    Rouxion,
    Sedenion,
    run_comprehensive_validation,
)
from .clifford import CliffordEngine, Multivector
from .jordan import AlbertAlgebraElement


__all__ = [
    "AlbertAlgebraElement",
    "Chingon",
    "CliffordEngine",
    "Complex",
    "E4RootSystem",
    "E5RootSystem",
    "E6RootSystem",
    "E7Properties",
    "E7RootSystem",
    "E8RootSystem",
    "E9RootSystem",
    "E10RootSystem",
    "E11RootSystem",
    "ExceptionalLieAlgebras",
    "LieAlgebraCalculator",
    "Multivector",
    "Octonion",
    "Pathion",
    "Polyxon",
    "Quaternion",
    "Real",
    "Rouxion",
    "Sedenion",
    "run_comprehensive_validation",
]
