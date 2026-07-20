"""Optional dependency handling for mathphysics package."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from types import ModuleType


# Track available optional dependencies
HAS_JAX = False
HAS_QISKIT = False
HAS_LIESYM = False
HAS_GUDHI = False
HAS_JAXLIE = False
HAS_PLOTLY = False

# Try importing JAX
jax: ModuleType | None
jnp: ModuleType | None
try:
    jax = importlib.import_module("jax")
    jnp = importlib.import_module("jax.numpy")

    HAS_JAX = True
except ImportError:
    jax = None
    jnp = None

# Try importing Qiskit
qiskit: ModuleType | None
try:
    qiskit = importlib.import_module("qiskit")

    HAS_QISKIT = True
except ImportError:
    qiskit = None

# Try importing liesym
liesym: ModuleType | None
try:
    liesym = importlib.import_module("liesym")

    HAS_LIESYM = True
except ImportError:
    liesym = None

# Try importing gudhi
gudhi: ModuleType | None
try:
    gudhi = importlib.import_module("gudhi")

    HAS_GUDHI = True
except ImportError:
    gudhi = None

# Try importing jaxlie
jaxlie: ModuleType | None
try:
    jaxlie = importlib.import_module("jaxlie")

    HAS_JAXLIE = True
except ImportError:
    jaxlie = None

# Try importing plotly
plotly: ModuleType | None
try:
    plotly = importlib.import_module("plotly")

    HAS_PLOTLY = True
except ImportError:
    plotly = None


def require_dependency(dep_name: str) -> None:
    """Raise ImportError if required dependency is not available.

    Args:
        dep_name: Name of the dependency (e.g., 'jax', 'qiskit')

    Raises:
        ImportError: If the dependency is not available
    """
    dep_map = {
        "jax": HAS_JAX,
        "qiskit": HAS_QISKIT,
        "liesym": HAS_LIESYM,
        "gudhi": HAS_GUDHI,
        "jaxlie": HAS_JAXLIE,
        "plotly": HAS_PLOTLY,
    }

    if dep_name not in dep_map:
        raise ValueError(f"Unknown dependency: {dep_name}")

    if not dep_map[dep_name]:
        install_map = {
            "jax": "pip install jax jaxlib",
            "qiskit": "pip install 'mathphysics-compendium[quantum]'",
            "liesym": "pip install 'mathphysics-compendium[topology]'",
            "gudhi": "pip install 'mathphysics-compendium[topology]'",
            "jaxlie": "pip install 'mathphysics-compendium[topology]'",
            "plotly": "pip install 'mathphysics-compendium[viz]'",
        }
        raise ImportError(
            f"Optional dependency '{dep_name}' is not installed. "
            f"Install with: {install_map[dep_name]}"
        )


def safe_import(module_name: str) -> Any | None:
    """Safely import a module, returning None if not available.

    Args:
        module_name: Full module name to import

    Returns:
        The imported module or None if import fails
    """
    try:
        return importlib.import_module(module_name)
    except ImportError:
        return None


__all__ = [
    "HAS_GUDHI",
    "HAS_JAX",
    "HAS_JAXLIE",
    "HAS_LIESYM",
    "HAS_PLOTLY",
    "HAS_QISKIT",
    "require_dependency",
    "safe_import",
]
