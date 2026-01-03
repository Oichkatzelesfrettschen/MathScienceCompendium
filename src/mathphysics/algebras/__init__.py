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

# Optional modules requiring JAX
_optional_exports = []

try:
    from .clifford import CliffordEngine, Multivector

    _optional_exports.extend(["CliffordEngine", "Multivector"])
except ImportError:
    pass

try:
    from .jordan import AlbertAlgebraElement

    _optional_exports.append("AlbertAlgebraElement")
except ImportError:
    pass


__all__ = [
    "Chingon",
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
    "Octonion",
    "Pathion",
    "Polyxon",
    "Quaternion",
    "Real",
    "Rouxion",
    "Sedenion",
    "run_comprehensive_validation",
] + _optional_exports

